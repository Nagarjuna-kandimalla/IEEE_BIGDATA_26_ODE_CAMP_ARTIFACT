"""Regression tests for executable training and interrupted learner ingestion."""
import ast
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CAMP = ROOT / "SCRIPTS/RQ5/experiment_template/camp"
ONLINE = CAMP / "live_online_learning"
sys.path[:0] = [str(ONLINE / "scripts"), str(ONLINE), str(CAMP / "scripts"), str(CAMP.parent / "WORKS_ML")]
import run_online_learner as learner
from camp_ml.online_history import TaskOutcome


class ReproductionRegressions(unittest.TestCase):
    def test_fallback_metadata_empty_and_nonempty_in_all_copies(self):
        paths = list((ROOT / "SCRIPTS/RQ5").rglob("modeling.py")) + list((ROOT / "Reviewer_Feedbacks").rglob("modeling.py"))
        checked = 0
        for path in paths:
            if "W2" in path.parts:  # this vendor copy already handles the empty case
                continue
            tree = ast.parse(path.read_text())
            assignment = next((n for n in ast.walk(tree) if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "fallback_processes" for t in n.targets)), None)
            if assignment is None:
                continue
            checked += 1
            code = compile(ast.Module(body=[assignment], type_ignores=[]), str(path), "exec")
            frame = pd.DataFrame({"workflow": ["w", "w", "a"], "process": ["p", "p", "z"]})
            for mask, expected in [(np.array([False]*3), []), (np.array([True]*3), ["a::z", "w::p"])]:
                ns = {"test": frame, "fallback_rows": mask}
                exec(code, ns)
                self.assertEqual(ns["fallback_processes"], expected, str(path))
        self.assertEqual(checked, 4)

    def make_learner(self, root):
        obj = learner.OnlineLearner.__new__(learner.OnlineLearner)
        obj.state = sqlite3.connect(root / "state.sqlite3")
        obj.state.row_factory = sqlite3.Row
        obj._create_schema()
        obj.lock = threading.RLock()
        obj.outcome_dir = root / "outcomes"; obj.outcome_dir.mkdir(exist_ok=True)
        obj.history_update_dir = root / "updates"; obj.history_update_dir.mkdir(exist_ok=True)
        obj.update_log = root / "events.jsonl"
        obj._published_history_sequence = 0
        obj.history = unittest.mock.Mock()
        obj._decision_for_outcome = lambda path: {}
        obj._training_row = lambda decision, outcome, sequence: {"task_id": outcome.task_id, "history_order": sequence}
        return obj

    def write_outcome(self, obj, task):
        # Populate the actual dataclass's required fields, not a learner substitute.
        import inspect
        values = {"task_id": task, "workflow": "bowtie2", "process": "ALIGN_CHUNK",
            "completion_time": "2026-01-01T00:00:00+00:00", "decision_time": "2025-12-31T23:59:00+00:00", "version": "1", "static_input_bytes": 4096, "peak_memory_bytes": 1024,
            "consumed_bytes": 2048, "oom_flag": False}
        for name, parameter in inspect.signature(TaskOutcome).parameters.items():
            if name not in values and parameter.default is inspect.Parameter.empty:
                raise AssertionError("Test needs TaskOutcome field " + name)
        (obj.outcome_dir / (task + ".outcome.json")).write_text(json.dumps({"task_outcome": values, "exit_status": 0}))

    def test_commit_then_interruption_recovers_and_next_update_is_contiguous(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); obj = self.make_learner(root)
            self.write_outcome(obj, "task1")
            with patch.object(learner, "write_json_atomic", side_effect=OSError("injected publication interruption")):
                with self.assertRaises(OSError): obj.ingest_available()
            self.assertEqual(obj.state.execute("SELECT COUNT(*) FROM processed_outcomes").fetchone()[0], 1)
            self.assertFalse((obj.history_update_dir / "00000001.json").exists())
            obj.state.close()
            obj = self.make_learner(root)  # restart with the same durable database
            self.assertEqual(obj.ingest_available(), 0)  # committed outcome is not trained twice
            self.assertEqual(json.loads((obj.history_update_dir / "00000001.json").read_text())["sequence"], 1)
            self.write_outcome(obj, "task2")
            self.assertEqual(obj.ingest_available(), 1)
            self.assertEqual(sorted(p.name for p in obj.history_update_dir.glob("*.json")), ["00000001.json", "00000002.json"])
            self.assertEqual(obj.ingest_available(), 0)
            self.assertEqual(obj.state.execute("SELECT COUNT(*) FROM online_rows").fetchone()[0], 2)
            obj.state.close()

    def test_conflicting_published_history_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            obj = self.make_learner(Path(folder)); self.write_outcome(obj, "task1")
            obj.ingest_available()
            (obj.history_update_dir / "00000001.json").write_text('{"sequence": 1, "row": {}}')
            obj._published_history_sequence = 0
            with self.assertRaisesRegex(RuntimeError, "immutable history update changed"):
                obj._publish_history_updates()
            obj.state.close()

    def test_default_update_threshold_and_invalid_override(self):
        required = ["workflow", "version-prefix", "history-db", "state-db", "history-update-dir", "outcome-dir", "decision-dir", "base-training-frame", "base-history-features", "initial-model-root", "canonical-model-root", "experiment-config", "current-pointer", "version-dir", "update-log", "stop-file", "ready-file"]
        args = ["learner"] + [value for name in required for value in ("--" + name, "test")]
        with patch.object(sys, "argv", args):
            config = learner.parse_args()
        self.assertEqual((config.first_update, config.update_every, config.calibration_window), (128, 128, 64))
        with patch.object(sys, "argv", args + ["--first-update", "32"]):
            with self.assertRaises(SystemExit): learner.parse_args()


if __name__ == "__main__":
    unittest.main()
