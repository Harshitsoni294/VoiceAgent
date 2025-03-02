import React, { useState, useRef, useEffect } from "react";

function useSpeechRecognition({ onResult, onEnd }) {
  const recognitionRef = useRef(null);

  const start = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Speech recognition not supported in this browser');
      return;
    }
    const SpeechRecognition = window.webkitSpeechRecognition || window.SpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      onResult(transcript);
    };
    recognition.onend = onEnd;
    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      onEnd();
    };
    recognition.start();
    recognitionRef.current = recognition;
  };

  const stop = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
  };

  return { start, stop };
}

function useSpeechSynthesis() {
  const speak = (text, onEnd) => {
    if (!window.speechSynthesis) {
      console.error('Speech synthesis not supported');
      if (onEnd) onEnd();
      return;
    }
    const utter = new window.SpeechSynthesisUtterance(text);
    utter.onend = onEnd;
    utter.text = text.replace(/http[^\s]+/g, ''); // Remove URLs from the text
    window.speechSynthesis.speak(utter);
  };
  return { speak };
}

export default function Chat({ setListening, setSpeaking }) {
  // Load messages from localStorage on component mount
  const [messages, setMessages] = useState(() => {
    const savedMessages = localStorage.getItem('voiceagent-chat-messages');
    return savedMessages ? JSON.parse(savedMessages) : [];
  });
  const [input, setInput] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  // Custom scrollbar styles
  useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      .custom-scrollbar::-webkit-scrollbar {
        width: 8px;
      }
      .custom-scrollbar::-webkit-scrollbar-track {
        background: transparent;
      }
      .custom-scrollbar::-webkit-scrollbar-thumb {
        background: rgba(156, 163, 175, 0.5);
        border-radius: 4px;
      }
      .custom-scrollbar::-webkit-scrollbar-thumb:hover {
        background: rgba(156, 163, 175, 0.7);
      }
      /* For Firefox */
      .custom-scrollbar {
        scrollbar-width: thin;
        scrollbar-color: rgba(156, 163, 175, 0.5) transparent;
      }
    `;
    document.head.appendChild(style);

    return () => {
      document.head.removeChild(style);
    };
  }, []);
  
  // Save messages to localStorage whenever messages change
  useEffect(() => {
    localStorage.setItem('voiceagent-chat-messages', JSON.stringify(messages));
  }, [messages]);
  
  const clearChat = () => {
    setMessages([]);
    localStorage.removeItem('voiceagent-chat-messages');
  };
  
  const { start, stop } = useSpeechRecognition({
    onResult: (text) => {
      setInput(text);
      setIsListening(false);
      setListening(false);
      handleSend(text);
    },
    onEnd: () => {
      setIsListening(false);
      setListening(false);
    },
  });
  const { speak } = useSpeechSynthesis();

  const handleMic = () => {
    setIsListening(true);
    setListening(true);
    start();
  };

  const saveReminderLocally = (text, datetime) => {
    const stored = localStorage.getItem('voiceagent_reminders');
    const reminders = stored ? JSON.parse(stored) : [];
    reminders.push({ text, datetime });
    localStorage.setItem('voiceagent_reminders', JSON.stringify(reminders));
    console.log('Saved reminder locally:', { text, datetime });
  };

  const handleSend = async (text) => {
    if (!text) return;
    setMessages((msgs) => [...msgs, { from: "user", text }]);
    setInput("");

    let answer = "";
    try {
      const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/mcp';

      const response = await fetch(`${API_BASE_URL}/intent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      });
      const data = await response.json();
      answer = data.answer || JSON.stringify(data);
      
      // Check if this was a reminder creation and save locally
      if (data.type === 'reminder' && data.reminder_data) {
        saveReminderLocally(data.reminder_data.text, data.reminder_data.datetime);
      }
      
      if (data.redirect_url) {
        window.open(data.redirect_url, "_blank");
      }
    } catch (e) {
      answer = "Sorry, I couldn't fetch a response.";
    }

    setMessages((msgs) => [...msgs, { from: "assistant", text: answer }]);
    setIsSpeaking(true);
    setSpeaking(true);
    speak(answer, () => {
      setIsSpeaking(false);
      setSpeaking(false);
    });
  };

  return (
    <div className="w-full h-screen flex flex-col relative">
      {/* Chat Header - Fixed */}
      <div className="bg-gray-800 text-white p-4 flex items-center gap-3 shadow-sm border-b border-gray-700">
        <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm">
          🤖
        </div>
        <div className="flex-1">
          <h3 className="font-semibold">AI Assistant</h3>
        </div>
        <button className="px-4 py-2 rounded-lg bg-white text-black hover:bg-gray-200 transition-colors" onClick={() => window.open('/todo', '_blank')}>
          ToDo
        </button>

        <button className="px-4 py-2 rounded-lg bg-white text-black hover:bg-gray-200 transition-colors" onClick={() => window.open('/calendar', '_blank')}>
          Calendar
        </button>
        <button
          onClick={clearChat}
          className="p-2 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-full transition-colors duration-200 shadow-md bg-white border"
          title="Clear chat history"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
      
      {/* Messages Area - Scrollable */}
      <div className="flex-1 bg-gray-800 p-4 border-l border-r border-gray-700 overflow-y-auto min-h-0 max-h-full custom-scrollbar"
        style={{ scrollbarGutter: 'stable' }}>
        <div className="space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 mt-8">
              <div className="text-4xl mb-4">🤖</div>
              <p className="text-lg">Hello! How can I help you today?</p>
              <p className="text-sm mt-2">Try: "Tell me a joke", "What's the weather?", "Open YouTube", "Schedule a meeting"</p>
            </div>
          ) : (
            messages.map((msg, i) => (
              <div
                key={i}
                className={`mb-4 flex ${msg.from === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`px-4 py-3 rounded-2xl max-w-xs lg:max-w-md shadow-sm ${
                    msg.from === "user"
                      ? "bg-blue-500 text-white rounded-br-none"
                      : "bg-gray-700 text-gray-200 rounded-bl-none"
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))
        )}
        </div>
      </div>
      
      {/* Input Area - Fixed Footer */}
      <div className="bg-gray-800 p-4 border-t border-gray-700">
        <div className="flex items-center gap-3">
          <button
            onClick={handleMic}
            className={`p-3 rounded-full shadow-lg transition-all duration-200 ${
              isListening 
                ? "bg-red-500 text-white animate-pulse" 
                : "bg-blue-500 text-white hover:bg-blue-600 hover:scale-105"
            }`}
            disabled={isSpeaking}
          >
            {isListening ? "🎙️" : "🎤"}
          </button>
          
          <input
            className="flex-1 px-4 py-3 rounded-full border border-gray-700 bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && handleSend(input)}
            placeholder="Type your message or click the mic..."
            disabled={isListening || isSpeaking}
          />
          
          <button
            onClick={() => handleSend(input)}
            className="bg-green-500 text-white px-6 py-3 rounded-full shadow-lg hover:bg-green-600 transition-all duration-200 hover:scale-105"
            disabled={isListening || isSpeaking || !input.trim()}
          >
            Send
          </button>
        </div>
        
        {isListening && (
          <div className="text-center mt-2 text-sm text-gray-400">
            🎙️ Listening...
          </div>
        )}
      </div>
    </div>
  );
}
