from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import platform
import pyttsx3
import json
import datetime
import webbrowser
import shutil
import subprocess
from groq import Groq
import config

app = Flask(__name__)
CORS(app)

MUSIC_PATH = r"D:\\Music\\can-you-hear-the-music.mp3"
COMMANDS_FILE = 'commands.json'
APP_COMMANDS_FILE = 'app_commands.json'
CHAT_RESET_CMD = "reset chat"
SHUTDOWN_CMD = "shutdown"
PLAY_MUSIC_CMD = "play music"
FACETIME_CMD = "open facetime"
PASS_CMD = "open pass"
VS_CODE = "open vs code"
CLOSE_VS_CODE = "close vs code"
CLOSE_MUSIC = "close music"

SITES = {
    "youtube": "https://www.youtube.com",
    "wikipedia": "https://www.wikipedia.com",
    "google": "https://www.google.com",
    "facebook": "https://www.facebook.com",
    "twitter": "https://www.twitter.com",
    "instagram": "https://www.instagram.com",
    "linkedin": "https://www.linkedin.com",
    "reddit": "https://www.reddit.com",
    "github website": "https://www.github.com",
    "amazon": "https://www.amazon.com",
    "netflix": "https://www.netflix.com",
    "spotify": "https://www.spotify.com",
    "news": "https://www.cnn.com",
    "email": "https://www.gmail.com"
}

chatStr = ""

def load_commands(file):
    try:
        with open(file, 'r') as f:
            return json.load(f).get('commands', {})
    except FileNotFoundError:
        return {}

def save_commands(commands, file):
    with open(file, 'w') as f:
        json.dump({'commands': commands}, f, indent=4)

commands = load_commands(COMMANDS_FILE)
app_commands = load_commands(APP_COMMANDS_FILE)

@app.route('/command', methods=['POST'])
def handle_command():
    global chatStr, commands, app_commands
    data = request.json
    queries = data.get('command', '').lower()

    chatStr += f"Captain: {queries}\nJarvis: "

    if queries == CHAT_RESET_CMD:
        chatStr = ""
        response_text = "Chat history reset."
    elif queries == SHUTDOWN_CMD:
        response_text = "Goodbye, sir."
    elif queries == PLAY_MUSIC_CMD:
        open_application("music")
        response_text = "Playing music."
    elif queries == CLOSE_MUSIC:
        close_application("music")
        response_text = "Closing music."
    elif queries == VS_CODE:
        open_application(r"C:\\Users\\hp\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe")
        response_text = "Opening VS Code."
    elif queries == CLOSE_VS_CODE:
        close_application("Code.exe")
        response_text = "Closing VS Code."
    elif "the time" in queries:
        current_time = datetime.datetime.now().strftime("%H:%M")
        response_text = f"Sir, the time is {current_time}"
    elif queries == FACETIME_CMD:
        response_text = "Opening FaceTime."
        open_application("facetime")
    elif queries == PASS_CMD:
        response_text = "Opening Pass."
        open_application("pass")
    elif any(f"open {site}" in queries for site in SITES):
        site_name = queries.split("open ")[1].strip()
        response_text = f"Opening {site_name}."
        open_site(site_name)
    elif any(f"close {site}" in queries for site in SITES):
        site_name = queries.split("close ")[1].strip()
        response_text = close_site(site_name)
    elif queries.startswith("open "):
        app_name = queries[5:].strip()
        result = open_application(app_name)
        response_text = result if isinstance(result, str) else f"Opening {app_name}."
    elif queries.startswith("close "):
        app_name = queries[6:].strip()
        result = close_application(app_name)
        response_text = result
    else:
        response_text = generate_response(queries)

    chatStr += f"{response_text}\n"
    return jsonify({"response": response_text})

def generate_response(queries):
    try:
        client = Groq(api_key=config.groq_apikey)
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "user", "content": queries}
            ],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
        )
        response_text = ""
        for chunk in completion:
            response_text += chunk.choices[0].delta.content or ""
        return response_text.strip()
    except Exception as e:
        return f"Some error occurred: {e}"

def say(text):
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Error in text-to-speech: {e}")

def open_application(app_name):
    os_name = platform.system()
    try:
        if os_name == "Darwin":  # macOS
            subprocess.Popen(["open", "-a", app_name])
        elif os_name == "Windows":
            app_path = shutil.which(app_name)
            if app_path:
                os.startfile(app_path)
            else:
                return f"{app_name} not found in system PATH."
        elif os_name == "Linux":
            subprocess.Popen([app_name])
        return f"Opened {app_name}."
    except Exception as e:
        return f"Error opening {app_name}: {e}"

def open_site(site_name):
    if site_name in SITES:
        webbrowser.open(SITES[site_name])

def close_application(app_name):
    os_name = platform.system()
    try:
        if os_name == "Darwin":  # macOS
            subprocess.run(["osascript", "-e", f'tell application "{app_name}" to quit'])
        elif os_name == "Windows":
            subprocess.run(["taskkill", "/F", "/IM", f"{app_name}"], check=True)
        elif os_name == "Linux":
            subprocess.run(["pkill", "-f", app_name])
        return f"Closed {app_name}."
    except subprocess.CalledProcessError:
        return f"Error: {app_name} is not running or couldn't be closed."
    except Exception as e:
        return f"Error closing {app_name}: {e}"

def close_site(site_name):
    if site_name in SITES:
        os_name = platform.system()
        url = SITES[site_name]
        try:
            if os_name == "Darwin":  # macOS
                apple_script = f'''
                tell application "Safari"
                    set window_list to every window
                    repeat with window_item in window_list
                        set tab_list to every tab of window_item
                        repeat with tab_item in tab_list
                            if URL of tab_item contains "{url}" then
                                close tab_item
                            end if
                        end repeat
                    end repeat
                end tell
                '''
                subprocess.run(["osascript", "-e", apple_script])
            elif os_name == "Windows":
                # For Windows, we'll use PowerShell to close specific tabs in Chrome
                ps_script = f'''
                $chrome = Get-Process chrome
                if ($chrome) {{
                    $chrome.CloseMainWindow()
                    $chrome | Where-Object {{$_.MainWindowTitle -like "*{url}*"}} | ForEach-Object {{$_.CloseMainWindow()}}
                }}
                '''
                subprocess.run(["powershell", "-Command", ps_script])
            elif os_name == "Linux":
                # For Linux, we'll use xdotool to close specific tabs in Firefox
                subprocess.run(["xdotool", "search", "--name", url, "windowactivate", "--sync", "key", "ctrl+w"])
            return f"Attempted to close tabs containing {site_name}."
        except subprocess.CalledProcessError:
            return f"Error: Couldn't close tabs for {site_name}."
        except Exception as e:
            return f"Error closing tabs for {site_name}: {e}"
    else:
        return f"{site_name} is not in the list of known sites."

if __name__ == '__main__':
    app.run(debug=True)