from app.services.recommendation_service import (
    recommend
)


result = recommend(
    space_id="sala-fitnes-sala-cardio",
    date="2026-11-10",
    preferred_start="18:00",
    preferred_end="20:00"
)

print(result)