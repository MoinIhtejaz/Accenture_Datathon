import pandas as pd, numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.contingency_tables import Table2x2
BASE='/sessions/elegant-vibrant-albattani/mnt/Accenture_Datathon/'
e=pd.read_csv(BASE+'original_csv/employees.csv'); p=pd.read_csv(BASE+'original_csv/performance.csv'); a=pd.read_csv(BASE+'original_csv/attrition_log.csv')
p['review_date']=pd.to_datetime(p['review_date']); p=p.sort_values(['employee_id','review_date'])
last=p.groupby('employee_id').tail(1).set_index('employee_id')
df=e.set_index('employee_id').join(last[['performance_rating']]).join(a.set_index('employee_id').drop(columns=['exit_date']))
df['ever_promo_rec']=p.groupby('employee_id')['promotion_recommendation'].max()
df['top']=df['performance_rating'].isin(['Outstanding','High Performer'])
df['vol']=(df['exit_type']=='voluntary').fillna(False)

print("="*70);print("A. CIRCULARITY CHECK — is regrettable_flag just a relabel of hipo/perf?");print("="*70)
lv=df[df['exit_type'].notna()]
for col in ['hipo_flag','performance_band_at_exit','promotion_eligible']:
    t=pd.crosstab(lv[col],lv['regrettable_flag'])
    c,pv,d,ex=stats.chi2_contingency(t,correction=False)
    v=np.sqrt(c/(t.values.sum()*(min(t.shape)-1)))
    print(f"\n{col} x regrettable_flag  (leavers, n={t.values.sum()})")
    print(t); print(f"  chi2={c:.1f} p={pv:.2e} Cramers V={v:.3f}")

print("\n"+"="*70);print("B. BASE-RATE COMPARISON the dashboard is missing");print("="*70)
for col,lab in [('hipo_flag','HiPo'),('promotion_eligible','Promotion-eligible')]:
    reg=df[df['regrettable_flag']==True][col].mean()
    volx=df[df['vol']][col].mean(); stay=df[df['status']=='active'][col].mean()
    print(f"{lab}:  regrettable leavers {reg:.1%} | all voluntary leavers {volx:.1%} | active staff {stay:.1%}")
    t=pd.crosstab(df[col],df['vol'])
    c,pv,d,ex=stats.chi2_contingency(t,correction=False)
    tt=Table2x2(t.values.astype(int))
    print(f"   {col} x voluntary exit: chi2={c:.2f} p={pv:.3f} OR={tt.oddsratio:.3f} CI{np.round(tt.oddsratio_confint(),3)}")

print("\n"+"="*70);print("C. Does 'blocked promotion' predict REGRETTABLE exit, within top performers?");print("="*70)
top=df[df['top']].copy(); top['reg']=(top['regrettable_flag']==True).fillna(False)
t=pd.crosstab(top['ever_promo_rec'],top['reg']).astype(int)
c,pv,d,ex=stats.chi2_contingency(t,correction=False); tt=Table2x2(t.values)
print(t); print((t.div(t.sum(1),axis=0)*100).round(2))
print(f"chi2={c:.2f} p={pv:.3e} OR={tt.oddsratio:.3f} CI{np.round(tt.oddsratio_confint(),3)} Fisher p={stats.fisher_exact(t.values)[1]:.3e} min exp={ex.min():.1f}")

print("\n"+"="*70);print("D. LOGIT REFIT (converged solver), formal interaction test");print("="*70)
m=df[['vol','top','ever_promo_rec','tenure_months','compa_ratio','role_level','department','age_band']].dropna().copy()
m['top']=m['top'].astype(int); m['promo']=m['ever_promo_rec'].astype(int)
m['inter']=m['top']*(1-m['promo']); m['tenure_yrs']=m['tenure_months']/12
X=pd.get_dummies(m[['top','promo','tenure_yrs','compa_ratio','role_level','department','age_band']],
                 columns=['role_level','department','age_band'],drop_first=True,dtype=float)
Xf=sm.add_constant(X.copy()); Xf['top_x_noPromo']=m['inter']
red=sm.Logit(m['vol'].astype(int),sm.add_constant(X)).fit(method='newton',maxiter=200,disp=0)
full=sm.Logit(m['vol'].astype(int),Xf).fit(method='newton',maxiter=200,disp=0)
print("converged:",red.mle_retvals['converged'],full.mle_retvals['converged'])
o=pd.DataFrame({'coef':full.params,'p':full.pvalues,'OR':np.exp(full.params),
 'lo':np.exp(full.conf_int()[0]),'hi':np.exp(full.conf_int()[1])})
print(o.loc[['top','promo','top_x_noPromo','tenure_yrs','compa_ratio']].round(4))
lr=2*(full.llf-red.llf); print(f"\nLikelihood-ratio test for interaction: LR={lr:.3f} df=1 p={stats.chi2.sf(lr,1):.4f}")
print(f"full pseudo-R2={full.prsquared:.4f}")

print("\n"+"="*70);print("E. Power check — smallest effect detectable at n=5347, 80% power");print("="*70)
from statsmodels.stats.power import GofChisquarePower
from statsmodels.stats.proportion import proportion_effectsize, samplesize_proportions_2indsample_onetail
base=0.063
for n in [5347,153]:
    w=GofChisquarePower().solve_power(effect_size=None,nobs=n,alpha=0.05,power=0.8,n_bins=2)
    print(f"n={n}: min detectable Cohen's w = {w:.4f}")
