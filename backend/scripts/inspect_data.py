import pandas as pd

FILE_PATH = "data/raw/saf-espais-2026-equips.xlsx"

excel = pd.ExcelFile(FILE_PATH)

print("FULLS:")
print(excel.sheet_names)

for sheet in excel.sheet_names:
    print("\n" + "=" * 60)
    print(f"FULL: {sheet}")
    print("=" * 60)

    df = pd.read_excel(
        FILE_PATH,
        sheet_name=sheet
    )

    print("\nCOLUMNES:")
    print(df.columns.tolist())

    print("\nDIMENSIONS:")
    print(df.shape)

    print("\nPRIMERES FILES:")
    print(df.head().to_string(index=False))