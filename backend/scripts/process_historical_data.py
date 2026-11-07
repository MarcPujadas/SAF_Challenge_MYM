import pandas as pd

from build_resource_mapping import detect_space_id

FILE_PATH = "data/raw/saf-espais-2026-equips.xlsx"
OUTPUT_PATH = "data/processed/historical_occupancy.csv"


df = pd.read_excel(
    FILE_PATH,
    sheet_name="Reserves per franja"
)

print("Registres originals:", len(df))

df["space_id"] = df["Recurs"].apply(detect_space_id)

mapped = df[df["space_id"].notna()].copy()

print("Registres mapats:", len(mapped))
print("Registres descartats:", len(df) - len(mapped))

mapped["DataUs"] = pd.to_datetime(mapped["DataUs"])

mapped["date"] = mapped["DataUs"].dt.strftime("%Y-%m-%d")
mapped["weekday"] = mapped["DataUs"].dt.day_of_week

mapped["start_time"] = mapped["HoraInici"].astype(str).str[:5]

result = mapped[
    [
        "space_id",
        "date",
        "weekday",
        "start_time",
        "Reserves"
    ]
].rename(
    columns={
        "Reserves": "reservations"
    }
)

result = (
    result
    .groupby(
        [
            "space_id",
            "date",
            "weekday",
            "start_time"
        ],
        as_index=False
    )
    ["reservations"]
    .sum()
)

result.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8"
)

print()
print("Fitxer creat:")
print(OUTPUT_PATH)

print()
print("Files finals:", len(result))

print()
print(result.head(20).to_string(index=False))