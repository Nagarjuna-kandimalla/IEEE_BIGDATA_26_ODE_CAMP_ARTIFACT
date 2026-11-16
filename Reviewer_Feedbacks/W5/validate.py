"""Check auditing costs against the preserved paper reference."""
from pathlib import Path
import numpy as np
import pandas as pd
r=Path(__file__).resolve().parent
expected=pd.read_csv(r/'expected_results/budget_summary.csv')
actual=pd.read_csv(r/'results/budget_summary.csv')
np.testing.assert_allclose(actual[expected.columns], expected, rtol=1e-12, atol=1e-10)
assert (actual.cost_seed_mean_ci95_low <= actual.paper_mean_audit_cost_gib_hours).all()
assert (actual.cost_seed_mean_ci95_high >= actual.paper_mean_audit_cost_gib_hours).all()
print('PASS: paper auditing-cost references')
