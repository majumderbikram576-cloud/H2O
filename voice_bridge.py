import subprocess
import json
import os
import time
import requests
from datetime import datetime

BASE = os.path.expanduser("~/myassistant_V3")
UI_STATE = os.path.join(BASE, "ui", "state.json")
CHAT_FILE = os.path.join(BASE, "ui", "chat.json")

API_KEY = os.environ.get("GEMINI_API_KEY")
URL = "https://generativelanguage.googleapis.com/v1/interactions"


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w") as f:
        json.dump(data, f)


def set_state(state):
    write_json(UI_STATE, {"state": state})


def add_chat(role, text):
    try:
        if os.path.exists(CHAT_FILE):
            with open(CHAT_FILE, "r") as f:
                messages = json.load(f)
        else:
            messages = []

        messages.append({
            "role": role,
            "text": text
        })

        write_json(CHAT_FILE, messages[-20:])

    except Exception as e:
        print("Chat save error:", e)


def speak(text):
    if not text:
        return

    set_state("speaking")

    try:
        subprocess.run(
            ["termux-tts-speak", text],
            check=False
        )

    except Exception as e:
        print("TTS error:", e)

    finally:
        set_state("idle")


def listen():
    set_state("listening")

    try:
        result = subprocess.run(
            ["termux-speech-to-text"],
            capture_output=True,
            text=True,
            timeout=30
        )

        text = result.stdout.strip()

        if text:
            print("Recognized:", text)
            return text

        if result.stderr.strip():
            print("Speech error:", result.stderr.strip())

        return ""

    except subprocess.TimeoutExpired:
        print("Speech timeout.")
        return ""

    except KeyboardInterrupt:
        raise

    except Exception as e:
        print("Speech error:", e)
        return ""


def local_reply(command):

    text = command.lower().strip()

    if not text:
        return "I didn't catch that, boss."

    if "hello" in text or "hi" in text:
        return "Hello boss. MyAssistant is ready."

    if "your name" in text or "who are you" in text:
        return "I'm MyAssistant. Nice to hear from you."

    if "how are you" in text:
        return "I'm doing great, boss. Ready when you are."

    if "thank" in text:
        return "You're welcome, boss."

    if "good morning" in text:
        return "Good morning, boss. Let's make today interesting."

    if "good night" in text:
        return "Good night, boss. Sleep well."

    if "time" in text:
        return "It's " + datetime.now().strftime("%I:%M %p") + " right now."

    if "date" in text or "today" in text:
        return "Today is " + datetime.now().strftime("%d %B %Y") + "."

    return "I heard you, boss. Gemini is temporarily unavailable."


def ask_ai(command):

    if not API_KEY:
        return local_reply(command)

    headers = {
        "x-goog-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "model": "gemini-3.6-flash",
        "input": command
    }

    try:
        response = requests.post(
            URL,
            headers=headers,
            json=data,
            timeout=15
        )

        if response.status_code == 429:
            print("Gemini quota exhausted. Using local reply.")
            return local_reply(command)

        if response.status_code != 200:
            print("Gemini HTTP:", response.status_code)
            return local_reply(command)

        result = response.json()

        for step in result.get("steps", []):

            if step.get("type") == "model_output":

                for item in step.get("content", []):

                    if item.get("type") == "text":

                        answer = item.get("text", "").strip()

                        if answer:
                            return answer

        return local_reply(command)

    except requests.Timeout:
        print("Gemini request timed out.")
        return local_reply(command)

    except Exception as e:
        print("AI connection error:", e)
        return local_reply(command)


def main():

    print("MyAssistant V3 starting...")

    set_state("idle")

    write_json(CHAT_FILE, [])

    speak("MyAssistant V3 is ready, boss.")

    while True:

        try:

            print("\nListening...")

            text = listen()

            if not text:

                print("No speech detected.")

                set_state("idle")

                time.sleep(2)

                continue

            print("You:", text)

            add_chat("you", text)

            command = text.lower().strip()

            if command in ["exit", "stop", "quit"]:

                answer = "Alright boss. See you later."

                print("Assistant:", answer)

                add_chat("assistant", answer)

                speak(answer)

                break

            answer = ask_ai(text)

            print("Assistant:", answer)

            add_chat("assistant", answer)

            speak(answer)

            time.sleep(0.5)

        except KeyboardInterrupt:

            print("\nMyAssistant V3 stopped.")

            set_state("idle")

            break

        except Exception as e:

            print("Main error:", e)

            set_state("idle")

            time.sleep(2)


if __name__ == "__main__":
    main()
