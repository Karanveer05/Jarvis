import json
import urllib.request

def understand(command):
    data = {
        "model": "qwen3:4b",
        "prompt": f"""
Convert this user command into simple structured JSON.

Return only JSON.
Understand the intention yourself.
Do not explain anything.

Format:
{{
    "commands": [
        {{
            "action": "...",
            "value": "...",
            "target": null
        }}
    ]
}}

User command:
{command}
""",
        "stream": False
    }

    request = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(request) as response:
        result = json.loads(response.read().decode())

    return json.loads(result["response"])

while True:
    text = input("Command: ").strip()

    if text.lower() == "exit":
        break

    try:
        result = understand(text)
        print(json.dumps(result, indent=4))
    except Exception as error:
        print("Error:", error)