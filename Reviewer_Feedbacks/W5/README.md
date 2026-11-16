# Auditing-cost reproduction

Figure 1(b) uses 5,026 paired no-audit/eBPF task runtimes and frozen audit selections at eight budgets (5, 10, 15, 20, 25, 30, 50 and 100%), each with seeds 1996-2000.

Cost per selected task is `max(eBPF_seconds - baseline_seconds, 0) * CAMP_request_MiB / 1024 / 3600`. Requests remain fixed. The 95% interval resamples the five seed totals 10,000 times with RNG seed 73129. This is auditing cost, not end-to-end net saving; inference, training and failed-attempt costs are outside this estimate.

From the repository root, in the analysis environment:

```bash
python Reviewer_Feedbacks/W5/analyze.py
python Reviewer_Feedbacks/W5/validate.py
```

Or run the root `SCRIPTS/BIGDATA/reproduce_paper.py` command, which independently calculates the same costs and intervals in an isolated output directory.

`inputs/` retains the exact measured rows and audit selections; historical input filenames are unchanged. `expected_results/budget_summary.csv` preserves the paper cost means. `results/` contains regenerated per-seed costs and confidence intervals. At 5%, 20%, 50%, and 100%, means are 5.999, 24.025, 66.534 and 139.680 GiB-h. This route recomputes retained measurements; it does not conduct new tracing experiments.
