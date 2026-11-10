import json
from time import perf_counter

import requests


first_text_time = None
start = perf_counter()

with requests.post(
    "http://127.0.0.1:8000/v1/chat/completions",
    json={
        "model": "Qwen/Qwen2.5-0.5B-Instruct",
        "messages": [
            {
                "role": "user",
                "content": "Explain what a REST API is in one sentence.",
            }
        ],
        "max_tokens": 60,
        "stream": True,
    },
    stream=True,
    timeout=120,
) as response:
    response.raise_for_status()
    print("Answer:")

    for line in response.iter_lines():
        if not line.startswith(b"data:"):
            continue

        data = line[len(b"data:"):].strip()
        if data == b"[DONE]":
            break

        chunk = json.loads(data)
        choices = chunk.get("choices", [])
        text = choices[0]["delta"].get("content") if choices else None

        if text:
            if first_text_time is None:
                first_text_time = perf_counter() - start

            print(text, end="", flush=True)

    elapsed = perf_counter() - start

print()
if first_text_time is not None:
    print(f"Time to first text: {first_text_time:.2f} seconds")
else:
    print("No answer text received.")

print(f"Total response time: {elapsed:.2f} seconds")