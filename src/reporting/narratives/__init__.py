from __future__ import annotations

# Word raporu için Bölüm 1–6 metinleri ve genel özet burada birleştirilir.

from dataclasses import dataclass

import pandas as pd

from src.analysis.statistics import AnalysisResults
from src.reporting.narratives.part1_descriptive import build_part1_descriptive
from src.reporting.narratives.part2_confidence import build_part2_confidence_intervals
from src.reporting.narratives.part3_one_sample import build_part3_one_sample
from src.reporting.narratives.part4_two_sample import build_part4_two_sample
from src.reporting.narratives.part5_regression import build_part5_regression
from src.reporting.narratives.part6_anova import build_part6_anova
from src.reporting.narratives.templates_tr import correlation_strength, format_number, format_p_value, is_significant


@dataclass
class ReportNarratives:
    part1_descriptive: list[str]
    part2_ci: list[str]
    part3_one_sample: list[str]
    part4_two_sample: list[str]
    part5_regression: list[str]
    part6_anova: list[str]
    part6_tukey: list[str]
    general_summary: list[str]


def _p_value_for_test(df: pd.DataFrame, test_name: str) -> float | None:
    rows = df[df["test"] == test_name]
    if rows.empty:
        return None
    return float(rows.iloc[0]["p_value"])


def _metric_value(df: pd.DataFrame, section: str, metric: str) -> float | None:
    rows = df[(df["section"] == section) & (df["metric"] == metric)]
    if rows.empty:
        return None
    return float(rows.iloc[0]["value"])


def _anova_p_value(df: pd.DataFrame) -> float | None:
    rows = df[df["source"] == "Between groups"]
    if rows.empty:
        return None
    return float(rows.iloc[0]["p_value"])


def build_general_summary(results: AnalysisResults, cities: tuple[str, str, str]) -> list[str]:
    # Tüm bölümlerden p-değerleri ve regresyon özetleriyle genel sonuç paragrafları üretir.
    city1, city2, city3 = cities
    one_sample = results.one_sample_tests
    two_sample = results.two_sample_tests
    regression = results.regression_summary
    anova = results.anova_table

    price_ref_p = _p_value_for_test(one_sample, "Price vs 2,000,000")
    price_vs_ref = (
        f"The average price in {city1} is statistically above the 2,000,000 TL reference."
        if is_significant(price_ref_p)
        else f"The difference between {city1} average price and the 2,000,000 TL reference is not strongly supported by current data."
    )

    p_price_2sample = _p_value_for_test(two_sample, f"Price {city1} vs {city2}")
    p_area_2sample = _p_value_for_test(two_sample, f"Area {city1} vs {city2}")
    if (not is_significant(p_price_2sample)) and is_significant(p_area_2sample):
        city_compare = (
            f"Between {city1} and {city2}, price difference is not significant while area difference is significant, indicating divergence in unit-size pricing."
        )
    elif is_significant(p_price_2sample) and is_significant(p_area_2sample):
        city_compare = f"{city1} and {city2} differ significantly in both price and area."
    elif is_significant(p_price_2sample):
        city_compare = f"{city1} and {city2} show a significant price gap, while area difference remains limited."
    else:
        city_compare = f"No clear difference is observed between {city1} and {city2} in either price or area."

    r_squared = _metric_value(regression, "Regression Statistics", "r_squared")
    pearson_r = _metric_value(regression, "Regression Statistics", "pearson_r")
    corr_summary = (
        f"The area-price relation is r={format_number(pearson_r)} ({correlation_strength(pearson_r)}), and model explanatory power is limited at R-squared={format_number(r_squared)}."
    )

    anova_p = _anova_p_value(anova)
    anova_summary = (
        f"There is a statistically significant mean-price difference across {city1}, {city2}, and {city3}."
        if is_significant(anova_p)
        else f"No statistically significant mean-price difference is detected across {city1}, {city2}, and {city3} (p={format_p_value(anova_p)})."
    )

    return [
        f"In this study, housing markets in {city1}, {city2}, and {city3} were evaluated using multiple statistical methods. {price_vs_ref} This emphasizes the need to benchmark market reality against reference price thresholds on a regular basis.",
        f"In pairwise city comparisons, {city_compare} This indicates that investment decisions should track unit-size composition as well as total listing price.",
        f"In regression analysis, {corr_summary} Therefore, uncertainty will remain high unless additional features such as location, building age, floor level, accessibility, and heating type are included.",
        f"According to ANOVA and multiple-comparison findings, {anova_summary} For stronger inference, expanding sample size and analyzing submarket segments separately is recommended.",
    ]


def build_report_narratives(results: AnalysisResults, cities: tuple[str, str, str]) -> ReportNarratives:
    # Word raporu için tüm bölüm metinlerini tek yerden toplar; şehir sırası (1., 2., 3.) sabittir.
    part6_anova, part6_tukey = build_part6_anova(results)
    return ReportNarratives(
        part1_descriptive=build_part1_descriptive(results, cities[0]),
        part2_ci=build_part2_confidence_intervals(results, cities[0]),
        part3_one_sample=build_part3_one_sample(results),
        part4_two_sample=build_part4_two_sample(results),
        part5_regression=build_part5_regression(results, cities[0]),
        part6_anova=part6_anova,
        part6_tukey=part6_tukey,
        general_summary=build_general_summary(results, cities),
    )
