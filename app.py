from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import platform
import datetime
import webbrowser
import shutil
import subprocess
from groq import Groq
import config
import paths

app = Flask(__name__)
CORS(app)

chatStr = ""

@app.route('/command', methods=['POST'])
def handle_command():
    global chatStr, commands, app_commands
    data = request.json
    queries = data.get('command', '').lower()

    chatStr += f"Captain: {queries}\nJarvis: "

    if queries == "shutdown":
        response_text = "Goodbye, sir."
    elif "the time" in queries:
        current_time = datetime.datetime.now().strftime("%H:%M")
        response_text = f"Sir, the time is {current_time}"
    elif any(f"open {site}" in queries for site in paths.sites):
        site_name = queries.split("open ")[1].strip()
        response_text = f"Opening {site_name}."
        open_site(site_name)
    elif any(f"close {site}" in queries for site in paths.sites):
        site_name = queries.split("close ")[1].strip()
        response_text = close_site(site_name)
    elif queries.startswith("open "):
        app_name = queries[5:].strip().lower()
        if app_name in paths.applications:
            result = open_application(paths.applications[app_name])
            response_text = f"Opening {app_name}"
        else:
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
    if site_name in paths.sites:
        webbrowser.open(paths.sites[site_name])

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
    if site_name in paths.sites:
        os_name = platform.system()
        url = paths.sites[site_name]
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