"""Regenerate the current manuscript evidence in an isolated, fresh directory."""
import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "Big_Data_paper/Big_Data_Camera_Ready"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "build/reproduction")
    parser.add_argument("--engine", choices=["latexmk", "tectonic"])
    parser.add_argument("--executable")
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists():
        parser.error("Output must not exist; choose a fresh --output directory")
    subprocess.run([sys.executable, str(ROOT / "SCRIPTS/RQ5/live/verify_package.py")], check=True)
    out.mkdir(parents=True)
    project = out / "paper-source"
    shutil.copytree(SOURCE, project, ignore=shutil.ignore_patterns("__pycache__", "*.log", "*.blg"))
    paper = project / "source/Camera_Ready_Introduction_Revision"
    commands = [
        [str(ROOT / "SCRIPTS/RQ5/live/reproduce_results.py"), "--output", str(out / "live")],
        [str(paper / "build_result_assets.py"), "--repo-root", str(ROOT)],
        [str(paper / "build_online_plot.py")],
    ]
    for command in commands:
        subprocess.run([sys.executable, *command], check=True)
    assets = paper / "result_assets"
    for name in ["mmap_rows.tex", "feature_rows.tex", "audit_tradeoffs.pdf", "online_deployment_compact.pdf"]:
        if not (assets / name).is_file():
            raise RuntimeError("Missing manuscript asset: " + name)
    # Independent full-stage recomputation and the paper snapshot must agree.
    full = json.loads((out / "live/results.json").read_text())
    compact = json.loads((assets / "transfer_provenance.json").read_text())["results"]
    for stage, metrics in compact.items():
        for key, full_key in [("request_gib", "request_gib"), ("peak_gib", "peak_gib"),
            ("unused_gibh", "unused_gib_hours"), ("coverage", "coverage_percent"), ("mdape", "mdape_percent")]:
            if not math.isclose(metrics[key], full["results"][stage][full_key], rel_tol=1e-10, abs_tol=1e-8):
                raise RuntimeError("Full records and compact paper snapshot disagree: " + stage + " " + key)
    report = {"status": "PASS", "checks": ["release hashes", "four live stages and flagstats",
        "mapped-access and feature configurations", "paired downstream auditing", "audit costs",
        "transfer snapshot hashes and parent checkpoint", "current figures and table rows"],
        "scope": "Retained measurements; no fresh model fitting or workflow execution.",
        "paper_source": str(paper), "live_results": full, "compiled": False}
    if args.engine:
        command = [sys.executable, str(ROOT / "SCRIPTS/BIGDATA/build_paper.py"),
            "--project", str(project), "--output-dir", str(out / "compiled"), "--engine", args.engine]
        if args.executable:
            command.extend(["--executable", args.executable])
        subprocess.run(command, check=True)
        report["compiled"] = True
        report["pdf"] = str(out / "compiled/camp_bigdata.pdf")
    (out / "reproduction.json").write_text(json.dumps(report, indent=2) + "\n")
    print("PASS:", out / "reproduction.json")


if __name__ == "__main__":
    main()
