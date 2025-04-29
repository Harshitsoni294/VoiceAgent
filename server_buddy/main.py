import os
import asyncio
import shutil
from typing import List, Dict, Any
from datetime import datetime
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_community.embeddings import FakeEmbeddings
from langchain_core.documents import Document
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage

# Load environment variables
load_dotenv()

# Disable ChromaDB telemetry to avoid warnings
os.environ["ANONYMIZED_TELEMETRY"] = "False"

app = FastAPI(title="Buddy - Your Friendly AI Assistant")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatMessage(BaseModel):
    text: str
    user_id: str  # Add user_id for session management

class ChatResponse(BaseModel):
    answer: str
    context_used: List[str] = []

# Initialize components
class BuddyRAG:
    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        # Initialize LLM
        # Try different Gemini models in order of preference
        # Based on current API limitations and availability
        model_options = [
            "gemini-2.0-flash-exp",      # Latest experimental model
            "gemini-1.5-flash",          # Most stable option
            "gemini-1.5-pro",            # If available in project
            "gemini-pro",                # Legacy fallback
            "models/gemini-1.5-flash",   # Alternative naming
        ]
        
        self.llm = None
        self.current_model = None
        
        for model_name in model_options:
            try:
                # Test the model with a simple initialization
                test_llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=self.google_api_key,
                    temperature=0.7,
                    max_retries=1,  # Reduce retries for faster failover
                    request_timeout=10  # 10 second timeout
                )
                
                # Test with a simple prompt to verify it works
                # (We'll do this lazily during first actual use)
                self.llm = test_llm
                self.current_model = model_name
                print(f"✅ Successfully initialized Buddy with model: {model_name}")
                break
                
            except Exception as e:
                print(f"❌ Failed to initialize model {model_name}: {str(e)[:100]}...")
                continue
        
        if not self.llm:
            print("⚠️ Warning: All Gemini models failed to initialize. Using fallback configuration.")
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=self.google_api_key,
                temperature=0.7,
                max_retries=1
            )
            self.current_model = "gemini-1.5-flash (fallback)"
        
        # Initialize embeddings (using lightweight fake embeddings for compatibility)
        self.embeddings = FakeEmbeddings(size=384)
        
        # Initialize ChromaDB
        self.chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        self.vector_store = Chroma(
            persist_directory=self.chroma_path,
            embedding_function=self.embeddings,
            collection_name="buddy_conversations"
        )
        
        # Initialize user-specific conversation memories
        self.user_memories = {}  # Dictionary to store memory for each user
        
        # System prompt
        self.system_prompt = """You are Buddy, a friendly AI chatbot who talks like a good friend. 

Key characteristics:
- Be warm, conversational, and personable
- Use casual, friendly language like you're talking to a close friend
- ONLY reference past conversations if they are explicitly provided in the context below
- Show genuine interest in the user's life and experiences
- Be supportive and encouraging
- Use humor appropriately
- Ask follow-up questions to keep conversations engaging

IMPORTANT: Only mention or reference specific past events, topics, or conversations if they are clearly mentioned in the conversation history provided. Do not make up or hallucinate past interactions."""

    def get_user_memory(self, user_id: str):
        """Get or create memory for a specific user"""
        if user_id not in self.user_memories:
            print(f"🧠 Creating new memory for user: {user_id}")
            self.user_memories[user_id] = ConversationBufferMemory(
                return_messages=True,
                memory_key="chat_history",
                max_token_limit=2000
            )
        return self.user_memories[user_id]

    async def store_conversation(self, user_message: str, assistant_message: str, user_id: str):
        """Store the conversation in ChromaDB for future retrieval with user_id"""
        try:
            # Create document with conversation
            conversation_text = f"User: {user_message}\nBuddy: {assistant_message}"
            
            # Create metadata with user_id for session management
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "user_message": user_message,
                "assistant_message": assistant_message,
                "user_id": user_id,  # Add user_id to metadata
                "conversation_id": f"conv_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            # Create document
            doc = Document(
                page_content=conversation_text,
                metadata=metadata
            )
            
            # Add to vector store
            await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.vector_store.add_documents([doc])
            )
            
        except Exception as e:
            print(f"Error storing conversation: {e}")

    async def retrieve_relevant_context(self, query: str, user_id: str, k: int = 3) -> List[str]:
        """Retrieve relevant past conversations for specific user"""
        try:
            print(f"🔍 Retrieving context for user_id: {user_id}")
            
            # First, get more results without filter to see what's in the database
            all_results = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.vector_store.similarity_search(query, k=k*3)  # Get more results
            )
            
            print(f"📝 Found {len(all_results)} total documents in database")
            
            # Manually filter by user_id to ensure it works correctly
            filtered_results = []
            for doc in all_results:
                doc_user_id = doc.metadata.get('user_id', 'unknown')
                print(f"📄 Document user_id: {doc_user_id}, Target user_id: {user_id}")
                
                if doc_user_id == user_id:
                    filtered_results.append(doc)
                    print(f"✅ Match found! Including document for user {user_id}")
                else:
                    print(f"❌ Skipping document for user {doc_user_id}")
            
            # Limit to requested number of results
            filtered_results = filtered_results[:k]
            
            print(f"🎯 Final filtered results: {len(filtered_results)} documents for user {user_id}")
            
            # Extract relevant context
            context = []
            for doc in filtered_results:
                context.append(doc.page_content)
                print(f"📖 Adding context: {doc.page_content[:100]}...")
            
            return context
            
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return []

    async def generate_response(self, user_message: str, user_id: str) -> tuple[str, List[str]]:
        """Generate response using RAG pipeline with user session"""
        try:
            # Retrieve relevant context for this specific user
            relevant_context = await self.retrieve_relevant_context(user_message, user_id)
            
            # Build context string
            context_string = ""
            if relevant_context:
                context_string = "\n\nHere are some relevant past conversations:\n"
                for i, context in enumerate(relevant_context, 1):
                    context_string += f"{i}. {context}\n"
            
            # Get conversation history from user-specific memory
            user_memory = self.get_user_memory(user_id)
            history = user_memory.chat_memory.messages
            history_string = ""
            if history:
                history_string = "\n\nRecent conversation history:\n"
                for msg in history[-6:]:  # Last 3 exchanges
                    if isinstance(msg, HumanMessage):
                        history_string += f"User: {msg.content}\n"
                    elif isinstance(msg, AIMessage):
                        history_string += f"Buddy: {msg.content}\n"
                print(f"📚 Using {len(history)} messages from user {user_id}'s memory")
            
            # Construct prompt
            if context_string or history_string:
                full_prompt = f"""{self.system_prompt}
            
{context_string}
{history_string}

Current user message: {user_message}

Please respond as Buddy. Only reference information from the context and history provided above. Do not mention or reference any events, topics, or conversations that are not explicitly shown in the context."""
            else:
                full_prompt = f"""{self.system_prompt}

Current user message: {user_message}

Please respond as Buddy. This appears to be the start of a new conversation, so respond naturally without referencing any past interactions."""

            # Generate response with comprehensive error handling
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    response = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.llm.invoke([HumanMessage(content=full_prompt)])
                    )
                    break  # Success!
                    
                except Exception as api_error:
                    error_str = str(api_error).lower()
                    
                    # Handle specific Gemini API errors
                    if "quota" in error_str or "429" in error_str:
                        return "Hey! I've hit my daily chat limit, but I'll be back tomorrow! Thanks for being patient with me! 😊", relevant_context
                    
                    elif "404" in error_str or "not found" in error_str:
                        return f"Oops! The AI model '{self.current_model}' isn't available right now. My developer needs to update my configuration! 🔧", relevant_context
                    
                    elif "500" in error_str or "internal" in error_str:
                        if attempt < max_attempts - 1:
                            print(f"⚠️ Gemini API internal error (attempt {attempt + 1}), retrying...")
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        else:
                            return "Sorry, I'm having some technical difficulties right now. The AI service seems to be having issues. Please try again in a few minutes! 🛠️", relevant_context
                    
                    elif "access" in error_str or "permission" in error_str:
                        return "It looks like there's an issue with my API access. My developer needs to check my credentials! 🔑", relevant_context
                    
                    else:
                        # Unknown error - try once more, then give friendly message
                        if attempt < max_attempts - 1:
                            print(f"⚠️ Unknown API error (attempt {attempt + 1}): {str(api_error)[:100]}...")
                            await asyncio.sleep(1)
                            continue
                        else:
                            return "I'm having a bit of trouble thinking right now. Please try asking me again! 🤔", relevant_context
            
            assistant_message = response.content
            
            # Update user-specific memory
            user_memory = self.get_user_memory(user_id)
            user_memory.chat_memory.add_user_message(user_message)
            user_memory.chat_memory.add_ai_message(assistant_message)
            print(f"💾 Updated memory for user {user_id}, total messages: {len(user_memory.chat_memory.messages)}")
            
            # Store conversation for future retrieval with user_id
            await self.store_conversation(user_message, assistant_message, user_id)
            
            return assistant_message, relevant_context
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return "Hey! I'm having a little trouble right now, but I'm still here for you. Can you try asking me again?", []

# Initialize Buddy RAG system
buddy_rag = BuddyRAG()

@app.post("/chat", response_model=ChatResponse)
async def chat_with_buddy(message: ChatMessage):
    """Chat endpoint for Buddy with user session management"""
    try:
        response, context = await buddy_rag.generate_response(message.text, message.user_id)
        return ChatResponse(
            answer=response,
            context_used=[ctx[:100] + "..." if len(ctx) > 100 else ctx for ctx in context]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.delete("/conversations")
async def clear_conversations():
    """Clear all conversation history"""
    try:
        import shutil
        # Clear ChromaDB
        if os.path.exists(buddy_rag.chroma_path):
            shutil.rmtree(buddy_rag.chroma_path)
        
        # Clear all user-specific memory buffers
        buddy_rag.user_memories.clear()
        
        # Reinitialize ChromaDB
        buddy_rag.vector_store = Chroma(
            persist_directory=buddy_rag.chroma_path,
            embedding_function=buddy_rag.embeddings,
            collection_name="buddy_conversations"
        )
        
        return {"message": "All conversations cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing conversations: {str(e)}")

@app.delete("/conversations/{user_id}")
async def clear_user_conversations(user_id: str):
    """Clear conversation history for a specific user"""
    try:
        # Note: ChromaDB doesn't support direct deletion by filter in all versions
        # So we'll recreate the collection without this user's conversations
        
        # Get all documents
        all_docs = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: buddy_rag.vector_store.similarity_search("", k=1000)
        )
        
        # Filter out documents from this user
        keep_docs = [doc for doc in all_docs if doc.metadata.get('user_id') != user_id]
        
        # Clear and recreate the vector store
        import shutil
        if os.path.exists(buddy_rag.chroma_path):
            shutil.rmtree(buddy_rag.chroma_path)
        
        buddy_rag.vector_store = Chroma(
            persist_directory=buddy_rag.chroma_path,
            embedding_function=buddy_rag.embeddings,
            collection_name="buddy_conversations"
        )
        
        # Re-add the documents we want to keep
        if keep_docs:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: buddy_rag.vector_store.add_documents(keep_docs)
            )
        
        return {"message": f"Conversations for user {user_id} cleared successfully", "remaining_conversations": len(keep_docs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing user conversations: {str(e)}")

@app.get("/debug/storage")
async def debug_storage_info():
    """Debug endpoint to check storage status"""
    try:
        # Check if ChromaDB directory exists
        chroma_exists = os.path.exists(buddy_rag.chroma_path)
        
        # Try to get collection info
        collection_info = None
        stored_count = 0
        
        if chroma_exists:
            try:
                # Get collection
                collection = buddy_rag.vector_store._collection
                stored_count = collection.count()
                collection_info = {
                    "name": collection.name,
                    "count": stored_count,
                    "metadata": getattr(collection, "metadata", {})
                }
            except Exception as e:
                collection_info = f"Error accessing collection: {e}"
        
        # Check memory buffer
        memory_messages = len(buddy_rag.memory.chat_memory.messages)
        
        return {
            "chroma_db_path": buddy_rag.chroma_path,
            "chroma_db_exists": chroma_exists,
            "collection_info": collection_info,
            "stored_conversations": stored_count,
            "memory_buffer_messages": memory_messages,
            "embedding_type": str(type(buddy_rag.embeddings)),
            "storage_status": "active" if chroma_exists else "not_initialized"
        }
    except Exception as e:
        return {"error": f"Debug failed: {e}", "storage_status": "error"}

@app.get("/debug/conversations")
async def debug_list_conversations():
    """Debug endpoint to list stored conversations"""
    try:
        # Try to retrieve all conversations
        results = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: buddy_rag.vector_store.similarity_search("", k=10)
        )
        
        conversations = []
        for doc in results:
            conversations.append({
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                "metadata": doc.metadata,
                "full_length": len(doc.page_content)
            })
        
        return {
            "total_conversations": len(conversations),
            "conversations": conversations
        }
    except Exception as e:
        return {"error": f"Failed to retrieve conversations: {e}"}

@app.get("/debug/sessions")
async def debug_user_sessions():
    """Debug endpoint to show user sessions and their conversation counts"""
    try:
        # Get all documents to analyze user sessions
        results = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: buddy_rag.vector_store.similarity_search("", k=100)  # Get more documents
        )
        
        # Group conversations by user_id
        user_sessions = {}
        for doc in results:
            user_id = doc.metadata.get('user_id', 'unknown')
            if user_id not in user_sessions:
                user_sessions[user_id] = {
                    'conversation_count': 0,
                    'first_seen': doc.metadata.get('timestamp', 'unknown'),
                    'last_seen': doc.metadata.get('timestamp', 'unknown'),
                    'recent_messages': []
                }
            
            user_sessions[user_id]['conversation_count'] += 1
            
            # Update timestamps
            timestamp = doc.metadata.get('timestamp', '')
            if timestamp > user_sessions[user_id]['last_seen']:
                user_sessions[user_id]['last_seen'] = timestamp
            if timestamp < user_sessions[user_id]['first_seen']:
                user_sessions[user_id]['first_seen'] = timestamp
            
            # Add recent message preview
            if len(user_sessions[user_id]['recent_messages']) < 3:
                user_sessions[user_id]['recent_messages'].append({
                    'content': doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content,
                    'timestamp': timestamp
                })
        
        return {
            "total_users": len(user_sessions),
            "total_conversations": len(results),
            "user_sessions": user_sessions
        }
    except Exception as e:
        return {"error": f"Failed to analyze user sessions: {e}"}

@app.post("/debug/test-session")
async def test_session(message: ChatMessage):
    """Test endpoint to verify user_id is being received correctly"""
    return {
        "received_user_id": message.user_id,
        "received_text": message.text,
        "timestamp": datetime.now().isoformat(),
        "user_memory_messages": len(buddy_rag.get_user_memory(message.user_id).chat_memory.messages),
        "total_users_in_memory": len(buddy_rag.user_memories)
    }

@app.post("/debug/test-session")
async def test_session(message: ChatMessage):
    """Test endpoint to verify user_id is being received correctly"""
    return {
        "received_user_id": message.user_id,
        "received_text": message.text,
        "user_id_length": len(message.user_id),
        "timestamp": datetime.now().isoformat(),
        "status": "session_test_successful"
    }

@app.get("/debug/model")
async def debug_model_status():
    """Debug endpoint to check current model and API status"""
    try:
        # Test a simple API call
        test_response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: buddy_rag.llm.invoke([HumanMessage(content="Hi")])
        )
        api_status = "working"
        test_result = test_response.content[:50] + "..." if len(test_response.content) > 50 else test_response.content
    except Exception as e:
        api_status = "error"
        test_result = str(e)[:100] + "..."
    
    return {
        "current_model": buddy_rag.current_model,
        "api_status": api_status,
        "test_result": test_result,
        "google_api_key_configured": bool(buddy_rag.google_api_key),
        "embedding_type": str(type(buddy_rag.embeddings))
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "buddy": "ready",
        "model": buddy_rag.current_model,
        "storage": "active" if os.path.exists(buddy_rag.chroma_path) else "not_initialized"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Buddy server is running!", "version": "1.0.0"}

if __name__ == "__main__":
    # Disable reload in production (when PORT is set by platform)
    is_production = os.getenv("PORT") is not None
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8001)),
        reload=not is_production
    )
