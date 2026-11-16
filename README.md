# IEEE Big Data 2026 CAMP Artifact

Code, datasets, model checkpoints, execution records, and reproduction instructions for CAMP component experiments and online Bowtie2 deployment.

## Contents

| Location | Contents |
|---|---|
| `Reviewer_Feedbacks/W3/` | Read-only and read-plus-mapped-access experiment: inputs, training code, predictions and analysis |
| `Reviewer_Feedbacks/chat_ablation/` | Four feature configurations: fixed split, modeling code, retained predictions and metrics |
| `Reviewer_Feedbacks/W2/` | Selective/random auditing replay: five budgets, five seeds, task records and validation |
| `Reviewer_Feedbacks/W5/` | Paired runtime measurements, audit selections and cost analysis |
| `SCRIPTS/RQ5/` | Offline seed construction, live allocator/learner, checkpoint restoration and Slurm execution |
| `SCRIPTS/BIGDATA/` | Combined result reproduction, integrity verification and regression tests |
| `DATA/RQ2/` | 33,516-task offline training cohort |
| `DATA/RQ5/` | Fixed split, input manifests, reference sequence, model/history bundles and container images |
| `RESULTS/RQ5/` | Four live-stage records, task attempts, predictions, outcomes, traces and flagstat outputs |
| `WORKFLOWS/` | Bowtie2 workflow and common integration helpers |
| `AUDIT/` | Tracer prerequisites and integration instructions |
| `DOCS/` | Technical provenance, code changes and verification records |

## Download and verify

```bash
git clone https://github.com/Nagarjuna-kandimalla/IEEE_BIGDATA_26_CAMP_ARTIFACT.git
cd IEEE_BIGDATA_26_CAMP_ARTIFACT
python SCRIPTS/RQ5/live/verify_package.py --require-tracked
python SCRIPTS/RQ5/live/models.py verify --deep
```

Run commands from the repository root unless a command changes directory. Use `python3` where required by your environment. For a ZIP download, omit `--require-tracked`.

## Reproduce all retained numerical results

Use Python 3.10+ and the analysis dependencies:

```bash
python3 -m venv /path/to/camp-analysis
/path/to/camp-analysis/bin/python -m pip install -r SCRIPTS/BIGDATA/requirements-analysis.txt
/path/to/camp-analysis/bin/python SCRIPTS/BIGDATA/reproduce_results.py
```

On Windows, use the environment's `Scripts/python.exe`. The command verifies package hashes, recomputes component metrics and auditing costs, and processes the four live stages. Outputs are written to `build/reproduced-results/`:

```text
reproduction.json
components/
  results.json
  feature_metrics.csv
  mapped_access_metrics.csv
  downstream_means.csv
  downstream_intervals.csv
  audit_cost_summary.csv
live/
  results.json
  metrics.tsv
  stage_details.json
```

For another execution, choose a fresh destination:

```bash
python SCRIPTS/BIGDATA/reproduce_results.py --output build/results-02
```

## Reproduce individual component analyses

W2, W3 and the feature-ablation packages provide Linux/Python 3.9 setup scripts with pinned dependencies. Run the relevant pair of commands from the repository root:

```bash
(cd Reviewer_Feedbacks/W3 && bash setup.sh && bash reproduce.sh)
(cd Reviewer_Feedbacks/chat_ablation && bash setup.sh && bash reproduce.sh)
(cd Reviewer_Feedbacks/W2 && bash setup.sh && bash reproduce.sh)
```

For auditing-cost analysis, use the analysis environment:

```bash
python Reviewer_Feedbacks/W5/analyze.py
python Reviewer_Feedbacks/W5/validate.py
```

| Experiment | Retained evaluation | Reference output |
|---|---|---|
| Read-only / read + mapped accesses | 5,026 tasks per configuration | 32 / 30 underallocations |
| Four feature configurations | 5,026 tasks per configuration | 85 / 46 / 52 / 30 underallocations |
| Selective / random auditing | 25 paired budget/seed runs | At 20% budget: 265.8 / 305.8 mean underallocations |
| Auditing costs | Eight budgets, five seeds | 5.999 / 24.025 / 66.534 / 139.680 GiB-h at 5 / 20 / 50 / 100% |

## Train fresh component models

After setting up each package's environment:

```bash
cd Reviewer_Feedbacks/W3
.venv/bin/python fresh_training.py /path/to/new-mapped-access-run --threads 8
```

```bash
cd Reviewer_Feedbacks/chat_ablation
bash run_full_ablation.sh
```

```bash
cd Reviewer_Feedbacks/W2
.venv/bin/python fresh_training.py /path/to/new-auditing-replay --workers 2 --threads 8
```

Use new output destinations. Package guides contain the experiment configuration and output layout:
[W3](Reviewer_Feedbacks/W3/README.md), [feature ablation](Reviewer_Feedbacks/chat_ablation/README.md), [W2](Reviewer_Feedbacks/W2/README.md), [W5](Reviewer_Feedbacks/W5/README.md).

## Reproduce live Bowtie2 deployment

The retained execution sequence is:

1. Original-input cold run from the offline seed.
2. Original-input warm run from the cold checkpoint.
3. Warm-Transfer on new inputs from the warm checkpoint.
4. Direct-Transfer on the same new inputs from the shared cold checkpoint.

Each stage contains 6,000 tasks across seven process types and 1,974 alignment chunks.

| Stage | Requested GiB | Peak-sum GiB | Unused GiB-h | Coverage |
|---|---:|---:|---:|---:|
| Original cold | 977.7871 | 229.3280 | 32.86089 | 99.53% |
| Original warm | 241.1211 | 229.3809 | 0.01847 | 99.58% |
| Warm-Transfer, new input | 319.2236 | 273.4394 | 0.12805 | 94.15% |
| Direct-Transfer, new input | 343.5586 | 277.9579 | 0.22109 | 95.78% |

Recompute these results directly:

```bash
python SCRIPTS/RQ5/live/reproduce_results.py --output build/live-results
```

For fresh execution, follow [LIVE_EXPERIMENTS.md](SCRIPTS/RQ5/LIVE_EXPERIMENTS.md). It includes:

- Linux/Slurm, Nextflow 25.10.7, Apptainer and BCC/eBPF prerequisites;
- the Python 3.9 model environment;
- original/new FASTQ acquisition and MD5 checks;
- checkpoint and exact container-image extraction;
- cluster configuration and four-stage submission;
- saved-cold Direct-Transfer execution;
- offline-seed rebuilding from the packaged cohort;
- stage validation and checkpoint handoff commands.

List available bundles or extract a checkpoint into a new destination:

```bash
python SCRIPTS/RQ5/live/models.py list
python SCRIPTS/RQ5/live/models.py extract initial /path/to/initial-state
python SCRIPTS/RQ5/live/models.py extract warm_transfer_cold /path/to/cold-checkpoint
```

## Technical checks

Run in the Linux model environment:

```bash
python -m unittest discover -s SCRIPTS/BIGDATA/tests -v
python -m unittest discover -s SCRIPTS/RQ5/live/tests -v
python -m unittest discover -s SCRIPTS/RQ5/experiment_template/camp/live_online_learning/tests -v
python SCRIPTS/RQ5/live/selfcheck.py
```

[Verification records](DOCS/VERIFICATION.md) list executed checks. [Code changes](DOCS/REPRODUCTION_CHANGES.md) document fallback handling, history-publication recovery and learner defaults. [Source provenance](DOCS/SOURCE_MANIFEST.json) identifies retained technical files imported from [IEEE_WORKS_26_ARTIFACT](https://github.com/Nagarjuna-kandimalla/IEEE_WORKS_26_ARTIFACT). `ARTIFACT_MANIFEST.json` contains current release checksums. See [third-party notices](THIRD_PARTY_NOTICES.md) for attribution.
