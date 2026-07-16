---
name: fleet-health
description: One-shot, read-only health snapshot across the personal fleet (DGX Spark, Jetson Orin Nano, homeserver, bond, obvm). Checks uptime, load, disk, memory, and each machine's key inference/service endpoints over SSH and curl, then renders a single status table with a pass/fail verdict. Use for a fleet status check, a morning brief before starting work, answering "is the spark available" or similar per-machine availability questions, or any general machine health check across the 5 hosts. Read-only — never restarts, stops, or reconfigures anything on any host.
allowed-tools: Bash(ssh:*), Bash(curl:*), Read
---

# Fleet Health

Fast, read-only health snapshot across all 5 machines in the personal fleet. Unlike `spark-audit` / `jetson-audit` (deep, single-machine, best-practices audits), this skill is a wide, shallow, fleet-wide pulse check — designed to answer "is everything up?" in well under a minute, with a final line a headless cron job can `grep` for.

**This skill reads the live system. It never modifies it.**

No `paths:` activation is configured — this skill runs only on explicit invocation ("fleet status", "morning brief", "is the spark available", etc.). Since it never auto-triggers, no loop guard is needed.

---

## Fleet Config

```yaml
ssh:
  key: "~/.ssh/id_claude_code"
  opts: "-o ConnectTimeout=5 -o BatchMode=yes"
  user: "claude"

curl:
  opts: "-sf -m 5"

fleet:
  - name: "DGX Spark"
    host: "spark.k4jda.net"
    lan_ip: "192.168.10.33"
    role: "LLM inference (vLLM) — chat, embeddings, NER"
    gpu: nvidia-smi
    key_ports:
      8000: { service: "spark-llm (Qwen3.6-35B-A3B-FP8)", check: "GET /v1/models, expect data[0].id == spark-llm" }
      8001: { service: "qwen3-embedding-4b",               check: "GET /v1/models, expect data[0].id == qwen3-embedding-4b" }
      8002: { service: "GLiNER NER",                       check: "GET /health, expect status == ok" }

  - name: "Jetson Orin Nano"
    host: "jetson.k4jda.net"
    lan_ip: "192.168.10.58"
    role: "Edge LLM inference (llama.cpp), single-process mode-switched"
    gpu: tegrastats   # NO nvidia-smi on this box — do not attempt it
    key_ports:
      8080: { service: "active llama-server mode (default qwen35)", check: "GET /health, expect status == ok" }
      8081: { service: "embedding mode (Qwen3-Embedding-4B)",        check: "see Known States — U2: expected DOWN unless mode.txt=embedding" }

  - name: "Homeserver"
    host: "homeserver.k4jda.net"
    role: "Docker host (Unraid) — ~55 containers, Prometheus/Grafana/Alertmanager stack"
    sudo_scoped: true   # `sudo -n docker ...` works; `sudo cat`/`sudo ls` do NOT — use plain cat/ls or docker's own output
    use_wget_locally: true  # curl is not reliably available ON the homeserver itself — use wget when SSH'd in

  - name: "Bond"
    host: "bond.k4jda.net"
    role: "General purpose"

  - name: "open-brain-vm (obvm)"
    host: "obvm.k4jda.net"
    role: "T2 Claude CLI batch, Python, ops"
```

---

## Execution

Run all checks in parallel — background each machine's SSH session and each spark/jetson curl probe with `&`, then `wait`. Target: **under 60 seconds** total. Do not run hosts sequentially.

### Universal checks (all 5 hosts)

For each host, over one SSH session:

```bash
ssh -i ~/.ssh/id_claude_code -o ConnectTimeout=5 -o BatchMode=yes claude@<host>.k4jda.net \
  "uptime; df -h / ; df -h --output=pcent,target 2>/dev/null | sort -rh | head -5; free -h"
```

Collect: uptime + 1/5/15-min load, `/` usage, the single largest non-`/` mount, and memory (total/used/available).

### Spark-specific

```bash
curl -sf -m 5 http://192.168.10.33:8000/v1/models   # expect data[0].id == "spark-llm"
curl -sf -m 5 http://192.168.10.33:8001/v1/models   # expect data[0].id == "qwen3-embedding-4b"
curl -sf -m 5 http://192.168.10.33:8002/health      # expect {"status":"ok",...}
ssh ... claude@spark.k4jda.net "nvidia-smi --query-gpu=temperature.gpu,utilization.gpu --format=csv,noheader"
```

### Jetson-specific

```bash
curl -sf -m 5 http://192.168.10.58:8080/health      # expect {"status":"ok"}
ssh ... claude@jetson.k4jda.net "timeout 3 tegrastats --interval 1000 | head -1"
# :8081 — evaluate per Known States (U2) below, do NOT treat a bare connection-refused as an anomaly on its own
curl -sf -m 5 http://192.168.10.58:8081/health
```

No `nvidia-smi` on the Jetson — always use `tegrastats` for GPU/thermal reads there.

### Homeserver-specific

```bash
ssh ... claude@homeserver.k4jda.net "sudo -n docker ps --format '{{.Names}} {{.Status}}'"
# count containers whose status contains "unhealthy" or "(restarting"
ssh ... claude@homeserver.k4jda.net "df -h /mnt/user | tail -1"
# Prometheus is loopback-bound on the homeserver — NEVER call it directly from outside.
# Reach it only via SSH, and use wget (not curl) once you're on the box itself:
ssh ... claude@homeserver.k4jda.net "wget -qO- http://127.0.0.1:9090/api/v1/alerts"
```

Sudo on the homeserver is **command-scoped**: `sudo -n docker ...` works, but `sudo cat`/`sudo ls` do not — don't route file reads through `sudo`.

---

## Known States — False-Alarm Prevention

Encode these before classifying anything as an anomaly. Each was verified against live behavior, not guessed.

**U2 — Jetson `:8081` embedding server (RESOLVED, expected-down).** The Jetson runs a single `llama-server` process at a time, selected by `~/llm-server/mode.txt` (`qwen35` [default], `nemotron`, `experiment`, `llm` — all port 8080 — or `embedding`, port 8081). Modes are mutually exclusive; only one port is ever live. Production default is `qwen35`, so port 8081 is **normally unreachable** — this is by design, not a fault. Verified 2026-07-12: `:8080/health` → `{"status":"ok"}`, `:8081` → connection refused. **Treat `:8081` connection-refused as expected-down, not an anomaly**, as long as `:8080/health` is healthy. Only escalate 8081 if `:8080` is ALSO down (that would indicate the whole llama-server process, not just the mode, is gone), or if mode.txt is known to have been switched to `embedding` and it's still unreachable.

**Homeserver load average.** This box runs ~55 containers on modest core count; a resting load average around **~3.5 is normal**, not degraded. Load also spikes transiently (observed 1-min spikes near 9 during bursts of parallel SSH/docker activity) while the 5/15-min trailing averages stay near baseline. **Judge load health on the 15-minute average, not the 1-minute figure** — a high 1-min with a normal 15-min average is noise, not an anomaly.

**Nightly AppdataBackup window (~00:00–03:00 EDT).** The Unraid AppdataBackup plugin stops and restarts containers during this window as part of a consistent backup. A container observed with a **fresh `StartedAt`** but an **unchanged `Created`** timestamp and **`RestartCount: 0`** during or shortly after this window is a normal backup-cycle restart, not a crash. Only flag it if `RestartCount > 0` or the restart falls outside the backup window.

**Jetson thermal reads — millidegree gotcha.** Raw `thermal_zone*/temp` files (and any node-exporter/textfile-collector wired directly to them) report **millidegrees C**, not degrees — a raw value like `51906` means 51.9°C, not a runaway 51,906°C thermal event. This skill sidesteps the issue by reading `tegrastats` (already human-readable, e.g. `cpu@51.468C`) rather than the raw thermal_zone files — but if this check is ever extended to read `/sys/devices/virtual/thermal/thermal_zone*/temp` directly, divide by 1000 before comparing against any threshold.

---

## Anomaly Thresholds

| Metric | Anomaly if |
|--------|-----------|
| SSH/curl unreachable | Any host fails to connect within the timeout (`ConnectTimeout=5`, `curl -m 5`) — except Jetson `:8081` per U2 |
| Disk (`/` or largest mount) | > 85% used |
| Memory | Available < 10% of total (adjust down for Spark/homeserver, where large buff/cache is normal and not a problem) |
| Load (15-min avg) | > 2x the host's normal baseline (homeserver baseline ~3.5; other hosts near-idle is normal) |
| Spark model endpoints | Any of 8000/8001/8002 non-2xx, wrong model `id`, or GLiNER `status != ok` |
| Jetson `:8080/health` | Non-2xx or `status != ok` |
| Homeserver containers | Any container status contains `unhealthy` or `restarting`, outside the nightly backup window logic above |
| Prometheus alerts | `data.alerts` non-empty |

---

## Output Format

Render exactly one table, then an optional ANOMALIES section, then exactly one verdict line.

```
| machine | up | disk | key service | anomaly |
|---------|----|----|-------------|---------|
| DGX Spark | up 27d | 42% (2.0T free) | 8000/8001/8002 OK, GPU 41C/0% | — |
| Jetson Orin Nano | up 12d | 17% | 8080 OK; 8081 down (expected, U2) | — |
| Homeserver | up 93d | /mnt/user 31% (21T free) | 0 unhealthy/restarting of 58, alerts: none | — |
| Bond | up 10d | 11% | n/a (general purpose) | — |
| obvm | up 90d | 46% | n/a (general purpose) | — |

VERDICT: ALL HEALTHY
```

Rules:
- Include the **ANOMALIES** section only when at least one row has a non-`—` anomaly. Omit it entirely on a clean run — don't print an empty section.
- The **final line of output is always** either `VERDICT: ALL HEALTHY` or `VERDICT: ACTION NEEDED — <short reason>`. This must be the literal last line, unindented, so a headless cron job can `grep '^VERDICT:'` reliably.
- Keep the table to the 5 required columns — don't add columns per-machine; put machine-specific detail (model IDs, GPU temps, container counts) inside the `key service` and `anomaly` cells.
