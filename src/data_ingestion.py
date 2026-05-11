from __future__ import annotations

# Boş çalışma tablosu oluşturma ve yüklenen Excel baytlarını okuma.

from io import BytesIO

import pandas as pd

from src.schema import REQUIRED_COLUMNS


def build_empty_dataframe() -> pd.DataFrame:
    # Başlangıçta satır yok; doğru kolonlar concat ile güvenli kayıt eklemek için hazır.
    return pd.DataFrame(columns=REQUIRED_COLUMNS)


def load_uploaded_excel(file_bytes: bytes) -> pd.DataFrame:
    # İlk okuma; kolon hizası ve tipler normalize_dataset ile yapılır.
    return pd.read_excel(BytesIO(file_bytes))
