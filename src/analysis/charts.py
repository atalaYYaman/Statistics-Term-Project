from __future__ import annotations

# Streamlit önizlemesi ve Word/Excel için PNG grafikleri; eksen biçimlendirmesi okunabilirlik içindir.

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter
import scipy.stats as stats
import seaborn as sns

from src.analysis.statistics import AnalysisResults


def _full_number_formatter(value: float, _pos: float) -> str:
    # NaN eksen etiketlerini gizle; diğer değerleri binlik ayraçlı tam sayı göster.
    if value != value:  # NaN check
        return ""
    return f"{int(value):,}"


def _format_numeric_axis(ax, axis: str = "x") -> None:
    # TL ve büyük sayılarda bilimsel gösterimi kapat; değerler düz metin gibi okunur.
    formatter = FuncFormatter(_full_number_formatter)
    if axis == "x":
        ax.ticklabel_format(style="plain", axis="x", useOffset=False)
        ax.xaxis.set_major_formatter(formatter)
    else:
        ax.ticklabel_format(style="plain", axis="y", useOffset=False)
        ax.yaxis.set_major_formatter(formatter)


def _plot_hypothesis_curve(
    out_path: Path,
    test_name: str,
    stat_value: float,
    alpha: float,
    tail: str,
    df_value: float | None,
) -> Path:
    # Bölüm 3 hipotez grafiği: sıfır dağılımı, kritik çizgiler ve gözlenen istatistik (t veya normal).
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.linspace(-5, 5, 1000)

    if df_value is None:
        y = stats.norm.pdf(x)
        curve_label = "N(0,1)"
        if tail == "greater":
            crit = stats.norm.ppf(1 - alpha)
            ax.axvline(crit, color="orange", linestyle="--", linewidth=2, label=f"critical={crit:.3f}")
        else:
            crit = stats.norm.ppf(1 - alpha / 2)
            ax.axvline(-crit, color="orange", linestyle="--", linewidth=2)
            ax.axvline(crit, color="orange", linestyle="--", linewidth=2, label=f"critical=±{crit:.3f}")
    else:
        y = stats.t.pdf(x, df=max(1, int(df_value)))
        curve_label = f"t(df={int(df_value)})"
        if tail == "greater":
            crit = stats.t.ppf(1 - alpha, df=max(1, int(df_value)))
            ax.axvline(crit, color="orange", linestyle="--", linewidth=2, label=f"critical={crit:.3f}")
        else:
            crit = stats.t.ppf(1 - alpha / 2, df=max(1, int(df_value)))
            ax.axvline(-crit, color="orange", linestyle="--", linewidth=2)
            ax.axvline(crit, color="orange", linestyle="--", linewidth=2, label=f"critical=±{crit:.3f}")

    ax.plot(x, y, color="#1f77b4", linewidth=2, label=curve_label)
    ax.axvline(stat_value, color="red", linewidth=2, label=f"test statistic={stat_value:.3f}")
    ax.set_title(f"Part 3 Hypothesis Plot - {test_name}")
    ax.set_xlabel("Statistic Value")
    ax.set_ylabel("Density")
    ax.legend()
    file_path = out_path / f"part3_{test_name.lower().replace(' ', '_').replace(',', '').replace('>', 'gt').replace('!', 'not')}_curve.png"
    fig.savefig(file_path, bbox_inches="tight", dpi=130)
    plt.close(fig)
    return file_path


def _plot_tukey_pairwise(out_path: Path, tukey_df) -> Path | None:
    # Bölüm 6: Tukey çift ortalama farkları; sıfır çizgisi ve güven aralıkları (yatay hata çubukları).
    required_cols = {"group1", "group2", "meandiff", "lower", "upper", "reject"}
    if tukey_df is None or tukey_df.empty or not required_cols.issubset(set(tukey_df.columns)):
        return None

    plot_df = tukey_df.copy()
    plot_df["pair"] = plot_df["group1"].astype(str) + " vs " + plot_df["group2"].astype(str)
    plot_df["meandiff"] = plot_df["meandiff"].astype(float)
    plot_df["lower"] = plot_df["lower"].astype(float)
    plot_df["upper"] = plot_df["upper"].astype(float)
    plot_df = plot_df.sort_values("meandiff", ascending=True).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    y = np.arange(len(plot_df))
    lower_err = plot_df["meandiff"] - plot_df["lower"]
    upper_err = plot_df["upper"] - plot_df["meandiff"]
    colors = ["#d62728" if bool(rej) else "#1f77b4" for rej in plot_df["reject"]]

    for idx in range(len(plot_df)):
        ax.errorbar(
            plot_df.loc[idx, "meandiff"],
            y[idx],
            xerr=np.array([[lower_err.iloc[idx]], [upper_err.iloc[idx]]]),
            fmt="o",
            color=colors[idx],
            ecolor=colors[idx],
            capsize=4,
            markersize=6,
        )

    ax.axvline(0, color="black", linestyle="--", linewidth=1.5)
    ax.set_yticks(y)
    ax.set_yticklabels(plot_df["pair"])
    ax.set_xlabel("Mean Difference (group1 - group2)")
    ax.set_title("Part 6 Tukey Pairwise Comparison (95% CI)")
    _format_numeric_axis(ax, "x")
    fig.tight_layout()
    file_path = out_path / "part6_tukey_pairwise_ci.png"
    fig.savefig(file_path, bbox_inches="tight", dpi=130)
    plt.close(fig)
    return file_path


def generate_charts(
    df,
    city1: str,
    city2: str,
    city3: str,
    out_dir: str | Path,
    results: AnalysisResults | None = None,
) -> list[Path]:
    # Keşif grafikleri ve varsa hipotez/Tukey ek görselleri üretir; çıktı yolları listelenir.
    sns.set_theme(style="whitegrid", context="talk")
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    chart_files: list[Path] = []

    c1 = df[df["City"] == city1]

    # Birinci şehir fiyat dağılımı: histogram ve yoğunluk eğrisi (KDE).
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(c1["Price"].dropna(), bins=10, kde=True, ax=ax)
    ax.set_title(f"{city1} Price Distribution")
    ax.set_xlabel("Price (TL)")
    ax.set_ylabel("Frequency")
    _format_numeric_axis(ax, "x")
    file_1 = out_path / f"{city1}_price_hist.png"
    fig.savefig(file_1, bbox_inches="tight", dpi=130)
    plt.close(fig)
    chart_files.append(file_1)

    # Birinci şehir fiyatı için kutu grafiği (medyan ve aykırı değerler).
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(data=c1, x="Price", ax=ax)
    ax.set_title(f"{city1} Price Boxplot")
    ax.set_xlabel("Price (TL)")
    _format_numeric_axis(ax, "x")
    file_2 = out_path / f"{city1}_price_box.png"
    fig.savefig(file_2, bbox_inches="tight", dpi=130)
    plt.close(fig)
    chart_files.append(file_2)

    # Birinci şehir alan dağılımı (histogram + KDE).
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(c1["Area"].dropna(), bins=10, kde=True, ax=ax)
    ax.set_title(f"{city1} Area Distribution")
    ax.set_xlabel("Area (m²)")
    ax.set_ylabel("Frequency")
    file_3 = out_path / f"{city1}_area_hist.png"
    fig.savefig(file_3, bbox_inches="tight", dpi=130)
    plt.close(fig)
    chart_files.append(file_3)

    # Birinci şehir: alan–fiyat saçılımı ve regresyon doğrusu.
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.regplot(data=c1, x="Area", y="Price", ax=ax, line_kws={"color": "red"})
    ax.set_title(f"{city1} Area vs Price")
    ax.set_xlabel("Area (m²)")
    ax.set_ylabel("Price (TL)")
    _format_numeric_axis(ax, "y")
    file_4 = out_path / f"{city1}_scatter_reg.png"
    fig.savefig(file_4, bbox_inches="tight", dpi=130)
    plt.close(fig)
    chart_files.append(file_4)

    # Üç şehir için fiyat karşılaştırması (ANOVA öncesi keşif kutusu).
    fig, ax = plt.subplots(figsize=(10, 5))
    subset = df[df["City"].isin([city1, city2, city3])]
    sns.boxplot(data=subset, x="City", y="Price", ax=ax)
    ax.set_title("ANOVA Price Comparison")
    ax.set_xlabel("City")
    ax.set_ylabel("Price (TL)")
    _format_numeric_axis(ax, "y")
    file_5 = out_path / "anova_price_boxplot.png"
    fig.savefig(file_5, bbox_inches="tight", dpi=130)
    plt.close(fig)
    chart_files.append(file_5)

    # Her tek örneklem testi için yoğunluk eğrisi; oran testinde normal, diğerlerinde t kullanılır.
    if results is not None and not results.one_sample_tests.empty:
        c1 = df[df["City"] == city1]
        price_n = float(c1["Price"].dropna().shape[0])
        area_n = float(c1["Area"].dropna().shape[0])
        for row in results.one_sample_tests.itertuples(index=False):
            test_name = str(getattr(row, "test", "one_sample"))
            stat = float(getattr(row, "stat", np.nan))
            alpha = float(getattr(row, "alpha", 0.05))
            tail = str(getattr(row, "tail", "two-sided"))
            if np.isnan(stat):
                continue
            if "proportion" in str(getattr(row, "test_type", "")).lower():
                df_value = None
            elif "Price" in test_name:
                df_value = max(1.0, price_n - 1.0)
            else:
                df_value = max(1.0, area_n - 1.0)
            chart_files.append(_plot_hypothesis_curve(out_path, test_name, stat, alpha, tail, df_value))

    # Tukey tablosu varsa çift karşılaştırma grafiğini listeye ekle.
    if results is not None and not results.tukey_table.empty:
        tukey_chart = _plot_tukey_pairwise(out_path, results.tukey_table)
        if tukey_chart is not None:
            chart_files.append(tukey_chart)

    return chart_files
