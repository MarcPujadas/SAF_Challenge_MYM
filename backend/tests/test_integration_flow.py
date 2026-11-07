from fastapi.testclient import TestClient

from app import main
from app.database import database
from app.routers import safi_admin


FITNESS_SPACE_ID = "sala-fitnes-sala-cardio"


def fake_historical_occupancy(
    space_id,
    weekday,
    start_time,
):
    """
    Simula dades historiques perquè el test
    no depengui del dataset real del SAF.
    """
    return {
        "space_id": space_id,
        "weekday": weekday,
        "requested_start": start_time,
        "start_time": start_time,
        "occupancy_score": 60,
        "occupancy_level": "medium",
        "average_reservations": 10,
        "samples": 20,
    }


def fake_recommend(
    space_id,
    date,
    preferred_start,
    preferred_end=None,
):
    """
    Simula el recommendation service.

    L'objectiu d'aquest test no és tornar
    a provar l'algoritme de recomanació,
    sinó comprovar que tot el flux API
    funciona de principi a fi.
    """
    return {
        "requested_slot": {
            "start": preferred_start,
            "occupancy_score": 60,
            "occupancy_level": "medium",
        },
        "recommended_slot": {
            "start": "19:45",
            "occupancy_score": 35,
            "occupancy_level": "low",
        },
        "message": (
            "Les 19:45 acostumen a tenir "
            "menys ocupació."
        ),
        "confidence": "high",
        "basis": {
            "space_id": space_id,
            "weekday": "Tuesday",
            "historical_period": (
                "2026-04-01 to 2026-10-31"
            ),
        },
    }


def make_client(
    tmp_path,
    monkeypatch,
):
    """
    Crea una base de dades temporal per evitar
    modificar la base de dades real durant els tests.
    """

    monkeypatch.setattr(
        database,
        "DB_PATH",
        tmp_path / "test_integration.db",
    )

    # /availability utilitza aquesta funció
    # importada directament a main.py.
    monkeypatch.setattr(
        main,
        "get_historical_occupancy",
        fake_historical_occupancy,
    )

    # /recommendations utilitza recommend
    # importat directament a safi_admin.py.
    monkeypatch.setattr(
        safi_admin,
        "recommend",
        fake_recommend,
    )

    return TestClient(
        main.app
    )


def seed_test_data():
    """
    Afegeix l'espai i el servei mínims
    necessaris per executar el flux complet.

    L'usuari demo-user ja és creat
    automàticament per init_db().
    """

    with database.get_connection() as connection:

        connection.execute(
            """
            INSERT INTO spaces (
                id,
                name,
                type,
                capacity,
                reservable
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                FITNESS_SPACE_ID,
                "Sala fitnes + sala cardio",
                "fitness",
                120,
                1,
            ),
        )

        connection.execute(
            """
            INSERT INTO services (
                id,
                name,
                description,
                space_id,
                reservable
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "fitness",
                "Fitness",
                "Sala de fitness i cardio",
                FITNESS_SPACE_ID,
                1,
            ),
        )


def test_complete_reservation_flow(
    tmp_path,
    monkeypatch,
):
    """
    Flux complet del MVP:

    GET /services
        ->
    GET /availability
        ->
    POST /recommendations
        ->
    POST /reservations
        ->
    GET /reservations
        ->
    GET /admin/reservations

    La reserva creada pel flux públic
    ha d'aparèixer també al dashboard admin.
    """

    with make_client(
        tmp_path,
        monkeypatch,
    ) as client:

        seed_test_data()

        # -------------------------------------------------
        # 1. GET /services
        # -------------------------------------------------

        services_response = client.get(
            "/api/v1/services"
        )

        assert (
            services_response.status_code
            == 200
        )

        services_body = (
            services_response.json()
        )

        assert (
            services_body["success"]
            is True
        )

        services = (
            services_body["data"]
        )

        fitness_service = next(
            service
            for service in services
            if service["id"] == "fitness"
        )

        assert (
            fitness_service["space_id"]
            == FITNESS_SPACE_ID
        )

        # IMPORTANT:
        # A partir d'aquí utilitzem
        # service.space_id, no "fitness".

        space_id = (
            fitness_service["space_id"]
        )

        # -------------------------------------------------
        # 2. GET /availability
        # -------------------------------------------------

        availability_response = client.get(
            "/api/v1/availability",
            params={
                "space_id": space_id,
                "date": "2026-11-10",
            },
        )

        assert (
            availability_response.status_code
            == 200
        )

        availability_body = (
            availability_response.json()
        )

        assert (
            availability_body["success"]
            is True
        )

        assert (
            availability_body["data"]["space_id"]
            == FITNESS_SPACE_ID
        )

        slots = (
            availability_body[
                "data"
            ]["slots"]
        )

        assert len(slots) > 0

        selected_slot = next(
            slot
            for slot in slots
            if (
                slot["start"]
                == "18:30"
            )
        )

        assert (
            selected_slot["available"]
            is True
        )

        assert (
            selected_slot["end"]
            == "19:45"
        )

        # -------------------------------------------------
        # 3. POST /recommendations
        # -------------------------------------------------

        recommendation_response = client.post(
            "/api/v1/recommendations",
            json={
                "space_id": space_id,
                "date": "2026-11-10",
                "preferred_start": (
                    selected_slot["start"]
                ),
                "preferred_end": (
                    selected_slot["end"]
                ),
            },
        )

        assert (
            recommendation_response.status_code
            == 200
        )

        recommendation_body = (
            recommendation_response.json()
        )

        assert (
            recommendation_body["success"]
            is True
        )

        recommendation = (
            recommendation_body["data"]
        )

        assert (
            recommendation[
                "basis"
            ]["space_id"]
            == FITNESS_SPACE_ID
        )

        assert (
            recommendation[
                "requested_slot"
            ]["start"]
            == "18:30"
        )

        # -------------------------------------------------
        # 4. POST /reservations
        # -------------------------------------------------

        reservation_response = client.post(
            "/api/v1/reservations",
            json={
                "user_id": "demo-user",
                "space_id": space_id,
                "date": "2026-11-10",
                "start": (
                    selected_slot["start"]
                ),
                "end": (
                    selected_slot["end"]
                ),
            },
        )

        assert (
            reservation_response.status_code
            == 200
        )

        reservation_body = (
            reservation_response.json()
        )

        assert (
            reservation_body["success"]
            is True
        )

        created_reservation = (
            reservation_body["data"]
        )

        assert (
            created_reservation["status"]
            == "confirmed"
        )

        assert (
            created_reservation["space_id"]
            == FITNESS_SPACE_ID
        )

        reservation_id = (
            created_reservation[
                "reservation_id"
            ]
        )

        assert reservation_id.startswith(
            "res_"
        )

        # -------------------------------------------------
        # 5. GET /reservations
        # -------------------------------------------------

        user_reservations_response = (
            client.get(
                "/api/v1/reservations",
                params={
                    "user_id": "demo-user",
                },
            )
        )

        assert (
            user_reservations_response.status_code
            == 200
        )

        user_reservations_body = (
            user_reservations_response.json()
        )

        assert (
            user_reservations_body["success"]
            is True
        )

        user_reservations = (
            user_reservations_body["data"]
        )

        assert len(
            user_reservations
        ) == 1

        assert (
            user_reservations[0][
                "reservation_id"
            ]
            == reservation_id
        )

        assert (
            user_reservations[0][
                "space_id"
            ]
            == FITNESS_SPACE_ID
        )

        assert (
            user_reservations[0]["start"]
            == "18:30"
        )

        assert (
            user_reservations[0]["end"]
            == "19:45"
        )

        # -------------------------------------------------
        # 6. GET /admin/reservations
        # -------------------------------------------------

        admin_response = client.get(
            "/api/v1/admin/reservations"
        )

        assert (
            admin_response.status_code
            == 200
        )

        admin_body = (
            admin_response.json()
        )

        assert (
            admin_body["success"]
            is True
        )

        admin_reservations = (
            admin_body["data"]
        )

        assert len(
            admin_reservations
        ) == 1

        admin_reservation = (
            admin_reservations[0]
        )

        # La mateixa reserva creada pel flux
        # públic ha d'arribar al dashboard.

        assert (
            admin_reservation[
                "reservation_id"
            ]
            == reservation_id
        )

        assert (
            admin_reservation[
                "space_id"
            ]
            == FITNESS_SPACE_ID
        )

        assert (
            admin_reservation["date"]
            == "2026-11-10"
        )

        assert (
            admin_reservation["start"]
            == "18:30"
        )

        assert (
            admin_reservation["status"]
            == "confirmed"
        )