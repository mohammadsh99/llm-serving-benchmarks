from time import perf_counter

import requests


start = perf_counter()

response = requests.post(
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
        "stream": False,
    },
    timeout=120,
)

elapsed = perf_counter() - start

response.raise_for_status()
answer = response.json()["choices"][0]["message"]["content"]

print("Answer:", answer)
print(f"Total response time: {elapsed:.2f} seconds")