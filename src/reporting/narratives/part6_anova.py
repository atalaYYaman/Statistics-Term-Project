from __future__ import annotations

# Bölüm 6: tek yönlü ANOVA ve Tukey sonrası çift karşılaştırma metinleri.

import pandas as pd

from src.analysis.statistics import AnalysisResults
from src.reporting.narratives.templates_tr import (
    decision_text,
    format_currency,
    format_number,
    format_p_value,
    is_significant,
    is_missing,
)


def _between_row(df: pd.DataFrame) -> pd.Series | None:
    rows = df[df["source"] == "Between groups"]
    if rows.empty:
        return None
    return rows.iloc[0]


def _format_direction(diff: float, group1: str, group2: str) -> str:
    if diff > 0:
        return f"{group1} has a higher mean than {group2}."
    if diff < 0:
        return f"{group2} has a higher mean than {group1}."
    return "The two group means are very close."


def build_part6_anova(results: AnalysisResults) -> tuple[list[str], list[str]]:
    anova_df = results.anova_table
    tukey_df = results.tukey_table

    anova_comments: list[str] = []
    tukey_comments: list[str] = []

    if anova_df.empty:
        anova_comments.append("ANOVA table is empty, so interpretation could not be generated.")
    else:
        between = _between_row(anova_df)
        within = anova_df[anova_df["source"] == "Within groups (Error)"]
        if between is None:
            anova_comments.append("ANOVA decision could not be generated because the 'Between groups' row is missing.")
        else:
            f_stat = between.get("f_stat")
            p_value = between.get("p_value")
            ms_within = None if within.empty else within.iloc[0].get("ms")
            significance_note = (
                "Between-group difference is statistically significant, and at least one city mean differs from the others."
                if is_significant(p_value)
                else "Between-group difference is not statistically significant; current data does not provide strong evidence that city means diverge."
            )
            anova_comments.append(
                "For ANOVA, H0 states that all city mean prices are equal, and H1 states that at least one city mean differs. "
                f"The ANOVA F statistic is {format_number(f_stat)} with p-value {format_p_value(p_value)}. "
                f"Decision: {decision_text(p_value)}"
            )
            anova_comments.append(
                f"{significance_note} The within-group mean square (MS_within) is {format_number(ms_within, 2)}, "
                "which suggests that high intra-city heterogeneity may mask inter-city differences. "
                "Therefore, a non-significant ANOVA result may reflect high variance rather than complete market equality."
            )

    if tukey_df.empty:
        tukey_comments.append("Tukey multiple-comparison table is empty, so pairwise interpretation could not be generated.")
    else:
        significant_pairs = 0
        for row in tukey_df.itertuples(index=False):
            group1 = str(getattr(row, "group1", "Group1"))
            group2 = str(getattr(row, "group2", "Group2"))
            meandiff = getattr(row, "meandiff", None)
            p_adj = getattr(row, "p_adj", None) if hasattr(row, "p_adj") else getattr(row, "p-adj", None)
            reject = getattr(row, "reject", None)
            mean_diff_value = 0.0 if is_missing(meandiff) else float(meandiff)
            reject_flag = bool(reject) if not is_missing(reject) else False
            if reject_flag:
                significant_pairs += 1
            decision = "H0 is rejected." if reject_flag else "H0 cannot be rejected."

            tukey_comments.append(
                f"For Tukey pair {group1}-{group2}, H0 states equal means and H1 states different means. "
                f"The mean price difference for {group1} - {group2} is {format_currency(mean_diff_value)} "
                f"(p-adj={format_p_value(p_adj)}). {decision} {_format_direction(mean_diff_value, group1, group2)}"
            )

        if significant_pairs == 0:
            tukey_comments.append(
                "No city pair shows a statistically significant difference in multiple-comparison results. "
                "This supports the view that city-level price hierarchy is not sharply separated and distributions overlap within a similar band. "
                "However, larger samples or segment-level splits may reveal additional differences."
            )
        else:
            tukey_comments.append(
                f"The number of significant city pairs in Tukey results is {significant_pairs}. "
                "This is critical for identifying which specific pairs carry post-ANOVA separation. "
                "City-level pricing strategy should be optimized using these pairwise differences."
            )

    return anova_comments, tukey_comments
