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
# NOTE: /api/v1/generate forces temperature 0 -> 1.0 and samples (legacy parity),
# so generations are NON-deterministic — an auto-picked stop word may not reappear.
# This end-to-end check is therefore INFORMATIONAL; the deterministic proof of the
# stop_sequences semantics is in section C (pure functions).
toks = [w.strip(".,!?;:") for w in cont.split() if len(w.strip(".,!?;:")) >= 4]
if toks:
    stopw = toks[len(toks) // 2]
    _, sj = call(ADAPTER, {"text": "List three colors:", "max_length": 40,
                           "temperature": 0, "stop_sequences": [stopw]})
    rcont = sj[0]["generated_text"][len("List three colors:"):] if sj else ""
    matched = sj and sj[0]["stop_reason"] == stopw
    print(f"  [INFO] e2e stop_sequences('{stopw}'): excluded={stopw not in rcont}, "
          f"reason={sj[0]['stop_reason'] if sj else None} (non-deterministic, see §C)")
else:
    print("  [SKIP] stop_sequences e2e (no usable continuation word)")

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

print("\n== C. PURE SEMANTICS (deterministic, model-independent) ==")
# Import the adapter's pure post-processing functions and verify exact behavior.
sys.path.insert(0, "/nvme0n1-disk/code/text-generator.io")
try:
    from questions.inference_server.vllm_parity_adapter import (
        _truncate_by_stop_sequences, _truncate_by_max_sentences,
        _truncate_by_min_probability, _split_thinking,
    )
    # stop_sequences: exclusive, first match wins, returns matched string
    t, m = _truncate_by_stop_sequences("alpha beta gamma delta", ["gamma"])
    check("stop_seq: truncates before match (exclusive)", t == "alpha beta " and m == "gamma", f"{t!r},{m}")
    t, m = _truncate_by_stop_sequences("no stop here", ["zzz"])
    check("stop_seq: no match -> unchanged, None", t == "no stop here" and m is None, f"{t!r},{m}")
    t, m = _truncate_by_stop_sequences("x END y END z", ["END"])
    check("stop_seq: first match wins", t == "x " and m == "END", f"{t!r}")

    # max_sentences: keep N sentences
    t, trim = _truncate_by_max_sentences("One. Two. Three. Four.", 2)
    check("max_sentences=2 keeps two sentences", t == "One. Two." and trim, f"{t!r},{trim}")
    t, trim = _truncate_by_max_sentences("Only one sentence here.", 3)
    check("max_sentences: under limit -> unchanged", t == "Only one sentence here." and not trim, f"{t!r}")

    # min_probability: product of per-token argmax probs, inclusive truncate
    keep, trig = _truncate_by_min_probability([0.9, 0.9, 0.5, 0.9], ["a", "b", "c", "d"], 0.5)
    # 0.9, 0.81, 0.405 < 0.5 -> keep 3 (inclusive)
    check("min_probability: inclusive truncate at first dip below thresh", keep == 3 and trig, f"keep={keep},trig={trig}")
    keep, trig = _truncate_by_min_probability([0.99, 0.99, 0.99], ["a", "b", "c"], 0.5)
    check("min_probability: never dips -> keep all, not triggered", keep == 3 and not trig, f"keep={keep},trig={trig}")
    keep, trig = _truncate_by_min_probability([0.9], ["a"], 0.0)
    check("min_probability=0 disabled -> keep all", keep == 1 and not trig, f"keep={keep}")

    # thinking split
    th, resp = _split_thinking("<think>reasoning here</think>\nThe answer is 42.")
    check("thinking split: extracts <think> + response", th == "reasoning here" and resp == "The answer is 42.", f"{th!r}|{resp!r}")
    th, resp = _split_thinking("just a normal response")
    check("thinking split: no tag -> None thinking, full response", th is None and resp == "just a normal response", f"{th!r}|{resp!r}")
except Exception as e:  # noqa: BLE001
    check("pure semantics import + run", False, repr(e))

print(f"\n== RESULT: {len(PASS)} passed, {len(FAIL)} failed ==")
if FAIL:
    print("FAILED:", ", ".join(FAIL))
sys.exit(1 if FAIL else 0)
