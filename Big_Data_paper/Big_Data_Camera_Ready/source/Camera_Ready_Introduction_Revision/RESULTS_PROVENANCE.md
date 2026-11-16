# Paper evidence provenance

All paths below are relative to the repository root. `ARTIFACT_MANIFEST.json` identifies release bytes.

- Table I: `Reviewer_Feedbacks/W3/results/paper_native_metrics.csv`, verified against both compressed task prediction tables under W3/runs.
- Table II: `Reviewer_Feedbacks/chat_ablation/results/paper_configuration/native_metrics.csv`, verified against paired seed-1996 predictions. Access uses global routing; consumption variants use eligible process-tail routing. The published 87/31 endpoints are separate frozen references, not the 85/46/52/30 native rerun.
- Figure 1(a): W2 downstream per-repetition metrics and paired summaries, after the first update, at native operating points. The 20% result has 17,067 evaluated tasks per repetition. Confidence intervals include zero.
- Figure 1(b): W5 paired task runtimes and frozen budget/seed selections. Positive tracing overhead is charged at the fixed CAMP request. Seed-mean bootstrap uses seed 73129 and 10,000 resamples. No net-saving interpretation is used.
- Figure 2 and transfer paragraphs: all four stage task records and summaries in `RESULTS/RQ5/live_experiments/`; compact copies under `result_assets/transfer_records/` retain source SHA256 metadata. `build_transfer_assets.py` recomputes request/peak totals, unused memory-time, coverage, median errors, retries and margins. `build_online_plot.py` independently checks the task-derived values before plotting.

Original inputs: PRJEB11501, 38 paired runs. New inputs: PRJNA486148, 38 disjoint paired runs. Each stage has 6,000 tasks and 1,974 alignment chunks. Direct-Transfer shares the cold checkpoint with Warm-Transfer and skips the original-data warm pass. Both use online learning and full auditing. The checkpoint ancestor and input selections are validated by the builders.

Requests, coverage, unused memory-time and margins exclude the separate 128 MiB execution allowance. Zero recorded OOMs are outcomes under that allowance. Runtime conventions and excluded costs are stated in the paper and root README. Offline reuse and new live executions are distinguished in the paper's text and WORKS citation.

`build_result_assets.py` verifies component records and generates table rows and Figure 1. It calls the transfer builder; then `build_online_plot.py` generates the compact Figure 2. `SCRIPTS/BIGDATA/reproduce_paper.py` runs all builders in an isolated source copy, alongside the independent four-stage result checker. Generated provenance JSONs contain input hashes and computed values. No retained numbers are substituted for a failed fresh model fit.
