from __future__ import annotations

# Bölüm 2 güven aralığı tablosundan yorum metinleri.

from src.analysis.statistics import AnalysisResults
from src.reporting.narratives.templates_tr import format_area, format_currency, format_number, is_missing


def build_part2_confidence_intervals(results: AnalysisResults, city: str) -> list[str]:
    df = results.confidence_intervals
    if df.empty:
        return ["Confidence interval table is empty, so interpretation could not be generated."]

    def row_for(metric: str, confidence: float) -> dict[str, float] | None:
        rows = df[(df["metric"] == metric) & (df["confidence"] == confidence)]
        if rows.empty:
            return None
        row = rows.iloc[0]
        return {
            "n": float(row["n"]),
            "std": float(row["std"]),
            "t_crit": float(row["t_crit"]),
            "margin": float(row["margin"]),
            "mean": float(row["mean"]),
            "low": float(row["low"]),
            "high": float(row["high"]),
        }

    comments: list[str] = []
    p95 = row_for("Price", 0.95)
    p99 = row_for("Price", 0.99)
    a95 = row_for("Area", 0.95)

    if p95 is not None and p99 is not None:
        width95 = p95["high"] - p95["low"]
        width99 = p99["high"] - p99["low"]
        width_diff = width99 - width95
        comments.append(
            f"For {city}, the 95% confidence interval for mean price is [{format_currency(p95['low'])}, {format_currency(p95['high'])}] "
            f"and the 99% interval is [{format_currency(p99['low'])}, {format_currency(p99['high'])}]. "
            f"The wider 99% interval reflects the trade-off between higher confidence and larger uncertainty bounds. "
            f"The width difference of {format_currency(width_diff)} shows the practical cost of increased certainty. "
            f"In real-estate terms, this impacts risk premium and negotiation buffers in pricing decisions."
        )
    elif p95 is not None:
        comments.append(
            f"For {city}, the 95% confidence interval for mean price is [{format_currency(p95['low'])}, {format_currency(p95['high'])}]. "
            f"This interval represents statistical uncertainty around the sample-based estimate. "
            f"Interval width is expected to increase as market volatility rises."
        )
    else:
        comments.append("Price confidence interval rows are missing, so detailed uncertainty interpretation is limited.")

    if a95 is not None:
        contains_100 = a95["low"] <= 100 <= a95["high"]
        relation_text = (
            "100 m² lies inside the interval, so there is no strong stand-alone evidence that mean area is above the 100 m² reference"
            if contains_100
            else "100 m² falls outside the interval, strengthening evidence of a difference from the reference value"
        )
        comments.append(
            f"For {city}, the 95% confidence interval for mean area is [{format_area(a95['low'])}, {format_area(a95['high'])}]. "
            f"This helps identify where typical unit size is concentrated in the housing stock. "
            f"In addition, {relation_text}, and this should be read together with the one-sample area test result. "
            f"From a market perspective, broad area dispersion may indicate coexistence of standard and premium inventory."
        )
    else:
        comments.append("Area confidence interval is unavailable, so no statistical context could be provided for size uncertainty.")

    for row in df.itertuples(index=False):
        metric = str(getattr(row, "metric", "Metric"))
        confidence = int(round(float(getattr(row, "confidence", 0.95)) * 100))
        low = getattr(row, "low", None)
        high = getattr(row, "high", None)
        if metric not in {"Price", "Area"} and not is_missing(low) and not is_missing(high):
            comments.append(
                f"For {metric}, the {confidence}% confidence interval is [{format_number(low)}, {format_number(high)}]. "
                f"This range defines uncertainty bounds for the plausible population value of the metric. "
                f"In decision workflows, interval width also provides indirect evidence about data quality and sample adequacy."
            )

    for row in df.itertuples(index=False):
        metric = str(getattr(row, "metric", "Metric"))
        confidence = int(round(float(getattr(row, "confidence", 0.95)) * 100))
        mean = getattr(row, "mean", None)
        std = getattr(row, "std", None)
        n = getattr(row, "n", None)
        t_crit = getattr(row, "t_crit", None)
        margin = getattr(row, "margin", None)
        low = getattr(row, "low", None)
        high = getattr(row, "high", None)
        if is_missing(mean) or is_missing(std) or is_missing(n) or is_missing(t_crit) or is_missing(margin):
            continue
        metric_unit_mean = format_currency(mean) if metric == "Price" else format_area(mean)
        metric_unit_std = format_currency(std) if metric == "Price" else format_area(std)
        metric_unit_margin = format_currency(margin) if metric == "Price" else format_area(margin)
        metric_unit_low = format_currency(low) if metric == "Price" else format_area(low)
        metric_unit_high = format_currency(high) if metric == "Price" else format_area(high)
        comments.append(
            f"Confidence interval calculation trace for {metric} ({confidence}%): sample mean={metric_unit_mean}, standard deviation={metric_unit_std}, n={format_number(n, 0)}, critical value={format_number(t_crit)}. "
            f"The margin of error is computed as t_crit*(std/sqrt(n)) = {metric_unit_margin}. "
            f"Finally, the interval is obtained as mean±margin = [{metric_unit_low}, {metric_unit_high}]."
        )

    return comments
