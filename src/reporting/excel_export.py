from __future__ import annotations

# Analiz tabloları, gömülü grafikler ve sütun açıklamalarını tek XLSX dosyasında toplar.

from pathlib import Path

import pandas as pd
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter

from src.analysis.statistics import AnalysisResults


_EXPLANATION_GAP_COLUMNS = 3

_COLUMN_EXPLANATIONS: dict[str, tuple[str, str]] = {
    "Price": ("House price in Turkish Lira (TL).", "Primary target variable for market-level comparisons."),
    "Area": ("House size in square meters (m²).", "Core explanatory variable for scale and pricing effects."),
    "metric": ("Computed statistic key.", "Helps distinguish reported metrics quickly."),
    "value": ("Numeric metric value.", "Provides the quantitative magnitude used in interpretation."),
    "section": ("Logical section of the result.", "Separates summary, ANOVA, and coefficient blocks."),
    "confidence": ("Confidence level (e.g., 0.95).", "Shows strength of interval certainty."),
    "mean": ("Sample mean estimate.", "Represents central tendency."),
    "n": ("Sample size.", "Directly affects interval width and test power."),
    "std": ("Sample standard deviation.", "Used to compute standard error and margin."),
    "t_crit": ("Critical t value.", "Threshold used for confidence interval boundaries."),
    "margin": ("Margin of error.", "Half-width of the confidence interval."),
    "low": ("Lower confidence bound.", "Conservative side of plausible values."),
    "high": ("Upper confidence bound.", "Optimistic side of plausible values."),
    "formula": ("Calculation formula.", "Documents how the value is obtained."),
    "interval": ("Final interval expression.", "Single-line summary of the computed interval."),
    "test": ("Hypothesis statement.", "Links each row to a statistical question."),
    "test_type": ("Applied statistical method.", "Clarifies assumptions and interpretation rules."),
    "tail": ("One-sided or two-sided direction.", "Defines alternative hypothesis direction."),
    "alpha": ("Significance threshold.", "Decision boundary for rejecting H0."),
    "stat": ("Observed test statistic.", "Measures signal strength against null model."),
    "p_value": ("Probability under H0.", "Primary evidence for statistical significance."),
    "t_critic": ("Critical t threshold.", "Secondary decision reference."),
    "source": ("ANOVA variance source.", "Shows where total variance comes from."),
    "ss": ("Sum of squares.", "Quantifies explained/unexplained variation."),
    "df": ("Degrees of freedom.", "Defines reference distributions and scaling."),
    "ms": ("Mean square (SS/df).", "Variance estimate used in F-statistic."),
    "f_stat": ("F test statistic.", "Compares explained variance to residual variance."),
    "group1": ("First group in pairwise comparison.", "Reference group in Tukey output."),
    "group2": ("Second group in pairwise comparison.", "Compared group in Tukey output."),
    "meandiff": ("Mean(group1) - Mean(group2).", "Shows direction and size of pairwise effect."),
    "p-adj": ("Adjusted p-value.", "Controls family-wise false-positive risk."),
    "lower": ("Lower pairwise CI bound.", "Minimum plausible difference."),
    "upper": ("Upper pairwise CI bound.", "Maximum plausible difference."),
    "reject": ("True if H0 is rejected.", "Quick significance decision after adjustment."),
}

_METRIC_EXPLANATIONS: dict[str, tuple[str, str]] = {
    "multiple_r": ("Gozlenen ve tahmin edilen degerler arasindaki korelasyon gucu.", "Lineer uyum gucunu hizlica gosterir."),
    "r_squared": ("Modelin acikladigi varyans orani.", "Model uyum kalitesinin temel gostergesidir."),
    "adjusted_r_squared": ("Degisken sayisina gore duzeltilmis R-kare.", "Model karmasikligi degistiginde daha adil karsilastirma sunar."),
    "standard_error": ("Regresyon artiklarinin standart sapmasi.", "Tahmin hatasinin hedef degisken birimindeki ortalama olcegini verir."),
    "observations": ("Regresyonda kullanilan gozlem sayisi.", "Cikarimlarin dayandigi orneklem buyuklugunu gosterir."),
    "pearson_r": ("Area ile Price arasindaki Pearson korelasyonu.", "Lineer iliskinin yonunu ve gucunu gosterir."),
    "pearson_p_value": ("Pearson korelasyonu icin p-degeri.", "Korelasyonun sifirdan farkli olduguna dair kanit duzeyini verir."),
    "predicted_price_120m2": ("120 m2 icin modelin tahmin ettigi fiyat.", "Is acisindan kolay yorumlanan referans tahmindir."),
    "regression_df": ("Model terimleri icin serbestlik derecesi.", "MS ve F hesaplamasi icin gereklidir."),
    "regression_ss": ("Aciklanan kareler toplami (model SSR).", "Yordayici(lar) tarafindan yakalanan varyasyonu gosterir."),
    "regression_ms": ("Regresyon SS'nin regresyon df'ye bolunmesi.", "F istatistiginin pay kismini olusturur."),
    "regression_f": ("Regresyonun genel F istatistigi.", "Modelin sadece sabit terimli modele gore daha iyi aciklayip aciklamadigini test eder."),
    "regression_significance_f": ("Genel F testinin p-degeri.", "Modelin genel olarak ise yarar olduguna dair kanit saglar."),
    "residual_df": ("Artiklar icin serbestlik derecesi.", "Artik varyans tahminini belirler."),
    "residual_ss": ("Artik kareler toplami.", "Model tarafindan aciklanamayan varyasyonu gosterir."),
    "residual_ms": ("Artik SS'nin artik df'ye bolunmesi.", "F istatistiginin payda kismini ve hata varyansini verir."),
    "total_df": ("Toplam serbestlik derecesi.", "Model ve artik varyansin ayrisiminda referans saglar."),
    "total_ss": ("Toplam kareler toplami.", "Ayrisim oncesi toplam varyasyonu gosterir."),
    "coefficient": ("Tahmin edilen parametre degeri.", "Etkinin yonunu ve buyuklugunu niceller."),
    "std_error": ("Katsayi tahmininin standart hatasi.", "Katsayi tahmininin hassasiyetini gosterir."),
    "t_stat": ("Katsayi icin t istatistigi.", "Katsayinin sinyal/gurultu oranini verir."),
    "lower_95": ("%95 guven araliginda katsayinin alt siniri.", "Temkinli etki buyuklugu senaryosunu gosterir."),
    "upper_95": ("%95 guven araliginda katsayinin ust siniri.", "Iyimser etki buyuklugu senaryosunu gosterir."),
}

_SOURCE_EXPLANATIONS: dict[str, tuple[str, str]] = {
    "Between groups": ("Sehir ortalamalari arasindaki farklardan dogan varyasyon.", "ANOVA'nin sinyal bilesenidir."),
    "Within groups (Error)": ("Her sehir grubunun kendi icindeki varyasyon.", "ANOVA'nin arka plan gurultu bilesenidir."),
    "Total": ("Verideki toplam varyasyon.", "Varyans ayrisiminin tutarliligini kontrol eder."),
}

_TEST_TYPE_EXPLANATIONS: dict[str, tuple[str, str]] = {
    "one-sample t-test": ("Orneklem ortalamasini sabit bir esikle karsilastirir.", "Hedef esik varsayimlarini test eder."),
    "one-sample proportion z-test": ("Gozlenen orani referans oran ile karsilastirir.", "Ikili oran iddialarinda kullanilir."),
    "two-sample t-test (Welch)": ("Iki ortalamayi esit varyans varsayimi olmadan karsilastirir.", "Varyanslar esit degilse daha guvenli sonuclar verir."),
}

_TAIL_EXPLANATIONS: dict[str, tuple[str, str]] = {
    "two-sided": ("Herhangi bir farki arar (daha yuksek veya daha dusuk).", "En tarafsiz alternatif hipotez yaklasimidir."),
    "greater": ("Orneklem ortalamasinin esikten buyuk olup olmadigini test eder.", "Yonlu artis iddialarinda kullanilir."),
}


_HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
_HEADER_FONT = Font(color="FFFFFF", bold=True)
_INFO_HEADER_FILL = PatternFill("solid", fgColor="385723")
_INFO_HEADER_FONT = Font(color="FFFFFF", bold=True)
_BODY_BORDER = Border(
    left=Side(style="thin", color="D9D9D9"),
    right=Side(style="thin", color="D9D9D9"),
    top=Side(style="thin", color="D9D9D9"),
    bottom=Side(style="thin", color="D9D9D9"),
)


def _apply_region_style(
    worksheet,
    start_row: int,
    start_col: int,
    end_row: int,
    end_col: int,
    *,
    header_fill: PatternFill,
    header_font: Font,
) -> None:
    for col_idx in range(start_col, end_col + 1):
        header_cell = worksheet.cell(row=start_row, column=col_idx)
        header_cell.fill = header_fill
        header_cell.font = header_font
        header_cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for row_idx in range(start_row + 1, end_row + 1):
        for col_idx in range(start_col, end_col + 1):
            cell = worksheet.cell(row=row_idx, column=col_idx)
            cell.border = _BODY_BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=True)


def _add_excel_table(
    worksheet,
    *,
    start_row: int,
    start_col: int,
    end_row: int,
    end_col: int,
    table_name: str,
) -> None:
    if end_row <= start_row:
        return
    ref = f"{get_column_letter(start_col)}{start_row}:{get_column_letter(end_col)}{end_row}"
    table = Table(displayName=table_name, ref=ref)
    table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium9",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False,
    )
    worksheet.add_table(table)


def _build_ci_trace(ci_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for row in ci_df.itertuples(index=False):
        metric = str(getattr(row, "metric", "Metric"))
        confidence = float(getattr(row, "confidence", 0.95))
        mean = float(getattr(row, "mean", 0.0))
        std = float(getattr(row, "std", 0.0))
        n = int(round(float(getattr(row, "n", 0.0))))
        t_crit = float(getattr(row, "t_crit", 0.0))
        margin = float(getattr(row, "margin", 0.0))
        low = float(getattr(row, "low", 0.0))
        high = float(getattr(row, "high", 0.0))
        rows.append(
            {
                "metric": metric,
                "confidence": f"{int(confidence * 100)}%",
                "mean": f"{mean:,.4f}",
                "std": f"{std:,.4f}",
                "n": str(n),
                "t_crit": f"{t_crit:,.4f}",
                "margin": f"{margin:,.4f}",
                "formula": "mean ± t_crit * (std / sqrt(n))",
                "interval": f"[{low:,.4f}, {high:,.4f}]",
            }
        )
    return pd.DataFrame(rows, columns=["metric", "confidence", "mean", "std", "n", "t_crit", "margin", "formula", "interval"])


def _target_sheet_for_chart(chart_name: str) -> str:
    lowered = chart_name.lower()
    if lowered.startswith("part3_"):
        return "part3_one_sample"
    if lowered.startswith("part6_tukey_") or "tukey" in lowered:
        return "part6_tukey"
    if "anova" in lowered:
        return "part6_anova"
    if "scatter_reg" in lowered:
        return "part5_regression"
    if "price_hist" in lowered or "price_box" in lowered or "area_hist" in lowered:
        return "part1_descriptive"
    return "part1_descriptive"


def _embed_charts(writer: pd.ExcelWriter, chart_paths: list[Path]) -> None:
    row_map: dict[str, int] = {}
    for chart in chart_paths:
        if not chart.exists():
            continue
        sheet_name = _target_sheet_for_chart(chart.name)
        if sheet_name not in writer.sheets:
            continue
        row = row_map.get(sheet_name, 2)
        image = XLImage(str(chart))
        image.width = 520
        image.height = 280
        writer.sheets[sheet_name].add_image(image, f"L{row}")
        row_map[sheet_name] = row + 16


def _add_row(rows: list[dict[str, str]], seen: set[str], key: str, meaning: str, why: str) -> None:
    if key in seen:
        return
    rows.append({"key": key, "what_it_means": meaning, "why_it_is_useful": why})
    seen.add(key)


def _build_explanations(sheet_name: str, df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()

    for col in df.columns:
        if col in _COLUMN_EXPLANATIONS:
            meaning, why = _COLUMN_EXPLANATIONS[col]
            _add_row(rows, seen, col, meaning, why)

    if sheet_name == "part1_descriptive":
        for stat_key in df.index.astype(str):
            meaning = f"Descriptive statistic: {stat_key}."
            why = "Supports interpretation of central tendency, dispersion, and shape."
            _add_row(rows, seen, stat_key, meaning, why)

    if "metric" in df.columns:
        for metric_key in df["metric"].dropna().astype(str).unique():
            meaning = f"Statistical metric: {metric_key}."
            why = "Adds interpretable detail for model output and reproducibility."
            _add_row(rows, seen, metric_key, meaning, why)

    if "source" in df.columns:
        for source_key in df["source"].dropna().astype(str).unique():
            meaning = f"ANOVA source component: {source_key}."
            why = "Clarifies how total variance is decomposed."
            _add_row(rows, seen, source_key, meaning, why)

    if "test_type" in df.columns:
        for test_key in df["test_type"].dropna().astype(str).unique():
            meaning = f"Hypothesis test type: {test_key}."
            why = "Documents the inference method used."
            _add_row(rows, seen, test_key, meaning, why)

    if "tail" in df.columns:
        for tail_key in df["tail"].dropna().astype(str).unique():
            meaning = f"Tail type: {tail_key}."
            why = "Defines directional interpretation of the decision."
            _add_row(rows, seen, tail_key, meaning, why)

    return pd.DataFrame(rows, columns=["key", "what_it_means", "why_it_is_useful"])


def _set_sheet_column_widths(writer: pd.ExcelWriter, sheet_name: str, df: pd.DataFrame, index: bool, note_start_col: int) -> None:
    worksheet = writer.sheets[sheet_name]
    base_columns = df.columns.tolist()
    if index:
        base_columns = [(df.index.name or "index")] + base_columns

    for i, col_name in enumerate(base_columns, start=1):
        width = max(12, min(30, len(str(col_name)) + 2))
        worksheet.column_dimensions[get_column_letter(i)].width = width

    for j, width in enumerate([20, 46, 50], start=note_start_col + 1):
        worksheet.column_dimensions[get_column_letter(j)].width = width


def _apply_unit_number_formats(worksheet, df: pd.DataFrame, *, index: bool = False) -> None:
    base_offset = 2 if index else 1
    for col_idx, col_name in enumerate(df.columns, start=base_offset):
        if col_name == "Price":
            for row_idx in range(2, df.shape[0] + 2):
                worksheet.cell(row=row_idx, column=col_idx).number_format = '#,##0.00 "TL"'
        if col_name == "Area":
            for row_idx in range(2, df.shape[0] + 2):
                worksheet.cell(row=row_idx, column=col_idx).number_format = '#,##0.00 "m²"'


def _write_analysis_sheet(
    writer: pd.ExcelWriter,
    sheet_name: str,
    df: pd.DataFrame,
    *,
    index: bool = False,
) -> None:
    df_for_write = df.copy()
    if index and not df_for_write.index.name:
        df_for_write.index.name = "metric"
    df_for_write.to_excel(writer, index=index, sheet_name=sheet_name)
    table_col_count = df_for_write.shape[1] + (1 if index else 0)
    notes_start_col = table_col_count + _EXPLANATION_GAP_COLUMNS
    explanations = _build_explanations(sheet_name, df_for_write)
    explanations.to_excel(writer, index=False, sheet_name=sheet_name, startcol=notes_start_col)
    _set_sheet_column_widths(writer, sheet_name, df_for_write, index=index, note_start_col=notes_start_col)

    worksheet = writer.sheets[sheet_name]
    data_start_row = 1
    data_end_row = max(2, df_for_write.shape[0] + 1)
    data_start_col = 1
    data_end_col = table_col_count
    _apply_region_style(
        worksheet,
        data_start_row,
        data_start_col,
        data_end_row,
        data_end_col,
        header_fill=_HEADER_FILL,
        header_font=_HEADER_FONT,
    )
    _add_excel_table(
        worksheet,
        start_row=data_start_row,
        start_col=data_start_col,
        end_row=data_end_row,
        end_col=data_end_col,
        table_name=f"{sheet_name}_data_tbl".replace("-", "_"),
    )

    if not explanations.empty:
        info_start_row = 1
        info_start_col = notes_start_col + 1
        info_end_row = max(2, explanations.shape[0] + 1)
        info_end_col = info_start_col + explanations.shape[1] - 1
        _apply_region_style(
            worksheet,
            info_start_row,
            info_start_col,
            info_end_row,
            info_end_col,
            header_fill=_INFO_HEADER_FILL,
            header_font=_INFO_HEADER_FONT,
        )
        _add_excel_table(
            worksheet,
            start_row=info_start_row,
            start_col=info_start_col,
            end_row=info_end_row,
            end_col=info_end_col,
            table_name=f"{sheet_name}_info_tbl".replace("-", "_"),
        )

    if sheet_name == "part2_ci":
        trace_df = _build_ci_trace(df_for_write)
        trace_start_row = df_for_write.shape[0] + 5
        trace_df.to_excel(writer, index=False, sheet_name=sheet_name, startrow=trace_start_row - 1, startcol=0)
        trace_end_row = trace_start_row + max(1, trace_df.shape[0])
        trace_end_col = trace_df.shape[1]
        _apply_region_style(
            worksheet,
            trace_start_row,
            1,
            trace_end_row,
            trace_end_col,
            header_fill=_HEADER_FILL,
            header_font=_HEADER_FONT,
        )
        _add_excel_table(
            worksheet,
            start_row=trace_start_row,
            start_col=1,
            end_row=trace_end_row,
            end_col=trace_end_col,
            table_name="part2_ci_calc_tbl",
        )

    _apply_unit_number_formats(worksheet, df_for_write, index=index)


def export_excel_bundle(
    clean_df: pd.DataFrame,
    results: AnalysisResults,
    output_path: str | Path,
    *,
    chart_paths: list[Path] | None = None,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        clean_df.to_excel(writer, index=False, sheet_name="clean_data")
        clean_ws = writer.sheets["clean_data"]
        clean_end_row = max(2, clean_df.shape[0] + 1)
        clean_end_col = clean_df.shape[1]
        _apply_region_style(
            clean_ws,
            1,
            1,
            clean_end_row,
            clean_end_col,
            header_fill=_HEADER_FILL,
            header_font=_HEADER_FONT,
        )
        _add_excel_table(
            clean_ws,
            start_row=1,
            start_col=1,
            end_row=clean_end_row,
            end_col=clean_end_col,
            table_name="clean_data_tbl",
        )
        for col_idx, col_name in enumerate(clean_df.columns, start=1):
            if col_name == "Price":
                for row_idx in range(2, clean_end_row + 1):
                    clean_ws.cell(row=row_idx, column=col_idx).number_format = '#,##0.00 "TL"'
            elif col_name == "Area":
                for row_idx in range(2, clean_end_row + 1):
                    clean_ws.cell(row=row_idx, column=col_idx).number_format = '#,##0.00 "m²"'
        _write_analysis_sheet(writer, "part1_descriptive", results.descriptive, index=True)
        freq_start_row = results.descriptive.shape[0] + 8
        freq_df = results.part1_price_frequency.copy()
        freq_df.to_excel(writer, index=False, sheet_name="part1_descriptive", startrow=freq_start_row - 1, startcol=0)
        freq_ws = writer.sheets["part1_descriptive"]
        freq_end_row = freq_start_row + max(1, freq_df.shape[0])
        freq_end_col = max(1, freq_df.shape[1])
        _apply_region_style(
            freq_ws,
            freq_start_row,
            1,
            freq_end_row,
            freq_end_col,
            header_fill=_HEADER_FILL,
            header_font=_HEADER_FONT,
        )
        _add_excel_table(
            freq_ws,
            start_row=freq_start_row,
            start_col=1,
            end_row=freq_end_row,
            end_col=freq_end_col,
            table_name="part1_price_freq_tbl",
        )
        for row_idx in range(freq_start_row + 1, freq_end_row + 1):
            if "midpoint" in freq_df.columns:
                midpoint_col = list(freq_df.columns).index("midpoint") + 1
                freq_ws.cell(row=row_idx, column=midpoint_col).number_format = '#,##0.00 "TL"'
        _write_analysis_sheet(writer, "part2_ci", results.confidence_intervals, index=False)
        _write_analysis_sheet(writer, "part3_one_sample", results.one_sample_tests, index=False)
        _write_analysis_sheet(writer, "part4_two_sample", results.two_sample_tests, index=False)
        _write_analysis_sheet(writer, "part5_regression", results.regression_summary, index=False)
        _write_analysis_sheet(writer, "part6_anova", results.anova_table, index=False)
        _write_analysis_sheet(writer, "part6_tukey", results.tukey_table, index=False)

        if chart_paths:
            _embed_charts(writer, chart_paths)

    return output_path
