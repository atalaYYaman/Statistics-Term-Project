from __future__ import annotations

# Raporun tüm bölümleri için merkezi istatistik hesapları burada toplanır.

from dataclasses import dataclass

import numpy as np
import pandas as pd
import scipy.stats as stats
import statsmodels.api as sm
from statsmodels.stats.multicomp import pairwise_tukeyhsd


@dataclass
class AnalysisResults:
    # Arayüz ve Excel/Word çıktıları aynı tabloları paylaşsın diye sonuçları tek yapıda tutarız.
    descriptive: pd.DataFrame
    part1_price_frequency: pd.DataFrame
    confidence_intervals: pd.DataFrame
    one_sample_tests: pd.DataFrame
    two_sample_tests: pd.DataFrame
    regression_summary: pd.DataFrame
    anova_table: pd.DataFrame
    tukey_table: pd.DataFrame


def _describe_series(series: pd.Series) -> dict[str, float]:
    # Tanımlayıcı istatistikler (ortalama, çeyrekler, çarpıklık vb.) tek seri için hesaplanır.
    s = series.dropna()
    mode_val = s.mode().iloc[0] if not s.mode().empty else np.nan
    q1, median, q3 = s.quantile([0.25, 0.5, 0.75])
    return {
        "mean": s.mean(),
        "median": median,
        "mode": mode_val,
        "range": s.max() - s.min(),
        "variance": s.var(ddof=1),
        "std": s.std(ddof=1),
        "cv": (s.std(ddof=1) / s.mean()) if s.mean() else np.nan,
        "skewness": s.skew(),
        "kurtosis": s.kurtosis(),
        "min": s.min(),
        "q1": q1,
        "q3": q3,
        "max": s.max(),
    }


def _ci_mean(series: pd.Series, confidence: float) -> dict[str, float]:
    # Ortalama için t-dağılımlı güven aralığı; marjın ve kritik t burada üretilir.
    s = series.dropna()
    n = len(s)
    mean = s.mean()
    std = s.std(ddof=1)
    t_crit = stats.t.ppf((1 + confidence) / 2, df=n - 1)
    margin = t_crit * std / np.sqrt(n)
    return {
        "n": float(n),
        "std": float(std),
        "t_crit": float(t_crit),
        "margin": float(margin),
        "mean": float(mean),
        "low": float(mean - margin),
        "high": float(mean + margin),
    }


def _price_frequency_table(series: pd.Series) -> pd.DataFrame:
    # Fiyat dağılımını sınıf aralıklarına böler; göreli ve birikimli frekansları raporlar.
    s = series.dropna().astype(float)
    if s.empty:
        return pd.DataFrame(columns=["class_interval", "midpoint", "frequency", "relative_frequency", "cumulative_frequency"])

    n = len(s)
    sturges_k = int(np.ceil(np.log2(n) + 1))
    k = max(5, sturges_k)
    min_val = float(s.min())
    max_val = float(s.max())
    if min_val == max_val:
        max_val = min_val + 1.0

    bins = np.linspace(min_val, max_val, k + 1)
    categories = pd.cut(s, bins=bins, include_lowest=True, right=True)
    freq = categories.value_counts(sort=False)
    rel = freq / n
    cum = rel.cumsum()
    midpoints = [(interval.left + interval.right) / 2 for interval in freq.index]
    labels = [f"[{interval.left:,.2f}, {interval.right:,.2f}]" for interval in freq.index]
    return pd.DataFrame(
        {
            "class_interval": labels,
            "midpoint": midpoints,
            "frequency": freq.values.astype(int),
            "relative_frequency": rel.values.astype(float),
            "cumulative_frequency": cum.values.astype(float),
        }
    )


def _welch_df(sample1: pd.Series, sample2: pd.Series) -> float:
    # İki örneklem t-testinde eşit varyans varsayımı yoksa kullanılan serbestlik derecesi (Welch–Satterthwaite).
    s1 = sample1.dropna()
    s2 = sample2.dropna()
    n1, n2 = len(s1), len(s2)
    if n1 < 2 or n2 < 2:
        return np.nan

    v1 = s1.var(ddof=1)
    v2 = s2.var(ddof=1)
    denom = ((v1 / n1) ** 2) / (n1 - 1) + ((v2 / n2) ** 2) / (n2 - 1)
    if denom == 0:
        return np.nan
    return ((v1 / n1) + (v2 / n2)) ** 2 / denom


def run_all_analyses(df: pd.DataFrame, city1: str, city2: str, city3: str) -> AnalysisResults:
    # Seçilen üç şehir için alt örneklem DataFrame'leri hazırlanır.
    c1 = df.loc[df["City"] == city1].copy()
    c2 = df.loc[df["City"] == city2].copy()
    c3 = df.loc[df["City"] == city3].copy()

    # Birinci şehir için fiyat ve alan tanımlayıcı özetleri.
    descriptive = pd.DataFrame(
        {
            "Price": _describe_series(c1["Price"]),
            "Area": _describe_series(c1["Area"]),
        }
    )
    part1_price_frequency = _price_frequency_table(c1["Price"])

    # Birinci şehirde ortalama fiyat ve alan için güven aralıkları tabloya yazılır (fiyat için %95 ve %99, alan için %95).
    price95 = _ci_mean(c1["Price"], 0.95)
    price99 = _ci_mean(c1["Price"], 0.99)
    area95 = _ci_mean(c1["Area"], 0.95)
    confidence_intervals = pd.DataFrame(
        [
            {"metric": "Price", "confidence": 0.95, **price95},
            {"metric": "Price", "confidence": 0.99, **price99},
            {"metric": "Area", "confidence": 0.95, **area95},
        ]
    )

    # Birinci şehirde tek örneklem t ve oran için z testi; kritik değerler grafiklerde kullanılsın diye saklanır.
    alpha = 0.05
    price_series = c1["Price"].dropna()
    area_series = c1["Area"].dropna()
    one_price = stats.ttest_1samp(price_series, popmean=2_000_000, alternative="two-sided")
    one_area = stats.ttest_1samp(area_series, popmean=100, alternative="greater")
    price_t_critical = stats.t.ppf(1 - alpha / 2, df=len(price_series) - 1) if len(price_series) > 1 else np.nan
    area_t_critical = stats.t.ppf(1 - alpha, df=len(area_series) - 1) if len(area_series) > 1 else np.nan
    combi = c1["HeatingType"].astype("string").str.contains("combi", case=False, na=pd.NA)
    p_hat = combi.mean()
    n = combi.notna().sum()
    z = (p_hat - 0.60) / np.sqrt((0.60 * 0.40) / n)
    p_val_prop = 2 * (1 - stats.norm.cdf(abs(z)))
    one_sample_tests = pd.DataFrame(
        [
            {
                "test": "Price vs 2,000,000",
                "test_type": "one-sample t-test",
                "tail": "two-sided",
                "alpha": alpha,
                "stat": one_price.statistic,
                "p_value": one_price.pvalue,
                "t_critic": price_t_critical,
            },
            {
                "test": "Area > 100",
                "test_type": "one-sample t-test",
                "tail": "greater",
                "alpha": alpha,
                "stat": one_area.statistic,
                "p_value": one_area.pvalue,
                "t_critic": area_t_critical,
            },
            {
                "test": "Combi proportion != 0.60",
                "test_type": "one-sample proportion z-test",
                "tail": "two-sided",
                "alpha": alpha,
                "stat": z,
                "p_value": p_val_prop,
                "t_critic": np.nan,
            },
        ]
    )

    # İlk iki şehir arasında fiyat ve alan karşılaştırması; Welch t-testi ve serbestlik derecesi.
    price_c1 = c1["Price"].dropna()
    price_c2 = c2["Price"].dropna()
    area_c1 = c1["Area"].dropna()
    area_c2 = c2["Area"].dropna()

    t_price = stats.ttest_ind(price_c1, price_c2, equal_var=False, alternative="two-sided")
    t_area = stats.ttest_ind(area_c1, area_c2, equal_var=False, alternative="two-sided")
    price_df = _welch_df(price_c1, price_c2)
    area_df = _welch_df(area_c1, area_c2)
    price_t_critical = stats.t.ppf(1 - alpha / 2, df=price_df) if not np.isnan(price_df) else np.nan
    area_t_critical = stats.t.ppf(1 - alpha / 2, df=area_df) if not np.isnan(area_df) else np.nan
    two_sample_tests = pd.DataFrame(
        [
            {
                "test": f"Price {city1} vs {city2}",
                "test_type": "two-sample t-test (Welch)",
                "tail": "two-sided",
                "alpha": alpha,
                "stat": t_price.statistic,
                "p_value": t_price.pvalue,
                "t_critic": price_t_critical,
            },
            {
                "test": f"Area {city1} vs {city2}",
                "test_type": "two-sample t-test (Welch)",
                "tail": "two-sided",
                "alpha": alpha,
                "stat": t_area.statistic,
                "p_value": t_area.pvalue,
                "t_critic": area_t_critical,
            },
        ]
    )

    # Birinci şehirde EKK regresyon (Fiyat ~ Alan); tahmin, Pearson r ve regresyon ANOVA özeti tek tabloda.
    reg_df = c1[["Price", "Area"]].dropna()
    x = sm.add_constant(reg_df["Area"])
    model = sm.OLS(reg_df["Price"], x).fit()
    pred_120 = float(model.predict([1, 120])[0])
    r, p_corr = stats.pearsonr(reg_df["Area"], reg_df["Price"])
    multiple_r = float(np.sqrt(model.rsquared))
    reg_standard_error = float(np.sqrt(model.mse_resid))
    ci_95 = model.conf_int(alpha=0.05)
    total_ss = float(model.ess + model.ssr)
    regression_summary_rows: list[dict[str, float | str]] = [
        {"section": "Regression Statistics", "metric": "multiple_r", "value": multiple_r},
        {"section": "Regression Statistics", "metric": "r_squared", "value": model.rsquared},
        {"section": "Regression Statistics", "metric": "adjusted_r_squared", "value": model.rsquared_adj},
        {"section": "Regression Statistics", "metric": "standard_error", "value": reg_standard_error},
        {"section": "Regression Statistics", "metric": "observations", "value": model.nobs},
        {"section": "Regression Statistics", "metric": "pearson_r", "value": r},
        {"section": "Regression Statistics", "metric": "pearson_p_value", "value": p_corr},
        {"section": "Regression Statistics", "metric": "predicted_price_120m2", "value": pred_120},
        {"section": "Regression ANOVA", "metric": "regression_df", "value": model.df_model},
        {"section": "Regression ANOVA", "metric": "regression_ss", "value": model.ess},
        {"section": "Regression ANOVA", "metric": "regression_ms", "value": model.mse_model},
        {"section": "Regression ANOVA", "metric": "regression_f", "value": model.fvalue},
        {"section": "Regression ANOVA", "metric": "regression_significance_f", "value": model.f_pvalue},
        {"section": "Regression ANOVA", "metric": "residual_df", "value": model.df_resid},
        {"section": "Regression ANOVA", "metric": "residual_ss", "value": model.ssr},
        {"section": "Regression ANOVA", "metric": "residual_ms", "value": model.mse_resid},
        {"section": "Regression ANOVA", "metric": "total_df", "value": model.df_model + model.df_resid},
        {"section": "Regression ANOVA", "metric": "total_ss", "value": total_ss},
    ]
    for term in model.params.index:
        regression_summary_rows.extend(
            [
                {"section": f"Coefficients ({term})", "metric": "coefficient", "value": model.params[term]},
                {"section": f"Coefficients ({term})", "metric": "std_error", "value": model.bse[term]},
                {"section": f"Coefficients ({term})", "metric": "t_stat", "value": model.tvalues[term]},
                {"section": f"Coefficients ({term})", "metric": "p_value", "value": model.pvalues[term]},
                {"section": f"Coefficients ({term})", "metric": "lower_95", "value": ci_95.loc[term, 0]},
                {"section": f"Coefficients ({term})", "metric": "upper_95", "value": ci_95.loc[term, 1]},
            ]
        )
    regression_summary = pd.DataFrame(regression_summary_rows)

    # Üç şehirde ortalama fiyat için tek yönlü ANOVA; kareler toplamı tablosu rapor için elle kurulur.
    anova_df = pd.concat([c1[["Price", "City"]], c2[["Price", "City"]], c3[["Price", "City"]]], ignore_index=True).dropna()
    grouped = list(anova_df.groupby("City"))
    groups = [g["Price"].values for _, g in grouped]
    f_stat, p_anova = stats.f_oneway(*groups)
    group_sizes = [len(g["Price"]) for _, g in grouped]
    group_means = [g["Price"].mean() for _, g in grouped]
    grand_mean = anova_df["Price"].mean()
    ss_between = float(np.sum([n_i * (mean_i - grand_mean) ** 2 for n_i, mean_i in zip(group_sizes, group_means)]))
    ss_within = float(np.sum([np.sum((grp - grp.mean()) ** 2) for grp in groups]))
    ss_total = ss_between + ss_within
    k = len(groups)
    n_total = int(sum(group_sizes))
    df_between = k - 1
    df_within = n_total - k
    df_total = n_total - 1
    ms_between = ss_between / df_between if df_between > 0 else np.nan
    ms_within = ss_within / df_within if df_within > 0 else np.nan
    anova_table = pd.DataFrame(
        [
            {
                "source": "Between groups",
                "ss": ss_between,
                "df": df_between,
                "ms": ms_between,
                "f_stat": f_stat,
                "p_value": p_anova,
            },
            {
                "source": "Within groups (Error)",
                "ss": ss_within,
                "df": df_within,
                "ms": ms_within,
                "f_stat": np.nan,
                "p_value": np.nan,
            },
            {
                "source": "Total",
                "ss": ss_total,
                "df": df_total,
                "ms": np.nan,
                "f_stat": np.nan,
                "p_value": np.nan,
            },
        ]
    )

    # Şehir çiftleri için Tukey HSD sonuç tablosu (Word/Excel ile uyumlu).
    tukey = pairwise_tukeyhsd(endog=anova_df["Price"], groups=anova_df["City"], alpha=0.05)
    tukey_table = pd.DataFrame(tukey._results_table.data[1:], columns=tukey._results_table.data[0])

    return AnalysisResults(
        descriptive=descriptive,
        part1_price_frequency=part1_price_frequency,
        confidence_intervals=confidence_intervals,
        one_sample_tests=one_sample_tests,
        two_sample_tests=two_sample_tests,
        regression_summary=regression_summary,
        anova_table=anova_table,
        tukey_table=tukey_table,
    )
