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
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=self.google_api_key,
            temperature=0.7
        )
        
        # Initialize embeddings (using lightweight fake embeddings for compatibility)
        self.embeddings = FakeEmbeddings(size=384)
        
        # Initialize ChromaDB
        self.chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        self.vector_store = Chroma(
            persist_directory=self.chroma_path,
            embedding_function=self.embeddings,
            collection_name="buddy_conversations"
        )
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history",
            max_token_limit=2000
        )
        
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

    async def store_conversation(self, user_message: str, assistant_message: str):
        """Store the conversation in ChromaDB for future retrieval"""
        try:
            # Create document with conversation
            conversation_text = f"User: {user_message}\nBuddy: {assistant_message}"
            
            # Create metadata
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "user_message": user_message,
                "assistant_message": assistant_message,
                "conversation_id": f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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

    async def retrieve_relevant_context(self, query: str, k: int = 3) -> List[str]:
        """Retrieve relevant past conversations"""
        try:
            # Search for relevant conversations
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.vector_store.similarity_search(query, k=k)
            )
            
            # Extract relevant context
            context = []
            for doc in results:
                context.append(doc.page_content)
            
            return context
            
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return []

    async def generate_response(self, user_message: str) -> tuple[str, List[str]]:
        """Generate response using RAG pipeline"""
        try:
            # Retrieve relevant context
            relevant_context = await self.retrieve_relevant_context(user_message)
            
            # Build context string
            context_string = ""
            if relevant_context:
                context_string = "\n\nHere are some relevant past conversations:\n"
                for i, context in enumerate(relevant_context, 1):
                    context_string += f"{i}. {context}\n"
            
            # Get conversation history from memory
            history = self.memory.chat_memory.messages
            history_string = ""
            if history:
                history_string = "\n\nRecent conversation history:\n"
                for msg in history[-6:]:  # Last 3 exchanges
                    if isinstance(msg, HumanMessage):
                        history_string += f"User: {msg.content}\n"
                    elif isinstance(msg, AIMessage):
                        history_string += f"Buddy: {msg.content}\n"
            
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

            # Generate response
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.llm.invoke([HumanMessage(content=full_prompt)])
            )
            
            assistant_message = response.content
            
            # Update memory
            self.memory.chat_memory.add_user_message(user_message)
            self.memory.chat_memory.add_ai_message(assistant_message)
            
            # Store conversation for future retrieval
            await self.store_conversation(user_message, assistant_message)
            
            return assistant_message, relevant_context
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return "Hey! I'm having a little trouble right now, but I'm still here for you. Can you try asking me again?", []

# Initialize Buddy RAG system
buddy_rag = BuddyRAG()

@app.post("/chat", response_model=ChatResponse)
async def chat_with_buddy(message: ChatMessage):
    """Chat endpoint for Buddy"""
    try:
        response, context = await buddy_rag.generate_response(message.text)
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
        
        # Clear in-memory conversation buffer
        buddy_rag.memory.clear()
        
        # Reinitialize ChromaDB
        buddy_rag.vector_store = Chroma(
            persist_directory=buddy_rag.chroma_path,
            embedding_function=buddy_rag.embeddings,
            collection_name="buddy_conversations"
        )
        
        return {"message": "All conversations cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing conversations: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "buddy": "ready"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Buddy server is running!", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8001)),
        reload=True
    )
