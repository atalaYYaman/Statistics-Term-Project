from __future__ import annotations

# Öğrenci başına üç şehir atamasını okur; arayüzdeki şehir seçenekleri buradan türetilir.

from pathlib import Path

import pandas as pd


def load_city_assignments(csv_path: str | Path) -> pd.DataFrame:
    # student_no ve city1–city3 beklenir; aynı öğrenci için yalnızca ilk satır kalır.
    df = pd.read_csv(csv_path, dtype={"student_no": str})
    expected = {"student_no", "city1", "city2", "city3"}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"City assignment file is missing columns: {sorted(missing)}")

    return df.drop_duplicates(subset=["student_no"], keep="first").reset_index(drop=True)
