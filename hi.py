import sys
import json
import requests

# Forces your Windows terminal to accept emojis/UTF-8 characters safely
sys.stdout.reconfigure(encoding="utf-8")

url = "http://localhost:11434/api/chat"
user_prompt = "Tell me a 1-sentence programming joke."

print(f"Sending prompt to Gemma 3: '{user_prompt}'\n")

payload = {
    "model": "gemma3:latest",
    "messages": [{"role": "user", "content": user_prompt}],
}

try:
    # stream=True keeps the connection open for incoming word chunks
    response = requests.post(url, json=payload, stream=True, timeout=60)

    if response.status_code == 200:
        print("Gemma 3 says:\n")

        for line in response.iter_lines(decode_unicode=True):
            if line:
                try:
                    json_data = json.loads(line)
                    if "message" in json_data and "content" in json_data["message"]:
                        # Simply print the string directly; sys.stdout handles the encoding now
                        print(json_data["message"]["content"], end="", flush=True)
                except json.JSONDecodeError:
                    pass

        print("\n\n---\nSuccess!")
    else:
        print(f"Error: {response.status_code}")

except requests.exceptions.ConnectionError:
    print("\n[ERROR]: Could not connect to Ollama. Is the Ollama app open?")