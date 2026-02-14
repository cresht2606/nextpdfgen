import requests, json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:4b-instruct"

def call_ollama_stream(prompt: str, stop_flag_callable):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.25,
            "num_predict": 512,
            "top_p": 0.9
        }
    }

    response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=600)
    response.raise_for_status()

    for line in response.iter_lines():
        if stop_flag_callable():
            break

        if line:
            data = json.loads(line.decode("utf-8"))
            token = data.get("response", "")
            yield token

            if data.get("done"):
                break

    response.close()

