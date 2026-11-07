import pandas as pd
import re
import unicodedata

FILE_PATH = "data/raw/saf-espais-2026-equips.xlsx"


def normalize_text(text):
    text = str(text).lower()

    text = unicodedata.normalize("NFD", text)
    text = "".join(
        c for c in text
        if unicodedata.category(c) != "Mn"
    )

    text = re.sub(r"\([^)]*\)", "", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def detect_space_id(resource):
    normalized = normalize_text(resource)

    # FITNESS
    if "sala fitnes" in normalized:
        return "sala-fitnes-sala-cardio"

    # PADEL
    if "padel/padbol" in normalized:
        match = re.search(r"pista\s+(\d+)", normalized)

        if match:
            number = match.group(1)
            return f"pistes-de-padel-pista-{number}"

    # TENNIS
    if "tennis/pikleball" in normalized:
        match = re.search(r"pista\s+(\d+)", normalized)

        if match:
            number = match.group(1)
            return f"tennis-tennis-{number}"

    # ESQUAIX
    if "esquaix/c.soccer" in normalized:
        match = re.search(r"pista\s+(\d+)", normalized)

        if match:
            number = match.group(1)
            return f"esquaix-esquaix-{number}"

    # FUTBOL 7
    if "futbol 7" in normalized:
        match = re.search(r"camp\s+(\d+)", normalized)

        if match:
            number = match.group(1)
            return f"futbol-7-camp-{number}"

    # PISCINA 25 M - CARRERS
    if "p. 25m" in normalized:
        match = re.search(r"c/(\d+)", normalized)

        if match:
            number = match.group(1)
            return f"piscina-25-metres-carrer-{number}"

    # PISCINA 16 M
    if "p. 16m" in normalized:
        return "piscina-de-16-metres"

    # ROCÒDROM
    if "rocodrom exterior" in normalized:
        return "rocodrom-exterior"

    if "rocodrom interior" in normalized:
        return "rocodrom-interior"

    # BARBELL
    if "espai barbell" in normalized:
        return "espai-barbell"

    # CAL·LISTÈNIA
    if "cal.listenia" in normalized or "calistenia" in normalized:
        return "zona-cal-listenia"

    # VÒLEI PLATJA
    if "volei platja" in normalized:
        return "voleibol-platja"

    # BÀSQUET EXTERIOR
    if "basquet exterior" in normalized or "basquet - pista exterior" in normalized:
        return "basquet-exterior"

    # FUTBOL SALA EXTERIOR
    if "futbol sala 1" in normalized:
        return "futbol-sala-extrerior"

    # ACTIVITATS DIRIGIDES
    if "sala 1- ritmes" in normalized:
        return "sales-activitats-dirigides-sala-1"

    if "sala 2- ritmes" in normalized:
        return "sales-activitats-dirigides-sala-2"

    if "sala 3- zen" in normalized:
        return "sales-activitats-dirigides-sala-3"

    # BOXTRAINING
    if "sala 6- boxtraining" in normalized:
        return "sala-boxtraining-esquaix-1"

    return None


df = pd.read_excel(
    FILE_PATH,
    sheet_name="Reserves"
)

resources = (
    df["Recurs"]
    .dropna()
    .drop_duplicates()
    .sort_values()
)

mapped = []
unmapped = []

for resource in resources:

    space_id = detect_space_id(resource)

    if space_id:
        mapped.append(
            {
                "resource": resource,
                "space_id": space_id
            }
        )
    else:
        unmapped.append(resource)


print("=" * 70)
print("RECURSOS MAPEJATS")
print("=" * 70)

for item in mapped:
    print(
        f"{item['resource']} "
        f"--> {item['space_id']}"
    )


print("\n")
print("=" * 70)
print("RECURSOS ENCARA NO MAPEJATS")
print("=" * 70)

for resource in unmapped:
    print(resource)


print("\nRESUM")
print("Mapejats:", len(mapped))
print("No mapejats:", len(unmapped))