import pandas as pd

FILE_PATH = "data/raw/saf-espais-2026-equips.xlsx"

df = pd.read_excel(
    FILE_PATH,
    sheet_name="Reserves"
)

print("=" * 70)
print("RECURSOS ÚNICS")
print("=" * 70)

print("Nombre total:", df["Recurs"].nunique())

keywords = [
    "FIT",
    "CARDIO",
    "PISC",
    "PADEL",
    "PÀDEL",
    "TENNIS",
    "ESQUAIX",
    "FUTBOL",
    "POLI",
    "BARBELL",
    "ROC",
]

for keyword in keywords:

    print("\n" + "=" * 70)
    print(f"RESULTATS PER: {keyword}")
    print("=" * 70)

    results = (
        df[df["Recurs"].str.contains(
            keyword,
            case=False,
            na=False
        )]
        [["EspaiPare", "Recurs"]]
        .drop_duplicates()
        .sort_values(["EspaiPare", "Recurs"])
    )

    if results.empty:
        print("Cap resultat")
    else:
        print(results.to_string(index=False))