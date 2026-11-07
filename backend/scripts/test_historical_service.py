from app.services.historical_service import (
    get_best_alternative,
    get_historical_occupancy
)


SPACE_ID = "sala-fitnes-sala-cardio"

# 0 = dilluns
# 1 = dimarts
# 2 = dimecres
# 3 = dijous
# 4 = divendres
# 5 = dissabte
# 6 = diumenge

WEEKDAY = 1

START_TIME = "18:00"


occupancy = get_historical_occupancy(
    space_id=SPACE_ID,
    weekday=WEEKDAY,
    start_time=START_TIME
)

print("OCUPACIÓ:")
print(occupancy)


alternative = get_best_alternative(
    space_id=SPACE_ID,
    weekday=WEEKDAY,
    preferred_start=START_TIME
)

print()
print("MILLOR ALTERNATIVA:")
print(alternative)