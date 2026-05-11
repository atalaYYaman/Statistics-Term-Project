from __future__ import annotations

# Şehir seçimi, veri yükleme/manuel giriş, doğrulama, analiz ve çıktı indirme akışı.

import hashlib
import re
from pathlib import Path

import pandas as pd
import streamlit as st

from src.analysis.charts import generate_charts
from src.analysis.statistics import run_all_analyses
from src.city_assignment import load_city_assignments
from src.data_ingestion import build_empty_dataframe, load_uploaded_excel
from src.reporting.excel_export import export_excel_bundle
from src.reporting.word_report import export_word_report
from src.validation import normalize_dataset, validate_dataset


# Atama CSV’si, Excel şablonu ve üretilen çıktılar uygulama klasörüne göre tanımlanır.

BASE_DIR = Path(__file__).resolve().parent
CITY_FILE = BASE_DIR / "data" / "city_assignments.csv"
TEMPLATE_FILE = BASE_DIR / "data" / "templates" / "input_template.xlsx"
OUTPUT_DIR = BASE_DIR / "outputs"
CHART_DIR = OUTPUT_DIR / "charts"

GUIDE_TOTAL_STEPS = 7


def _guide_step_content(step: int) -> tuple[str, str, list[str]]:
    """Step title, description, and caution bullets."""
    steps: list[tuple[str, str, list[str]]] = [
        (
            "City selection",
            "Choose the **1st, 2nd, and 3rd city** from the lists below. You can search by typing.",
            [
                "All three cities must be **different**; duplicate selection is not allowed.",
                "Your choices define which cities are compared in the analysis.",
            ],
        ),
        (
            "Confirm and continue",
            "Click **Confirm Cities and Continue to Data Upload**.",
            [
                "After confirmation, upload, manual entry, and preview sections are enabled.",
                "If you selected the wrong city, reselect and confirm again.",
            ],
        ),
        (
            "Excel data input",
            "Optionally download the template, fill it, and upload an Excel file.",
            [
                "Excel columns must match the template; use selected city names in the **City** field.",
                "If you upload the same file again, the system will **not** duplicate it.",
            ],
        ),
        (
            "Manual row entry",
            "To add listings one by one, choose a city, fill the form, and click **Add Record**.",
            [
                "**Price** and **Area** are critical; enter positive and complete values.",
                "Records are automatically tagged with the selected **City**.",
            ],
        ),
        (
            "Data preview and checks",
            "Review the table and city-level record counts.",
            [
                "Ensure enough records per city (**minimum 30** for analysis).",
                "Fix missing/incorrect **City** labels via Excel or manual input.",
            ],
        ),
        (
            "Run analysis",
            "Click **Run Analyses** to generate all statistical outputs and charts.",
            [
                "If you see validation errors, read the messages; they usually come from sample size or missing fields.",
                "The app converts **Price/Area** fields to numeric; correct any text formatting issues.",
            ],
        ),
        (
            "Output files",
            "After analysis, download the Excel and Word outputs.",
            [
                "Files are also saved under the `outputs` folder; download buttons appear after analysis.",
                "Report and Excel file names are generated from selected cities.",
            ],
        ),
    ]
    step = max(0, min(step, len(steps) - 1))
    title, body, tips = steps[step]
    return title, body, tips


def _init_state() -> None:
    # Oturum başında çalışma tablosu ve yüklenen dosya parmak izi kümesi oluşturulur.
    if "working_df" not in st.session_state:
        st.session_state.working_df = build_empty_dataframe()
    if "processed_upload_signatures" not in st.session_state:
        st.session_state.processed_upload_signatures = set()
    if "cities_confirmed" not in st.session_state:
        st.session_state.cities_confirmed = False
    if "selected_cities" not in st.session_state:
        st.session_state.selected_cities = []
    if "guide_open" not in st.session_state:
        st.session_state.guide_open = True
    if "guide_step" not in st.session_state:
        st.session_state.guide_step = 0


def _guide_prev() -> None:
    st.session_state.guide_step = max(0, int(st.session_state.guide_step) - 1)


def _guide_next() -> None:
    st.session_state.guide_step = min(GUIDE_TOTAL_STEPS - 1, int(st.session_state.guide_step) + 1)


def _guide_close() -> None:
    st.session_state.guide_open = False


def _guide_restart() -> None:
    st.session_state.guide_open = True
    st.session_state.guide_step = 0


def _render_guide_panel() -> None:
    """Step-by-step guide card shown at top by default."""
    if not st.session_state.guide_open:
        return

    step = int(st.session_state.guide_step)
    step = max(0, min(step, GUIDE_TOTAL_STEPS - 1))
    st.session_state.guide_step = step

    title, body, tips = _guide_step_content(step)
    with st.container(border=True):
        st.markdown(f"#### Guide — Step {step + 1}/{GUIDE_TOTAL_STEPS}: {title}")
        st.markdown(body)
        if tips:
            st.markdown("**Caution:**")
            for tip in tips:
                st.markdown(f"- {tip}")

        c_prev, c_next, c_close, c_spacer = st.columns([1, 1, 1, 3])
        with c_prev:
            st.button(
                "Back",
                key="guide_btn_prev",
                disabled=step <= 0,
                on_click=_guide_prev,
                use_container_width=True,
            )
        with c_next:
            st.button(
                "Next",
                key="guide_btn_next",
                disabled=step >= GUIDE_TOTAL_STEPS - 1,
                on_click=_guide_next,
                use_container_width=True,
            )
        with c_close:
            st.button("Close", key="guide_btn_close", on_click=_guide_close, use_container_width=True)


def _section_guide_popover(step_for_section: int, short_title: str) -> None:
    """Short guide popover when current step matches this section."""
    if not st.session_state.guide_open:
        return
    if int(st.session_state.guide_step) != step_for_section:
        return
    with st.popover(f"Guide: {short_title}", use_container_width=True):
        _title, body, tips = _guide_step_content(step_for_section)
        st.markdown(body)
        if tips:
            st.markdown("**Caution:**")
            for tip in tips:
                st.markdown(f"- {tip}")


def _render_manual_form(city: str) -> None:
    st.subheader(f"Add Manual Record - {city}")
    with st.form(f"manual_form_{city}"):
        col1, col2 = st.columns(2)
        price = col1.number_input("Price (TL)", min_value=0.0, step=1000.0)
        area = col2.number_input("Area (m2)", min_value=0.0, step=1.0)
        rooms = col1.number_input("Rooms", min_value=0.0, step=1.0)
        b_age = col2.number_input("BuildingAge", min_value=0.0, step=1.0)
        floor_num = col1.number_input("FloorNumber", step=1.0)
        floor_total = col2.number_input("NumberOfFloors", min_value=0.0, step=1.0)
        heating = st.text_input("HeatingType")
        district = st.text_input("District")
        src = st.text_input("SourceURL")
        submitted = st.form_submit_button("Add Record")
        if submitted:
            row = pd.DataFrame(
                [
                    {
                        "Price": price,
                        "Area": area,
                        "Rooms": rooms,
                        "BuildingAge": b_age,
                        "FloorNumber": floor_num,
                        "NumberOfFloors": floor_total,
                        "HeatingType": heating,
                        "District": district,
                        "City": city,
                        "SourceURL": src,
                    }
                ]
            )
            st.session_state.working_df = pd.concat([st.session_state.working_df, row], ignore_index=True)
            st.success("Record added.")


def _download_button_for_file(path: Path, label: str, mime: str) -> None:
    # Kaydedilmiş çıktıyı okuyup Streamlit indirme düğmesine verir.
    with open(path, "rb") as fh:
        st.download_button(label=label, data=fh.read(), file_name=path.name, mime=mime)


def _build_run_label(cities: list[str]) -> str:
    # İndirilecek Excel/Word dosya adları için ASCII uyumlu etiket üretir.
    city_part = "_".join(cities)
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", city_part).strip("_")
    return slug or "manual_selection"


def _guide_open() -> None:
    st.session_state.guide_open = True


def main() -> None:
    # Ana akış: rehber, şehir seçimi, Excel/manuel veri, önizleme, analiz, tablolar ve indirmeler.
    st.set_page_config(page_title="Istatistik Otomasyonu", layout="wide")
    st.title("Streamlit-Based Statistics Automation")
    st.caption("City selection, data entry, analysis, and report automation")
    _init_state()

    with st.sidebar:
        st.subheader("Usage Guide")
        st.caption("Follow steps from the top guide card.")
        st.button("Restart Guide", key="sidebar_guide_restart", on_click=_guide_restart, use_container_width=True)
        if not st.session_state.guide_open:
            st.button("Open Guide", key="sidebar_guide_open", on_click=_guide_open, use_container_width=True)

    assignments_df = load_city_assignments(CITY_FILE)
    city_columns = ["city1", "city2", "city3"]
    available_cities = (
        assignments_df[city_columns].stack().dropna().astype(str).str.strip().sort_values().unique().tolist()
    )
    if not available_cities:
        st.error("City list not found. Please check city_assignments.csv.")
        return

    _render_guide_panel()

    st.header("1) City Selection")
    st.caption("Search by typing and select the cities in order.")
    _section_guide_popover(0, "City selection")
    city1 = st.selectbox("1st City", options=available_cities, key="city_pick_1")
    city2 = st.selectbox("2nd City", options=available_cities, key="city_pick_2")
    city3 = st.selectbox("3rd City", options=available_cities, key="city_pick_3")

    col_confirm, col_guide_confirm = st.columns([2, 1])
    with col_confirm:
        if st.button("Confirm Cities and Continue to Data Upload"):
            selected = [city1, city2, city3]
            if len(set(selected)) != 3:
                st.error("Please choose 3 distinct cities.")
            else:
                st.session_state.selected_cities = selected
                st.session_state.cities_confirmed = True
                st.success("Cities saved. You can proceed to data upload.")
    with col_guide_confirm:
        _section_guide_popover(1, "Confirmation")

    if not st.session_state.cities_confirmed:
        st.info("Select and confirm 3 cities to continue.")
        return

    cities = st.session_state.selected_cities
    run_label = _build_run_label(cities)
    st.success(f"Selected cities: {cities[0]}, {cities[1]}, {cities[2]}")

    st.header("2) Data Input")
    _section_guide_popover(2, "Excel input")
    if TEMPLATE_FILE.exists():
        _download_button_for_file(
            TEMPLATE_FILE,
            "Download Excel Template",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    uploaded = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])
    if uploaded is not None:
        # Aynı Excel dosyasının yeniden yüklenmesini SHA-256 parmak izi ile engelle.
        upload_bytes = uploaded.getvalue()
        upload_signature = hashlib.sha256(upload_bytes).hexdigest()
        if upload_signature not in st.session_state.processed_upload_signatures:
            df_upload = load_uploaded_excel(upload_bytes)
            st.session_state.working_df = pd.concat([st.session_state.working_df, df_upload], ignore_index=True)
            st.session_state.processed_upload_signatures.add(upload_signature)
            st.success("Excel data added.")
        else:
            st.info("This Excel file was already uploaded; duplicate import skipped.")

    st.header("3) Manual Row Entry")
    _section_guide_popover(3, "Manual row")
    manual_city = st.selectbox("City for manual entry", options=cities, key="manual_city")
    _render_manual_form(manual_city)

    st.header("4) Data Preview")
    _section_guide_popover(4, "Preview")
    st.dataframe(st.session_state.working_df, use_container_width=True)
    st.caption(f"Total records: {len(st.session_state.working_df)}")
    if not st.session_state.working_df.empty and "City" in st.session_state.working_df.columns:
        city_counts = st.session_state.working_df["City"].value_counts(dropna=False)
        st.write("City-level record count:")
        st.dataframe(city_counts.rename_axis("City").reset_index(name="Count"), use_container_width=True)

    st.markdown("---")
    col_an, col_gan = st.columns([2, 1])
    with col_an:
        run_analysis = st.button("Run Analyses", key="run_analysis_btn")
    with col_gan:
        _section_guide_popover(5, "Analysis")

    if run_analysis:
        # Normalize et, doğrula, istatistik ve grafikleri üret, Excel ile Word dışa aktar.
        raw_df = st.session_state.working_df.copy()
        clean_df = normalize_dataset(raw_df)
        errors = validate_dataset(clean_df, cities, min_per_city=30)
        if errors:
            st.error("Data validation errors:")
            for err in errors:
                st.write(f"- {err}")
            return

        results = run_all_analyses(clean_df, cities[0], cities[1], cities[2])
        chart_paths = generate_charts(clean_df, cities[0], cities[1], cities[2], CHART_DIR, results=results)
        excel_path = export_excel_bundle(clean_df, results, OUTPUT_DIR / f"{run_label}_analysis.xlsx", chart_paths=chart_paths)
        word_path = export_word_report(
            "manual_selection",
            (cities[0], cities[1], cities[2]),
            results,
            chart_paths,
            OUTPUT_DIR / f"{run_label}_report.docx",
        )

        st.subheader("Part 1 - Descriptive")
        st.dataframe(results.descriptive.round(4), use_container_width=True)
        st.subheader("Part 1 - Price Frequency Table")
        st.dataframe(results.part1_price_frequency.round(4), use_container_width=True)
        st.subheader("Part 2 - Confidence Intervals")
        st.dataframe(results.confidence_intervals.round(4), use_container_width=True)
        st.subheader("Part 3 - One Sample")
        st.dataframe(results.one_sample_tests.round(4), use_container_width=True)
        st.subheader("Part 4 - Two Sample")
        st.dataframe(results.two_sample_tests.round(4), use_container_width=True)
        st.subheader("Part 5 - Regression")
        st.dataframe(results.regression_summary.round(4), use_container_width=True)
        st.subheader("Part 6 - ANOVA")
        st.dataframe(results.anova_table.round(4), use_container_width=True)
        st.dataframe(results.tukey_table, use_container_width=True)

        st.subheader("Charts")
        for chart in chart_paths:
            st.image(str(chart), caption=chart.name, use_container_width=True)

        st.subheader("5) Output Files")
        _section_guide_popover(6, "Outputs")
        _download_button_for_file(excel_path, "Download Excel Output", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        _download_button_for_file(word_path, "Download Word Report", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")


if __name__ == "__main__":
    main()
