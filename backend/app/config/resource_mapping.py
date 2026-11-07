from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

from app.config.service_spaces import SERVICE_SPACE_BY_KEY


MappingStatus = Literal["mapped", "manual_review", "ignored"]
HistoricalCapacityMode = Literal["people", "resource_units", "unknown"]

IGNORED_RESOURCE_ALIASES = frozenset(
    {
        "total",
        "total general",
        "grand total",
    }
)


@dataclass(frozen=True)
class ResourceMappingResult:
    service_id: str | None
    space_id: str | None
    mapping_status: MappingStatus
    capacity_mode: HistoricalCapacityMode
    capacity_share: float | None
    raw_resource_name: str | None

    def as_dict(self) -> dict:
        return {
            "service_id": self.service_id,
            "space_id": self.space_id,
            "mapping_status": self.mapping_status,
            "capacity_mode": self.capacity_mode,
            "capacity_share": self.capacity_share,
            "raw_resource_name": self.raw_resource_name,
        }


@dataclass(frozen=True)
class ResourceAliasRule:
    service_id: str
    pattern: str
    space_id_template: str


RESOURCE_ALIAS_REGISTRY = (
    ResourceAliasRule(
        "fitness",
        r"\b(?:sala\s+)?fitnes(?:s)?\b",
        "sala-fitnes-sala-cardio",
    ),
    # Explicit normalization for Padel Pista 2, which can be absent from
    # the source spaces sheet but is present in normalized SAF history.
    ResourceAliasRule(
        "padel",
        r"\b(?:padel|padbol)\b.*\bpista\s+2\b",
        "pistes-de-padel-pista-2",
    ),
    ResourceAliasRule(
        "padel",
        r"\b(?:padel|padbol)\b.*\bpista\s+(?P<number>\d+)\b",
        "pistes-de-padel-pista-{number}",
    ),
    ResourceAliasRule(
        "tennis",
        r"\b(?:tennis|pickleball|pikleball)\b.*\bpista\s+(?P<number>\d+)\b",
        "tennis-tennis-{number}",
    ),
    ResourceAliasRule(
        "squash",
        r"\b(?:esquaix|squash|c\s+soccer)\b.*\bpista\s+(?P<number>\d+)\b",
        "esquaix-esquaix-{number}",
    ),
    ResourceAliasRule(
        "football",
        r"\b(?:futbol|football)\s+7\b.*\bcamps?\s+(?P<number>\d+)\b",
        "futbol-7-camp-{number}",
    ),
    ResourceAliasRule(
        "pool-25m",
        r"\b(?:p\s+25m|piscina\s+(?:de\s+)?25\s*m?)\b.*"
        r"\b(?:c|carrer|carril)\s+(?P<number>\d+)\b",
        "piscina-25-metres-carrer-{number}",
    ),
    ResourceAliasRule(
        "pool-16m",
        r"\b(?:p\s+16m|piscina\s+(?:de\s+)?16\s*m?)\b",
        "piscina-de-16-metres",
    ),
    ResourceAliasRule(
        "guided-activities",
        r"\bsala\s+(?P<number>\d+)\b.*"
        r"\b(?:activitats\s+dirigides|ritmes|zen)\b",
        "sales-activitats-dirigides-sala-{number}",
    ),
)

RESOURCE_SERVICE_HINTS = (
    (r"\b(?:padel|padbol)\b", "padel"),
    (r"\b(?:tennis|pickleball|pikleball)\b", "tennis"),
    (r"\b(?:esquaix|squash|c\s+soccer)\b", "squash"),
    (r"\b(?:futbol|football)\s+7\b", "football"),
    (r"\b(?:p\s+25m|piscina\s+(?:de\s+)?25\s*m?)\b", "pool-25m"),
    (r"\b(?:p\s+16m|piscina\s+(?:de\s+)?16\s*m?)\b", "pool-16m"),
    (r"\b(?:activitats\s+dirigides|ritmes|zen)\b", "guided-activities"),
    (r"\b(?:sala\s+)?fitnes(?:s)?\b", "fitness"),
)

RESOURCE_HIERARCHY = {
    service_id: tuple(
        mapping.space_id
        for mapping in SERVICE_SPACE_BY_KEY.values()
        if mapping.service_id == service_id
    )
    for service_id in dict.fromkeys(
        mapping.service_id for mapping in SERVICE_SPACE_BY_KEY.values()
    )
}


def normalize_resource_name(value: object) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFD", text.casefold())
    text = "".join(
        character
        for character in text
        if unicodedata.category(character) != "Mn"
    )
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _mapping_for(service_id: str, space_id: str, raw_name: object):
    resource = SERVICE_SPACE_BY_KEY.get((service_id, space_id))
    if resource is None:
        return None
    return ResourceMappingResult(
        service_id=service_id,
        space_id=space_id,
        mapping_status="mapped",
        capacity_mode=resource.capacity_mode,
        capacity_share=1.0,
        raw_resource_name=(
            None if raw_name is None else str(raw_name)
        ),
    )


def resolve_resource_mapping(raw_resource_name: object) -> ResourceMappingResult:
    normalized = normalize_resource_name(raw_resource_name)
    raw_name = (
        None
        if raw_resource_name is None
        else str(raw_resource_name)
    )

    if not normalized:
        return ResourceMappingResult(
            None, None, "ignored", "unknown", None, raw_name
        )
    if normalized in IGNORED_RESOURCE_ALIASES:
        return ResourceMappingResult(
            None, None, "ignored", "unknown", None, raw_name
        )

    is_football_subdivision = (
        "futbol 7" in normalized or "football 7" in normalized
    ) and re.search(r"\b(mitja|mig|half|1 2)\b", normalized)
    if not is_football_subdivision:
        for rule in RESOURCE_ALIAS_REGISTRY:
            match = re.search(rule.pattern, normalized)
            if match is None:
                continue
            space_id = rule.space_id_template.format(**match.groupdict())
            mapped = _mapping_for(
                rule.service_id,
                space_id,
                raw_resource_name,
            )
            if mapped is not None:
                return mapped

    service_id = next(
        (
            candidate_service_id
            for pattern, candidate_service_id in RESOURCE_SERVICE_HINTS
            if re.search(pattern, normalized)
        ),
        None,
    )
    return ResourceMappingResult(
        service_id, None, "manual_review", "unknown", None, raw_name
    )


def documented_subdivisions() -> list[dict[str, str]]:
    """Return only explicit resource subdivisions; none are validated yet."""
    return []
