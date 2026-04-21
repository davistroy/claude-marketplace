---
name: spark-audit
description: SSH into the DGX Spark and audit all running containers against known best practices and community optimizations. Reports gaps, misconfigurations, and optimization opportunities. Complements spark-recon (external landscape) with internal config validation.
allowed-tools: Read, Edit, Glob, Grep, Bash, Agent
---

# Spark Audit

Live configuration audit of the DGX Spark inference system. SSHes into the device, inspects running containers, compares against documented best practices and community benchmarks in SPARK_BASELINE.md, and reports optimization opportunities.

**This skill reads the live system. It never modifies it.**

---

## Machine Config

```yaml
machine:
  name: "DGX Spark"
  ssh_target: "claude@spark.k4jda.net"
  ssh_key: "~/.ssh/id_claude_code"
  baseline_file: "SPARK_BASELINE.md"
  config_file: "SPARK_CONFIG.md"
  project_root: "~/dev/personal/spark/"
  notebook_file: "LAB_NOTEBOOK.md"

check1_config:
  containers: [qwen35, qwen3-embed, gliner]
  drift_reference: "SPARK_CONFIG.md"

check2_config:
  # qwen35 (primary LLM) optimization flags:
  known_good_flags:
    - flag: "--speculative-config '{\"method\":\"mtp\",\"num_speculative_tokens\":2}'"
      severity: HIGH
      impact: "+40% single-stream throughput"
    - flag: "--attention-backend FLASHINFER"
      severity: MEDIUM
    - flag: "--enable-prefix-caching"
      severity: MEDIUM
    - flag: "--enable-chunked-prefill"
      severity: LOW  # may be default
    - flag: "--load-format fastsafetensors"
      severity: LOW
    - env: "VLLM_FLASHINFER_MOE_BACKEND=latency"
      severity: MEDIUM
  anti_patterns:
    - flag: "VLLM_TEST_FORCE_FP8_MARLIN=1"
      severity: HIGH
      reason: "Removed in v0.19.0"
    - flag: "--no-async-scheduling"
      severity: MEDIUM
      reason: "Async is better in v0.19.0"
    - model_path_contains: "Qwen3.5-35B-A3B-FP8"
      severity: CRITICAL
      reason: "Pre-quantized FP8 path hangs on v0.19.0"
    - volume_contains: "~/.cache"
      severity: CRITICAL
      reason: "Tilde expansion fails in Docker"
  # qwen3-embed:
  embed_required_flags:
    - "--enforce-eager"    # CRITICAL: required for pooling models
    - "--runner pooling"   # CRITICAL: required for embedding mode
  # gliner:
  gliner_checks:
    - env: "GLINER_DEVICE=cuda"
      severity: HIGH
    - hf_cache_writable: true
      severity: MEDIUM

check3_config:
  memory_ceiling: "121.6 GiB GPU"
  thresholds:
    swap_used:      { healthy: "< 100 MB", warn: "100 MB–1 GB", critical: "> 1 GB" }
    available_ram:  { healthy: "> 12 GiB", warn: "8–12 GiB",    critical: "< 8 GiB" }
    gpu_temp_idle:  { healthy: "< 45C",    warn: "45–55C",       critical: "> 55C" }
    gpu_temp_load:  { healthy: "< 65C",    warn: "65–75C",       critical: "> 75C" }
    total_gpu_alloc:{ healthy: "< 95 GiB", warn: "95–105 GiB",  critical: "> 105 GiB" }
    free_gpu:       { healthy: "> 20 GiB", warn: "12–20 GiB",   critical: "< 12 GiB" }
  gpu_utilization_targets:
    single_model: 0.85
    three_model_setup: "0.75–0.80"  # adjusted for embed + gliner
    flag_if_below: 0.75             # flag as OPTIMIZATION OPPORTUNITY

check4_config:
  health_endpoints:
    - "http://localhost:8000/health"   # qwen35
    - "http://localhost:8001/health"   # qwen3-embed
    - "http://localhost:8002/health"   # gliner
  inference_port: [8000, 8001, 8002]
  sysctl_targets:
    vm.swappiness: { healthy: 1, warn: "2–10", critical: "> 10 or 60 (default)" }

check5_config:
  baseline_version_key: "vllm_latest_observed"
  version_sources:
    vllm:       "docker exec qwen35 python3 -c 'import vllm; print(vllm.__version__)'"
    vllm_embed: "docker exec qwen3-embed python3 -c 'import vllm; print(vllm.__version__)'"
    cuda:       "docker exec qwen35 python3 -c 'import torch; print(torch.version.cuda)'"
    pytorch:    "docker exec qwen35 python3 -c 'import torch; print(torch.__version__)'"
    flashinfer: "docker exec qwen35 pip show flashinfer | grep Version"
    driver:     "nvidia-smi --query-gpu=driver_version --format=csv,noheader"
    images:     "docker inspect qwen35 qwen3-embed gliner --format '{{.Config.Image}}'"
  version_gaps:
    vllm_minor_behind: HIGH
    flashinfer_behind: MEDIUM
    cuda_toolkit_cu130_vs_cu132: LOW
    driver_behind: INFO   # only flag if no known regressions
    embed_different_vllm_than_qwen35: INFO
  known_safe_driver: "580.142"
  community_flashinfer: "0.6.7"
```

---

## Execution

Follow the **Audit Five-Check Template** in `plugins/personal-plugin/references/patterns/audit-recon-system.md` using the machine config above.

Required files to read before starting:
- `~/dev/personal/spark/SPARK_BASELINE.md`
- `~/dev/personal/spark/SPARK_CONFIG.md`

Connection: `ssh -i ~/.ssh/id_claude_code claude@spark.k4jda.net`

The `claude` user has passwordless sudo for: `docker nvidia-smi systemctl`.

### Spark-Specific Check Commands

**Check 1 — Container Config Drift (docker inspect, not systemctl):**
```bash
# For each container: qwen35, qwen3-embed, gliner
docker inspect <name> --format '{{json .Config.Cmd}}'
docker inspect <name> --format '{{json .Config.Env}}'
docker inspect <name> --format '{{json .HostConfig.Binds}}'
docker inspect <name> --format '{{.Config.Image}}'
docker inspect <name> --format '{{json .HostConfig.PortBindings}}'
docker inspect <name> --format '{{json .HostConfig.RestartPolicy}}'
docker inspect <name> --format '{{json .HostConfig.ShmSize}}'
docker inspect <name> --format '{{json .HostConfig.IpcMode}}'
```

**Check 3 — GPU Memory (nvidia-smi, not tegrastats):**
```bash
nvidia-smi
nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader
free -h
swapon --show
cat /proc/swaps
# Per-process swap (top 5):
for pid in $(ls /proc/[0-9]*/status 2>/dev/null | head -100 | cut -d/ -f3); do
  swap=$(grep VmSwap /proc/$pid/status 2>/dev/null | awk '{print $2}')
  name=$(grep Name /proc/$pid/status 2>/dev/null | awk '{print $2}')
  [ "$swap" -gt 1000 ] 2>/dev/null && echo "$swap kB - $name ($pid)"
done | sort -rn | head -5
```

**Check 4 — System Health:**
```bash
uptime
docker ps --format '{{.Names}}\t{{.Status}}\t{{.Image}}'
docker inspect --format '{{.Name}} {{.RestartCount}}' $(docker ps -q)
curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health
curl -s -o /dev/null -w '%{http_code}' http://localhost:8001/health
curl -s -o /dev/null -w '%{http_code}' http://localhost:8002/health
df -h /
uname -r
nvidia-smi --query-gpu=driver_version --format=csv,noheader
docker system df
sudo dmesg --level=err,warn | tail -20
sysctl vm.swappiness vm.min_free_kbytes
```

---

## LAB_NOTEBOOK Entry

Use the Audit Entry Template from `audit-recon-system.md §6`. Append to `~/dev/personal/spark/LAB_NOTEBOOK.md` using `Edit` tool. Auto-increment entry number.

Skill name field: `spark-audit skill`

## /schedule Integration

Register a recurring audit run:

```
/schedule create --name spark-audit-weekly --cron "0 2 * * 2" --skill spark-audit
```

Recommended: **weekly Tuesday 02:00 UTC.** Pairs with spark-recon (bi-weekly Sunday 23:00 UTC).
