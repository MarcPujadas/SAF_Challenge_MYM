from __future__ import annotations

from dataclasses import dataclass


GENERAL_SLOT_DURATION_MINUTES = 60
STANDARD_SLOT_DURATION_MINUTES = 75


@dataclass(frozen=True)
class ServiceConfig:
    service_id: str
    name: str
    description: str
    space_id: str
    search_phrases: tuple[str, ...]
    slot_duration_minutes: int = GENERAL_SLOT_DURATION_MINUTES


SERVICES = (
    ServiceConfig(
        "fitness",
        "Fitness",
        "Sala de fitness i cardio",
        "sala-fitnes-sala-cardio",
        ("fitness", "fitnes"),
        STANDARD_SLOT_DURATION_MINUTES,
    ),
    ServiceConfig(
        "pool-25m",
        "Piscina 25 m",
        "Piscina de 25 metres",
        "piscina-25-metres-carrer-1",
        (
            "piscina de 25",
            "pool de 25",
            "pool 25",
            "piscina 25",
            "pool",
            "piscina",
            "swimming pool",
            "natacio",
        ),
    ),
    ServiceConfig(
        "pool-16m",
        "Piscina 16 m",
        "Piscina de 16 metres",
        "piscina-de-16-metres",
        ("piscina de 16", "pool de 16", "pool 16", "piscina 16"),
    ),
    ServiceConfig(
        "padel",
        "Pàdel",
        "Pistes de pàdel",
        "pistes-de-padel-pista-1",
        ("padel",),
        STANDARD_SLOT_DURATION_MINUTES,
    ),
    ServiceConfig(
        "tennis",
        "Tennis",
        "Pistes de tennis",
        "tennis-tennis-1",
        ("tennis", "tenis"),
        STANDARD_SLOT_DURATION_MINUTES,
    ),
    ServiceConfig(
        "squash",
        "Esquaix",
        "Pistes d'esquaix",
        "esquaix-esquaix-2",
        ("esquaix", "squash"),
        STANDARD_SLOT_DURATION_MINUTES,
    ),
    ServiceConfig(
        "football",
        "Futbol",
        "Camps de futbol",
        "futbol-7-camp-1",
        ("futbol", "football"),
    ),
    ServiceConfig(
        "guided-activities",
        "Activitats dirigides",
        "Sales d'activitats dirigides",
        "sales-activitats-dirigides-sala-1",
        (
            "activitats dirigides",
            "activitat dirigida",
            "guided activities",
            "clases dirigidas",
            "clase dirigida",
        ),
    ),
)

SERVICE_BY_ID = {service.service_id: service for service in SERVICES}
SPACE_ID_BY_SERVICE_ID = {
    service.service_id: service.space_id for service in SERVICES
}
SPACE_ID_BY_ALIAS = {
    key: service.space_id
    for service in SERVICES
    for key in (service.service_id, service.space_id)
}
SERVICE_SEARCH_PHRASES = tuple(
    sorted(
        (
            (phrase, service.service_id)
            for service in SERVICES
            for phrase in service.search_phrases
        ),
        key=lambda item: len(item[0]),
        reverse=True,
    )
)


def services_for_database() -> list[dict[str, str]]:
    return [
        {
            "id": service.service_id,
            "name": service.name,
            "description": service.description,
            "space_id": service.space_id,
        }
        for service in SERVICES
    ]
