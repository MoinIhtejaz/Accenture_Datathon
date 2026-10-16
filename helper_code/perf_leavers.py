import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

D='original_csv/'
perf=pd.read_csv(D+'performance.csv',parse_dates=['review_date'])
att=pd.read_csv(D+'attrition_log.csv',parse_dates=['exit_date'])

reg=set(att.loc[att.regrettable_flag==True,'employee_id'])
allexit=set(att.employee_id)

perf=perf[perf.review_cycle.isin(['2024-H1','2024-H2','2025-H1'])].copy()
perf['grp']=np.where(perf.employee_id.isin(reg),'Regrettable leavers',
             np.where(perf.employee_id.isin(allexit),'DROP','Stayers'))
perf=perf[perf.grp!='DROP']

# only count reviews BEFORE the person's exit date
ex=att.set_index('employee_id').exit_date
perf['exit_date']=perf.employee_id.map(ex)
perf=perf[perf.exit_date.isna()|(perf.review_date<perf.exit_date)]

cycles=['2024-H1','2024-H2','2025-H1']
groups=['Stayers','Regrettable leavers']
COL={'Stayers':'#4C78A8','Regrettable leavers':'#E45756'}

# ---- Chart 1: mean goal achievement score ----
g=perf.groupby(['review_cycle','grp']).goal_achievement_score.agg(['mean','sem','count'])
fig,ax=plt.subplots(figsize=(9,5.5))
w=0.36; x=np.arange(len(cycles))
for i,gr in enumerate(groups):
    m=[g.loc[(c,gr),'mean'] if (c,gr) in g.index else np.nan for c in cycles]
    e=[1.96*g.loc[(c,gr),'sem'] if (c,gr) in g.index else np.nan for c in cycles]
    n=[int(g.loc[(c,gr),'count']) if (c,gr) in g.index else 0 for c in cycles]
    b=ax.bar(x+(i-0.5)*w,m,w,yerr=e,capsize=4,label=f'{gr}',color=COL[gr],edgecolor='white')
    for rect,v,nn in zip(b,m,n):
        ax.text(rect.get_x()+rect.get_width()/2,v+1.2,f'{v:.1f}\nn={nn:,}',ha='center',va='bottom',fontsize=8.5)
ax.set_xticks(x); ax.set_xticklabels(cycles,fontsize=11)
ax.set_ylabel('Mean goal achievement score'); ax.set_ylim(0,95)
ax.set_title('Goal achievement by review cycle: regrettable leavers vs stayers',fontsize=13,fontweight='bold',loc='left')
ax.legend(frameon=False); ax.spines[['top','right']].set_visible(False)
ax.grid(axis='y',alpha=.25); ax.set_axisbelow(True)
fig.text(0.01,-0.02,'Reviews prior to exit date only. Error bars = 95% CI. 2025-H2 cycle absent from source data.',fontsize=8,color='#555')
fig.tight_layout(); fig.savefig('eda_charts/perf_goal_by_cycle.png',dpi=200,bbox_inches='tight'); plt.close()

# ---- Chart 2: % top-rated ----
perf['top']=perf.performance_rating.isin(['High Performer','Outstanding'])
perf['low']=perf.performance_rating.isin(['Below Expectations','Unsatisfactory'])
t=perf.groupby(['review_cycle','grp']).agg(top=('top','mean'),low=('low','mean'),n=('top','size'))

fig,axes=plt.subplots(1,2,figsize=(13,5.2),sharex=True)
for ax,(key,title) in zip(axes,[('top','% rated High Performer or Outstanding'),('low','% rated Below Expectations or Unsatisfactory')]):
    for i,gr in enumerate(groups):
        v=[t.loc[(c,gr),key]*100 if (c,gr) in t.index else np.nan for c in cycles]
        b=ax.bar(x+(i-0.5)*w,v,w,label=gr,color=COL[gr],edgecolor='white')
        for rect,val in zip(b,v):
            ax.text(rect.get_x()+rect.get_width()/2,val+0.5,f'{val:.1f}%',ha='center',fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels(cycles)
    ax.set_title(title,fontsize=11.5,fontweight='bold',loc='left')
    ax.spines[['top','right']].set_visible(False); ax.grid(axis='y',alpha=.25); ax.set_axisbelow(True)
axes[0].set_ylabel('% of reviews'); axes[0].legend(frameon=False)
fig.suptitle('Rating mix by review cycle: regrettable leavers vs stayers',fontsize=13.5,fontweight='bold',x=0.008,ha='left')
fig.tight_layout(); fig.savefig('eda_charts/perf_rating_mix_by_cycle.png',dpi=200,bbox_inches='tight'); plt.close()

print(g.round(2).to_string()); print()
print((t.assign(top=(t.top*100).round(1),low=(t.low*100).round(1))).to_string())
