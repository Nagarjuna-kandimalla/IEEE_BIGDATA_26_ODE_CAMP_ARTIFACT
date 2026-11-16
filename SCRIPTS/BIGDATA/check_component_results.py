"""Verify component experiments and export numerical results to CSV/JSON."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--repo-root', type=Path, default=HERE.parents[1])
parser.add_argument('--output-dir', type=Path, default=HERE.parents[1] / 'build/component-results')
args = parser.parse_args()
ROOT = args.repo_root.resolve()
OUT = args.output_dir.resolve()
OUT.mkdir(parents=True, exist_ok=True)
sources = {}

def read(name, **kwargs):
    path = ROOT / name
    sources[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return pd.read_csv(path, **kwargs)

def check(actual, expected):
    np.testing.assert_allclose(actual, expected, rtol=1e-10, atol=1e-8)

routes = read('Reviewer_Feedbacks/chat_ablation/results/route_analysis/route_stratified_metrics.csv')
feature_metrics = read('Reviewer_Feedbacks/chat_ablation/results/paper_configuration/native_metrics.csv').set_index('variant')
stems = {'A+P':'a_plus_p', 'A+P+CH':'a_plus_p_plus_ch',
         'A+P+CHAT':'a_plus_p_plus_chat', 'A+P+CH+CHAT':'a_plus_p_plus_c'}
identity = None
for row in routes.itertuples():
    stem = stems[row.variant] + ('_final_global_base' if row.route == 'global' else '')
    d = read(f'Reviewer_Feedbacks/chat_ablation/reference_predictions/seed_1996/{stem}/task_predictions.tsv', sep='\t').sort_values('logical_task_id')
    assert len(d) == 5026 and d.logical_task_id.is_unique
    if identity is None:
        identity = d[['logical_task_id','actual_peak_mib']].reset_index(drop=True)
    else:
        pd.testing.assert_frame_equal(identity, d[['logical_task_id','actual_peak_mib']].reset_index(drop=True))
    check((d.first_allocation_mib < d.actual_peak_mib).sum(), row.underallocations)
    check(d.first_allocation_mib.sum()/1024, row.total_request_gib)
    check(100*np.median(abs(d.point_q50_prediction_mib-d.actual_peak_mib)/d.actual_peak_mib), row.q50_mdape_percent)
    if row.route == ('global' if row.variant == 'A+P' else 'process_tail'):
        recorded = feature_metrics.loc[row.variant]
        check([row.underallocations, row.q50_mdape_percent, row.total_request_gib],
              [recorded.underallocations, recorded.mdape_percent, recorded.total_request_gib])
        runtime = pd.to_numeric(d.runtime_seconds, errors='coerce').fillna(0)
        check((np.maximum(d.first_allocation_mib-d.actual_peak_mib,0)*runtime).sum()/1024/3600,
              recorded.unused_gib_hours)


endpoints = read('Reviewer_Feedbacks/chat_ablation/results/route_analysis/paper_endpoint_reproduction.csv')
for name, filename in [('Access (A+P)','a_plus_p_task_predictions.tsv.gz'), ('Full CAMP','a_plus_p_plus_c_task_predictions.tsv.gz')]:
    d = read('Reviewer_Feedbacks/chat_ablation/published_reference/'+filename, sep='\t')
    ref = endpoints[(endpoints.method==name)&(endpoints.source=='paper_frozen')].iloc[0]
    check((d.first_allocation_mib<d.actual_peak_mib).sum(),ref.underallocations)
    check(d.first_allocation_mib.sum()/1024,ref.total_request_gib)

mmap = read('Reviewer_Feedbacks/W3/results/paper_native_metrics.csv')
for row in mmap.itertuples():
    paths = list((ROOT/f'Reviewer_Feedbacks/W3/runs/{row.signal}').rglob('task_predictions.tsv.gz'))
    assert len(paths)==1, paths
    d=read(paths[0].relative_to(ROOT).as_posix(),sep='\t')
    check((d.first_allocation_mib<d.actual_peak_mib).sum(),row.underallocations)
    check(d.first_allocation_mib.sum()/1024,row.requested_gib)

reps = read('Reviewer_Feedbacks/W2/results/downstream_allocation/per_repetition_metrics.tsv',sep='\t')
paired = read('Reviewer_Feedbacks/W2/results/downstream_allocation/paired_summary.tsv',sep='\t')
native = reps[(reps.evaluation=='after_first_update')&(reps.operating_point=='native')]
assert len(native)==50 and set(native.tasks)=={17067}
means = native.groupby(['budget','method'])[['underallocations','requested_gib']].mean()
ci = paired[(paired.evaluation=='after_first_update')&(paired.operating_point=='native')].sort_values('budget')
for row in ci.itertuples():
    delta = (means.loc[(row.budget,'selective'),'underallocations']-means.loc[(row.budget,'random'),'underallocations'])/17067
    check(delta,row.selective_minus_random_rate)

cost = read('Reviewer_Feedbacks/W5/inputs/task_level_full_ebpf_net_benefit.csv')
selections = read('Reviewer_Feedbacks/W5/inputs/audit_selections.tsv.gz',sep='\t')
budgets = read('Reviewer_Feedbacks/W5/results/budget_summary.csv')
assert len(cost)==5026 and cost.logical_task_id.is_unique
check(cost.audit_cost_positive_gib_hours, np.maximum(cost.ebpf_wrapper_seconds-cost.baseline_wrapper_seconds,0)*cost.camp_request_mib/1024/3600)
audit_rows=[]
for (budget,seed), group in selections.groupby(['budget','seed']):
    ids = group.loc[group.audited.astype(bool),'logical_task_id']
    charge = cost.set_index('logical_task_id').loc[ids,'audit_cost_positive_gib_hours'].sum()
    audit_rows.append({'budget':budget,'seed':int(seed),'audits':len(ids),'cost':float(charge)})
audit_costs=pd.DataFrame(audit_rows)
for idx,row in budgets.iterrows():
    group=audit_costs[np.isclose(audit_costs.budget,row.budget_percent/100)]
    assert len(group)==5
    check(group.cost.mean(),row.paper_mean_audit_cost_gib_hours)
    check(group.audits,row.audited_test_tasks)
    rng=np.random.default_rng(73129)
    low,high=np.quantile(rng.choice(group.cost.to_numpy(),size=(10000,5),replace=True).mean(axis=1),[.025,.975])
    budgets.loc[idx,'cost_seed_mean_ci95_low']=low
    budgets.loc[idx,'cost_seed_mean_ci95_high']=high
budgets[['budget_percent','audited_test_tasks','paper_mean_audit_cost_gib_hours','cost_seed_mean_ci95_low','cost_seed_mean_ci95_high']].to_csv(OUT/'audit_cost_summary.csv',index=False)

feature_metrics.reset_index().to_csv(OUT/'feature_metrics.csv',index=False)
mmap.to_csv(OUT/'mapped_access_metrics.csv',index=False)
means.reset_index().to_csv(OUT/'downstream_means.csv',index=False)
ci.to_csv(OUT/'downstream_intervals.csv',index=False)
report={'status':'PASS','source_sha256':sources,
    'feature_metrics':feature_metrics.reset_index().to_dict('records'),
    'mapped_access':mmap.to_dict('records'),
    'downstream_means':means.reset_index().to_dict('records'),
    'downstream_intervals':ci.to_dict('records'),
    'audit_costs':budgets[['budget_percent','audited_test_tasks','paper_mean_audit_cost_gib_hours','cost_seed_mean_ci95_low','cost_seed_mean_ci95_high']].to_dict('records')}
(OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: component experiments; CSV/JSON outputs:',OUT)
