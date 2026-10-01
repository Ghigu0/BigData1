import pandas as pd

FILE_NAME = "../porto/porto.csv"
CHUNK_SIZE = 100000

call_type_counts = {}
day_type_counts = {}
missing_data_counts = {}
taxi_trip_counts = {}

total_rows = 0

for chunk in pd.read_csv(FILE_NAME, chunksize=CHUNK_SIZE):

    total_rows += len(chunk)

    # -------------------------
    # CALL_TYPE
    # -------------------------

    counts = chunk["CALL_TYPE"].value_counts()

    for value, count in counts.items():
        call_type_counts[value] = (
            call_type_counts.get(value, 0) + count
        )

    # -------------------------
    # DAY_TYPE
    # -------------------------

    counts = chunk["DAY_TYPE"].value_counts()

    for value, count in counts.items():
        day_type_counts[value] = (
            day_type_counts.get(value, 0) + count
        )

    # -------------------------
    # MISSING_DATA
    # -------------------------

    counts = chunk["MISSING_DATA"].value_counts()

    for value, count in counts.items():
        missing_data_counts[value] = (
            missing_data_counts.get(value, 0) + count
        )

    # -------------------------
    # TAXI_ID
    # -------------------------

    counts = chunk["TAXI_ID"].value_counts()

    for taxi_id, count in counts.items():
        taxi_trip_counts[taxi_id] = (
            taxi_trip_counts.get(taxi_id, 0) + count
        )


# ==================================================
# RISULTATI
# ==================================================

print("=== DATASET ===")
print("Numero totale di viaggi:", total_rows)


print("\n=== DISTRIBUZIONE CALL_TYPE ===")

for value, count in sorted(call_type_counts.items()):

    percentage = count / total_rows * 100

    print(
        f"{value}: {count} viaggi "
        f"({percentage:.2f}%)"
    )


print("\n=== DISTRIBUZIONE DAY_TYPE ===")

for value, count in sorted(day_type_counts.items()):

    percentage = count / total_rows * 100

    print(
        f"{value}: {count} viaggi "
        f"({percentage:.2f}%)"
    )


print("\n=== DISTRIBUZIONE MISSING_DATA ===")

for value, count in missing_data_counts.items():

    percentage = count / total_rows * 100

    print(
        f"{value}: {count} viaggi "
        f"({percentage:.2f}%)"
    )


# ==================================================
# STATISTICHE TAXI
# ==================================================

trips_per_taxi = pd.Series(taxi_trip_counts)

print("\n=== DISTRIBUZIONE VIAGGI PER TAXI ===")

print("Numero di taxi:", len(trips_per_taxi))

print(
    "Media viaggi per taxi:",
    round(trips_per_taxi.mean(), 2)
)

print(
    "Mediana viaggi per taxi:",
    round(trips_per_taxi.median(), 2)
)

print(
    "Minimo viaggi per taxi:",
    trips_per_taxi.min()
)

print(
    "Massimo viaggi per taxi:",
    trips_per_taxi.max()
)