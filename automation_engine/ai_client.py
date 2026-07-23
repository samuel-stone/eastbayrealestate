import os
import time
import random
import json
import requests

from google import genai
from google.genai import errors


# Lazy-loaded Gemini client
_gemini_client = None


def get_gemini_client():
    """
    Lazily initialize Gemini only when required.

    This prevents worker startup failures when
    GEMINI_API_KEY is not configured.
    """

    global _gemini_client

    if _gemini_client is not None:
        return _gemini_client

    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    _gemini_client = genai.Client(
        api_key=api_key
    )

    return _gemini_client



def route_task(task_type: str) -> str:
    """
    Hybrid AI routing.

    Cheap deterministic tasks:
        Ollama

    Complex reasoning:
        Gemini
    """

    ollama_tasks = [
        "formatting",
        "lint_summary",
        "static_analysis_restatement",
        "simple_review"
    ]

    if task_type in ollama_tasks:
        return "ollama"

    return "gemini"



def ask_ollama(prompt: str):
    """
    Local Ollama generation.
    """

    model = os.environ.get(
        "OLLAMA_MODEL",
        "llama3.2:3b"
    )

    url = "http://127.0.0.1:11434/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 1200
        }
    }

    response = requests.post(
        url,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    return data.get(
        "response",
        ""
    ).strip()



def ask_gemini(prompt: str, max_retries: int = 4):
    """
    Gemini generation with exponential backoff.
    """

    client = get_gemini_client()

    for attempt in range(max_retries):

        try:

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            return response.text.strip()


        except Exception as exc:

            print(
                f"[Gemini] Attempt {attempt + 1}/{max_retries} failed: {exc}"
            )

            if attempt == max_retries - 1:
                raise

            sleep_time = (
                2 ** attempt
            ) + random.random()

            time.sleep(
                sleep_time
            )



def ask_ai(
    prompt: str,
    task_type: str = "judgment_call",
    max_retries: int = 4
):
    """
    Main AI gateway.

    Routes requests between:
        - Ollama
        - Gemini

    Automatically falls back when Gemini
    is unavailable.
    """

    provider = route_task(task_type)

    print(
        f"[AI Client] Routing task '{task_type}' -> {provider}"
    )


    if provider == "ollama":

        try:

            return {
                "provider": "ollama",
                "response": ask_ollama(prompt)
            }

        except Exception as exc:

            return {
                "provider": "ollama",
                "response": "",
                "error": str(exc)
            }



    # Gemini path

    try:

        return {
            "provider": "gemini",
            "response": ask_gemini(
                prompt,
                max_retries=max_retries
            )
        }


    except Exception as gemini_error:

        print(
            "[AI Client] Gemini unavailable. "
            "Falling back to Ollama."
        )

        try:

            return {
                "provider": "ollama_fallback",
                "response": ask_ollama(prompt),
                "gemini_error": str(gemini_error)
            }


        except Exception as ollama_error:

            return {
                "provider": "failed",
                "response": "",
                "gemini_error": str(gemini_error),
                "ollama_error": str(ollama_error)
            }