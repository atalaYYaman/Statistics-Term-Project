# Excel veya manuel giriş için beklenen kolon sırası ve isimleri.

REQUIRED_COLUMNS = [
    "Price",
    "Area",
    "Rooms",
    "BuildingAge",
    "FloorNumber",
    "NumberOfFloors",
    "HeatingType",
    "District",
    "City",
    "SourceURL",
]

# normalize_dataset içinde sayıya çevrilecek kolonlar; geçersiz değer NaN olur.

NUMERIC_COLUMNS = [
    "Price",
    "Area",
    "Rooms",
    "BuildingAge",
    "FloorNumber",
    "NumberOfFloors",
]
