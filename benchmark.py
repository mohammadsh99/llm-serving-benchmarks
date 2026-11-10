from time import perf_counter

import requests


start = perf_counter()

response = requests.post(
    "http://localhost:11434/api/chat",
    json={
        "model": "llama3.1:8b",
        "messages": [
            {"role": "user", "content": "Explain what a REST API is in one sentence."}
        ],
        "stream": False,
    },
    timeout=120,
)

elapsed = perf_counter() - start

response.raise_for_status()
answer = response.json()["message"]["content"]

print("Answer:", answer)
print(f"Total response time: {elapsed:.2f} seconds")