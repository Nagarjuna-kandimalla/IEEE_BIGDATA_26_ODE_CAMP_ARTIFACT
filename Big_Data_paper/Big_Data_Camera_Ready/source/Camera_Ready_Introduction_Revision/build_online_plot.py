"""Compact paper layout of the existing deployment plots; validate against task records."""
from pathlib import Path
import csv, gzip, hashlib, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
ASSETS=HERE/'result_assets'
DATA=ASSETS/'transfer_records'
PHASES=['warm_transfer_cold','warm_transfer_warm','warm_transfer_new_input','direct_transfer_new_input']
NAMES=['Cold','Warm','WT','DT']
manifest=json.loads((DATA/'source_manifest.json').read_text())
saved=json.loads((ASSETS/'figure_data.json').read_text())['metrics']
metrics=[]
for phase in PHASES:
    rel=phase+'/task_instances.tsv.gz'
    assert hashlib.sha256((DATA/rel).read_bytes()).hexdigest()==manifest['files'][rel]['sha256']
    with gzip.open(DATA/rel,'rt',newline='') as f: rows=list(csv.DictReader(f,delimiter='\t'))
    assert len(rows)==6000 and len({(r['process'],r['task_instance']) for r in rows})==6000
    request=np.array([float(r['first_applied_allocation_mib']) for r in rows])
    peak=np.array([float(r['final_peak_mib']) for r in rows])
    runtime=np.array([float(r['final_runtime_seconds']) for r in rows])
    ratio=request/peak
    fractions=[np.mean(mask)*100 for mask in [ratio<1,(ratio>=1)&(ratio<=1.05),(ratio>1.05)&(ratio<=1.1),(ratio>1.1)&(ratio<=1.25),ratio>1.25]]
    m=[request.sum()/1024,peak.sum()/1024,(np.maximum(request-peak,0)*runtime/3600/1024).sum(),fractions]
    assert np.allclose(m[:3],[saved[phase][k] for k in ['request_gib','peak_gib','wastage_gibh']])
    assert np.allclose(fractions,list(saved[phase]['margin_percent'].values()))
    metrics.append(m)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':7,'axes.labelsize':7,'axes.titlesize':8,'axes.titleweight':'bold','xtick.labelsize':7,'ytick.labelsize':6.5,'legend.fontsize':6.2,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.6,'hatch.linewidth':.35,'pdf.fonttype':42})
fig,axs=plt.subplots(1,3,figsize=(7.15,1.95),gridspec_kw={'width_ratios':[1.12,1,1.12]})
fig.subplots_adjust(left=.065,right=.995,bottom=.25,top=.78,wspace=.46)
x=np.arange(4)
ax=axs[0]
ax.bar(x-.18,[m[1] for m in metrics],.36,color='#d0d0d0',edgecolor='#555555',hatch='////',linewidth=.5,label='Observed peak')
ax.bar(x+.18,[m[0] for m in metrics],.36,color='#78b552',edgecolor='#3c6733',hatch='...',linewidth=.5,label='CAMP request')
ax.set_ylim(0,1150);ax.set_ylabel('Aggregate memory (GiB)');ax.set_title('(a) Requests and peaks',pad=27)
ax.legend(frameon=False,ncol=2,loc='lower center',bbox_to_anchor=(.5,1.0),columnspacing=.6,handlelength=1)
for i,m in enumerate(metrics):ax.text(i+.12,m[0]+35,f'{m[0]:.1f}',ha='center',fontsize=6)
ax=axs[1]
ax.bar(x,[m[2] for m in metrics],.64,color='#78b552',edgecolor='#3c6733',hatch='...',linewidth=.5)
ax.set_yscale('log');ax.set_ylim(.007,150)
ax.set_yticks([.01,.1,1,10,100]);ax.set_ylabel('$W$ (GiB-hours, log)');ax.set_title('(b) Unused memory-time',pad=27)
for i,m in enumerate(metrics):ax.annotate(f'{m[2]:.5f}',(i,m[2]),xytext=(0,4),textcoords='offset points',ha='center',fontsize=6,rotation=0)
ax=axs[2]
colors=['#df765b','#198561','#73b99b','#85a8c5','#cdcdcd'];hatches=['...','...','////','xxxx','////'];labels=['Below peak','0-5%','5-10%','10-25%','>25%']
bottom=np.zeros(4)
for j,(color,hatch,label) in enumerate(zip(colors,hatches,labels)):
 vals=np.array([m[3][j] for m in metrics]);ax.bar(x,vals,.62,bottom=bottom,color=color,edgecolor='#3a3a3a',hatch=hatch,linewidth=.4,label=label);bottom+=vals
ax.set_ylim(0,100);ax.set_ylabel('Tasks (%)');ax.set_title('(c) Request margins',pad=27)
ax.text(.5,1.16,'Below peak (%)',transform=ax.transAxes,ha='center',fontsize=6.2,color='#9b3827')
for i,m in enumerate(metrics):ax.text(i,103,f'{m[3][0]:.2f}',ha='center',fontsize=6,color='#9b3827')
for ax in axs:
 ax.set_xticks(x,NAMES);ax.set_axisbelow(True);ax.grid(axis='y',color='#bbb',linestyle='--',linewidth=.4,alpha=.6)
handles,labels=axs[2].get_legend_handles_labels()
fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.53,0),frameon=False,ncol=5,handlelength=1.5,columnspacing=1.2)
fig.savefig(ASSETS/'online_deployment_compact.pdf',bbox_inches='tight',pad_inches=.025)
fig.savefig(ASSETS/'online_deployment_compact.png',dpi=300,bbox_inches='tight',pad_inches=.025)
print('Verified all four stages against retained records and existing plot data.')
