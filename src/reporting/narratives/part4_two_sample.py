from __future__ import annotations

# Bölüm 4: ilk iki şehir arası Welch iki örneklem karşılaştırmasının yorumu.

from src.analysis.statistics import AnalysisResults
from src.reporting.narratives.templates_tr import decision_text, format_number, format_p_value, is_missing, is_significant


def _direction_text(stat: float | int | None, test_name: str) -> str:
    if is_missing(stat):
        return "directional interpretation is unavailable"
    stat_float = float(stat)
    if stat_float < 0:
        return f"the negative test statistic suggests the first city may be relatively lower for {test_name}"
    if stat_float > 0:
        return f"the positive test statistic suggests the first city may be relatively higher for {test_name}"
    return "a near-zero statistic suggests highly similar groups"


def build_part4_two_sample(results: AnalysisResults) -> list[str]:
    df = results.two_sample_tests
    if df.empty:
        return ["Two-sample test table is empty, so interpretation could not be generated."]

    comments: list[str] = []
    decision_map: dict[str, bool] = {}

    for row in df.itertuples(index=False):
        test_name = str(getattr(row, "test", "Two-city comparison"))
        stat = getattr(row, "stat", None)
        p_value = getattr(row, "p_value", None)
        alpha = float(getattr(row, "alpha", 0.05))
        is_sig = is_significant(p_value, alpha)
        decision_map[test_name] = is_sig
        comments.append(
            f"For {test_name}, H0 states that the two city means are equal, and H1 states that they are different. "
            f"Welch's t-test is used because it remains reliable without assuming equal group variances. "
            f"The computed t statistic is {format_number(stat)} and the p-value is {format_p_value(p_value)}; decision: {decision_text(p_value, alpha)} "
            f"Additionally, {_direction_text(stat, test_name)}. "
            "This helps distinguish whether observed price/area differences reflect random fluctuation or structural market divergence."
        )

    price_key = next((k for k in decision_map if "Price" in k), None)
    area_key = next((k for k in decision_map if "Area" in k), None)
    if price_key and area_key:
        price_sig = decision_map[price_key]
        area_sig = decision_map[area_key]
        if (not price_sig) and area_sig:
            comments.append(
                "An insignificant price difference alongside a significant area difference suggests divergence in unit-size pricing between the two cities. "
                "In this scenario, similar total prices may coexist with different typical property sizes, implying different TL-per-m² levels. "
                "From an investment perspective, this supports monitoring unit-price metrics in addition to total listing price."
            )
        elif price_sig and (not area_sig):
            comments.append(
                "A significant price difference with an insignificant area difference suggests that pricing is driven more by quality, location, or structural attributes. "
                "Despite similar unit sizes, price separation may reflect demand pressure or supply-side premium effects. "
                "Portfolio strategy should therefore include micro-location and building quality factors, not only size."
            )
        elif price_sig and area_sig:
            comments.append(
                "When both price and area differences are significant, evidence supports structurally different market segments across cities. "
                "In this case, both property size and total value diverge, so a single-metric comparison is insufficient. "
                "City-specific parameterization is likely to produce more robust valuation and modeling outcomes."
            )
        else:
            comments.append(
                "If both price and area differences are insignificant, the two city profiles appear to move within a similar market band. "
                "This does not prove complete equality; limited sample size or high within-group variance may reduce statistical power. "
                "Still, with the current data, a strong inter-city separation is difficult to justify."
            )

    return comments
