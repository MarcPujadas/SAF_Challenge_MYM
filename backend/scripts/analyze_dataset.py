import pandas as pd

FILE_PATH = "data/raw/saf-espais-2026-equips.xlsx"

# RESERVES
reservations = pd.read_excel(
    FILE_PATH,
    sheet_name="Reserves"
)

print("=" * 60)
print("RESERVES")
print("=" * 60)

print("\nRANG DE DATES:")
print("Primera:", reservations["DataUs"].min())
print("Última:", reservations["DataUs"].max())

print("\nNOMBRE D'ESPAIS:")
print(reservations["EspaiPare"].nunique())

print("\nESPAIS:")
for space in sorted(reservations["EspaiPare"].dropna().unique()):
    print(space)

# ACTIVITATS DIRIGIDES
activities = pd.read_excel(
    FILE_PATH,
    sheet_name="Activitats dirigides"
)

print("\n" + "=" * 60)
print("ACTIVITATS DIRIGIDES")
print("=" * 60)

print("\nRANG DE DATES:")
print("Primera:", activities["DataInscripcio"].min())
print("Última:", activities["DataInscripcio"].max())

print("\nNOMBRE D'ACTIVITATS:")
print(activities["Activitat"].nunique())

print("\nACTIVITATS:")
for activity in sorted(activities["Activitat"].dropna().unique()):
    print(activity)