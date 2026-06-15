#!/usr/bin/env python
"""Parity test: vLLM adapter (/api/v1/generate) vs real inference_server.

Checks:
  A. SCHEMA parity  — adapter response shape matches the real server's.
  B. PARAM behavior — each GenerateParams field does what the spec says,
                      exercised on the adapter with well-designed inputs.

The two servers run DIFFERENT models (real=Qwen3.5-4B HF, adapter=Gemma vLLM),
so we do NOT compare generated text — we compare API contract + param semantics.

Usage:
  python parity_test.py [ADAPTER_URL] [REAL_URL] [REAL_SECRET]
"""
import json
import os
import sys
import urllib.request

ADAPTER = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8300"
REAL = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:9080"
# Secret for the real inference_server (only needed for the schema-parity call).
SECRET = sys.argv[3] if len(sys.argv) > 3 else os.environ.get("INFERENCE_SERVER_SECRET", "")

PASS, FAIL = [], []


def call(base, body, secret=None, timeout=120):
    headers = {"Content-Type": "application/json"}
    if secret:
        headers["secret"] = secret
    req = urllib.request.Request(base + "/api/v1/generate",
                                 data=json.dumps(body).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, None


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  — {detail}" if detail and not cond else ""))


def words(result):
    """response continuation = generated_text minus the echoed prompt."""
    return result


print("== A. SCHEMA PARITY (real server vs adapter) ==")
body = {"text": "The quick brown fox", "max_length": 24, "temperature": 0.0}
rs, rj = call(REAL, body, SECRET)
as_, aj = call(ADAPTER, body)
real_keys = set(rj[0].keys()) if rj else set()
ad_keys = set(aj[0].keys()) if aj else set()
print(f"  real keys   : {sorted(real_keys)}")
print(f"  adapter keys: {sorted(ad_keys)}")
check("adapter returns a JSON list", isinstance(aj, list))
check("adapter has generated_text/stop_reason/thinking_content",
      {"generated_text", "stop_reason", "thinking_content"}.issubset(ad_keys))
check("adapter schema is superset of real server schema",
      real_keys.issubset(ad_keys), f"missing {real_keys - ad_keys}")
check("generated_text echoes the input prompt",
      bool(aj) and aj[0]["generated_text"].startswith(body["text"]))

print("\n== B. PARAM BEHAVIOR (adapter) ==")

# empty text -> 400
st, _ = call(ADAPTER, {"text": ""})
check("empty text -> HTTP 400", st == 400, f"got {st}")

# number_of_results
_, j = call(ADAPTER, {"text": "Write a tiny rhyme.", "max_length": 20,
                      "temperature": 0.9, "number_of_results": 3})
check("number_of_results=3 -> 3 results", bool(j) and len(j) == 3, f"got {len(j) if j else 0}")

# max_length bounds response length (chars as a proxy: fewer tokens => shorter)
_, short = call(ADAPTER, {"text": "Tell me about the ocean.", "max_length": 8, "temperature": 0})
_, long = call(ADAPTER, {"text": "Tell me about the ocean.", "max_length": 120, "temperature": 0})
slen = len(short[0]["generated_text"]) if short else 0
llen = len(long[0]["generated_text"]) if long else 0
check("max_length: small cap yields shorter output than large cap", slen < llen, f"{slen} vs {llen}")

# stop_sequences: two-phase — generate, pick a word from the continuation, stop on it
_, base = call(ADAPTER, {"text": "List three colors:", "max_length": 40, "temperature": 0})
cont = base[0]["generated_text"][len("List three colors:"):].strip() if base else ""
toks = [w.strip(".,!?;:") for w in cont.split() if len(w.strip(".,!?;:")) >= 4]
if toks:
    stopw = toks[len(toks) // 2]
    _, sj = call(ADAPTER, {"text": "List three colors:", "max_length": 40,
                           "temperature": 0, "stop_sequences": [stopw]})
    rcont = sj[0]["generated_text"][len("List three colors:"):] if sj else ""
    check(f"stop_sequences excludes the stop word ('{stopw}')", stopw not in rcont,
          f"still present in: {rcont!r}")
    check("stop_sequences sets stop_reason to the matched sequence",
          sj and sj[0]["stop_reason"] == stopw, f"reason={sj[0]['stop_reason'] if sj else None}")
else:
    print("  [SKIP] stop_sequences (no usable continuation word)")

# max_sentences
_, ms = call(ADAPTER, {"text": "Describe a sunset in several sentences.",
                       "max_length": 200, "temperature": 0, "max_sentences": 2})
import re
if ms:
    txt = ms[0]["generated_text"][len("Describe a sunset in several sentences."):]
    n_sent = len(re.findall(r"[.!?](?:\s|$)", txt))
    check("max_sentences=2 -> <=2 sentence enders", n_sent <= 2, f"found {n_sent}")

# min_probability: a high threshold should truncate and set reason
_, mp = call(ADAPTER, {"text": "Invent a surprising twist:", "max_length": 120,
                       "temperature": 0, "min_probability": 0.5})
if mp:
    check("min_probability high threshold truncates (reason or short output)",
          mp[0]["stop_reason"] in ("min_probability", "max_length", "stop"),
          f"reason={mp[0]['stop_reason']}")
    check("min_probability=0.5 triggered min_probability stop_reason",
          mp[0]["stop_reason"] == "min_probability",
          f"reason={mp[0]['stop_reason']} (may be ok if model very confident)")

print(f"\n== RESULT: {len(PASS)} passed, {len(FAIL)} failed ==")
if FAIL:
    print("FAILED:", ", ".join(FAIL))
sys.exit(1 if FAIL else 0)
