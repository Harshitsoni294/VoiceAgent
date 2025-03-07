import React from "react";
import Chat from "./components/Chat";
import VoiceCircle from "./components/VoiceCircle";
import MainSection from "./components/MainSection";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/mcp';

export default function App() {
  const [listening, setListening] = React.useState(false);
  const [speaking, setSpeaking] = React.useState(false);
  const [currentView, setCurrentView] = React.useState("chat");
  const [lastCheckedTime, setLastCheckedTime] = React.useState(new Date());
  const [currentAlarm, setCurrentAlarm] = React.useState(null);
  const [sidebarOpen, setSidebarOpen] = React.useState(true); // For responsive drawer
  const [isMobile, setIsMobile] = React.useState(false);

  // Check screen size - responsive to actual viewport size, not device type
  React.useEffect(() => {
    const checkScreenSize = () => {
      const mobile = window.innerWidth < 768; // Based on actual screen width
      setIsMobile(mobile);
      if (mobile) {
        setSidebarOpen(false); // Close sidebar on small screens by default
      } else {
        setSidebarOpen(true); // Open sidebar on larger screens
      }
    };

    // Set CSS custom property for viewport height that updates on resize
    const setVH = () => {
      const vh = window.innerHeight * 0.01;
      document.documentElement.style.setProperty('--vh', `${vh}px`);
    };
    
    checkScreenSize();
    setVH();
    
    window.addEventListener('resize', () => {
      checkScreenSize();
      setVH();
    });
    window.addEventListener('orientationchange', setVH);
    
    return () => {
      window.removeEventListener('resize', checkScreenSize);
      window.removeEventListener('orientationchange', setVH);
    };
  }, []);

  // Request notification permission on component mount
  React.useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission().then(permission => {
        console.log('Notification permission:', permission);
      });
    }
  }, []);

  // Background alarm monitoring
  React.useEffect(() => {
    const getRemindersFromLocal = () => {
      const stored = localStorage.getItem('voiceagent_reminders');
      return stored ? JSON.parse(stored) : [];
    };

    const playAlarmSound = () => {
      console.log('🔊 Starting alarm sound...');
      
      // Strategy 1: Try to play audio file with background-friendly settings
      try {
        const audio = new Audio('/alarm.mp3');
        audio.volume = 1.0; // Max volume
        audio.loop = true;
        
        // Force audio to continue in background
        audio.setAttribute('autoplay', 'true');
        audio.setAttribute('controls', 'controls');
        audio.style.position = 'fixed';
        audio.style.top = '-1000px'; // Hide but keep in DOM
        audio.style.left = '-1000px';
        document.body.appendChild(audio);
        
        // Multiple attempts to ensure playback
        const attemptPlay = () => {
          audio.play()
            .then(() => {
              console.log('✅ Alarm audio started successfully');
              window.currentAlarmAudio = audio;
              
              // Keep trying to play if paused (happens when tab becomes inactive)
              const keepAlive = setInterval(() => {
                if (audio.paused && document.getElementById('alarmOverlay')) {
                  console.log('🔄 Restarting paused alarm audio');
                  audio.play().catch(e => console.log('Restart failed:', e));
                } else if (!document.getElementById('alarmOverlay')) {
                  clearInterval(keepAlive);
                }
              }, 1000);
              
            })
            .catch(error => {
              console.log('❌ Audio play failed, trying fallback:', error);
              if (audio.parentNode) {
                audio.parentNode.removeChild(audio);
              }
              playBeepFallback();
            });
        };
        
        // Try to play immediately and retry if needed
        attemptPlay();
        setTimeout(attemptPlay, 100);
        setTimeout(attemptPlay, 500);
        
      } catch (error) {
        console.log('❌ Error creating alarm audio, using fallback:', error);
        playBeepFallback();
      }
      
      // Strategy 2: Always start Web Audio API as additional backup
      setTimeout(() => {
        if (document.getElementById('alarmOverlay')) {
          playBeepFallback();
        }
      }, 1000);
    };

    const playBeepFallback = () => {
      // Enhanced Web Audio API fallback that's more persistent
      try {
        console.log('🔊 Starting Web Audio API fallback');
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        // Resume audio context if suspended (common when tab becomes inactive)
        if (audioContext.state === 'suspended') {
          audioContext.resume().then(() => {
            console.log('Audio context resumed');
          });
        }
        
        let beepInterval;
        
        const playBeepSequence = () => {
          if (!document.getElementById('alarmOverlay')) {
            if (beepInterval) clearInterval(beepInterval);
            return;
          }
          
          // Resume context if needed
          if (audioContext.state === 'suspended') {
            audioContext.resume();
          }
          
          try {
            // High frequency beep
            const oscillator1 = audioContext.createOscillator();
            const gainNode1 = audioContext.createGain();
            oscillator1.connect(gainNode1);
            gainNode1.connect(audioContext.destination);
            oscillator1.frequency.setValueAtTime(1200, audioContext.currentTime);
            oscillator1.type = 'square';
            gainNode1.gain.setValueAtTime(0.5, audioContext.currentTime);
            gainNode1.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.4);
            oscillator1.start();
            oscillator1.stop(audioContext.currentTime + 0.4);
            
            // Lower frequency beep after delay
            setTimeout(() => {
              if (!document.getElementById('alarmOverlay')) return;
              try {
                const oscillator2 = audioContext.createOscillator();
                const gainNode2 = audioContext.createGain();
                oscillator2.connect(gainNode2);
                gainNode2.connect(audioContext.destination);
                oscillator2.frequency.setValueAtTime(800, audioContext.currentTime);
                oscillator2.type = 'square';
                gainNode2.gain.setValueAtTime(0.5, audioContext.currentTime);
                gainNode2.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.4);
                oscillator2.start();
                oscillator2.stop(audioContext.currentTime + 0.4);
              } catch (e) {
                console.log('Error in delayed beep:', e);
              }
            }, 400);
            
          } catch (e) {
            console.log('Error in beep sequence:', e);
          }
        };
        
        // Start immediately and then repeat
        playBeepSequence();
        beepInterval = setInterval(playBeepSequence, 1200);
        
        // Store interval reference for cleanup
        window.currentBeepInterval = beepInterval;
        
        console.log('✅ Web Audio API fallback started');
        
      } catch (fallbackError) {
        console.log('❌ Web Audio API also failed:', fallbackError);
        // Final fallback - try to use hidden video element for sound
        tryVideoFallback();
      }
    };
    
    const tryVideoFallback = () => {
      try {
        console.log('🔊 Trying video element fallback');
        const video = document.createElement('video');
        video.style.position = 'fixed';
        video.style.top = '-1000px';
        video.style.left = '-1000px';
        video.volume = 1.0;
        video.loop = true;
        video.muted = false;
        
        // Create a simple audio data URL (beep sound)
        const audioDataUrl = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBjiKzfLZgj0IBnLI7eGTRAoUWqi+7K1hEwc+ltryxXknBTSF0PX...(truncated base64 data)';
        video.src = audioDataUrl;
        
        document.body.appendChild(video);
        video.play().then(() => {
          console.log('✅ Video fallback started');
          window.currentVideoAlarm = video;
        }).catch(e => {
          console.log('❌ Video fallback failed:', e);
          if (video.parentNode) video.parentNode.removeChild(video);
        });
      } catch (error) {
        console.log('❌ Video fallback error:', error);
      }
    };

    const checkReminders = () => {
      const reminders = getRemindersFromLocal();
      console.log('🔔 Checking reminders:', reminders.length);
      const now = new Date();
      
      reminders.forEach(reminder => {
        const reminderTime = new Date(reminder.datetime);
        console.log(`Checking reminder: ${reminder.text} at ${reminder.datetime}`);
        
        // Check if reminder is due and hasn't been triggered yet
        if (reminderTime <= now && reminderTime > lastCheckedTime) {
          console.log('🚨 ALARM TRIGGERED:', reminder.text);
          playAlarmSound();
          showAlarmOverlay(reminder);
          
          // Show browser notification even when page is minimized
          if (Notification.permission === 'granted') {
            new Notification('⏰ VoiceAgent Alarm!', { 
              body: `${reminder.text}\n⏰ ${reminder.datetime}`,
              icon: '/favicon.ico',
              requireInteraction: true, // Keeps notification visible until user interacts
              tag: 'alarm-' + Date.now() // Unique tag for each alarm
            });
          }
          
          // Focus the window to bring it to front (if possible)
          if (window.focus) {
            window.focus();
          }
        }
      });
      
      setLastCheckedTime(now);
    };

    // Start checking immediately
    checkReminders();
    
    // Then check every 10 seconds
    const interval = setInterval(checkReminders, 10000);
    
    // Enhanced visibility change handler for background operation
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        console.log('📱 Tab became inactive - ensuring alarm continues');
        
        // If there's an active alarm, try to restart audio
        if (document.getElementById('alarmOverlay')) {
          // Try to restart main audio
          if (window.currentAlarmAudio && window.currentAlarmAudio.paused) {
            window.currentAlarmAudio.play().catch(e => console.log('Failed to resume main audio:', e));
          }
          
          // Ensure beep fallback is running
          if (!window.currentBeepInterval) {
            playBeepFallback();
          }
          
          // Send additional notification when tab becomes inactive
          if (Notification.permission === 'granted') {
            new Notification('🚨 VoiceAgent Alarm Still Active!', {
              body: 'Your alarm is ringing! Click to return to the app.',
              requireInteraction: true,
              tag: 'alarm-background-' + Date.now()
            });
          }
        }
      } else if (document.visibilityState === 'visible') {
        console.log('👁️ Tab became active');
        // Tab is back in focus - audio should work normally
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // Also listen for focus/blur events as additional backup
    const handleFocus = () => {
      if (document.getElementById('alarmOverlay') && window.currentAlarmAudio && window.currentAlarmAudio.paused) {
        window.currentAlarmAudio.play().catch(e => console.log('Focus audio restart failed:', e));
      }
    };
    
    const handleBlur = () => {
      if (document.getElementById('alarmOverlay')) {
        console.log('🔄 Window lost focus, ensuring alarm persistence');
        setTimeout(() => {
          if (document.getElementById('alarmOverlay') && !window.currentBeepInterval) {
            playBeepFallback();
          }
        }, 1000);
      }
    };
    
    window.addEventListener('focus', handleFocus);
    window.addEventListener('blur', handleBlur);
    
    return () => {
      clearInterval(interval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
      window.removeEventListener('blur', handleBlur);
    };
  }, [lastCheckedTime]);

  const showAlarmOverlay = (reminder) => {
    // Remove existing overlay if any
    const existingOverlay = document.getElementById('alarmOverlay');
    if (existingOverlay) {
      existingOverlay.remove();
    }

    const overlay = document.createElement('div');
    overlay.id = 'alarmOverlay';
    overlay.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: linear-gradient(45deg, #ff0000, #ff6b6b);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 9999;
      animation: flash 1s infinite;
    `;

    const style = document.createElement('style');
    style.textContent = `
      @keyframes flash {
        0%, 100% { background: linear-gradient(45deg, #ff0000, #ff6b6b); }
        50% { background: linear-gradient(45deg, #cc0000, #ff4444); }
      }
      @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-15px); }
        75% { transform: translateX(15px); }
      }
    `;
    document.head.appendChild(style);

    overlay.innerHTML = `
      <div style="
        background: white;
        padding: 3rem;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 0 50px rgba(0,0,0,0.8);
        animation: shake 0.5s infinite;
        max-width: 500px;
        margin: 2rem;
      ">
        <div style="font-size: 5rem; margin-bottom: 1rem;">⏰</div>
        <h1 style="color: #dc2626; font-size: 2.5rem; font-weight: bold; margin-bottom: 1rem;">
          🚨 ALARM! 🚨
        </h1>
        <div style="background: #f3f4f6; padding: 1.5rem; border-radius: 15px; margin: 1.5rem 0;">
          <p style="font-size: 1.5rem; font-weight: bold; margin: 0; color: #374151;">${reminder.text}</p>
          <p style="margin: 0.5rem 0 0 0; color: #6b7280;">📅 ${reminder.datetime}</p>
        </div>
        <button onclick="window.stopCurrentAlarm()" style="
          background: linear-gradient(135deg, #dc2626, #ef4444);
          color: white;
          border: none;
          padding: 1.5rem 3rem;
          font-size: 1.5rem;
          border-radius: 15px;
          cursor: pointer;
          font-weight: bold;
          text-transform: uppercase;
          box-shadow: 0 4px 15px rgba(220, 38, 38, 0.4);
          transition: all 0.2s ease;
        " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
          🛑 STOP ALARM
        </button>
      </div>
    `;

    document.body.appendChild(overlay);

    // Handle keyboard shortcuts
    const handleKeydown = (event) => {
      if (event.code === 'Space' || event.code === 'Enter' || event.code === 'Escape') {
        event.preventDefault();
        stopCurrentAlarm();
      }
    };
    
    document.addEventListener('keydown', handleKeydown);
    overlay.keydownHandler = handleKeydown;

    // Auto-close after 10 minutes
    setTimeout(() => {
      if (document.getElementById('alarmOverlay')) {
        stopCurrentAlarm();
      }
    }, 600000);
  };

  const stopCurrentAlarm = () => {
    console.log('🛑 Stopping all alarm sounds and overlays');
    
    // Stop main audio
    if (window.currentAlarmAudio) {
      try {
        window.currentAlarmAudio.pause();
        window.currentAlarmAudio.currentTime = 0;
        if (window.currentAlarmAudio.parentNode) {
          window.currentAlarmAudio.parentNode.removeChild(window.currentAlarmAudio);
        }
      } catch (e) {
        console.log('Error stopping main audio:', e);
      }
      window.currentAlarmAudio = null;
    }
    
    // Stop Web Audio API beeps
    if (window.currentBeepInterval) {
      clearInterval(window.currentBeepInterval);
      window.currentBeepInterval = null;
    }
    
    // Stop video fallback
    if (window.currentVideoAlarm) {
      try {
        window.currentVideoAlarm.pause();
        if (window.currentVideoAlarm.parentNode) {
          window.currentVideoAlarm.parentNode.removeChild(window.currentVideoAlarm);
        }
      } catch (e) {
        console.log('Error stopping video alarm:', e);
      }
      window.currentVideoAlarm = null;
    }
    
    // Stop React state audio
    if (currentAlarm) {
      try {
        currentAlarm.pause();
        currentAlarm.currentTime = 0;
      } catch (e) {
        console.log('Error stopping React audio:', e);
      }
      setCurrentAlarm(null);
    }
    
    // Remove overlay
    const overlay = document.getElementById('alarmOverlay');
    if (overlay) {
      if (overlay.keydownHandler) {
        document.removeEventListener('keydown', overlay.keydownHandler);
      }
      overlay.remove();
    }
    
    // Clear any alarm notifications
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.ready.then(registration => {
        registration.getNotifications().then(notifications => {
          notifications.forEach(notification => {
            if (notification.tag && notification.tag.startsWith('alarm-')) {
              notification.close();
            }
          });
        });
      }).catch(e => console.log('Error clearing notifications:', e));
    }
    
    console.log('✅ All alarm components stopped');
  };

  // Make stopCurrentAlarm globally accessible for the button
  React.useEffect(() => {
    window.stopCurrentAlarm = stopCurrentAlarm;
    return () => {
      delete window.stopCurrentAlarm;
    };
  }, [currentAlarm]);

  const capabilities = [
    { 
      icon: '⏰', 
      text: 'Remind me to call a friend at 10am tomorrow',
      gradient: 'from-blue-500 to-purple-600'
    },
    { 
      icon: '😄', 
      text: 'Tell me a joke',
      gradient: 'from-orange-400 to-pink-500'
    },
    { 
      icon: '🕐', 
      text: "What's the time",
      gradient: 'from-green-400 to-blue-500'
    },
    { 
      icon: '📺', 
      text: 'Open YouTube',
      gradient: 'from-red-500 to-pink-500'
    },
    { 
      icon: '⏰', 
      text: 'Set alarm for 3pm today',
      gradient: 'from-indigo-500 to-purple-600'
    },
    { 
      icon: '✉️', 
      text: 'Write an email to harshitsoni2026@gmail.com informing him we have a job offer for him at XYZ.',
      gradient: 'from-purple-600 to-blue-600',
      featured: true
    }
  ];

  // Chat Interface Component
  const ChatInterface = ({ setListening, setSpeaking }) => {
    const [messages, setMessages] = React.useState([]);
    const [inputValue, setInputValue] = React.useState('');
    const [isTyping, setIsTyping] = React.useState(false);

    const handleSendMessage = () => {
      if (inputValue.trim()) {
        setMessages(prev => [...prev, { type: 'user', content: inputValue }]);
        setInputValue('');
        
        // Simulate AI response
        setIsTyping(true);
        setTimeout(() => {
          setMessages(prev => [...prev, { 
            type: 'ai', 
            content: `I understand you want to: "${inputValue}". I'm processing your request...` 
          }]);
          setIsTyping(false);
        }, 1500);
      }
    };

    const handleKeyPress = (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    };

    return (
      <div className="flex flex-col h-full">
        {/* Chat Messages */}
        <div className="flex-1 p-4 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md">
                <div className="w-16 h-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center text-white text-2xl mx-auto mb-4 shadow-lg">
                  🤖
                </div>
                <h3 className="text-xl font-semibold text-gray-800 mb-2">How can I help you today?</h3>
                <p className="text-gray-600 text-sm">
                  Choose an example from the sidebar or type your own message below.
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-4 max-w-4xl mx-auto">
              {messages.map((message, index) => (
                <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[70%] p-3 rounded-lg ${
                    message.type === 'user' 
                      ? 'bg-blue-600 text-white rounded-br-sm' 
                      : 'bg-gray-100 text-gray-800 rounded-bl-sm'
                  }`}>
                    <div className="text-sm leading-relaxed">{message.content}</div>
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 text-gray-800 p-3 rounded-lg rounded-bl-sm">
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 p-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-3 items-end">
              <div className="flex-1 relative">
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Send a message..."
                  rows={1}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  style={{ minHeight: '44px', maxHeight: '120px' }}
                />
              </div>
              <button
                onClick={handleSendMessage}
                disabled={!inputValue.trim()}
                className="p-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center justify-center"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
            <div className="text-xs text-gray-500 mt-2 text-center">
              Press Enter to send, Shift+Enter for new line
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Voice Circle Component
  const VoiceCircleComponent = ({ listening, speaking }) => {
    return (
      <div className="relative">
        <div className={`w-32 h-32 rounded-full border-4 border-blue-500 flex items-center justify-center bg-white shadow-2xl ${
          listening ? 'animate-pulse' : ''
        }`}>
          <div className={`w-16 h-16 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center text-white text-2xl ${
            listening ? 'animate-bounce' : ''
          }`}>
            🎤
          </div>
        </div>
        {listening && (
          <>
            <div className="absolute inset-0 rounded-full border-4 border-blue-300 animate-ping"></div>
            <div className="absolute inset-0 rounded-full border-4 border-blue-400 animate-ping" style={{animationDelay: '0.5s'}}></div>
          </>
        )}
        <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 text-white text-sm font-medium">
          {listening ? 'Listening...' : 'Voice Ready'}
        </div>
      </div>
    );
  };

  const SidebarContent = () => (
    <div className="h-full bg-gray-900 flex flex-col">
      {/* Sidebar Header */}
      <div className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            
            <h2 className="text-lg font-semibold text-gray-200">
              Examples
            </h2>
          </div>
          {isMobile && (
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-2 rounded-lg hover:bg-gray-700 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
        <p className="text-gray-400 text-xs mt-2">
          These are my capabilities 💪🏻.
        </p>
      </div>

      {/* Capabilities List */}
      <div className="flex-1 p-4 space-y-2 overflow-y-auto">
        {capabilities.map((capability, index) => (
          <div
            key={index}
            className={`group p-3 rounded-lg cursor-pointer transition-all duration-200 hover:shadow-sm ${
              capability.featured 
                ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700' 
                : 'bg-gray-700 hover:bg-gray-600 border border-gray-600 hover:border-gray-500'
            }`}
            onClick={() => {
              // Handle capability click
              console.log('Clicked:', capability.text);
              if (isMobile) {
                setSidebarOpen(false);
              }
            }}
          >
            <div className="flex items-start gap-3">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm shrink-0 ${
                capability.featured 
                  ? 'bg-white/20 backdrop-blur-sm' 
                  : ''
              }`}>
                {capability.icon}
              </div>
              <span className={`text-sm leading-snug ${
                capability.featured ? 'text-white font-medium' : 'text-gray-300 group-hover:text-gray-100'
              }`}>
                {capability.text}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Sidebar Footer */}
      <div className="p-4 bg-gray-900">
        <div className="text-xs text-white text-center">
          💡 You can also type custom requests
        </div>
      </div>
    </div>
  );

  console.log('🔔 VoiceAgent with background alarm monitoring loaded');

  return (
    <div className="flex bg-gradient-to-r from-gray-300 to-black overflow-hidden" style={{ height: 'calc(var(--vh, 1vh) * 100)' }}>
      {/* Sidebar - Show only when screen is wide enough */}
      {window.innerWidth >= 768 && !isMobile && (
        <div className="w-80 flex-shrink-0">
          <SidebarContent />
        </div>
      )}

      {/* Mobile/Small Screen Sidebar Overlay */}
      {(isMobile || window.innerWidth < 768) && sidebarOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 z-40"
            onClick={() => setSidebarOpen(false)}
          />
          {/* Drawer */}
          <div className="fixed left-0 top-0 h-full w-80 z-50 transform transition-transform duration-300 ease-in-out">
            <SidebarContent />
          </div>
        </>
      )}

      {/* Chat Area - Fully Responsive */}
      <div className="flex-1 relative min-w-0 w-full">
        <Chat 
          setListening={setListening} 
          setSpeaking={setSpeaking} 
          isMobile={isMobile}
          sidebarOpen={sidebarOpen}
          setSidebarOpen={setSidebarOpen}
        />
        
        {/* Voice Circles Overlay */}
        {listening && (
          <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-20 pointer-events-none z-10">
            <VoiceCircle listening={listening} speaking={false} />
          </div>
        )}
      </div>
    </div>
  );
}