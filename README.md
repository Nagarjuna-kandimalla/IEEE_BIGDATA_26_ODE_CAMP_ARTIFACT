# IEEE Big Data 2026 CAMP Artifact

Reproduction package for **Online Deployment and Evaluation of Consumption-Aware Memory Allocation for Scientific Workflows**.

This repository contains the current six-page manuscript and the code, retained measurements, input manifests, and model checkpoints required for its component, auditing, and live-deployment experiments. It preserves the CAMP implementation and offline cohort needed by these experiments. Historical directory labels (`RQ5`, `W2`, `W3`, `W5`) are retained so executable paths stay consistent.

## Get the artifact

```bash
git clone https://github.com/Nagarjuna-kandimalla/IEEE_BIGDATA_26_CAMP_ARTIFACT.git
cd IEEE_BIGDATA_26_CAMP_ARTIFACT
python SCRIPTS/RQ5/live/verify_package.py --require-tracked
```

All commands start at this repository root unless stated otherwise. Use `python3` where `python` is unavailable. Omit `--require-tracked` for a ZIP download without Git metadata. Verify before regeneration; output metadata can change PDF bytes.

## Reproduce the paper's tables, figures, and numerical results

Use Python 3.10+ for analysis. Create an environment outside the checkout:

```bash
python3 -m venv /path/to/bigdata-analysis
/path/to/bigdata-analysis/bin/python -m pip install -r SCRIPTS/BIGDATA/requirements-analysis.txt
/path/to/bigdata-analysis/bin/python SCRIPTS/BIGDATA/reproduce_paper.py
```

On Windows, use the environment's `Scripts/python.exe`. The command verifies the release, recomputes all four live stages, checks the component and audit measurements, regenerates both manuscript figures and table rows, and writes an isolated copy of the paper under `build/reproduction/`. It does not alter the packaged reference files, train models, or execute workflows.

To also compile the paper, append `--engine tectonic` (Tectonic 0.17) or `--engine latexmk` (an installed TeX distribution). Use `--executable /path/to/compiler` if the compiler is not on PATH. First use of Tectonic may download TeX resources. The final PDF is `build/reproduction/compiled/camp_bigdata.pdf`; the numerical verification report is `build/reproduction/reproduction.json`.

The source and included preview are in [the camera-ready directory](Big_Data_paper/Big_Data_Camera_Ready/source/Camera_Ready_Introduction_Revision/). For Overleaf, upload `Big_Data_paper/Big_Data_Camera_Ready/` and select `source/Camera_Ready_Introduction_Revision/INTRODUCTION_REVISION_PREVIEW.tex`. The wrapper applies the same T1 font encoding as the local build.

## What each paper result uses

| Paper evidence | Inputs and executable analysis | Reference result |
|---|---|---|
| Table I: explicit reads vs reads + mapped accesses | [W3](Reviewer_Feedbacks/W3/README.md); retained predictions for 5,026 tasks | 32 vs 30 underallocations; 41,853 vs 34,271 GiB requested |
| Table II: four feature configurations | [Feature ablation](Reviewer_Feedbacks/chat_ablation/README.md) | 85 / 46 / 52 / 30 underallocations; native configurations differ in routing |
| Figure 1(a): selective vs random downstream auditing | [W2](Reviewer_Feedbacks/W2/README.md); five budgets and five seeds | At 20%: 265.8 vs 305.8 mean underallocations on 17,067 post-update tasks; paired interval includes zero |
| Figure 1(b): auditing cost | [W5](Reviewer_Feedbacks/W5/README.md); paired runtimes and frozen audit selections | 5.999 / 24.025 / 66.534 GiB-h at 5 / 20 / 50%; 139.680 GiB-h at 100% |
| Figure 2 and live result paragraphs | [Live reproduction guide](SCRIPTS/RQ5/LIVE_EXPERIMENTS.md); four stages, 6,000 tasks each | See table below |

Published WORKS endpoints (87/31) remain labeled separately from the four-feature rerun (85/46/52/30); do not combine their counts. Underallocation means a request below the measured peak, not an observed OOM. Missing runtimes for 449 offline evaluation tasks contribute zero to unused memory-time, consistently across feature variants. Auditing cost is paired positive runtime overhead multiplied by the fixed CAMP request; it is not an end-to-end net saving.

| Live stage | Requested GiB | Peak-sum GiB | Unused GiB-h | First-request coverage |
|---|---:|---:|---:|---:|
| Original cold | 977.7871 | 229.3280 | 32.86089 | 99.53% |
| Original warm | 241.1211 | 229.3809 | 0.01847 | 99.58% |
| Warm-Transfer, new input | 319.2236 | 273.4394 | 0.12805 | 94.15% |
| Direct-Transfer, new input | 343.5586 | 277.9579 | 0.22109 | 95.78% |

Warm-Transfer executes cold, then warm on original inputs, then new inputs. Direct-Transfer branches from the **same cold checkpoint** and executes the same new inputs without the intervening warm pass. Both transfer arms continue online learning, and all live tasks are audited. Selective auditing is evaluated separately by replay.

Requests, coverage, margins, and unused memory-time exclude the separate **128 MiB execution allowance**. Recorded zero OOMs apply to execution with that allowance. Request/peak sums are not simultaneous occupancy. Unused memory-time uses successful-attempt runtimes and excludes failed attempts, audit, inference, and retraining cost. The two new-input arms have identical flagstat summaries for all 1,974 alignment chunks.

## Retrain and execute experiments

Analysis from recorded measurements and fresh execution are separate routes:

- **Read/mapped-access models:** follow [W3](Reviewer_Feedbacks/W3/README.md), including its `fresh_training.py` command in a new destination.
- **Four feature models:** follow [feature ablation](Reviewer_Feedbacks/chat_ablation/README.md), including `run_full_ablation.sh` in its pinned environment.
- **Selective-auditing replay:** follow [W2](Reviewer_Feedbacks/W2/README.md), including `fresh_training.py` for the full model/replay experiment.
- **Auditing costs:** [W5](Reviewer_Feedbacks/W5/README.md) recomputes paired retained measurements; no new training is needed.
- **Bowtie2 live study:** follow [LIVE_EXPERIMENTS.md](SCRIPTS/RQ5/LIVE_EXPERIMENTS.md) for exact input acquisition, checkpoint restoration, cluster configuration, full four-stage execution, or a saved-cold Direct-Transfer repeat. The guide also covers rebuilding the offline seed from the packaged 33,516-task cohort.

Full live execution requires Linux, Slurm, Nextflow 25.10.7, Apptainer, BCC/eBPF privileges and the pinned Python 3.9 model environment. It is not a Windows execution route or a single-machine emulation. Raw FASTQ inputs (~30 GiB) are downloaded from exact ENA URLs and checked against supplied MD5/size metadata. Large BAM/work files are regenerated. The exact reference snapshot, initial/terminal model-history bundles, matching databases and Bowtie2/samtools container images are included in a compressed content-addressed store:

```bash
python SCRIPTS/RQ5/live/models.py list
python SCRIPTS/RQ5/live/models.py verify --deep
```

Fresh hardware, completion order and asynchronous training may change numerical outcomes. The retained records reproduce the reported numerical realization; fresh runs test the procedure and must report their measured results.

## Repository map

```text
Big_Data_paper/   Current manuscript, bibliography, figures and figure builders
Reviewer_Feedbacks/{W2,W3,W5,chat_ablation}/
                  Self-contained analyses, training inputs and reference predictions
SCRIPTS/BIGDATA/  Paper reproduction/build helpers and release regression tests
SCRIPTS/RQ5/      Offline-seed build and live execution/learning implementation
DATA/RQ2/        Source cohort needed to rebuild the offline seed
DATA/RQ5/        Fixed split, exact input manifests, model/history/container store
RESULTS/RQ5/     Four live-stage records and compact transfer snapshots
WORKFLOWS/       Bowtie2 workflow and its common integration helpers
AUDIT/           Consumption-measurement helpers and prerequisites
DOCS/            Scope, provenance, changes and verification evidence
```

## Verification and provenance

See [verification](DOCS/VERIFICATION.md) for checks actually run and their limits, and [release changes](DOCS/REPRODUCTION_CHANGES.md) for fixes to fresh-training fallback handling, incremental history publication and learner defaults. These fixes do not replace or rewrite retained experimental outcomes.

The CAMP method and reused measurements derive from [IEEE_WORKS_26_ARTIFACT](https://github.com/Nagarjuna-kandimalla/IEEE_WORKS_26_ARTIFACT); cite WORKS as recorded in the manuscript. [Source provenance](DOCS/SOURCE_MANIFEST.json) records the original import, and [paper provenance](Big_Data_paper/Big_Data_Camera_Ready/source/Camera_Ready_Introduction_Revision/RESULTS_PROVENANCE.md) maps this paper to its retained evidence. Original import inventories are historical, not the current package inventory: `ARTIFACT_MANIFEST.json` defines this release. See [third-party notices](THIRD_PARTY_NOTICES.md).
