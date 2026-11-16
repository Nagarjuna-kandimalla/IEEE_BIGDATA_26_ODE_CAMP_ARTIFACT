# Reproduction fixes, 2026-11-16

These operational fixes apply to future execution. Archived predictions, task results, checkpoints, and model history bytes remain unchanged.

1. Four retained modeling implementations now construct fallback process labels by iterating tuples. With no unseen test processes, the result is an empty list; pandas no longer turns an empty row aggregation into a DataFrame and raises a sort error. Nonempty labels remain sorted and deduplicated.
2. The online learner treats committed `online_rows` as a durable publication log. Startup and every ingestion pass reconstruct missing sequential history JSON files from committed rows before accepting later outcomes. Existing files are validated, publication is idempotent, and conflicting contents fail explicitly. This closes the outcome-commit/file-publication interruption window. It does not claim general power-loss recovery or safe automatic recovery of every live-stage component.
3. Learner defaults are 128 outcomes for the first update and subsequent updates, with a 64-row calibration window, matching the launcher. Invalid first-update <= calibration-window settings fail before work starts.
4. Current manuscript and figure scripts replace the older source. The figure builder no longer consumes the older cold/warm study. Paper builds use T1 encoding for both supported engines. Table bodies load generated rows.

Regression tests are in `SCRIPTS/BIGDATA/tests/`; run them with the pinned model environment. Retained package checksum manifests are refreshed for intentionally changed code. Their original-source provenance remains separately labeled.
