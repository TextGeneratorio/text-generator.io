#!/usr/bin/env python
"""Tests for autocomplete token healing in the vLLM parity adapter.

Section A: DETERMINISTIC pure-function tests (no server needed) — the core
           healing logic: tail split (with leading space), token-boundary index,
           straddle-remainder reconstruction, logprob parsing.
Section B: LIVE invariants against a running adapter (optional) — the user's
           input is always preserved as a prefix, and the reported boundary bug
           ("lookingfor") does not recur.

Usage:
  python test_autocomplete_healing.py            # section A only
  python test_autocomplete_healing.py http://127.0.0.1:8300   # + live section B
"""
import sys

sys.path.insert(0, "/nvme0n1-disk/code/text-generator.io")

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  — {detail}" if detail and not cond else ""))


from questions.inference_server.vllm_parity_adapter import (  # noqa: E402
    _split_heal_tail, _token_index_after_chars,
    _argmax_probs_from_completion_logprobs,
)

print("== A. PURE HEALING SEMANTICS (deterministic) ==")

# --- _split_heal_tail: tail INCLUDES leading whitespace (true token boundary) ---
cases = {
    "I am goin": ("I am", " goin"),                 # mid-word typo -> heal " goin"->" going"
    "She said hello to": ("She said hello", " to"),  # complete word -> keep " to"
    "Hi i'm bored so looking": ("Hi i'm bored so", " looking"),
    "a b c": ("a b", " c"),
    "Photosynthe": ("Photosynthe", ""),             # single leading word -> no head, no heal
    "single": ("single", ""),
    "": ("", ""),
    "trailing space ": ("trailing space ", ""),     # between words -> no heal
    "two  spaces": ("two", "  spaces"),             # tail grabs the FULL ws run (preserves input)
}
for text, (eh, et) in cases.items():
    h, t = _split_heal_tail(text)
    check(f"split {text!r} -> head/tail", (h, t) == (eh, et), f"got {(h, t)!r} want {(eh, et)!r}")
    check(f"invariant head+tail==text for {text!r}", h + t == text, f"{h+t!r} != {text!r}")

# --- _token_index_after_chars: first token index covering >= nchars ---
check("token_index: ' going'/' to', 5 chars -> 1",
      _token_index_after_chars([" going", " to"], 5) == 1)
check("token_index: ['ab','cd','ef'], 4 chars -> 2",
      _token_index_after_chars(["ab", "cd", "ef"], 4) == 2)
check("token_index: exact boundary ['ab','cd'], 2 -> 1",
      _token_index_after_chars(["ab", "cd"], 2) == 1)
check("token_index: beyond end -> len",
      _token_index_after_chars(["ab"], 99) == 1)

# --- straddle-remainder reconstruction (the byte-correctness invariant) ---
# Simulate: tail=" goin", regen text=" going to", tokens=[" going"," to"].
def reconstruct(tail, text, tokens, probs):
    boundary = _token_index_after_chars(tokens, len(tail))
    covered = sum(len(t) for t in tokens[:boundary])
    remainder = text[len(tail):covered]
    new_tokens = ([remainder] if remainder else []) + tokens[boundary:]
    return "".join(new_tokens)

# generated_text must equal user_text + new_content == head + regen_text
nc = reconstruct(" goin", " going to", [" going", " to"], [0.9, 0.8])
check("straddle: ' goin'+regen -> new content 'g to'", nc == "g to", f"got {nc!r}")
check("straddle: head 'I am' + ' going to' == 'I am goin' + new content",
      "I am" + " going to" == "I am goin" + nc)
# clean boundary (no straddle): tail=" to", regen=" to me", tokens=[" to"," me"]
nc2 = reconstruct(" to", " to me", [" to", " me"], [0.9, 0.9])
check("clean boundary: ' to'+' me' -> new content ' me'", nc2 == " me", f"got {nc2!r}")

# --- _argmax_probs_from_completion_logprobs ---
import math  # noqa: E402
lp = {"tokens": [" a", " b"], "token_logprobs": [-0.1, -2.0],
      "top_logprobs": [{" a": -0.05}, {" X": -0.5}]}
toks, probs = _argmax_probs_from_completion_logprobs(lp)
check("logprobs: tokens parsed", toks == [" a", " b"])
check("logprobs: argmax prob = exp(max top_logprob)",
      abs(probs[0] - math.exp(-0.05)) < 1e-9 and abs(probs[1] - math.exp(-0.5)) < 1e-9,
      f"got {probs}")
check("logprobs: empty -> empty", _argmax_probs_from_completion_logprobs({}) == ([], []))

# --- Section B: live invariants (optional) ---
if len(sys.argv) > 1:
    import json
    import urllib.request
    A = sys.argv[1]
    print("\n== B. LIVE INVARIANTS (against running adapter) ==")

    def gen(text, **kw):
        body = {"text": text, "max_length": 16, "temperature": 0.7, "seed": 7,
                "min_probability": 0, **kw}
        req = urllib.request.Request(A + "/api/v1/generate",
                                     data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())[0]

    # The user's exact input must ALWAYS be a prefix of generated_text.
    for text in ["Hi i'm bored so looking", "I am goin", "She said hello to",
                 "The capital of Franc", "user@example", "He said \"hi"]:
        g = gen(text)["generated_text"]
        check(f"input preserved as prefix: {text!r}", g.startswith(text), f"got {g[:60]!r}")

    # Reported bug: word-boundary join must keep a separator (no "lookingfor").
    g = gen("Hi i'm bored so looking")["generated_text"]
    after = g[len("Hi i'm bored so looking"):]
    check("reported case: separator present after 'looking'",
          after[:1] in (" ", "\n", "", ",", ".", "!", "?", ";", ":") or not after,
          f"glued: {g[:60]!r}")

    # Healing: a known mid-word typo should not be left stranded with a space.
    # (soft: assert input preserved AND something was generated)
    g = gen("I am goin")["generated_text"]
    check("healing produced continuation past 'I am goin'", len(g) > len("I am goin"))

print(f"\n== RESULT: {len(PASS)} passed, {len(FAIL)} failed ==")
if FAIL:
    print("FAILED:", ", ".join(FAIL))
sys.exit(1 if FAIL else 0)
