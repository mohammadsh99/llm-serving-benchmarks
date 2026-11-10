from concurrent.futures import ThreadPoolExecutor
from statistics import mean
from time import perf_counter

import requests


def send_request():
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
            "options": {"max_tokens": 60},
            "stream": False,
        },
        timeout=180,
    ) as response:
        response.raise_for_status()

    return perf_counter() - start


def run_test(request_count, workers):
    start = perf_counter()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        tasks = [executor.submit(send_request) for _ in range(request_count)]
        latencies = [task.result() for task in tasks]

    elapsed = perf_counter() - start

    print(f"\nRequests: {request_count} | Workers: {workers}")

    for number, latency in enumerate(latencies, start=1):
        print(f"Request {number}: {latency:.2f} seconds")

    print(f"Average latency: {mean(latencies):.2f} seconds")
    print(f"Total test time: {elapsed:.2f} seconds")
    print(f"Request throughput: {request_count / elapsed:.2f} requests/sec")


print("Warming up the model...")
send_request()

run_test(request_count=1, workers=1)
run_test(request_count=3, workers=3)