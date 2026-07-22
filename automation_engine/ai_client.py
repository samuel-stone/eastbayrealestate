import os
import requests


OLLAMA_URL = os.getenv(
    "OLLAMA_HOST",
    "http://localhost:11434/api/generate"
)

MODEL_NAME = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2:3b"
)


def ask_ollama(prompt, timeout=120):

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 768
        }
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=timeout
        )

        response.raise_for_status()

        return response.json().get(
            "response",
            ""
        )

    except Exception as e:

        return (
            f"AI unavailable. "
            f"Fallback analysis required. "
            f"Error: {e}"
        )
