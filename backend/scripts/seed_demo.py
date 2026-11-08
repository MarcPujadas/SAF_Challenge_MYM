"""Create an explicitly SYNTHETIC, reproducible offline demo dataset.

Never overwrites real SAF data. It is not an import of SAF observations.
"""
from __future__ import annotations
import csv
from datetime import date, timedelta
from pathlib import Path
from app.config.service_spaces import SERVICE_SPACE_MAPPINGS
from app.config.services import SERVICES
from app.config.schedules import STANDARD_75_MINUTE_SLOTS
from app.database.database import get_connection, init_db
from app.database.service_spaces import seed_service_spaces

BASE = Path(__file__).resolve().parents[1]
HISTORY = BASE / "data" / "local" / "historical_occupancy.csv"
MAP_TYPE = {
    "fitness": "fitness", "pool-25m": "pool", "pool-16m": "pool",
    "padel": "court", "tennis": "court", "squash": "court",
    "football": "court", "guided-activities": "activity_room",
}
CAPACITY = {
    "fitness": 120, "pool-25m": 12, "pool-16m": 40,
    "padel": 1, "tennis": 1, "squash": 1, "football": 1,
    "guided-activities": 25,
}

def main():
    init_db()
    with get_connection() as con:
        existing = con.execute("SELECT COUNT(*) FROM spaces").fetchone()[0]
        if existing:
            print(f"Base de dades existent: {existing} espais (conservats).")
        for item in SERVICE_SPACE_MAPPINGS:
            con.execute(
                "INSERT OR IGNORE INTO spaces (id,name,type,capacity,reservable) VALUES (?,?,?,?,1)",
                (item.space_id,item.label,MAP_TYPE[item.service_id],CAPACITY[item.service_id]),
            )
        for item in SERVICES:
            con.execute(
                "INSERT OR IGNORE INTO services (id,name,description,space_id,reservable) VALUES (?,?,?,?,1)",
                (item.service_id,item.name,item.description,item.space_id),
            )
        seed_service_spaces(con)
        print("Cataleg de demostracio preparat. Reserves existents conservades.")
    if HISTORY.exists():
        print("Historics existents conservats:", HISTORY)
        return
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    first=date(2026,5,4)
    with HISTORY.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=["space_id","date","weekday","start_time","reservations","source"])
        writer.writeheader()
        for day_offset in range(84):
            day=first+timedelta(days=day_offset)
            starts=STANDARD_75_MINUTE_SLOTS.get(day.weekday(),[])
            for index,start in enumerate(starts):
                # Deterministic synthetic peak around late afternoons.
                value=5+((day.weekday()*3+index*7+day_offset)%13)
                if "17:" in start or "18:" in start: value+=35
                elif "16:" in start or "19:" in start: value+=19
                elif "07:" in start or "08:" in start: value+=8
                writer.writerow({"space_id":"sala-fitnes-sala-cardio","date":day.isoformat(),"weekday":day.weekday(),"start_time":start,"reservations":value,"source":"SYNTHETIC_DEMO"})
    print("ATENCIO: creada PREVISIO SINTETICA de demo, no dades reals del SAF.")
    print("Fitxer local ignorat per Git:", HISTORY)

if __name__=="__main__":
    main()
