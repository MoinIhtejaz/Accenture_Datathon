import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
D='original_csv/'
perf=pd.read_csv(D+'performance.csv',parse_dates=['review_date'])
att=pd.read_csv(D+'attrition_log.csv',parse_dates=['exit_date'])

vol=att[att.exit_type=='voluntary'].set_index('employee_id')
perf=perf[perf.review_cycle.isin(['2024-H1','2024-H2','2025-H1'])]
perf['exit_date']=perf.employee_id.map(vol.exit_date)
inv=set(att.loc[att.exit_type=='involuntary','employee_id'])
perf=perf[~perf.employee_id.isin(inv)]                       # drop involuntary entirely
perf=perf[perf.exit_date.isna()|(perf.review_date<perf.exit_date)]

w=perf.pivot_table(index='employee_id',columns='review_cycle',values='goal_achievement_score')
w['exit_date']=w.index.map(vol.exit_date)

pairs=[('2024-H1','2024-H2','2024-H2 review\n(vs 2024-H1)'),('2024-H2','2025-H1','2025-H1 review\n(vs 2024-H2)')]
CYC_END={'2024-H2':pd.Timestamp('2025-01-01'),'2025-H1':pd.Timestamp('2025-07-01')}
rows=[]
for a,b,lab in pairs:
    d=w[[a,b,'exit_date']].dropna(subset=[a,b]).copy()
    d['delta']=d[b]-d[a]
    end=CYC_END[b]
    # left within 6 months AFTER that review cycle
    left=d.exit_date.notna()&(d.exit_date>=end)&(d.exit_date<end+pd.DateOffset(months=6))
    d['grp']=np.where(left,'Left within 6 months','Stayed >6 months / still employed')
    for g,s in d.groupby('grp'):
        rows.append(dict(pair=lab,grp=g,mean=s.delta.mean(),sem=s.delta.sem(),n=len(s),
                         base=s[a].mean(),after=s[b].mean()))
r=pd.DataFrame(rows)

groups=['Stayed >6 months / still employed','Left within 6 months']
COL={groups[0]:'#4C78A8',groups[1]:'#E45756'}
labs=[p[2] for p in pairs]; x=np.arange(len(labs)); bw=0.36
fig,ax=plt.subplots(figsize=(9.5,5.6))
for i,g in enumerate(groups):
    sub=r[r.grp==g].set_index('pair').reindex(labs)
    b=ax.bar(x+(i-0.5)*bw,sub['mean'],bw,yerr=1.96*sub['sem'],capsize=4,label=g,color=COL[g],edgecolor='white')
    for rect,v,n in zip(b,sub['mean'],sub['n']):
        off=0.55 if v>=0 else -0.9
        ax.text(rect.get_x()+rect.get_width()/2,v+off,f'{v:+.2f}\nn={int(n):,}',ha='center',
                va='bottom' if v>=0 else 'top',fontsize=9)
ax.axhline(0,color='#333',lw=1)
ax.set_xticks(x); ax.set_xticklabels(labs,fontsize=10.5)
ax.set_ylabel('Change in own goal achievement score vs prior cycle')
ax.set_title('Do people decline before they quit? Within-person change, voluntary leavers vs stayers',
             fontsize=12.5,fontweight='bold',loc='left')
ax.legend(frameon=False,loc='upper right'); ax.spines[['top','right']].set_visible(False)
ax.grid(axis='y',alpha=.25); ax.set_axisbelow(True)
fig.text(0.01,-0.03,'Each employee compared to themselves. Involuntary exits excluded. Error bars = 95% CI.\nGroups defined by exit timing only — no performance-based labelling, so not circular.',fontsize=8.2,color='#555')
fig.tight_layout(); fig.savefig('eda_charts/perf_within_person_delta.png',dpi=200,bbox_inches='tight'); plt.close()
print(r.round(2).to_string(index=False))

from scipy import stats
for a,b,lab in pairs:
    d=w[[a,b,'exit_date']].dropna(subset=[a,b]).copy(); d['delta']=d[b]-d[a]
    end=CYC_END[b]; left=d.exit_date.notna()&(d.exit_date>=end)&(d.exit_date<end+pd.DateOffset(months=6))
    t,p=stats.ttest_ind(d.delta[left],d.delta[~left],equal_var=False)
    print(f'{b}: t={t:.2f} p={p:.3f}')
