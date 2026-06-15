#!/usr/bin/env python
"""Single-stream decode TPS benchmark against a vLLM OpenAI server.

Mirrors the challenge metric (output_tps, greedy temp=0). Sends a few
completion requests forcing a fixed number of output tokens and reports
the marginal decode tok/s (excludes prompt/HTTP overhead by differencing
two output lengths).
"""
import sys
import time
import json
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
MODEL = sys.argv[2] if len(sys.argv) > 2 else "gemma-4-e4b-it"
PROMPT = "Once upon a time in a distant galaxy,"


def call(max_tokens):
    body = json.dumps({
        "model": MODEL,
        "prompt": PROMPT,
        "max_tokens": max_tokens,
        "min_tokens": max_tokens,   # force full-length decode
        "temperature": 0.0,
        "ignore_eos": True,
    }).encode()
    req = urllib.request.Request(BASE + "/v1/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=600) as r:
        out = json.loads(r.read())
    dt = time.perf_counter() - t0
    n = out["usage"]["completion_tokens"]
    return n, dt


def main():
    print("warmup...", flush=True)
    call(16)
    rows = []
    for mt in (64, 256, 512):
        n, dt = call(mt)
        rows.append((n, dt))
        print(f"  {n:4d} tok  {dt:7.3f}s  {n/dt:7.1f} tok/s (incl overhead)", flush=True)
    # marginal decode rate between longest two runs cancels fixed overhead
    (n1, t1), (n2, t2) = rows[-2], rows[-1]
    marginal = (n2 - n1) / (t2 - t1)
    print(f"\nMARGINAL DECODE TPS = {marginal:.1f} tok/s", flush=True)


if __name__ == "__main__":
    main()
