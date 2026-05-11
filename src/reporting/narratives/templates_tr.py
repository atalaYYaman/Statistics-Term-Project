from __future__ import annotations

# Rapor metinlerinde ortak biçimlendirme, hipotez ifadeleri ve yardımcı fonksiyonlar.

from typing import Final

import pandas as pd

ALPHA_DEFAULT: Final[float] = 0.05
BORDERLINE_DELTA: Final[float] = 0.02

ONE_SAMPLE_HYPOTHESES: Final[dict[str, tuple[str, str]]] = {
    "Price vs 2,000,000": (
        "H0: The city mean house price equals 2,000,000 TL.",
        "H1: The city mean house price differs from 2,000,000 TL.",
    ),
    "Area > 100": (
        "H0: The city mean house area is 100 m² or lower.",
        "H1: The city mean house area is greater than 100 m².",
    ),
    "Combi proportion != 0.60": (
        "H0: The population proportion of combi heating equals 0.60.",
        "H1: The population proportion of combi heating differs from 0.60.",
    ),
}

METRIC_LABELS: Final[dict[str, str]] = {
    "mean": "mean",
    "median": "median",
    "mode": "mode",
    "range": "range",
    "variance": "variance",
    "std": "standard deviation",
    "cv": "coefficient of variation",
    "skewness": "skewness",
    "kurtosis": "kurtosis",
    "min": "minimum",
    "q1": "1st quartile",
    "q3": "3rd quartile",
    "max": "maximum",
}


def is_missing(value: float | int | str | None) -> bool:
    return value is None or pd.isna(value)


def format_number(value: float | int | None, digits: int = 4) -> str:
    if is_missing(value):
        return "not available"
    return f"{float(value):,.{digits}f}"


def format_currency(value: float | int | None, digits: int = 2) -> str:
    if is_missing(value):
        return "not available"
    return f"{float(value):,.{digits}f} TL"


def format_area(value: float | int | None, digits: int = 2) -> str:
    if is_missing(value):
        return "not available"
    return f"{float(value):,.{digits}f} m²"


def format_p_value(value: float | int | None) -> str:
    if is_missing(value):
        return "not available"
    p_value = float(value)
    if p_value < 0.0001:
        return "< 0.0001"
    return f"{p_value:.4f}"


def decision_text(p_value: float | int | None, alpha: float = ALPHA_DEFAULT) -> str:
    if is_missing(p_value):
        return "A decision could not be produced due to insufficient sample/distribution information."
    if float(p_value) < alpha:
        return f"Since p-value {format_p_value(p_value)} < {alpha:.2f}, H0 is rejected."
    return f"Since p-value {format_p_value(p_value)} >= {alpha:.2f}, H0 cannot be rejected."


def is_significant(p_value: float | int | None, alpha: float = ALPHA_DEFAULT) -> bool:
    return not is_missing(p_value) and float(p_value) < alpha


def is_borderline(p_value: float | int | None, alpha: float = ALPHA_DEFAULT) -> bool:
    if is_missing(p_value):
        return False
    p_float = float(p_value)
    return alpha <= p_float <= (alpha + BORDERLINE_DELTA)


def cv_level(cv_value: float | int | None) -> str:
    if is_missing(cv_value):
        return "uncertain"
    cv_float = float(cv_value)
    if cv_float < 0.2:
        return "low"
    if cv_float < 0.5:
        return "moderate"
    return "high"


def skewness_level(skew_value: float | int | None) -> str:
    if is_missing(skew_value):
        return "uncertain"
    skew_float = float(skew_value)
    abs_skew = abs(skew_float)
    if abs_skew < 0.5:
        strength = "mild"
    elif abs_skew < 1.0:
        strength = "moderate"
    else:
        strength = "strong"
    direction = "right-skewed" if skew_float > 0 else "left-skewed"
    if abs_skew < 0.1:
        direction = "approximately symmetric"
    return f"{strength} {direction}"


def kurtosis_level(kurtosis_value: float | int | None) -> str:
    if is_missing(kurtosis_value):
        return "uncertain"
    kurt_float = float(kurtosis_value)
    if kurt_float < -0.5:
        return "platykurtic"
    if kurt_float > 0.5:
        return "leptokurtic"
    return "mesokurtic"


def correlation_strength(corr_value: float | int | None) -> str:
    if is_missing(corr_value):
        return "uncertain"
    abs_corr = abs(float(corr_value))
    if abs_corr < 0.2:
        return "very weak"
    if abs_corr < 0.4:
        return "weak-to-moderate"
    if abs_corr < 0.6:
        return "moderate"
    if abs_corr < 0.8:
        return "strong"
    return "very strong"
