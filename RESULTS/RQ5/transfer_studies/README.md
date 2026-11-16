# Live Warm-Transfer and Direct-Transfer records

Four stages contain 6,000 successful tasks each. The execution sequence is original cold, original warm, Warm-Transfer on new inputs, and Direct-Transfer on the same new inputs from the shared cold checkpoint.

Each stage includes task records, a summary and checkpoint handoff metadata. Dataset manifests, ENA metadata and the selection record identify the original/new inputs. SHA256SUMS contains checksums for the retained records.

From the repository root:

```bash
python SCRIPTS/BIGDATA/reproduce_results.py
```

Live outputs are written to `build/reproduced-results/live/`: `results.json`, `metrics.tsv`, and `stage_details.json`. Fresh execution commands are in `SCRIPTS/RQ5/LIVE_EXPERIMENTS.md`.
