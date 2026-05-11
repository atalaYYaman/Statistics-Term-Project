from __future__ import annotations

# Arayüz olmadan uçtan uca doğrulama; sahte üç şehir verisi, grafik ve Excel/Word çıktıları.

from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.charts import generate_charts
from src.analysis.statistics import run_all_analyses
from src.reporting.excel_export import export_excel_bundle
from src.reporting.word_report import export_word_report
from src.validation import normalize_dataset, validate_dataset


def build_fake_data(city: str, n: int, seed: int) -> pd.DataFrame:
    # Doğrulamayı geçecek şekilde her şehir için yeterli sayıda sahte ilan satırı üretir.
    rng = np.random.default_rng(seed)
    area = rng.normal(loc=120, scale=25, size=n).clip(55, 240)
    price = 450_000 + area * rng.normal(14_000, 1_500, size=n) + rng.normal(0, 120_000, size=n)
    return pd.DataFrame(
        {
            "Price": price.round(0),
            "Area": area.round(1),
            "Rooms": rng.integers(1, 6, size=n),
            "BuildingAge": rng.integers(0, 35, size=n),
            "FloorNumber": rng.integers(0, 15, size=n),
            "NumberOfFloors": rng.integers(3, 20, size=n),
            "HeatingType": np.where(rng.random(n) > 0.35, "Dogalgaz", "Merkezi"),
            "District": [f"District_{i%7}" for i in range(n)],
            "City": city,
            "SourceURL": "manual://smoke-test",
        }
    )


def main() -> None:
    # Sabit şehir adları ve tohumlar ile tekrarlanabilir test verisi.
    c1, c2, c3 = "Adana", "Ankara", "Gaziantep"
    raw_df = pd.concat(
        [build_fake_data(c1, 32, 1), build_fake_data(c2, 31, 2), build_fake_data(c3, 30, 3)],
        ignore_index=True,
    )
    clean_df = normalize_dataset(raw_df)
    errors = validate_dataset(clean_df, [c1, c2, c3], min_per_city=30)
    if errors:
        raise RuntimeError(f"Validation failed: {errors}")

    results = run_all_analyses(clean_df, c1, c2, c3)
    charts = generate_charts(clean_df, c1, c2, c3, Path("outputs/charts"), results=results)
    export_excel_bundle(clean_df, results, "outputs/smoke_analysis.xlsx", chart_paths=charts)
    export_word_report("23100121023", (c1, c2, c3), results, charts, "outputs/smoke_report.docx")
    print("Smoke test completed successfully.")


if __name__ == "__main__":
    main()
