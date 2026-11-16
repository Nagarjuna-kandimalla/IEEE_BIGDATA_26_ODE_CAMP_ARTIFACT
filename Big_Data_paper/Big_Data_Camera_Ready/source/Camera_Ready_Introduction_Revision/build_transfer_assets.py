"""Recompute live-transfer assets from the camera-ready-local data snapshot.

Run with Python and matplotlib. No models are loaded and no workflows run.
The snapshot contains experiment records only; source hashes are checked first.
"""
import csv
import gzip
import hashlib
import json
import statistics
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "result_assets"
DATA = OUT / "transfer_records"


def main():
    manifest = json.loads((DATA / "source_manifest.json").read_text())
    for name, source in manifest["files"].items():
        assert hashlib.sha256((DATA / name).read_bytes()).hexdigest() == source["sha256"], name
    phases = json.loads((DATA / "studies.json").read_text())["phases"]
    assert phases["direct_transfer_new_input"]["parent"] == "warm_transfer_cold"
    results = {}
    for stage in phases:
        with gzip.open(DATA / stage / "task_instances.tsv.gz", "rt", newline="") as f:
            rows = list(csv.DictReader(f, delimiter="\t"))
        assert len(rows) == 6000
        assert len({(r["process"], r["task_instance"]) for r in rows}) == 6000
        assert all(r["final_success"].lower() in ("true", "1") for r in rows)
        assert len({r["process"] for r in rows}) == 7
        handoff = json.loads((DATA / stage / "handoff.original.json").read_text())
        summary = json.loads((DATA / stage / "summary.json").read_text())["global"]
        assert handoff["status"] == "PASS" and handoff["duplicate_success_observations"] == 0
        req = [float(r["first_applied_allocation_mib"]) for r in rows]
        peak = [float(r["final_peak_mib"]) for r in rows]
        seconds = [float(r["final_runtime_seconds"]) for r in rows]
        assert min(peak) > 0 and min(seconds) >= 0
        ratios = [a / b for a, b in zip(req, peak)]
        def error(part):
            return statistics.median(100 * abs(float(r["a_plus_p_plus_c_point_q50_mib"]) / float(r["final_peak_mib"]) - 1) for r in part)
        alignment = [r for r in rows if r["process"] == "ALIGN_CHUNK"]
        assert len(alignment) == 1974
        metrics = {
            "tasks": len(rows),
            "request_gib": sum(req) / 1024,
            "peak_gib": sum(peak) / 1024,
            "unused_gibh": sum(max(a-b, 0) * t / 1024 / 3600 for a, b, t in zip(req, peak, seconds)),
            "coverage": 100 * sum(a >= b for a, b in zip(req, peak)) / len(rows),
            "below_peak": sum(a < b for a, b in zip(req, peak)),
            "mdape": error(rows),
            "alignment_mdape": error(alignment),
            "retries": int(summary["total_retry_attempts"]),
            "ooms": int(summary["total_oom_attempts"]),
            "margin_percent": [100 * sum(test(x) for x in ratios) / len(rows) for test in
                               (lambda x: x < 1, lambda x: 1 <= x <= 1.05,
                                lambda x: 1.05 < x <= 1.10, lambda x: 1.10 < x <= 1.25,
                                lambda x: x > 1.25)],
        }
        assert abs(metrics["mdape"] - summary["a_plus_p_plus_c_point_median_ape_percent"]) < 1e-8
        assert abs(metrics["coverage"] - 100 * summary["applied_first_request_coverage"]) < 1e-8
        results[stage] = metrics

    original = list(csv.DictReader((DATA / "original_6000.tsv").open(), delimiter="\t"))
    new = list(csv.DictReader((DATA / "new_6000.tsv").open(), delimiter="\t"))
    assert len(original) == len(new) == 38
    for field in ("run_accession", "fastq1_url", "fastq2_url"):
        assert not ({r[field] for r in original} & {r[field] for r in new})
    selection = json.loads((DATA / "new_dataset_selection.json").read_text())
    assert all(not ids for ids in selection["overlap_with_entire_PRJEB11501"].values())

    cold, warm, wt, dt = results.values()
    report = {"source_commit": manifest["commit"], "results": results,
              "cold_to_warm_request_reduction_percent": 100 * (1-warm["request_gib"]/cold["request_gib"]),
              "direct_vs_warm_request_increase_percent": 100 * (dt["request_gib"]/wt["request_gib"]-1),
              "direct_vs_warm_unused_increase_percent": 100 * (dt["unused_gibh"]/wt["unused_gibh"]-1),
              "definitions": "First nominal CAMP request paired with final successful peak/runtime. Excludes 128 MiB execution allowance and failed-attempt, auditing, prediction and retraining costs.",
              "source_hashes": manifest["files"], "flagstat_validation": manifest["flagstat_validation"]}
    (OUT / "transfer_provenance.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Verified four stages of 6000 successful tasks; generated transfer provenance.")


if __name__ == "__main__":
    main()
