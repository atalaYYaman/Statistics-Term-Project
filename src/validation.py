from __future__ import annotations

# Kolon düzeni ve tipleri düzenler; analiz öncesi şehir başına yeterli kayıt kontrolü yapar.

import pandas as pd

from src.schema import NUMERIC_COLUMNS, REQUIRED_COLUMNS


def normalize_dataset(df: pd.DataFrame) -> pd.DataFrame:
    # Şemaya göre hizala; boş metinleri NA yap; sayıları dönüştür; metinleri kırp.
    out = df.copy()

    for col in REQUIRED_COLUMNS:
        if col not in out.columns:
            out[col] = pd.NA

    out = out[REQUIRED_COLUMNS]
    out = out.replace(r"^\s*$", pd.NA, regex=True)

    for col in NUMERIC_COLUMNS:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    for col in ("HeatingType", "District", "City", "SourceURL"):
        out[col] = out[col].astype("string").str.strip()

    return out


def validate_dataset(df: pd.DataFrame, assigned_cities: list[str], min_per_city: int = 30) -> list[str]:
    # Kurallar sağlanmazsa analizi durduracak Türkçe hata mesajları döner.
    errors: list[str] = []
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        errors.append(f"Eksik sutunlar: {', '.join(missing_cols)}")
        return errors

    null_ratio = df[["Price", "Area", "City"]].isna().mean()
    for key, value in null_ratio.items():
        if value > 0.2:
            errors.append(f"{key} kolonunda eksik oran yuksek (%{value*100:.1f}).")

    non_positive = (df["Price"] <= 0).sum(skipna=True)
    if non_positive:
        errors.append(f"{non_positive} kayitta Price <= 0 bulundu.")

    non_positive_area = (df["Area"] <= 0).sum(skipna=True)
    if non_positive_area:
        errors.append(f"{non_positive_area} kayitta Area <= 0 bulundu.")

    city_counts = (
        df.dropna(subset=["City"])
        .groupby("City", as_index=False)
        .size()
        .rename(columns={"size": "count"})
    )
    for city in assigned_cities:
        count_row = city_counts.loc[city_counts["City"] == city, "count"]
        count = int(count_row.iloc[0]) if not count_row.empty else 0
        if count < min_per_city:
            errors.append(f"{city} icin en az {min_per_city} kayit gerekir. Mevcut: {count}")

    return errors
