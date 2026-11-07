import pandas as pd

FILE_PATH = "data/processed/historical_occupancy.csv"

df = pd.read_csv(FILE_PATH)

fitness = df[
    df["space_id"] == "sala-fitnes-sala-cardio"
].copy()

print("NOMBRE DE REGISTRES FITNESS:")
print(len(fitness))

print("\nFRANGES ÚNIQUES:")
for slot in sorted(fitness["start_time"].dropna().unique()):
    print(slot)

print("\nRESUM PER DIA DE LA SETMANA:")
summary = (
    fitness
    .groupby(["weekday", "start_time"])["reservations"]
    .mean()
    .reset_index()
)

print(summary.to_string(index=False))