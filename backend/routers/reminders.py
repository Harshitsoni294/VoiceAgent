from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import json
import os
from datetime import datetime
import asyncio
import threading
import tempfile
import webbrowser

router = APIRouter()
REMINDERS_FILE = "reminders.json"
BASE_URL = os.getenv('BASE_URL', 'http://localhost:8000/mcp')

# Helper to load reminders

def load_reminders():
    if not os.path.exists(REMINDERS_FILE):
        return []
    with open(REMINDERS_FILE, "r") as f:
        return json.load(f)

# Helper to save reminders

def save_reminders(reminders):
    with open(REMINDERS_FILE, "w") as f:
        json.dump(reminders, f)

@router.get("")
async def list_reminders():
    reminders = load_reminders()
    # Only return reminders with valid datetime format
    valid_reminders = []
    
    for reminder in reminders:
        if "datetime" in reminder:
            try:
                datetime.strptime(reminder["datetime"], "%Y-%m-%d %H:%M:%S")
                valid_reminders.append(reminder)
            except ValueError:
                print(f"Invalid datetime format in reminder: {reminder}")
        else:
            print(f"Skipping reminder without datetime: {reminder}")
    
    # Save only valid reminders back to file
    if len(valid_reminders) != len(reminders):
        save_reminders(valid_reminders)
    
    return valid_reminders

@router.post("")
async def add_reminder(request: Request):
    data = await request.json()
    print("Received data:", data)  # Debugging log

    # Combine date and time if separate fields are provided
    if "date" in data and "time" in data:
        # Ensure time is in HH:MM:SS format
        if len(data["time"].split(":")) == 2:
            data["time"] += ":00"
        data["datetime"] = f"{data['date']} {data['time']}"

    # Validate date and time
    try:
        reminder_time = datetime.strptime(data["datetime"], "%Y-%m-%d %H:%M:%S")
        if reminder_time < datetime.now():
            return JSONResponse(content={"error": "Cannot set a reminder for a past time."}, status_code=400)
    except (KeyError, ValueError):
        print("Invalid datetime format or missing field")  # Debugging log
        return JSONResponse(content={"error": "Invalid or missing 'datetime' field. Use format 'YYYY-MM-DD HH:MM:SS'."}, status_code=400)

    reminders = load_reminders()
    reminders.append({"text": data["text"], "datetime": data["datetime"]})
    save_reminders(reminders)
    print("Reminder added:", {"text": data["text"], "datetime": data["datetime"]})  # Debugging log
    return {"status": "added", "reminder": {"text": data["text"], "datetime": data["datetime"]}}

@router.delete("")
async def delete_reminder(request: Request):
    data = await request.json()
    reminders = load_reminders()

    # Match text and datetime for precise deletion
    reminders = [r for r in reminders if not (
        r.get("text") == data.get("text") and 
        r.get("datetime") == data.get("datetime")
    )]

    save_reminders(reminders)
    return {"status": "deleted"}

@router.post("/stop-alarm")
async def stop_alarm(request: Request):
    # Optional endpoint for alarm popup to call when stopped
    return {"status": "alarm_stopped"}

@router.get("/alarm/{reminder_text}")
async def get_alarm_popup(reminder_text: str):
    from fastapi.responses import HTMLResponse
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚨 ALARM - VoiceAgent</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>⏰</text></svg>">
    <style>
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.1); }}
        }}
        @keyframes shake {{
            0%, 100% {{ transform: translateX(0); }}
            25% {{ transform: translateX(-15px); }}
            75% {{ transform: translateX(15px); }}
        }}
        @keyframes flash {{
            0%, 100% {{ background: linear-gradient(135deg, #ef4444, #ec4899); }}
            50% {{ background: linear-gradient(135deg, #dc2626, #db2777); }}
        }}
        .alarm-pulse {{
            animation: pulse 1s infinite, shake 0.8s infinite;
        }}
        .alarm-bg {{
            animation: flash 2s infinite;
        }}
        body {{
            overflow: hidden;
        }}
    </style>
</head>
<body class="alarm-bg min-h-screen flex items-center justify-center p-4">
    <div class="alarm-pulse bg-white rounded-3xl shadow-2xl p-8 max-w-lg w-full mx-4 text-center border-4 border-red-500">
        <div class="text-8xl mb-6 animate-bounce">⏰</div>
        <h1 class="text-4xl font-black text-red-600 mb-6 uppercase tracking-wide">🚨 ALARM! 🚨</h1>
        <div class="bg-gradient-to-r from-red-100 to-pink-100 rounded-2xl p-6 mb-8 border-2 border-red-300">
            <p class="text-2xl font-bold text-gray-800">{reminder_text}</p>
        </div>
        <button 
            onclick="stopAlarm()" 
            class="w-full bg-gradient-to-r from-red-600 to-pink-600 text-white text-2xl font-black py-6 px-8 rounded-2xl hover:from-red-700 hover:to-pink-700 transform hover:scale-105 transition-all duration-200 shadow-2xl border-4 border-red-800 uppercase tracking-wide">
            🛑 STOP ALARM 🛑
        </button>
        <div class="mt-6 text-lg text-gray-700 font-semibold">
            <p>Press <kbd class="bg-gray-200 px-2 py-1 rounded">SPACE</kbd>, <kbd class="bg-gray-200 px-2 py-1 rounded">ENTER</kbd>, or <kbd class="bg-gray-200 px-2 py-1 rounded">ESC</kbd> to stop</p>
        </div>
    </div>
    
    <script>
        console.log('🚨 Alarm popup loaded for: {reminder_text}');
        
        // Multiple alarm sounds for better compatibility
        let audioContext = null;
        let oscillator = null;
        let gainNode = null;
        
        // Create Web Audio API alarm sound
        function createWebAudioAlarm() {{
            try {{
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                oscillator = audioContext.createOscillator();
                gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
                gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
                
                oscillator.start();
                
                // Create alarm pattern
                let isHigh = true;
                setInterval(() => {{
                    if (oscillator && audioContext) {{
                        oscillator.frequency.setValueAtTime(isHigh ? 1000 : 800, audioContext.currentTime);
                        isHigh = !isHigh;
                    }}
                }}, 500);
                
                console.log('✅ Web Audio alarm started');
            }} catch (e) {{
                console.log('❌ Web Audio failed:', e);
            }}
        }}
        
        // HTML5 Audio fallback
        function createHTMLAudioAlarm() {{
            try {{
                // Create multiple beep sounds
                const audioData = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2+LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+LyvmgdEQgz';
                const audio = new Audio(audioData);
                audio.loop = true;
                audio.volume = 0.7;
                
                const playPromise = audio.play();
                if (playPromise !== undefined) {{
                    playPromise.then(() => {{
                        console.log('✅ HTML5 Audio alarm started');
                        window.alarmAudio = audio;
                    }}).catch(e => {{
                        console.log('❌ HTML5 Audio failed:', e);
                        createWebAudioAlarm();
                    }});
                }}
            }} catch (e) {{
                console.log('❌ HTML5 Audio creation failed:', e);
                createWebAudioAlarm();
            }}
        }}
        
        function stopAlarm() {{
            console.log('🛑 Stopping alarm...');
            
            // Stop Web Audio
            if (oscillator) {{
                try {{
                    oscillator.stop();
                    oscillator = null;
                }} catch (e) {{}}
            }}
            if (audioContext) {{
                try {{
                    audioContext.close();
                    audioContext = null;
                }} catch (e) {{}}
            }}
            
            // Stop HTML5 Audio
            if (window.alarmAudio) {{
                try {{
                    window.alarmAudio.pause();
                    window.alarmAudio.currentTime = 0;
                }} catch (e) {{}}
            }}
            
            // Send stop request to backend
            fetch('/mcp/reminders/stop-alarm', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{'action': 'stop'}})
            }}).catch(() => {{}});
            
            // Close or redirect
            if (window.opener) {{
                window.close();
            }} else {{
                window.location.href = '/';
            }}
        }}
        
        // Start alarm sounds immediately
        createHTMLAudioAlarm();
        
        // Backup: also try Web Audio after a delay
        setTimeout(() => {{
            if (!window.alarmAudio) {{
                createWebAudioAlarm();
            }}
        }}, 1000);
        
        // Handle keyboard shortcuts
        document.addEventListener('keydown', function(event) {{
            if (event.code === 'Space' || event.code === 'Enter' || event.code === 'Escape') {{
                event.preventDefault();
                stopAlarm();
            }}
        }});
        
        // Handle clicks anywhere to stop
        document.addEventListener('click', function() {{
            stopAlarm();
        }});
        
        // Auto-close after 10 minutes
        setTimeout(() => {{
            console.log('⏰ Auto-closing alarm after 10 minutes');
            stopAlarm();
        }}, 600000);
        
        // Focus window and make sure it's visible
        window.focus();
        
        // Change page title to flash
        let titleFlash = true;
        setInterval(() => {{
            document.title = titleFlash ? '🚨🚨🚨 ALARM! 🚨🚨🚨' : '⏰⏰⏰ REMINDER! ⏰⏰⏰';
            titleFlash = !titleFlash;
        }}, 1000);
        
        // Try to enable sound on any user interaction
        document.addEventListener('touchstart', createHTMLAudioAlarm);
        document.addEventListener('mousedown', createHTMLAudioAlarm);
    </script>
</body>
</html>
    """
    
    return HTMLResponse(content=html_content)

# Function to create alarm popup
def create_alarm_popup(reminder_text):
    print(f"Creating alarm popup for: {reminder_text}")
    
    try:
        import urllib.parse
        encoded_text = urllib.parse.quote(reminder_text)
        alarm_url = f"{BASE_URL}/reminders/alarm/{encoded_text}"
        
        print(f"Alarm URL: {alarm_url}")
        print("🚨 ALARM TRIGGERED! 🚨")
        print(f"Open this URL in your browser: {alarm_url}")
        print("=" * 50)
        
        # Try to open in default browser as backup
        try:
            webbrowser.open(alarm_url)
            print("✅ Opened alarm in browser")
        except Exception as e:
            print(f"❌ Could not open browser: {e}")
        
        return alarm_url
        
    except Exception as e:
        print(f"Error creating alarm popup: {e}")
        raise

# Function to monitor reminders and play alarm
async def monitor_reminders():
    while True:
        reminders = load_reminders()
        current_time = datetime.now()
        updated_reminders = []
        
        for reminder in reminders:
            if "datetime" not in reminder:
                continue
                
            try:
                reminder_time = datetime.strptime(reminder["datetime"], "%Y-%m-%d %H:%M:%S")
                print(f"Parsed reminder time: {reminder_time}, Current time: {current_time}")
                if reminder_time <= current_time:
                    print(f"Alarm for reminder: {reminder['text']}")
                    # Create and show alarm popup
                    try:
                        create_alarm_popup(reminder['text'])
                        print("Alarm popup created successfully")
                    except Exception as e:
                        print(f"Error creating alarm popup: {e}")
                    # Don't add to updated list (removes the reminder)
                else:
                    updated_reminders.append(reminder)
            except ValueError as e:
                print(f"Invalid datetime format in reminder: {reminder}, Error: {e}")
                # Still add invalid reminders to keep them (don't remove them)
                updated_reminders.append(reminder)
            except Exception as e:
                print(f"Unexpected error processing reminder: {reminder}, Error: {e}")
                updated_reminders.append(reminder)
        
        # Save updated reminders (without triggered ones)
        if len(updated_reminders) != len(reminders):
            save_reminders(updated_reminders)
            
        await asyncio.sleep(60)  # Check every minute

# Start the monitoring in a separate thread - REMOVED: Now handled client-side
# threading.Thread(target=lambda: asyncio.run(monitor_reminders()), daemon=True).start()
