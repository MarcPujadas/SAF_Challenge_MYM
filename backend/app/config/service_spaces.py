from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


CapacityMode = Literal["people", "resource_units"]


@dataclass(frozen=True)
class ResourceMapping:
    service_id: str
    space_id: str
    label: str
    display_order: int
    capacity_mode: CapacityMode
    reservation_capacity: int | None = None
    allow_virtual: bool = False


def _resources(
    service_id: str,
    prefix: str,
    numbers: range,
    label: str,
    capacity_mode: CapacityMode,
    *,
    virtual_numbers: frozenset[int] = frozenset(),
    first_order: int = 1,
) -> tuple[ResourceMapping, ...]:
    return tuple(
        ResourceMapping(
            service_id=service_id,
            space_id=f"{prefix}{number}",
            label=f"{label} {number}",
            display_order=order,
            capacity_mode=capacity_mode,
            reservation_capacity=(
                1 if capacity_mode == "resource_units" else None
            ),
            allow_virtual=number in virtual_numbers,
        )
        for order, number in enumerate(numbers, start=first_order)
    )


# Padel Pista 2 is present in the normalized reservation history, but can be
# absent from the source "Espais" sheet. Keep its canonical ID here without
# editing that source; the seed marks it virtual only when SQLite lacks it.
SERVICE_SPACE_MAPPINGS = (
    ResourceMapping(
        service_id="fitness",
        space_id="sala-fitnes-sala-cardio",
        label="Sala Fitness",
        display_order=1,
        capacity_mode="people",
    ),
    *_resources(
        "pool-25m",
        "piscina-25-metres-carrer-",
        range(1, 9),
        "Carril",
        "people",
    ),
    ResourceMapping(
        service_id="pool-16m",
        space_id="piscina-de-16-metres",
        label="Piscina 16 m",
        display_order=1,
        capacity_mode="people",
    ),
    *_resources(
        "padel",
        "pistes-de-padel-pista-",
        range(1, 5),
        "Pista",
        "resource_units",
        virtual_numbers=frozenset({2}),
    ),
    *_resources(
        "tennis",
        "tennis-tennis-",
        range(1, 6),
        "Pista",
        "resource_units",
    ),
    *_resources(
        "squash",
        "esquaix-esquaix-",
        range(2, 5),
        "Pista",
        "resource_units",
    ),
    *_resources(
        "football",
        "futbol-7-camp-",
        range(1, 5),
        "Camp",
        "resource_units",
    ),
    *_resources(
        "guided-activities",
        "sales-activitats-dirigides-sala-",
        range(1, 4),
        "Sala",
        "people",
    ),
)


SERVICE_SPACE_BY_KEY = {
    (resource.service_id, resource.space_id): resource
    for resource in SERVICE_SPACE_MAPPINGS
}
SPACE_IDS_BY_SERVICE_ID: dict[str, tuple[str, ...]] = {
    service_id: tuple(
        resource.space_id
        for resource in SERVICE_SPACE_MAPPINGS
        if resource.service_id == service_id
    )
    for service_id in dict.fromkeys(
        resource.service_id for resource in SERVICE_SPACE_MAPPINGS
    )
}
