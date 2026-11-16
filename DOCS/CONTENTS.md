# Technical artifact contents

The root README lists directories and reproduction commands.

Component packages contain mapped-access ablation (W3), four feature configurations (chat_ablation), downstream selective/random auditing (W2), and auditing-cost analysis (W5). Each includes its inputs and analysis code; training packages include fixed splits, modeling code and reference predictions.

The live package contains the offline seed, matching model/history/database checkpoints, exact tool images, original/new input manifests, execution code, and four stages of Bowtie2 results. The six-workflow cohort and fixed split support offline-seed rebuilding.

`SCRIPTS/BIGDATA/reproduce_results.py` verifies and exports the retained numerical results to CSV/JSON. `SCRIPTS/RQ5/LIVE_EXPERIMENTS.md` contains fresh live-execution instructions.
