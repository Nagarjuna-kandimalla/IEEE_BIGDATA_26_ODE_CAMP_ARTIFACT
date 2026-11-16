"""Verify the artifact and reproduce component and live experiment results."""
import argparse
import csv
import gzip
import json
from pathlib import Path
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=ROOT/'build/reproduced-results')
    a = p.parse_args()
    out = a.output.resolve()
    if out.exists():
        p.error('Choose a fresh --output directory')
    subprocess.run([sys.executable,str(ROOT/'SCRIPTS/RQ5/live/verify_package.py')],check=True)
    out.mkdir(parents=True)
    for command in [
        ['SCRIPTS/BIGDATA/check_component_results.py','--output-dir',str(out/'components')],
        ['SCRIPTS/RQ5/live/reproduce_results.py','--output',str(out/'live')],
    ]:
        subprocess.run([sys.executable,str(ROOT/command[0]),*command[1:]],check=True)
    full=json.loads((out/'live/results.json').read_text())
    details={}
    for stage in full['results']:
        base=ROOT/'RESULTS/RQ5/live_experiments'/stage
        with gzip.open(base/'task_instances.tsv.gz','rt',newline='') as f:
            rows=list(csv.DictReader(f,delimiter='\t'))
        assert len(rows)==6000 and all(x['final_success'].lower() in ('true','1') for x in rows)
        ratios=[float(x['first_applied_allocation_mib'])/float(x['final_peak_mib']) for x in rows]
        counts=[sum(test(x) for x in ratios) for test in (
            lambda x:x<1,lambda x:1<=x<=1.05,lambda x:1.05<x<=1.10,
            lambda x:1.10<x<=1.25,lambda x:x>1.25)]
        alignment=[x for x in rows if x['process']=='ALIGN_CHUNK']
        assert len(alignment)==1974 and sum(counts)==6000
        summary=json.loads((base/'summary.json').read_text())['global']
        details[stage]={'margin_counts':dict(zip(['below_peak','0_to_5_percent','5_to_10_percent','10_to_25_percent','over_25_percent'],counts)),
            'margin_percent':[x/60 for x in counts],
            'alignment_mdape_percent':statistics.median(100*abs(float(x['a_plus_p_plus_c_point_q50_mib'])/float(x['final_peak_mib'])-1) for x in alignment),
            'retry_attempts':int(summary['total_retry_attempts'])}
    (out/'live/stage_details.json').write_text(json.dumps(details,indent=2)+'\n')
    report={'status':'PASS','outputs':['components/results.json','components/feature_metrics.csv',
        'components/mapped_access_metrics.csv','components/downstream_means.csv',
        'components/downstream_intervals.csv','components/audit_cost_summary.csv',
        'live/results.json','live/metrics.tsv','live/stage_details.json']}
    (out/'reproduction.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',out/'reproduction.json')


if __name__=='__main__':main()
