---
name: jetson-audit
description: SSH into the Jetson Orin Nano and audit the running inference config against known best practices and community optimizations. Reports gaps, misconfigurations, and optimization opportunities. Complements jetson-recon (external landscape) with internal config validation.
allowed-tools: Read, Edit, Glob, Grep, Bash, Agent
---

# Jetson Audit

Live configuration audit of the Jetson Orin Nano Super inference system. SSHes into the device, inspects the running llama.cpp server and system state, compares against documented best practices in JETSON_BASELINE.md, and reports optimization opportunities.

**This skill reads the live system. It never modifies it.**

**Framework:** Follow `plugins/personal-plugin/references/patterns/audit-recon-system.md` — Sections 1–6 (Execution Framework, Audit Five-Check Template, Severity Matrices, LAB_NOTEBOOK Entry). Use the Jetson-specific config and commands below as the machine config layer.

---

## Machine Config

```yaml
machine:
  name: "Jetson Orin Nano Super"
  ssh_target: "claude@jetson.k4jda.net"
  ssh_key: "~/.ssh/id_claude_code"
  baseline_file: "JETSON_BASELINE.md"
  config_file: "JETSON_CONFIG.md"
  project_root: "~/dev/personal/jetson/"
  notebook_file: "LAB_NOTEBOOK.md"

check1_config:
  drift_reference: "JETSON_CONFIG.md"
  service_name: "myscript"
  launch_script: "~/llm-server/start.sh"
  mode_file: "~/llm-server/mode.txt"

check2_config:
  memory_ceiling: "8 GB unified"
  inference_port: 8080

check3_config:
  memory_ceiling: "8 GB unified"

check4_config:
  inference_port: 8080
  thermals_path: "/sys/devices/virtual/thermal/thermal_zone*/temp"

check5_config:
  baseline_version_key: "llamacpp_latest_seen"
  secondary_version_key: "jetpack_latest_orin_nano"
```

---

## Required Files

| File | Location | Purpose |
|------|----------|---------|
| `JETSON_BASELINE.md` | `~/dev/personal/jetson/` | Performance baselines + known-best config to compare against |
| `JETSON_CONFIG.md` | `~/dev/personal/jetson/` | Documented system config (ground truth for drift detection) |
| `LAB_NOTEBOOK.md` | `~/dev/personal/jetson/` | Append-only audit results log |

If any required file is missing, note it in the report and proceed with available data.

---

## Machine-Specific Commands

### Check 1 — Service Config Drift

```bash
# Service status
systemctl status myscript

# Read the actual launch script to extract llama-server flags
cat ~/llm-server/start.sh 2>/dev/null || cat ~/llm-server/run.sh 2>/dev/null

# Current mode
cat ~/llm-server/mode.txt 2>/dev/null

# Check what process is actually running and its flags
ps aux | grep llama-server | grep -v grep
# Or alternatively:
pgrep -a llama

# Check if server is listening
ss -tlnp | grep -E '(8080|8081)'
```

### Check 2 — Missing Optimizations

Known-good flags for Jetson Orin Nano 8 GB unified memory:

| Flag | Best Practice | Severity if Missing |
|------|--------------|-------------------|
| `-ngl 999` or `--gpu-layers 999` | Full GPU offload (all layers) | CRITICAL |
| `-fa` or `--flash-attn` | Flash attention for memory efficiency | HIGH |
| `--mlock` | Lock model in memory (prevent swap) | HIGH |
| `-ctk q8_0` or `--cache-type-k q8_0` | Quantized KV cache (saves memory) | MEDIUM |
| `-ctv q8_0` or `--cache-type-v q8_0` | Quantized KV cache values | MEDIUM |
| `-c 32768` or appropriate context | Context size matches model capability | MEDIUM |
| `-np 1` or `--parallel 1` | Appropriate parallel slot count for 8 GB | MEDIUM |
| `-t 1` or `--threads 1` | Single thread (GPU-bound, more threads waste cycles) | LOW |
| `--cont-batching` | Continuous batching for concurrent requests | LOW |

Anti-patterns:

| Anti-Pattern | Check | Severity |
|-------------|-------|----------|
| `-ngl 0` or missing GPU offload | All inference on CPU = extremely slow | CRITICAL |
| Context size > model max | Wastes memory, may cause errors | HIGH |
| `--threads` > 2 | GPU-bound workload, extra CPU threads add overhead | MEDIUM |
| `--parallel` > 2 on 8 GB | Each slot needs KV cache memory | MEDIUM |
| No `--mlock` with swap enabled | Model pages to swap under pressure | MEDIUM |

### Check 3 — Memory Budget

```bash
free -h
swapon --show
# RSS of the llama-server process
ps -o pid,rss,vsz,comm -p $(pgrep llama-server) 2>/dev/null
# Or broader:
ps aux --sort=-rss | head -10
# Tegra memory info (if available)
cat /sys/kernel/debug/nvmap/iovmm/clients 2>/dev/null | head -20
# Available vs total
cat /proc/meminfo | grep -E '(MemTotal|MemAvailable|SwapTotal|SwapFree|Buffers|Cached)'
```

Memory thresholds for 8 GB unified:

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Available RAM | > 500 MB | 200–500 MB | < 200 MB |
| Swap used | < 50 MB | 50–500 MB | > 500 MB |
| llama-server RSS | < baseline + 20% | +20–50% above baseline | > +50% or > 6 GB |
| Total RSS (all processes) | < 7 GB | 7–7.5 GB | > 7.5 GB |

Memory budget breakdown (4B Q4_K_M model):
1. Model GGUF: ~3 GB
2. KV cache: context_size × layers × head_dim × 2 (K+V) × quant_factor
3. Runtime: ~200–400 MB
4. OS + other: ~1–1.5 GB
5. Required headroom: >= 500 MB

### Check 4 — System Health

```bash
uptime
# Thermals (Jetson-specific)
cat /sys/devices/virtual/thermal/thermal_zone*/temp 2>/dev/null
cat /sys/devices/virtual/thermal/thermal_zone*/type 2>/dev/null
# Or tegrastats snapshot
sudo tegrastats --interval 1000 --count 3 2>/dev/null
# Fan status (if managed)
cat /sys/devices/pwm-fan/target_pwm 2>/dev/null
# Power mode
sudo nvpmodel -q 2>/dev/null
# Clock frequencies
sudo jetson_clocks --show 2>/dev/null
# Disk usage
df -h /
# Journal errors (last hour)
journalctl --since "1 hour ago" --priority=err --no-pager | tail -20
# Quick inference test
curl -s http://localhost:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"default","messages":[{"role":"user","content":"Say hello in exactly 5 words"}],"max_tokens":32}' | \
  python3 -c 'import sys,json; r=json.load(sys.stdin); u=r.get("usage",{}); print(f"Tokens: {u.get(\"completion_tokens\",\"?\")}, Gen speed: check /slots endpoint")'
# Slot status
curl -s http://localhost:8080/slots 2>/dev/null | python3 -c 'import sys,json; s=json.load(sys.stdin); print(f"Slots: {len(s)}, Busy: {sum(1 for x in s if x.get(\"is_processing\",False))}")' 2>/dev/null
```

Jetson-specific health thresholds:

| Check | Healthy | Warning | Critical |
|-------|---------|---------|----------|
| Inference responds | Yes, < 5s | Slow (> 10s) | No response / error |
| GPU temp (idle) | < 50C | 50–65C | > 65C |
| GPU temp (load) | < 65C | 65–80C | > 80C |
| Power mode | MAXN (15W) | 10W mode | Unknown / 7W |
| Disk usage | < 70% | 70–85% | > 85% |
| System uptime | Stable (> 1 day) | < 1 day | Service down |
| Journal errors | None relevant | GPU/CUDA warnings | OOM kills |

### Check 5 — Version Currency

```bash
# llama.cpp version
cd ~/llm-server/llama.cpp && git log --oneline -1
# Or binary version:
~/llm-server/llama.cpp/build/bin/llama-server --version 2>/dev/null || \
  ~/llm-server/llama-server --version 2>/dev/null
# JetPack version
cat /etc/nv_tegra_release 2>/dev/null
dpkg -l nvidia-jetpack 2>/dev/null | grep nvidia-jetpack
# CUDA version
nvcc --version 2>/dev/null | grep release
# Kernel
uname -r
# L4T version
head -1 /etc/nv_tegra_release 2>/dev/null
# Model file
ls -la ~/llm-server/models/ 2>/dev/null | grep -i gguf
```

Version gap severity for Jetson:

| Gap | Severity |
|-----|----------|
| llama.cpp > 5 builds behind latest | HIGH |
| llama.cpp 1–5 builds behind | MEDIUM |
| JetPack behind latest for Orin Nano | INFO (reflash required, high effort) |
| Model file doesn't match documented model | WARNING |

Compare against baseline fields: `llamacpp_latest_seen`, `jetpack_latest_orin_nano`, `current_model`.

---

## LAB_NOTEBOOK Entry

Append using `Edit` tool. Auto-increment entry number by reading the last `## Entry NNN` or `### Entry NNN` line. Use the Audit Entry Template from `audit-recon-system.md` Section 6.

## /schedule Integration

Register a recurring audit run:

```
/schedule create --name jetson-audit-weekly --cron "0 2 * * 2" --skill jetson-audit
```

Recommended: **weekly Tuesday 02:00 UTC.** Pairs with jetson-recon (bi-weekly Sunday 23:00 UTC).
