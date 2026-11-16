"""Recompute paper auditing costs from paired runtimes and frozen selections."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", type=Path, default=ROOT / "results")
    a = p.parse_args()
    tasks = pd.read_csv(ROOT / "inputs/task_level_full_ebpf_net_benefit.csv")
    selections = pd.read_csv(ROOT / "inputs/audit_selections.tsv.gz", sep="\t")
    assert len(tasks) == 5026 and tasks.logical_task_id.is_unique
    costs = np.maximum(tasks.ebpf_wrapper_seconds - tasks.baseline_wrapper_seconds, 0) * tasks.camp_request_mib / 1024 / 3600
    np.testing.assert_allclose(costs, tasks.audit_cost_positive_gib_hours, rtol=1e-10, atol=1e-10)
    costs.index = tasks.logical_task_id
    per_seed = []
    for (budget, seed), group in selections.groupby(["budget", "seed"]):
        assert len(group) == 5026 and group.logical_task_id.is_unique
        assert set(group.logical_task_id) == set(tasks.logical_task_id)
        selected = group.loc[group.audited.astype(bool), "logical_task_id"]
        per_seed.append(dict(budget_percent=100*budget, seed=int(seed), audited_test_tasks=len(selected), audit_cost_gib_hours=float(costs.loc[selected].sum())))
    per_seed = pd.DataFrame(per_seed)
    assert len(per_seed) == 40
    rows = []
    for budget, group in per_seed.groupby("budget_percent"):
        assert set(group.seed) == set(range(1996, 2001))
        assert group.audited_test_tasks.nunique() == 1
        values = group.audit_cost_gib_hours.to_numpy()
        means = np.random.default_rng(73129).choice(values, size=(10000, 5), replace=True).mean(axis=1)
        low, high = np.quantile(means, [.025, .975])
        rows.append(dict(budget_percent=budget, audited_test_tasks=int(group.audited_test_tasks.iloc[0]),
            paper_mean_audit_cost_gib_hours=float(values.mean()), cost_seed_mean_ci95_low=low, cost_seed_mean_ci95_high=high))
    a.output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(a.output_dir / "budget_summary.csv", index=False)
    per_seed.to_csv(a.output_dir / "per_seed_costs.csv", index=False)
    print("Recomputed auditing costs: 8 budgets x 5 seeds, 5,026 paired tasks")

if __name__ == "__main__": main()
