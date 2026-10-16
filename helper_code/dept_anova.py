import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import itertools

pd.set_option('display.width', 140)

df = pd.read_csv('/mnt/user-data/uploads/Accenture_Datathon/eddited_csv/wave_risk_set.csv')

# DV: regret_180 = regrettable voluntary exit within 180 days of this survey wave
# This is the exposure-bias-corrected outcome (person-wave risk set, per project memory)
# Group: department

d = df[['department', 'regret_180']].dropna()
print("N rows:", len(d))
print("\nDepartment sizes and regrettable-exit rate:")
summary = d.groupby('department')['regret_180'].agg(['count', 'mean', 'std']).sort_values('mean', ascending=False)
summary.columns = ['n_waves', 'regret_rate', 'std']
print(summary)

groups = [g['regret_180'].values for _, g in d.groupby('department')]
labels = [name for name, _ in d.groupby('department')]

# Assumption checks
levene_stat, levene_p = stats.levene(*groups)
print(f"\nLevene's test for homogeneity of variance: stat={levene_stat:.3f}, p={levene_p:.4g}")

# One-way ANOVA
f_stat, p_anova = stats.f_oneway(*groups)
print(f"\nOne-way ANOVA: F={f_stat:.4f}, p={p_anova:.6g}, df_between={len(groups)-1}, df_within={len(d)-len(groups)}")

# Effect size: eta squared
grand_mean = d['regret_180'].mean()
ss_between = sum(len(g) * (g.mean() - grand_mean)**2 for g in groups)
ss_total = sum((d['regret_180'] - grand_mean)**2)
eta_sq = ss_between / ss_total
print(f"Eta-squared (effect size): {eta_sq:.4f}")

summary.to_csv('/home/claude/work/dept_anova_summary.csv')


print("\n" + "="*70)
print("POST-HOC: Tukey HSD (controls family-wise error rate at alpha=0.05)")
print("="*70)
tukey = pairwise_tukeyhsd(endog=d['regret_180'], groups=d['department'], alpha=0.05)
print(tukey)
tukey_df = pd.DataFrame(data=tukey._results_table.data[1:], columns=tukey._results_table.data[0])
tukey_df.to_csv('/home/claude/work/dept_tukey_posthoc.csv', index=False)

print("\n" + "="*70)
print("ROBUSTNESS CHECK 1: Games-Howell post-hoc (does not assume equal variances")
print("-- more appropriate here since Levene's test flagged unequal variances)")
print("="*70)
import pingouin as pg
gh = pg.pairwise_gameshowell(data=d, dv='regret_180', between='department')
print(gh[['A','B','mean_A','mean_B','diff','se','T','df','pval']].to_string(index=False))
gh.to_csv('/home/claude/work/dept_gameshowell_posthoc.csv', index=False)

print("\n" + "="*70)
print("ROBUSTNESS CHECK 2: Chi-square omnibus test on department x regret_180 (binary DV,")
print("more natural than ANOVA for a 0/1 outcome) + pairwise proportion z-tests, Holm-Bonferroni corrected")
print("="*70)
ct = pd.crosstab(d['department'], d['regret_180'])
chi2, chi2_p, dof, exp = stats.chi2_contingency(ct)
print(f"Chi-square: stat={chi2:.4f}, df={dof}, p={chi2_p:.6g}")

from statsmodels.stats.proportion import proportions_ztest
from statsmodels.stats.multitest import multipletests

pairs = list(itertools.combinations(labels, 2))
rows = []
for a, b in pairs:
    na = d.loc[d.department==a, 'regret_180']
    nb = d.loc[d.department==b, 'regret_180']
    count = np.array([na.sum(), nb.sum()])
    nobs = np.array([len(na), len(nb)])
    stat, p = proportions_ztest(count, nobs)
    rows.append({'dept_A': a, 'dept_B': b, 'rate_A': na.mean(), 'rate_B': nb.mean(), 'z_stat': stat, 'p_raw': p})

pp = pd.DataFrame(rows)
reject, p_holm, _, _ = multipletests(pp['p_raw'], alpha=0.05, method='holm')
pp['p_holm'] = p_holm
pp['sig_holm_0.05'] = reject
pp = pp.sort_values('p_holm')
print(pp.to_string(index=False))
pp.to_csv('/home/claude/work/dept_pairwise_proportions_holm.csv', index=False)
