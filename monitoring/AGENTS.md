# On-call Codex instructions

When a synthetic probe or 500 incident fails, own the incident through production verification.

1. Read `../AGENTS.md`. Do not launch duplicate servers and do not use `pkill`.
2. Run `python monitoring/service_probe.py --profile all` and preserve its JSON as the initial failure matrix.
3. Inspect systemd state before trusting a listening port. Port 8791 must belong to `omniserve-native.service`, which owns the public API data plane. Port 9083 must belong to the managed `text-generator-inference.service` compatibility worker. Port 9080 is legacy and must not appear in nginx or native upstream configuration. Port 9082 belongs to the forecast service and must not be disturbed.
4. Inspect Supervisor before public cutovers. `cloudflared-inference` must target port 8791; use `supervisorctl reread` and `supervisorctl update` for tunnel deployment, never signal or kill the process directly.
5. Inspect `mainserver.log`, the inference logs in `/var/log/supervisor/`, the relevant service journal, and OmniServe `/status`. Redact credentials from notes and command output.
6. Reproduce with the exact legacy autocomplete payload and both embedding payloads from `service_probe.py`. A shallow health endpoint is insufficient.
7. Make the smallest focused fix and preserve unrelated dirty-tree changes. Add or update a regression test.
8. Run narrow tests first, then the affected service suite. For native C changes, run the C tests and sanitizer build if the change touches parsing, HTTP framing, scheduling, or memory ownership.
9. Deploy only with systemd. Verify that each restarted unit is active/running and owns its expected port. Validate nginx before reload and confirm its API upstream is port 8791.
10. Retest local native, local compatibility, both production text endpoints, legacy feature extraction, and OpenAI-compatible embeddings. Verify vector dimensions and finite values, not only HTTP 200. Use a dedicated `RA1_MONITOR_API_KEY` for a paid RA1 generation check; never copy an example or personal key into code.
11. If a stale process outside systemd owns a production port, report its PID, parent, and cgroup. Do not kill another agent's process without explicit coordination.

The C gateway is optimized around epoll, persistent upstream pools, a bounded worker pool, allocation-light parsing, priority admission, modality permits, prefix-aware llama.cpp contexts, and direct byte relaying. Do not replace these paths with Python request handling or per-request process/model startup.

Finish the incident report with root cause, changed files, tests, deployment commands, service/PID ownership, local results, production results, and any remaining blocker.
