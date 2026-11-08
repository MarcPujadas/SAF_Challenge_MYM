from __future__ import annotations

import hashlib
import math
import re
from dataclasses import replace
from datetime import date as date_type
from datetime import datetime, time, timedelta
from pathlib import Path

import pandas as pd

from app.config.resource_mapping import (
    normalize_resource_name,
    resolve_resource_mapping,
)
from app.database.database import get_connection, init_db
from app.database.historical_usage import (
    register_data_source,
    upsert_historical_usage,
)


BASE_DIR = Path(__file__).resolve().parents[1]
FILE_PATH = BASE_DIR / "data" / "local" / "saf-espais-2026-equips.xlsx"
GUIDED_ACTIVITIES_PATH = (
    BASE_DIR / "data" / "local" / "guided_activity_sessions.csv"
)
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "historical_occupancy.csv"
LEGACY_COLUMNS = [
    "space_id",
    "date",
    "weekday",
    "start_time",
    "reservations",
]


def _source_for_sheet(sheet_name: str) -> str:
    normalized = sheet_name.casefold()
    if "activitat" in normalized or "guided" in normalized:
        return "saf_guided_activities_2026"
    return "saf_reserves_2026"


def _is_named_historical_sheet(sheet_name: str) -> bool:
    normalized = sheet_name.casefold()
    return any(
        marker in normalized
        for marker in ("reserva", "reserve", "activitat", "guided")
    )


def _date_value(value) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        try:
            return date_type.fromisoformat(text).isoformat()
        except ValueError:
            return None
    parsed = pd.to_datetime(value, errors="coerce", dayfirst=True)
    if pd.isna(parsed):
        return None
    return parsed.strftime("%Y-%m-%d")


def _time_value(value) -> str | None:
    if pd.isna(value):
        return None
    if isinstance(value, time):
        return value.strftime("%H:%M")
    if isinstance(value, (int, float)):
        if not math.isfinite(float(value)) or not 0 <= float(value) < 1:
            return None
        seconds = round(float(value) * 24 * 60 * 60)
        return (datetime.min + timedelta(seconds=seconds)).strftime("%H:%M")
    text = str(value).strip()
    if not text:
        return None
    for time_format in ("%H:%M", "%H:%M:%S", "%H:%M:%S.%f"):
        try:
            return datetime.strptime(text, time_format).strftime("%H:%M")
        except ValueError:
            continue
    return text[:5]


def _numeric_count(value) -> tuple[int | float | None, str | None]:
    if pd.isna(value):
        return None, None
    raw_value = str(value)
    parsed = pd.to_numeric(value, errors="coerce")
    if pd.isna(parsed) or not math.isfinite(float(parsed)) or float(parsed) < 0:
        return None, raw_value
    numeric = float(parsed)
    if numeric.is_integer():
        return int(numeric), raw_value
    return numeric, raw_value


def _capacity_snapshots(connection, service_id, space_id, capacity_mode):
    if service_id is None or space_id is None:
        return None, None
    row = connection.execute(
        """
        SELECT
            service_spaces.person_capacity,
            service_spaces.reservation_capacity,
            spaces.capacity AS space_capacity
        FROM service_spaces
        LEFT JOIN spaces ON spaces.id = service_spaces.space_id
        WHERE service_spaces.service_id = ?
            AND service_spaces.space_id = ?
        """,
        (service_id, space_id),
    ).fetchone()
    if row is None:
        return None, None
    person_capacity = row["person_capacity"]
    if person_capacity is None and capacity_mode == "people":
        person_capacity = row["space_capacity"]
    return (
        person_capacity,
        row["reservation_capacity"],
    )


def _known_space_aliases(connection) -> dict[str, str]:
    candidates: dict[str, set[str]] = {}
    for row in connection.execute("SELECT id, name FROM spaces"):
        for value in (row["id"], row["name"]):
            normalized = normalize_resource_name(value)
            if normalized:
                candidates.setdefault(normalized, set()).add(row["id"])
    return {
        normalized: next(iter(space_ids))
        for normalized, space_ids in candidates.items()
        if len(space_ids) == 1
    }


def normalize_source_rows(
    frame: pd.DataFrame,
    *,
    sheet_name: str,
    source_id: str,
    source_checksum: str,
    connection,
) -> list[dict]:
    required = {"Recurs", "DataUs", "HoraInici", "Reserves"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(
            f"Missing required columns in {sheet_name}: "
            + ", ".join(sorted(missing))
        )

    known_space_aliases = _known_space_aliases(connection)
    rows = []
    for row_number, (_, row) in enumerate(frame.iterrows(), start=2):
        raw_resource_name = (
            None if pd.isna(row["Recurs"]) else str(row["Recurs"])
        )
        mapping = resolve_resource_mapping(raw_resource_name)
        if mapping.space_id is None and raw_resource_name is not None:
            existing_space_id = known_space_aliases.get(
                normalize_resource_name(raw_resource_name)
            )
            if existing_space_id is not None:
                mapping = replace(mapping, space_id=existing_space_id)
        date = _date_value(row["DataUs"])
        raw_count, raw_value = _numeric_count(row["Reserves"])
        capacity_people, capacity_units = _capacity_snapshots(
            connection,
            mapping.service_id,
            mapping.space_id,
            mapping.capacity_mode,
        )
        rows.append(
            {
                "source_id": source_id,
                "source_checksum": source_checksum,
                "source_record_key": f"{sheet_name}:row:{row_number}",
                "service_id": mapping.service_id,
                "space_id": mapping.space_id,
                "date": date,
                "weekday": (
                    int(pd.Timestamp(date).dayofweek)
                    if date is not None
                    else None
                ),
                "start_time": _time_value(row["HoraInici"]),
                "end_time": (
                    _time_value(row["HoraFi"])
                    if "HoraFi" in frame.columns
                    else None
                ),
                "raw_reservation_count": raw_count,
                "raw_reservation_value": raw_value,
                "people_count": None,
                "occupied_units": None,
                "capacity_people_snapshot": capacity_people,
                "capacity_units_snapshot": capacity_units,
                "occupancy_ratio": None,
                "raw_resource_name": raw_resource_name,
                "capacity_mode": mapping.capacity_mode,
                "mapping_status": mapping.mapping_status,
                "capacity_share": mapping.capacity_share,
            }
        )
    return rows


def normalize_guided_activity_rows(
    frame: pd.DataFrame,
    *,
    source_checksum: str,
    connection,
) -> list[dict]:
    if "date" not in frame.columns and "session_date" in frame.columns:
        frame = frame.rename(columns={"session_date": "date"})
    required = {
        "date",
        "start_time",
        "end_time",
        "room",
        "capacity",
        "peak_enrolled",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(
            "Missing required columns in guided activities: "
            + ", ".join(sorted(missing))
        )

    known_space_aliases = _known_space_aliases(connection)
    rows = []
    for row_number, (_, row) in enumerate(frame.iterrows(), start=2):
        room = None if pd.isna(row["room"]) else str(row["room"]).strip()
        raw_resource_name = room
        mapping = resolve_resource_mapping(
            f"{room} - Activitats dirigides"
            if room
            else "Activitats dirigides - ubicació desconeguda"
        )
        if mapping.space_id is None and room:
            normalized_room = normalize_resource_name(room)
            existing_space_id = known_space_aliases.get(
                normalized_room
            )
            if existing_space_id is None and re.fullmatch(
                r"sala\s+\d+",
                normalized_room,
            ):
                existing_space_id = known_space_aliases.get(
                    normalize_resource_name(
                        f"sales activitats dirigides {room}"
                    )
                )
            if existing_space_id is not None:
                mapping = replace(mapping, space_id=existing_space_id)
        location_is_mapped = (
            mapping.service_id == "guided-activities"
            and mapping.mapping_status == "mapped"
        )
        mapping = replace(
            mapping,
            service_id="guided-activities",
            mapping_status=(
                "mapped" if location_is_mapped else "manual_review"
            ),
            capacity_mode="people",
        )
        date = _date_value(row["date"])
        people_count, _ = _numeric_count(row["peak_enrolled"])
        capacity_people, _ = _numeric_count(row["capacity"])
        occupancy_percent, _ = _numeric_count(
            row.get("peak_occupancy_pct")
        )
        session_id = row.get("session_id")
        source_record_key = (
            str(session_id)
            if not pd.isna(session_id)
            else f"session-row:{row_number}"
        )
        rows.append(
            {
                "source_id": "saf_guided_activities_2026",
                "source_checksum": source_checksum,
                "source_record_key": source_record_key,
                "service_id": mapping.service_id,
                "space_id": mapping.space_id,
                "date": date,
                "weekday": (
                    int(pd.Timestamp(date).dayofweek)
                    if date is not None
                    else None
                ),
                "start_time": _time_value(row["start_time"]),
                "end_time": _time_value(row["end_time"]),
                "raw_reservation_count": None,
                "raw_reservation_value": None,
                "people_count": people_count,
                "occupied_units": None,
                "capacity_people_snapshot": capacity_people,
                "capacity_units_snapshot": None,
                "occupancy_ratio": (
                    round(
                        float(people_count) / float(capacity_people),
                        4,
                    )
                    if (
                        people_count is not None
                        and capacity_people is not None
                        and float(capacity_people) > 0
                    )
                    else float(occupancy_percent) / 100
                    if occupancy_percent is not None
                    else None
                ),
                "raw_resource_name": raw_resource_name,
                "capacity_mode": "people",
                "mapping_status": mapping.mapping_status,
                "capacity_share": mapping.capacity_share,
            }
        )
    return rows


def _current_frame_period(rows: list[dict]) -> tuple[str | None, str | None]:
    dates = [row["date"] for row in rows if row["date"] is not None]
    return (min(dates), max(dates)) if dates else (None, None)


def _legacy_occupancy_frame(rows: list[dict]) -> pd.DataFrame:
    mapped_rows = [
        row
        for row in rows
        if row["mapping_status"] == "mapped"
        and row["space_id"] is not None
        and row["date"] is not None
        and row["start_time"] is not None
        and row["raw_reservation_count"] is not None
    ]
    if not mapped_rows:
        return pd.DataFrame(columns=LEGACY_COLUMNS)

    frame = pd.DataFrame(mapped_rows)
    frame = frame[
        frame["source_id"] == "saf_reserves_2026"
    ].copy()
    if frame.empty:
        return pd.DataFrame(columns=LEGACY_COLUMNS)

    grouped = (
        frame.groupby(
            [
                "source_id",
                "service_id",
                "space_id",
                "date",
                "weekday",
                "start_time",
                "raw_resource_name",
                "capacity_mode",
                "mapping_status",
            ],
            as_index=False,
        )["raw_reservation_count"]
        .sum()
    )
    grouped["reservations"] = grouped["raw_reservation_count"]
    return grouped[
        LEGACY_COLUMNS
        + [
            "source_id",
            "service_id",
            "raw_resource_name",
            "raw_reservation_count",
            "capacity_mode",
            "mapping_status",
        ]
    ]


def _write_legacy_csv(frame: pd.DataFrame) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = OUTPUT_PATH.with_suffix(".csv.tmp")
    frame.to_csv(temporary_path, index=False, encoding="utf-8")
    temporary_path.replace(OUTPUT_PATH)


def process_workbook(file_path: Path = FILE_PATH) -> dict:
    if not file_path.exists():
        raise FileNotFoundError(
            f"No s'ha trobat el dataset privat: {file_path}"
        )

    checksum = hashlib.sha256(file_path.read_bytes()).hexdigest()
    workbook = pd.ExcelFile(file_path)
    frames = {
        sheet_name: pd.read_excel(workbook, sheet_name=sheet_name)
        for sheet_name in workbook.sheet_names
    }
    has_individual_reservations = any(
        sheet_name.strip().casefold() == "reserves"
        and {"Recurs", "DataUs", "HoraInici"}.issubset(frame.columns)
        for sheet_name, frame in frames.items()
    )
    source_rows_by_id: dict[str, list[dict]] = {}

    with get_connection() as connection:
        for sheet_name, frame in frames.items():
            required_columns = {
                "Recurs",
                "DataUs",
                "HoraInici",
                "Reserves",
            }
            if (
                has_individual_reservations
                and "reserves per franja" in sheet_name.casefold()
            ):
                continue
            if (
                "reserves" in sheet_name.casefold()
                and "Recurs" in frame.columns
                and "DataUs" in frame.columns
                and "HoraInici" in frame.columns
                and "Reserves" not in frame.columns
            ):
                frame = frame.copy()
                frame["Reserves"] = 1
            if not required_columns.issubset(frame.columns):
                if (
                    _is_named_historical_sheet(sheet_name)
                    and not (
                        "activitat" in sheet_name.casefold()
                        or "guided" in sheet_name.casefold()
                    )
                ):
                    missing = required_columns - set(frame.columns)
                    raise ValueError(
                        f"Missing required columns in historical sheet "
                        f"{sheet_name}: {', '.join(sorted(missing))}"
                    )
                continue
            source_id = _source_for_sheet(sheet_name)
            rows = normalize_source_rows(
                frame,
                sheet_name=sheet_name,
                source_id=source_id,
                source_checksum=checksum,
                connection=connection,
            )
            source_rows_by_id.setdefault(source_id, []).extend(rows)

        if not source_rows_by_id:
            raise ValueError(
                "No workbook sheet has the required historical columns."
            )

        source_definitions = {
            "saf_reserves_2026": (
                "saf_reserves",
                "SAF reserves 2026",
            ),
            "saf_guided_activities_2026": (
                "saf_guided_activities",
                "SAF guided activities 2026",
            ),
        }
        for source_id, (source_type, label) in source_definitions.items():
            rows = source_rows_by_id.get(source_id, [])
            if source_id == "saf_guided_activities_2026" and not rows:
                continue
            period_from, period_to = _current_frame_period(rows)
            register_data_source(
                connection,
                source_id=source_id,
                source_type=source_type,
                label=label,
                period_from=period_from,
                period_to=period_to,
                checksum=checksum,
            )
            if rows:
                upsert_historical_usage(connection, rows)

    all_rows = [
        row
        for rows in source_rows_by_id.values()
        for row in rows
    ]
    legacy_frame = _legacy_occupancy_frame(all_rows)
    _write_legacy_csv(legacy_frame)

    return {
        "source_checksum": checksum,
        "raw_rows": len(all_rows),
        "mapped_rows": sum(
            row["mapping_status"] == "mapped" for row in all_rows
        ),
        "manual_review_rows": sum(
            row["mapping_status"] == "manual_review" for row in all_rows
        ),
        "ignored_rows": sum(
            row["mapping_status"] == "ignored" for row in all_rows
        ),
        "legacy_csv_rows": len(legacy_frame),
    }


def main():
    init_db()
    if not GUIDED_ACTIVITIES_PATH.exists():
        raise FileNotFoundError(
            "No s'ha trobat el dataset privat d'activitats dirigides: "
            f"{GUIDED_ACTIVITIES_PATH}"
        )
    summary = process_workbook()
    guided_checksum = hashlib.sha256(
        GUIDED_ACTIVITIES_PATH.read_bytes()
    ).hexdigest()
    guided_frame = pd.read_csv(GUIDED_ACTIVITIES_PATH)
    with get_connection() as connection:
        guided_rows = normalize_guided_activity_rows(
            guided_frame,
            source_checksum=guided_checksum,
            connection=connection,
        )
        period_from, period_to = _current_frame_period(guided_rows)
        register_data_source(
            connection,
            source_id="saf_guided_activities_2026",
            source_type="saf_guided_activities",
            label="SAF guided activities 2026",
            period_from=period_from,
            period_to=period_to,
            checksum=guided_checksum,
        )
        upsert_historical_usage(connection, guided_rows)
    summary["guided_activity_rows"] = len(guided_rows)
    summary["guided_activity_mapped_rows"] = sum(
        row["mapping_status"] == "mapped" for row in guided_rows
    )
    summary["guided_activity_manual_review_rows"] = sum(
        row["mapping_status"] == "manual_review"
        for row in guided_rows
    )
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
