"""Regenerate manuscript tables/figures from retained results; never trains models.

Run from any directory with Python, numpy, pandas and matplotlib installed.
Pass --repo-root when this camera-ready directory is outside the full artifact.
"""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--repo-root', type=Path, default=HERE.parents[3])
ROOT = parser.parse_args().repo_root.resolve()
OUT = HERE / 'result_assets'
OUT.mkdir(exist_ok=True)
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

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':9,
 'axes.labelsize':8,'xtick.labelsize':7.5,'ytick.labelsize':7.5,'legend.fontsize':7,
 'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
blue='#23699B'; orange='#B75B21'
fig,axes=plt.subplots(1,2,figsize=(7.1,2.25),layout='constrained')
ax=axes[0];x=ci.budget.to_numpy()*100;y=ci.selective_minus_random_rate.to_numpy()*100
ax.axhline(0,color='0.4',lw=.8)
ax.errorbar(x,y,yerr=np.array([y-ci.ci_low.to_numpy()*100,ci.ci_high.to_numpy()*100-y]),fmt='o-',color=blue,capsize=3,lw=1.2)
ax.set(xlabel='Audit budget (%)',ylabel='Selective - random (pp)',title='(a) Downstream underallocation rate',xticks=x)
ax.grid(axis='y',alpha=.2)
ax=axes[1];c=budgets[budgets.budget_percent<=50];x=c.budget_percent.to_numpy();y=c.paper_mean_audit_cost_gib_hours.to_numpy()
ax.axhline(0,color='0.4',lw=.8)
ax.errorbar(x,y,yerr=np.array([y-c.cost_seed_mean_ci95_low.to_numpy(),c.cost_seed_mean_ci95_high.to_numpy()-y]),fmt='s-',color=orange,capsize=3,lw=1.2)
ax.set(xlabel='Audit budget (%)',ylabel='Auditing cost (GiB-h)',title='(b) Auditing cost at fixed requests',xticks=x)
ax.grid(axis='y',alpha=.2)
for ext in ['pdf','png']:fig.savefig(OUT/f'audit_tradeoffs.{ext}',dpi=220)
plt.close(fig)

labels_tex={'A+P':'Access','A+P+CH':r'Access+$\mathbf{h}_{c,t}$', 'A+P+CHAT':r'Access+$\hat c_t$', 'A+P+CH+CHAT':'CAMP'}
rows=[]
for variant in stems:
    result = feature_metrics.loc[variant]
    rows.append(f"{labels_tex[variant]} & {int(result.underallocations)} & {result.mdape_percent:.2f} & {result.total_request_gib:,.2f} & {result.unused_gib_hours:.2f} " + r'\\')
(OUT/'feature_rows.tex').write_text('\n'.join(rows)+'\n')
(OUT/'mmap_rows.tex').write_text('\n'.join(f"{'Read-only' if r.signal=='read' else 'Read + mapped'} & {r.underallocations} & {r.requested_gib:,.0f} & {r.mdape_pct:.2f} "+r'\\' for r in mmap.itertuples())+'\n')
tables={
 'mmap':(r'@{}lrrr@{}',r'Signal & Underalloc. & Requests (GiB) & MdAPE (\%)\\'),
 'feature':(r'@{}lrrrr@{}',r'Feature view & Underalloc. & MdAPE & Requests & $W$\\'+'\n'+r' & & (\%) & (GiB) & (GiB-h)\\')}
for name,(columns,header) in tables.items():
    body=(OUT/f'{name}_rows.tex').read_text()
    (OUT/f'{name}_table.tex').write_text(r'\begin{tabular}{'+columns+'}\n'+r'\toprule'+'\n'+header+'\n'+r'\midrule'+'\n'+body+r'\bottomrule'+'\n'+r'\end{tabular}'+'\n')
manifest={'source_sha256':sources,'verified_route_metrics':routes.to_dict('records'),'feature_metrics':feature_metrics.reset_index().to_dict('records'),'published_and_reproduced_endpoints':endpoints.to_dict('records'),
 'mmap':mmap.to_dict('records'),'downstream_native_means':means.reset_index().to_dict('records'),'downstream_intervals':ci.to_dict('records'),
 'audit_accounting':budgets.to_dict('records'),
 'scope':'Reanalysis/plotting of retained records; no new model training or workflow execution.'}
(OUT/'result_provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Verified 8 feature/configuration rows, 2 published endpoints, 2 mmap arms, 25 paired downstream summaries, 40 audit-budget selections.')
print('Assets:',OUT)

# Transfer records are packaged locally and have a separate provenance manifest.
from build_transfer_assets import main as build_transfer_assets
build_transfer_assets()
