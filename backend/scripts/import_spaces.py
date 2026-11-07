import sqlite3
import unicodedata
import re

import pandas as pd


CSV_PATH = "data/raw/saf-espais-2026-equips(Espais).csv"
DB_PATH = "app/database/safhack.db"


def slugify(text):
    text = str(text).lower()

    text = unicodedata.normalize("NFD", text)
    text = "".join(
        char for char in text
        if unicodedata.category(char) != "Mn"
    )

    text = re.sub(r"[^a-z0-9]+", "-", text)

    return text.strip("-")


def get_space_type(name):
    name = name.lower()

    if "fitness" in name or "fitnes" in name or "cardio" in name:
        return "fitness"

    if "piscina" in name:
        return "pool"

    if (
        "pàdel" in name
        or "padel" in name
        or "tennis" in name
        or "esquaix" in name
        or "futbol" in name
        or "bàsquet" in name
        or "voleibol" in name
        or "poliesportiu" in name
    ):
        return "court"

    if "rocòdrom" in name or "cal·listènia" in name:
        return "outdoor"

    if "activitats dirigides" in name:
        return "activity_room"

    return "other"


df = pd.read_csv(
    CSV_PATH,
    encoding="cp1252",
    sep=";"
)

# Eliminar duplicats exactes
duplicates = df[df.duplicated()]

if not duplicates.empty:
    print("DUPLICATS DETECTATS:")
    print(duplicates.to_string(index=False))
    print()

df = df.drop_duplicates()


connection = sqlite3.connect(DB_PATH)

cursor = connection.cursor()


for _, row in df.iterrows():

    espai = str(row["Espai"]).strip()

    if pd.notna(row["Subespai"]):
        subespai = str(row["Subespai"]).strip()
    else:
        subespai = None

    capacity = int(row["Aforament"])

    if subespai:
        space_id = slugify(f"{espai}-{subespai}")
        name = f"{espai} - {subespai}"
    else:
        space_id = slugify(espai)
        name = espai

    space_type = get_space_type(espai)

    cursor.execute(
        """
        INSERT OR REPLACE INTO spaces (
            id,
            name,
            type,
            capacity,
            reservable
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            space_id,
            name,
            space_type,
            capacity,
            1
        )
    )

    print(
        f"{space_id:45} "
        f"{capacity:3} persones   "
        f"{space_type}"
    )


connection.commit()
connection.close()

print()
print(f"Importació completada: {len(df)} espais.")