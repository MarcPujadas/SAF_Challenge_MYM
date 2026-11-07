import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from recommendation_service import recommend
from safi_service import advice, chat

import backendapi


class RecommendationTests(unittest.TestCase):
    def test_recommends_a_less_busy_alternative_for_demo_request(self) -> None:
        result = recommend("fitness", "2026-11-10", "18:00", "20:00")

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["requested_slot"]["occupancy_score"], 89)
        self.assertEqual(result["requested_slot"]["occupancy_level"], "very_high")
        self.assertEqual(result["recommended_slot"]["start"], "19:00")
        self.assertEqual(result["confidence"], "low")
        self.assertIn("not historical", result["basis"]["historical_period"])

    def test_api_endpoint_returns_the_contract_envelope(self) -> None:
        response = backendapi.create_recommendation(
            backendapi.RecommendationRequest(
                space_id="fitness",
                date="2026-11-10",
                preferred_start="18:00",
                preferred_end="20:00",
            )
        )

        self.assertTrue(response["success"])
        self.assertIsNone(response["error"])
        self.assertEqual(response["data"]["recommended_slot"]["start"], "19:00")

    def test_refuses_to_guess_for_unsupported_space(self) -> None:
        self.assertIsNone(recommend("court", "2026-11-10", "18:00", "20:00"))

    def test_does_not_recommend_fitness_turn_change_hours(self) -> None:
        result = recommend("fitness", "2026-11-10", "09:00", "16:00")

        self.assertIsNotNone(result)
        assert result is not None
        self.assertNotIn(
            result["recommended_slot"]["start"] if result["recommended_slot"] else "",
            {"10:00", "15:00"},
        )


class SAFiTests(unittest.TestCase):
    def test_advice_returns_the_recommendation(self) -> None:
        result = advice("fitness", "2026-11-10", "18:00")

        self.assertEqual(result["type"], "warning")
        self.assertEqual(result["occupancy_score"], 89)
        self.assertEqual(result["alternative"]["start"], "19:00")

    def test_chat_says_it_does_not_know_without_matching_data(self) -> None:
        result = chat("Quan hi ha menys gent a la piscina?")

        self.assertFalse(result["can_answer"])
        self.assertEqual(result["sources"], [])


class AdminEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        self.path_patcher = patch.object(backendapi, "DATABASE_PATH", self.database_path)
        self.path_patcher.start()
        backendapi.initialize_database()

    def tearDown(self) -> None:
        self.path_patcher.stop()
        self.temp_dir.cleanup()

    def test_stats_and_reservations_read_persisted_app_reservations(self) -> None:
        with closing(backendapi.sqlite3.connect(self.database_path)) as connection:
            connection.execute(
                """
                INSERT INTO reservations
                    (reservation_id, user_id, space_id, date, start, end, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "res_1",
                    "demo-user",
                    "fitness",
                    "2026-11-10",
                    "19:00",
                    "20:15",
                    "confirmed",
                ),
            )
            connection.commit()

        summary = backendapi.get_admin_summary()
        self.assertTrue(summary["success"])
        self.assertEqual(summary["data"]["total_reservations"], 1)
        self.assertEqual(summary["data"]["busiest_space"]["id"], "fitness")

        stats = backendapi.get_admin_stats()
        self.assertEqual(stats["data"]["reservations_created_by_app"], 1)
        self.assertEqual(stats["data"]["most_used_spaces"][0]["space_id"], "fitness")
        self.assertIsNone(stats["data"]["busiest_hour"])
        self.assertIsNone(stats["data"]["quietest_hour"])

        reservations = backendapi.get_admin_reservations()
        self.assertEqual(reservations["data"][0]["reservation_id"], "res_1")

    def test_occupancy_does_not_invent_processed_data(self) -> None:
        response = backendapi.get_admin_occupancy(None, None, None)

        self.assertEqual(response["data"]["spaces"], [])


if __name__ == "__main__":
    unittest.main()
