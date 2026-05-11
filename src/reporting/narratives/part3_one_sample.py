from __future__ import annotations

# Bölüm 3 tek örneklem testleri için hipotez ve karar cümleleri.

from src.analysis.statistics import AnalysisResults
from src.reporting.narratives.templates_tr import (
    ONE_SAMPLE_HYPOTHESES,
    decision_text,
    format_number,
    format_p_value,
    is_borderline,
    is_missing,
)


def _stat_strength(stat: float | int | None) -> str:
    if is_missing(stat):
        return "effect size category could not be determined because the statistic is unavailable"
    abs_stat = abs(float(stat))
    if abs_stat < 1:
        return "a weak deviation"
    if abs_stat < 2:
        return "a limited deviation"
    if abs_stat < 4:
        return "a clear deviation"
    return "a very strong deviation"


def build_part3_one_sample(results: AnalysisResults) -> list[str]:
    df = results.one_sample_tests
    if df.empty:
        return ["One-sample test table is empty, so interpretation could not be generated."]

    comments: list[str] = []
    for row in df.itertuples(index=False):
        test_name = str(getattr(row, "test", ""))
        stat = getattr(row, "stat", None)
        p_value = getattr(row, "p_value", None)
        alpha = float(getattr(row, "alpha", 0.05))

        h0, h1 = ONE_SAMPLE_HYPOTHESES.get(
            test_name,
            ("H0: The tested parameter matches the reference value.", "H1: The tested parameter differs from the reference value."),
        )
        borderline_note = (
            "The p-value is near the significance threshold, so a larger sample could change the conclusion. "
            if is_borderline(p_value, alpha)
            else ""
        )
        comments.append(
            f"Hypothesis setup for {test_name}: {h0} {h1} The computed test statistic is {format_number(stat)}, which indicates {_stat_strength(stat)} from the reference assumption. "
            f"The p-value is {format_p_value(p_value)}, and the decision is: {decision_text(p_value, alpha)} {borderline_note}"
            "This statistical result should not be read in isolation; in real-estate markets it must be interpreted together with cost, location, and inventory composition. "
            "Therefore, policy or investment decisions should be finalized only after combining test outcomes with market conditions."
        )
    return comments
