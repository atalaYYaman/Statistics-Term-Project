from __future__ import annotations

# Bölüm 1 tanımlayıcı tablosundan Türkçe yorum paragrafları üretir.

from src.analysis.statistics import AnalysisResults
from src.reporting.narratives.templates_tr import (
    cv_level,
    format_area,
    format_currency,
    format_number,
    is_missing,
    kurtosis_level,
    skewness_level,
)


def build_part1_descriptive(results: AnalysisResults, city: str) -> list[str]:
    df = results.descriptive
    if df.empty:
        return ["Descriptive statistics table is empty, so interpretation could not be generated."]

    def value(metric: str, column: str) -> float | None:
        if metric not in df.index or column not in df.columns:
            return None
        v = df.at[metric, column]
        return None if is_missing(v) else float(v)

    p_mean = value("mean", "Price")
    p_median = value("median", "Price")
    p_mode = value("mode", "Price")
    p_std = value("std", "Price")
    p_cv = value("cv", "Price")
    p_skew = value("skewness", "Price")
    p_kurt = value("kurtosis", "Price")
    p_q1 = value("q1", "Price")
    p_q3 = value("q3", "Price")
    p_max = value("max", "Price")

    a_mean = value("mean", "Area")
    a_median = value("median", "Area")
    a_mode = value("mode", "Area")
    a_std = value("std", "Area")
    a_cv = value("cv", "Area")
    a_skew = value("skewness", "Area")
    a_kurt = value("kurtosis", "Area")
    a_min = value("min", "Area")
    a_max = value("max", "Area")

    comments: list[str] = []

    central_gap = None if is_missing(p_mean) or is_missing(p_median) else abs(float(p_mean) - float(p_median))
    symmetry_text = (
        "the closeness of mean and median indicates a relatively balanced price distribution"
        if central_gap is not None and central_gap <= 0.1 * float(p_mean)
        else "the gap between mean and median indicates potential asymmetry in the price distribution"
    )
    comments.append(
        f"In {city}, the average house price is {format_currency(p_mean)} and the median is {format_currency(p_median)}; "
        f"{symmetry_text}. The mode at {format_currency(p_mode)} suggests concentration around a specific price band, "
        f"while upper-segment listings still pull the average upward. On the area side, mean={format_area(a_mean)}, "
        f"median={format_area(a_median)}, and mode={format_area(a_mode)}, indicating concentration around mid-sized properties."
    )

    comments.append(
        f"Price standard deviation is {format_currency(p_std)} and the coefficient of variation is {format_number(p_cv)}, indicating {cv_level(p_cv)} volatility. "
        f"This supports segmented pricing rather than purely random dispersion. "
        f"The area coefficient of variation is {format_number(a_cv)}, which is higher than price and indicates greater heterogeneity in listing sizes. "
        f"Area standard deviation of {format_area(a_std)} shows that typical listings can deviate materially from the mean."
    )

    comments.append(
        f"Price skewness is {format_number(p_skew)}, so the distribution is {skewness_level(p_skew)}; this may indicate that a small number of expensive listings stretch the right tail. "
        f"Price kurtosis is {format_number(p_kurt)} ({kurtosis_level(p_kurt)}), meaning peak/tail behavior differs from a normal distribution. "
        f"Area skewness is {format_number(a_skew)} ({skewness_level(a_skew)}), which reinforces the effect of large-unit listings. "
        f"Area kurtosis at {format_number(a_kurt)} suggests that outlier behavior can materially affect market interpretation."
    )

    iqr = None if is_missing(p_q1) or is_missing(p_q3) else float(p_q3) - float(p_q1)
    upper_fence = None if is_missing(iqr) or is_missing(p_q3) else float(p_q3) + 1.5 * float(iqr)
    outlier_note = (
        "the observed maximum remains below the technical upper fence, so clear outlier evidence is weak under the Tukey rule"
        if not is_missing(upper_fence) and not is_missing(p_max) and float(p_max) <= float(upper_fence)
        else "the maximum is near/above the technical upper fence, so upper-segment outlier influence should be considered"
    )
    comments.append(
        f"The first and third price quartiles are {format_currency(p_q1)} and {format_currency(p_q3)}, with an interquartile range of {format_currency(iqr)}. "
        f"This captures where the middle 50% of the market is concentrated and is critical for price-stability assessment. "
        f"With a Tukey upper fence of {format_currency(upper_fence)} and a maximum price of {format_currency(p_max)}, {outlier_note}. "
        f"Area ranges from {format_area(a_min)} to {format_area(a_max)}, confirming a broad inventory mix."
    )

    return comments
