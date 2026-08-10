"""
Statistical significance tests for the 'high performers blocked from promotion leave' hypothesis.
Cohort = ALL 13,403 employees (stayers + leavers). Leaver-only data cannot test this.
"""
import pandas as pd, numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.contingency_tables import StratifiedTable, Table2x2

BASE='/sessions/elegant-vibrant-albattani/mnt/Accenture_Datathon/'
e=pd.read_csv(BASE+'original_csv/employees.csv')
p=pd.read_csv(BASE+'original_csv/performance.csv')
a=pd.read_csv(BASE+'original_csv/attrition_log.csv')

# ---- build person-level frame ----
p['review_date']=pd.to_datetime(p['review_date'])
p=p.sort_values(['employee_id','review_date'])
last=p.groupby('employee_id').tail(1).set_index('employee_id')
# ever recommended for promotion across observed cycles
ever_rec=p.groupby('employee_id')['promotion_recommendation'].max()

df=e.set_index('employee_id').join(last[['performance_rating','promotion_recommendation','goal_achievement_score']])
df['ever_promo_rec']=ever_rec
df=df.join(a.set_index('employee_id')[['exit_type','regrettable_flag','stated_exit_reason']])

df['top_performer']=df['performance_rating'].isin(['Outstanding','High Performer'])
df['voluntary_exit']=(df['exit_type']=='voluntary').fillna(False)
df['regrettable']=(df['regrettable_flag']==True).fillna(False)
df=df[df['performance_rating'].notna()]
print(f"Analysis cohort: {len(df)} employees with >=1 performance review")
print(f"  voluntary exits: {df.voluntary_exit.sum()}   regrettable: {df.regrettable.sum()}\n")

def chi2_report(tab, label):
    tab=tab.astype(int)
    chi2,pv,dof,exp=stats.chi2_contingency(tab, correction=False)
    n=tab.values.sum()
    v=np.sqrt(chi2/(n*(min(tab.shape)-1)))
    print(f"--- {label} ---")
    print(tab)
    print(f"row %: \n{(tab.div(tab.sum(1),axis=0)*100).round(2)}")
    print(f"chi2={chi2:.2f}  dof={dof}  p={pv:.3e}  n={n}  Cramers V={v:.3f}  min expected={exp.min():.1f}")
    if tab.shape==(2,2):
        t=Table2x2(tab.values)
        print(f"odds ratio={t.oddsratio:.3f}  95% CI {np.round(t.oddsratio_confint(),3)}")
        print(f"risk ratio={t.riskratio:.3f}  95% CI {np.round(t.riskratio_confint(),3)}")
        print(f"Fisher exact p={stats.fisher_exact(tab.values)[1]:.3e}")
    print()

print("="*70); print("TEST 1 — Does performance predict voluntary exit at all?"); print("="*70)
t1=pd.crosstab(df['performance_rating'],df['voluntary_exit'])
t1=t1.reindex(['Unsatisfactory','Below Expectations','Meets Expectations','High Performer','Outstanding'])
chi2_report(t1,"performance_rating x voluntary_exit (5x2)")

print("="*70); print("TEST 2 — Blocked promotion x voluntary exit, WITHIN top performers"); print("="*70)
top=df[df['top_performer']]
t2=pd.crosstab(top['ever_promo_rec'],top['voluntary_exit'])
chi2_report(t2,"ever recommended for promotion x voluntary exit | top performers only")

low=df[~df['top_performer']]
t2b=pd.crosstab(low['ever_promo_rec'],low['voluntary_exit'])
chi2_report(t2b,"same test | NON-top performers (placebo / contrast group)")

print("="*70); print("TEST 2c — promotion_eligible (HR field) within top performers"); print("="*70)
t2c=pd.crosstab(top['promotion_eligible'],top['voluntary_exit'])
chi2_report(t2c,"promotion_eligible x voluntary exit | top performers")

print("="*70); print("TEST 3 — 4-way interaction cell test"); print("="*70)
df['cell']=np.where(df['top_performer'],'Top ','Other ')+np.where(df['ever_promo_rec']==True,'+promo','-promo')
t3=pd.crosstab(df['cell'],df['voluntary_exit'])
chi2_report(t3,"performance x promotion cell x voluntary exit (4x2)")

print("="*70); print("TEST 4 — Cochran-Mantel-Haenszel, stratified by department"); print("="*70)
strata=[]
for d,g in top.groupby('department'):
    tt=pd.crosstab(g['ever_promo_rec'],g['voluntary_exit'])
    if tt.shape==(2,2) and tt.values.min()>=0 and tt.values.sum()>20:
        strata.append(tt.values)
st=StratifiedTable(np.dstack(strata))
print(f"strata used: {len(strata)} departments")
print(f"CMH pooled odds ratio = {st.oddsratio_pooled:.3f}  95% CI {np.round(st.oddsratio_pooled_confint(),3)}")
r=st.test_null_odds(); print(f"CMH test of no association: stat={r.statistic:.2f}  p={r.pvalue:.3e}")
r2=st.test_equal_odds(); print(f"Breslow-Day homogeneity of OR: stat={r2.statistic:.2f}  p={r2.pvalue:.3f}  (p>0.05 => OR consistent across depts)\n")

print("="*70); print("TEST 5 — Logistic regression with interaction (controls for confounds)"); print("="*70)
m=df[['voluntary_exit','top_performer','ever_promo_rec','tenure_months','salary','compa_ratio','role_level','department','age_band']].dropna().copy()
m['top']=m['top_performer'].astype(int); m['promo']=m['ever_promo_rec'].astype(int)
m['blocked']=((m['top']==1)&(m['promo']==0)).astype(int)
X=pd.get_dummies(m[['top','promo','tenure_months','compa_ratio','role_level','department','age_band']],
                 columns=['role_level','department','age_band'],drop_first=True,dtype=float)
X['top_x_noPromo']=m['blocked']
X['tenure_months']=X['tenure_months']/12
X=sm.add_constant(X)
res=sm.Logit(m['voluntary_exit'].astype(int),X).fit(disp=0)
out=pd.DataFrame({'coef':res.params,'p':res.pvalues,'OR':np.exp(res.params),
                  'OR_lo':np.exp(res.conf_int()[0]),'OR_hi':np.exp(res.conf_int()[1])})
print(out.loc[[i for i in out.index if not i.startswith(('department_','age_band_','role_level_'))]].round(4))
print(f"\nPseudo R2={res.prsquared:.4f}  n={int(res.nobs)}  LLR p={res.llr_pvalue:.3e}")
print("(department, age_band, role_level fixed effects included but suppressed)")
