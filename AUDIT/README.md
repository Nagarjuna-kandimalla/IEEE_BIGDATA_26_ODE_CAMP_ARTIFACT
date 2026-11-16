# Consumption auditing for the live experiment

The executable tracer and isolation launcher are in `SCRIPTS/RQ5/live/runtime/ebpf_audit_py39.py` and `isolated_audit_python_parallel.sh`. `configure.py` copies these into the external experiment workspace. Use the complete launch procedure in [LIVE_EXPERIMENTS.md](../SCRIPTS/RQ5/LIVE_EXPERIMENTS.md).

The tracer attributes explicit read return bytes and file-backed mapped page-fault bytes to tasks and their descendants. A successful mmap call establishes a mapping; its length is not a measurement of bytes consumed. Fault-based accounting may count repeated accesses and is not unique input volume or resident memory.

Workers need Linux, matching kernel headers, BCC Python bindings, and the tracing privileges used by the launcher. On Debian/Ubuntu, the recorded prerequisites were:

```bash
sudo apt-get install -y bpfcc-tools python3-bpfcc "linux-headers-$(uname -r)"
sudo -n /usr/bin/python3 -c 'from bcc import BPF'
```

Check these on the actual task workers. The system Python/BCC environment is distinct from the pinned Python 3.9 learning environment. Validate known-file attribution, readiness and permissions before a run. The portable launcher isolates auditors from task grants, uses a 384 MiB auditor cap, and configures NFS audit-directory access explicitly. Kernel compatibility and permissions must be validated at the execution site.

All four live stages audit every task. The paper's selective-auditing comparison is a separate replay in W2; the paired cost analysis uses frozen measurements in W5. This artifact does not rerun the unrelated WORKS STRACE/whole-workflow comparison.
