from __future__ import annotations

# Bölüm 5 regresyon özetinden model uyumu ve 120 m² tahmin cümleleri.

import pandas as pd

from src.analysis.statistics import AnalysisResults
from src.reporting.narratives.templates_tr import (
    decision_text,
    correlation_strength,
    format_currency,
    format_number,
    format_p_value,
    is_borderline,
    is_missing,
)


def _metric_value(df: pd.DataFrame, section: str, metric: str) -> float | None:
    rows = df[(df["section"] == section) & (df["metric"] == metric)]
    if rows.empty:
        return None
    value = rows.iloc[0]["value"]
    return None if is_missing(value) else float(value)


def build_part5_regression(results: AnalysisResults, city: str) -> list[str]:
    df = results.regression_summary
    if df.empty:
        return ["Regression summary table is empty, so interpretation could not be generated."]

    comments: list[str] = []
    r_squared = _metric_value(df, "Regression Statistics", "r_squared")
    adj_r_squared = _metric_value(df, "Regression Statistics", "adjusted_r_squared")
    observations = _metric_value(df, "Regression Statistics", "observations")
    pearson_r = _metric_value(df, "Regression Statistics", "pearson_r")
    pearson_p = _metric_value(df, "Regression Statistics", "pearson_p_value")
    pred_120 = _metric_value(df, "Regression Statistics", "predicted_price_120m2")
    model_f = _metric_value(df, "Regression ANOVA", "regression_f")
    model_p = _metric_value(df, "Regression ANOVA", "regression_significance_f")
    area_coef = _metric_value(df, "Coefficients (Area)", "coefficient")
    area_coef_p = _metric_value(df, "Coefficients (Area)", "p_value")
    area_low = _metric_value(df, "Coefficients (Area)", "lower_95")
    area_high = _metric_value(df, "Coefficients (Area)", "upper_95")
    intercept = _metric_value(df, "Coefficients (const)", "coefficient")

    border_note = (
        "The p-value is close to the 0.05 threshold, suggesting significance could emerge with a larger sample."
        if is_borderline(pearson_p)
        else "The current p-value position supports a clearer classification of relationship strength."
    )
    comments.append(
        f"The Pearson correlation between Area and Price is r={format_number(pearson_r)} (p={format_p_value(pearson_p)}), indicating a {correlation_strength(pearson_r)} relationship. "
        f"Decision note: {decision_text(pearson_p)} {border_note} "
        "In real-estate terms, this suggests that area alone has limited explanatory power for price formation."
    )
    comments.append(
        f"The model-wide F statistic is {format_number(model_f)} and model p-value is {format_p_value(model_p)}. "
        f"At model level: {decision_text(model_p)} "
        "If the overall model is not significant, a meaningful share of price variance is likely explained by external variables such as location, building age, floor level, and accessibility."
    )
    comments.append(
        f"R-squared is {format_number(r_squared)} and adjusted R-squared is {format_number(adj_r_squared)} based on {format_number(observations, 0)} observations. "
        "These are core model-quality indicators showing how much price variation is captured by area. "
        "When R-squared remains low, predictive power is limited and a single-variable setup cannot capture complex market pricing behavior. "
        "A stronger model should include additional variables such as room count, location tier, and building quality."
    )
    includes_zero = (not is_missing(area_low)) and (not is_missing(area_high)) and (float(area_low) <= 0 <= float(area_high))
    coeff_note = (
        "Because the confidence interval includes zero, there is no strong statistical evidence that the area coefficient differs from zero."
        if includes_zero
        else "Because the confidence interval excludes zero, the direction of the area coefficient is statistically more stable."
    )
    comments.append(
        f"The Area coefficient is {format_number(area_coef)} TL/m² (p={format_p_value(area_coef_p)}) with a 95% confidence interval of [{format_number(area_low)}, {format_number(area_high)}]. "
        f"{coeff_note} The intercept is {format_currency(intercept)}; while a 0 m² interpretation is not practical, it defines the model baseline. "
        "Therefore, coefficient interpretation should focus on marginal effect rather than absolute baseline pricing."
    )
    comments.append(
        f"The expected price for a 120 m² property is {format_currency(pred_120)} under this model. "
        "As a point estimate, it includes uncertainty, and prediction error bands may widen when explanatory power is limited. "
        "Combined with interval evidence, this estimate is useful for directional planning but should not be treated as a definitive standalone reference."
    )
    return comments
