from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import platform
import pyttsx3
import json
import datetime
import webbrowser
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
TIME_CMD = "the time"
FACETIME_CMD = "open facetime"
PASS_CMD = "open pass"
VS_CODE = "open vs code"

SITES = {
    "youtube": "https://www.youtube.com",
    "wikipedia": "https://www.wikipedia.com",
    "google": "https://www.google.com",
    "facebook": "https://www.facebook.com",
    "twitter": "https://www.twitter.com",
    "instagram": "https://www.instagram.com",
    "linkedin": "https://www.linkedin.com",
    "reddit": "https://www.reddit.com",
    "github": "https://www.github.com",
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
        # Optional: Implement system shutdown if needed
    elif queries == PLAY_MUSIC_CMD:
        open_application("music")
        response_text = "Playing music."
    elif queries == VS_CODE:
        open_application(r"C:\\Users\\hp\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe")
        response_text = "Opening VS Code."
    elif TIME_CMD in queries:
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
    else:
        response_text = generate_response(queries)

    say(response_text)
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
    if os.path.isfile(app_name):
        os.startfile(app_name)
    else:
        try:
            if os_name == "Darwin":  # macOS
                open_mac_application(app_name)
            elif os_name == "Windows":
                os.system(f"start {app_name}")
            elif os_name == "Linux":
                os.system(f"xdg-open {app_name}")
        except Exception as e:
            print(f"Error opening {app_name}: {e}")

def open_mac_application(app_name):
    if app_name == "facetime":
        os.system("open /System/Applications/FaceTime.app")
    elif app_name == "pass":
        os.system("open /Applications/Passky.app")
    elif app_name == "music":
        os.system(f"open {MUSIC_PATH}")

def open_site(site_name):
    if site_name in SITES:
        webbrowser.open(SITES[site_name])

if __name__ == '__main__':
    app.run(debug=True)