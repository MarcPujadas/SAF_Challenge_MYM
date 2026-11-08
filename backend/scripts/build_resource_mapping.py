from pathlib import Path

import pandas as pd

from app.config.resource_mapping import (
    documented_subdivisions,
    normalize_resource_name,
    resolve_resource_mapping,
)


BASE_DIR = Path(__file__).resolve().parents[1]
FILE_PATH = BASE_DIR / "data" / "local" / "saf-espais-2026-equips.xlsx"


def normalize_text(text):
    """Compatibility alias for older script callers."""
    return normalize_resource_name(text)


def build_mapping(resource):
    return resolve_resource_mapping(resource).as_dict()


def detect_space_id(resource):
    """Compatibility helper: unknown resources remain unmapped, not discarded."""
    result = resolve_resource_mapping(resource)
    return result.space_id if result.mapping_status == "mapped" else None


def main():
    if not FILE_PATH.exists():
        raise FileNotFoundError(
            f"No s'ha trobat el dataset privat: {FILE_PATH}"
        )

    workbook = pd.ExcelFile(FILE_PATH)
    resource_frames = []
    for sheet_name in workbook.sheet_names:
        frame = pd.read_excel(workbook, sheet_name=sheet_name)
        if "Recurs" in frame.columns:
            resource_frames.append(frame["Recurs"])

    if not resource_frames:
        raise ValueError("No s'ha trobat cap columna 'Recurs' al workbook.")

    resources = pd.concat(resource_frames, ignore_index=True).dropna().unique()
    mapped = []
    for raw_resource in sorted(resources, key=str):
        mapped.append(build_mapping(raw_resource))

    mapping_frame = pd.DataFrame(mapped)
    print("RESUM DE MAPPINGS")
    print(mapping_frame["mapping_status"].value_counts().to_string())
    print()
    print("RECURSOS PER REVISAR")
    for item in mapped:
        if item["mapping_status"] != "mapped":
            print(
                f"{item['mapping_status']}: "
                f"{item['raw_resource_name']}"
            )
    print()
    print("SUBDIVISIONS EXPLÍCITES")
    for item in documented_subdivisions():
        print(item)


if __name__ == "__main__":
    main()
