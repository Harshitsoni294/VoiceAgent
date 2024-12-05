import React, { useState } from 'react';

const MainSection = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');

  const capabilities = [
    { 
      icon: '⏰', 
      text: 'Remind me to call a friend at 10am tomorrow',
      color: 'from-blue-500 to-purple-600'
    },
    { 
      icon: '😄', 
      text: 'Tell me a joke',
      color: 'from-orange-400 to-pink-500'
    },
    { 
      icon: '🕐', 
      text: "What's the time",
      color: 'from-green-400 to-blue-500'
    },
    { 
      icon: '📺', 
      text: 'Open YouTube',
      color: 'from-red-500 to-pink-500'
    },
    { 
      icon: '✉️', 
      text: 'Write an email to harshitsoni2026@gmail.com informing him we have a job offer for him at XYZ.',
      color: 'from-gradient-to-r from-purple-600 to-blue-600',
      featured: true
    }
  ];

  const handleCapabilityClick = (text) => {
    setInputValue(text);
  };

  const renderContent = () => {
    if (messages.length === 0) {
      return (
        <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50">
          <div className="text-center max-w-md px-6">
            <div className="mb-6">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center text-white text-2xl mx-auto mb-4 shadow-lg">
                🤖
              </div>
              <h3 className="text-2xl font-bold text-gray-800 mb-2">AI Assistant Ready</h3>
              <p className="text-gray-600 leading-relaxed">
                Select any capability from the left panel or start typing your request below.
              </p>
            </div>
            <button className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 py-3 rounded-full font-medium transition-all duration-200 transform hover:scale-105 shadow-lg">
              Start Conversation
            </button>
          </div>
        </div>
      );
    }
    
    return (
      <div className="flex-1 p-4 bg-white overflow-y-auto">
        {messages.map((message, index) => (
          <div key={index} className="mb-4">
            <div className="bg-blue-100 p-3 rounded-lg max-w-md ml-auto">
              {message}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <main className="flex-1 overflow-hidden flex bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* Left Section: Try This */}
      <div className="flex-1 bg-white border-r border-gray-200 shadow-lg">
        <div className="p-6 h-full">
          <div className="mb-6">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center text-white text-sm font-bold">
                ✨
              </div>
              <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Try This
              </h2>
            </div>
            <p className="text-gray-600 text-sm">
              Discover what your AI assistant can do. Click any example below to get started.
            </p>
          </div>

          <div className="space-y-3">
            {capabilities.map((capability, index) => (
              <div
                key={index}
                onClick={() => handleCapabilityClick(capability.text)}
                className={`group relative p-4 rounded-xl cursor-pointer transition-all duration-300 hover:shadow-lg hover:scale-[1.02] border ${
                  capability.featured 
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white border-transparent shadow-lg' 
                    : 'bg-gray-50 hover:bg-white border-gray-100 hover:border-gray-200'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg shrink-0 ${
                    capability.featured 
                      ? 'bg-white/20 backdrop-blur-sm' 
                      : 'bg-gradient-to-r ' + capability.color + ' text-white'
                  }`}>
                    {capability.icon}
                  </div>
                  <span className={`text-sm font-medium leading-snug ${
                    capability.featured ? 'text-white' : 'text-gray-800 group-hover:text-gray-900'
                  }`}>
                    {capability.text}
                  </span>
                </div>
                
                {/* Hover effect overlay */}
                {!capability.featured && (
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-purple-500/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                )}
              </div>
            ))}
          </div>

          <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border border-blue-100">
            <p className="text-xs text-gray-600 text-center">
              💡 <strong>Tip:</strong> You can also type custom commands in the chat box
            </p>
          </div>
        </div>
      </div>

      {/* Right Section: Chat Box */}
      <div className="flex-2 flex flex-col bg-white">
        {/* Chat Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 flex items-center gap-3 shadow-sm">
          <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm">
            🤖
          </div>
          <div>
            <h3 className="font-semibold">AI Assistant</h3>
            <div className="flex items-center gap-1 text-xs opacity-90">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              Online
            </div>
          </div>
        </div>

        {/* Chat Content */}
        {renderContent()}

        {/* Input Section */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex gap-3">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Type your message or click a suggestion above..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
            />
            <button 
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white p-3 rounded-xl transition-all duration-200 transform hover:scale-105 shadow-md"
              onClick={() => {
                if (inputValue.trim()) {
                  setMessages([...messages, inputValue]);
                  setInputValue('');
                }
              }}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </main>
  );
};

export default MainSection;
