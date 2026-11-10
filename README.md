# LLM Serving Benchmarks

A hands-on Python project for serving language models locally and measuring how they respond to single and concurrent requests. The project uses Ollama on Windows and vLLM in a Linux container through Docker Desktop. The vLLM setup runs on CPU.

The benchmarks measure how long a user waits for the first visible text, how long the full response takes, and how many requests the server completes per second under a small concurrent load.

## Benchmark scripts

| Script                     | Server | What it measures                                                                           |
| -------------------------- | ------ | ------------------------------------------------------------------------------------------ |
| `benchmark.py`             | Ollama | Total response time for one non-streaming request                                          |
| `benchmark_stream.py`      | Ollama | Time to first text, total response time, average text chunk gap, and generation throughput |
| `benchmark_load.py`        | Ollama | Per-request latency, average latency, total test time, and request throughput              |
| `benchmark_vllm.py`        | vLLM   | Total response time for one non-streaming request                                          |
| `benchmark_vllm_stream.py` | vLLM   | Time to first text and total response time                                                 |
| `benchmark_vllm_load.py`   | vLLM   | Per-request latency, average latency, total test time, and request throughput              |

## Prerequisites

- Python with the `requests` package
- Ollama for the Ollama benchmarks
- Docker Desktop running Linux containers for the vLLM benchmarks
- Internet access for the initial image and model downloads

Run the commands below in PowerShell from the project directory.

```powershell
python -m pip install requests
```

## Run the Ollama benchmarks

Open Ollama and download the model if it is missing.

```powershell
ollama list
ollama pull llama3.1:8b
```

The scripts send requests to `http://localhost:11434/api/chat`.

```powershell
python benchmark.py
python benchmark_stream.py
python benchmark_load.py
```

## Run the vLLM benchmarks

### 1. Start the CPU server

With Docker Desktop running, download the vLLM CPU image for x86-64.

```powershell
docker pull vllm/vllm-openai-cpu:latest-x86_64
```

Start the container in a dedicated PowerShell terminal.

```powershell
docker run --rm --name vllm-cpu `
    --shm-size=1g `
    -p 127.0.0.1:8000:8000 `
    -v vllm-hf-cache:/root/.cache/huggingface `
    -e VLLM_CPU_KVCACHE_SPACE=1 `
    vllm/vllm-openai-cpu:latest-x86_64 `
    Qwen/Qwen2.5-0.5B-Instruct --dtype float32 --max-model-len 1024
```

The named Docker volume caches model files across container restarts. The server listens locally on port `8000`. Allow several minutes for the initial model load and warm-up, and keep the terminal open while running the benchmarks.

### 2. Verify the model is available

Wait for `Application startup complete`, then open a second PowerShell terminal.

```powershell
(Invoke-RestMethod http://127.0.0.1:8000/v1/models).data |
    Select-Object id
```

Expected model ID:

```text
Qwen/Qwen2.5-0.5B-Instruct
```

### 3. Run the scripts

The vLLM scripts send requests to the OpenAI-compatible endpoint at `http://127.0.0.1:8000/v1/chat/completions`.

```powershell
python benchmark_vllm.py
python benchmark_vllm_stream.py
python benchmark_vllm_load.py
```

To stop the server, press `Ctrl+C` in its terminal or run `docker stop vllm-cpu` from the second terminal.

## How the measurements work

The scripts use Python's `perf_counter()` to measure elapsed time. Both load scripts send one warm-up request before measuring a single request and a batch of three concurrent requests. They use `ThreadPoolExecutor` to submit the concurrent requests and set a maximum of 60 generated tokens per request. Actual output lengths can vary.

| Metric                     | Definition                                                                                                                                                          |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Total response time**    | Time from starting the HTTP request until the client receives the full response or finishes reading the stream                                                      |
| **Time to first text**     | Time until the client reads the first non-empty text chunk. This is a practical approximation of time to first token (TTFT).                                        |
| **Average text chunk gap** | Average time between consecutive text chunks received by the client. A chunk can contain multiple tokens, so this is an approximation of inter-token latency (ITL). |
| **Generation throughput**  | Generated tokens divided by the generation duration reported by Ollama, in tokens per second                                                                        |
| **Average latency**        | Arithmetic mean of the individual request durations in a load test                                                                                                  |
| **Request throughput**     | Completed requests divided by the total test duration, in requests per second                                                                                       |

## Observed results

The tests were run on Windows with an **Intel Core i5-12450H** (8 cores), **15.7 GB RAM**, and **Intel UHD Graphics**. The vLLM container used the CPU and reported vLLM version `0.33.0`.

### Streaming

| Server and model                  | Time to first text | Total response time | Average text chunk gap | Generation throughput |
| --------------------------------- | -----------------: | ------------------: | ---------------------: | --------------------: |
| Ollama · Llama 3.1 8B             |            26.38 s |             42.29 s |              388.91 ms |         2.64 tokens/s |
| Ollama · Llama 3.1 8B, repeat run |             2.27 s |             15.54 s |              270.91 ms |         3.77 tokens/s |
| vLLM · Qwen 2.5 0.5B Instruct     |             1.42 s |             10.39 s |                      — |                     — |

The vLLM streaming script reports the first-text and total response times. In a separate non-streaming run, the vLLM script received the full response in **13.87 seconds**.

### Load test

| Server and model              | Concurrent requests | Average latency | Total test time | Request throughput |
| ----------------------------- | ------------------: | --------------: | --------------: | -----------------: |
| Ollama · Llama 3.1 8B         |                   1 |         14.90 s |         14.90 s |   0.067 requests/s |
| Ollama · Llama 3.1 8B         |                   3 |         30.85 s |         45.70 s |   0.066 requests/s |
| vLLM · Qwen 2.5 0.5B Instruct |                   1 |         10.44 s |         10.45 s |   0.096 requests/s |
| vLLM · Qwen 2.5 0.5B Instruct |                   3 |          8.20 s |          9.49 s |   0.316 requests/s |

Request throughput is shown to three decimal places using the recorded test times. The scripts print two decimal places.

In the Ollama run, increasing concurrency from one to three raised average latency while request throughput stayed close to its original value. In the vLLM run, the three-request batch completed in 9.49 seconds and achieved about 3.3 times the single-request throughput.

These results describe two local configurations using different models. To isolate the effect of the serving engine, use the same model and comparable generation settings on both servers, then repeat each test across several runs.

## Troubleshooting

| Symptom                                                  | What to check                                                                                                             |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Ollama connection error                                  | Open Ollama, then run `ollama list` to verify that the server responds and `llama3.1:8b` is available.                    |
| vLLM connection closes during startup                    | Check the container logs and wait for `Application startup complete` before calling `/v1/models`.                         |
| `Insufficient space in /dev/shm`                         | Start the container with `--shm-size=1g`. The initial run had 64 MiB available and vLLM requested 160 MiB.                |
| vLLM logs show `Warming up model for the compilation...` | Leave the terminal open while the server finishes initializing. Check the logs for an error if startup stops progressing. |
