# Technical verification

Verified on 2026-11-16. These checks distinguish retained-result reproduction from a new scientific execution.

## Passed

- Recomputed all four live stages from full task/attempt records: 6,000 unique successful tasks each. All 1,974 new-input flagstat summaries agree between transfer arms.
- Deep-verified all 1,264 compressed model/container blobs, including decoded original bytes.
- Ran the self-contained W2, W3, four-feature and W5 analysis commands under Linux. W2's six causal/protocol tests passed; W3 reproduces 32/30 counts; feature configurations reproduce 85/46/52/30; all eight audit-cost budgets match the retained means.
- Four new regression tests pass: empty/nonempty fallback labels in all four retained modeling copies; fault injection after outcome commit and before history publication, followed by restart and a contiguous second update; conflicting history file rejection; safe default thresholds and invalid override rejection.
- Two live I/O/routing tests pass, including corrupt partial-download rejection and the explicit execution allowance. Fourteen CAMP policy/history/calibration tests pass.
- Linux integration selfcheck passes: restore the offline seed and shared-cold checkpoint to new paths, validate model/history/calibration/SQLite consistency, verify configured source hashes, simulate Slurm submission dependencies and duplicate-submit refusal, and verify the saved-cold branch skips cold/warm.

Model/integration checks used Linux via WSL, CPython 3.9.25, numpy 1.26.4, pandas 2.3.3, LightGBM 4.6.0, scikit-learn 1.6.1 and scipy 1.13.1. Numerical analysis also ran in the local Windows analysis environment. Logs and machine-readable integration evidence are in `validation/`.

## Re-run the checks

```bash
python SCRIPTS/RQ5/live/verify_package.py --require-tracked
python SCRIPTS/RQ5/live/models.py verify --deep
python SCRIPTS/BIGDATA/reproduce_results.py
# Linux, with the pinned model environment:
python -m unittest discover -s SCRIPTS/BIGDATA/tests -v
python -m unittest discover -s SCRIPTS/RQ5/live/tests -v
python -m unittest discover -s SCRIPTS/RQ5/experiment_template/camp/live_online_learning/tests -v
python SCRIPTS/RQ5/live/selfcheck.py
```

## Limits

No fresh full offline fit, new FASTQ download, privileged BCC/eBPF trace, or complete biological Slurm workflow was executed during this release check. The cluster selfcheck simulates scheduler commands. It validates packaging and continuation prerequisites, not a replacement biological experiment. Full-run instructions and inputs/checkpoints are included, but fresh executions may produce different measurements and learning trajectories.

The root manifest is generated after intentional changes and verifies release bytes. Component input/model/result provenance is preserved separately; it must not be replaced to mask unexpected differences during independent reproduction.
