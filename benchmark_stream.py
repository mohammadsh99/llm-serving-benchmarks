import json
from time import perf_counter

import requests


first_text_time = None
text_arrival_times = []
start = perf_counter()

with requests.post(
    "http://localhost:11434/api/chat",
    json={
        "model": "llama3.1:8b",
        "messages": [
            {"role": "user", "content": "Explain what a REST API is in one sentence."}
        ],
        "stream": True,
    },
    stream=True,
    timeout=120,
) as response:
    response.raise_for_status()
    print("Answer:")

    for line in response.iter_lines():
        if not line:
            continue

        chunk = json.loads(line)
        text = chunk.get("message", {}).get("content", "")

        if text:
            arrived_at = perf_counter()
            text_arrival_times.append(arrived_at)

            if first_text_time is None:
                first_text_time = arrived_at - start

            print(text, end="", flush=True)

        if chunk.get("done"):
            break

    elapsed = perf_counter() - start

print()

if first_text_time is not None:
    print(f"Time to first text: {first_text_time:.2f} seconds")
else:
    print("No answer text received.")

print(f"Total response time: {elapsed:.2f} seconds")

if len(text_arrival_times) >= 2:
    first_arrival = text_arrival_times[0]
    last_arrival = text_arrival_times[-1]
    gap_count = len(text_arrival_times) - 1

    average_gap_ms = (last_arrival - first_arrival) / gap_count * 1000
    print(f"Average text chunk gap: {average_gap_ms:.2f} ms")

generated_tokens = chunk.get("eval_count", 0)
generation_ns = chunk.get("eval_duration", 0)

if generation_ns > 0:
    generation_seconds = generation_ns / 1_000_000_000
    tokens_per_second = generated_tokens / generation_seconds
    print(f"Generation throughput: {tokens_per_second:.2f} tokens/sec")