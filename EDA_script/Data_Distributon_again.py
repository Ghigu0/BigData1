import pandas as pd

FILE_NAME = "../porto/porto.csv"
CHUNK_SIZE = 100000

# =========================
# Contatori generali
# =========================

trip_ids_seen = set()
duplicate_trip_ids = 0

# Coerenza ORIGIN_CALL / ORIGIN_STAND
a_without_origin_call = 0
a_with_origin_stand = 0

b_without_origin_stand = 0
b_with_origin_call = 0

c_with_origin_call = 0
c_with_origin_stand = 0

# MISSING_DATA
missing_data_true_count = 0
missing_data_true_polylines = []

# TIMESTAMP
min_timestamp = None
max_timestamp = None


for chunk in pd.read_csv(
    FILE_NAME,
    chunksize=CHUNK_SIZE
):

    # ==================================================
    # 1. DUPLICATI TRIP_ID
    # ==================================================

    for trip_id in chunk["TRIP_ID"]:
        if trip_id in trip_ids_seen:
            duplicate_trip_ids += 1
        else:
            trip_ids_seen.add(trip_id)

    # ==================================================
    # 2. COERENZA CALL_TYPE / ORIGIN
    # ==================================================

    a_without_origin_call += (
        (chunk["CALL_TYPE"] == "A")
        & chunk["ORIGIN_CALL"].isnull()
    ).sum()

    a_with_origin_stand += (
        (chunk["CALL_TYPE"] == "A")
        & chunk["ORIGIN_STAND"].notnull()
    ).sum()


    b_without_origin_stand += (
        (chunk["CALL_TYPE"] == "B")
        & chunk["ORIGIN_STAND"].isnull()
    ).sum()

    b_with_origin_call += (
        (chunk["CALL_TYPE"] == "B")
        & chunk["ORIGIN_CALL"].notnull()
    ).sum()


    c_with_origin_call += (
        (chunk["CALL_TYPE"] == "C")
        & chunk["ORIGIN_CALL"].notnull()
    ).sum()

    c_with_origin_stand += (
        (chunk["CALL_TYPE"] == "C")
        & chunk["ORIGIN_STAND"].notnull()
    ).sum()

    # ==================================================
    # 3. IMPATTO MISSING_DATA = TRUE
    # ==================================================

    missing_rows = chunk[
        chunk["MISSING_DATA"] == True
    ]

    missing_data_true_count += len(missing_rows)

    for polyline in missing_rows["POLYLINE"]:

        if polyline == "[]":
            n_points = 0
        else:
            n_points = polyline.count("],[") + 1

        missing_data_true_polylines.append(n_points)

    # ==================================================
    # 4. RANGE TEMPORALE
    # ==================================================

    chunk_min = chunk["TIMESTAMP"].min()
    chunk_max = chunk["TIMESTAMP"].max()

    if min_timestamp is None or chunk_min < min_timestamp:
        min_timestamp = chunk_min

    if max_timestamp is None or chunk_max > max_timestamp:
        max_timestamp = chunk_max


# ==================================================
# RISULTATI
# ==================================================

print("=== DUPLICATI TRIP_ID ===")
print("TRIP_ID duplicati:", duplicate_trip_ids)


print("\n=== COERENZA CALL_TYPE / ORIGIN ===")

print("CALL_TYPE A senza ORIGIN_CALL:", a_without_origin_call)
print("CALL_TYPE A con ORIGIN_STAND valorizzato:", a_with_origin_stand)

print("CALL_TYPE B senza ORIGIN_STAND:", b_without_origin_stand)
print("CALL_TYPE B con ORIGIN_CALL valorizzato:", b_with_origin_call)

print("CALL_TYPE C con ORIGIN_CALL valorizzato:", c_with_origin_call)
print("CALL_TYPE C con ORIGIN_STAND valorizzato:", c_with_origin_stand)


print("\n=== MISSING_DATA = TRUE ===")

print("Numero record con MISSING_DATA=True:", missing_data_true_count)

print(
    "Numero di punti nelle loro POLYLINE:",
    missing_data_true_polylines
)

if len(missing_data_true_polylines) > 0:
    invalid_missing = sum(
        1 for n in missing_data_true_polylines
        if n < 3
    )

    print(
        "Di questi, invalidi (<3 punti):",
        invalid_missing
    )


print("\n=== RANGE TEMPORALE ===")

print(
    "TIMESTAMP minimo:",
    min_timestamp,
    "->",
    pd.to_datetime(min_timestamp, unit="s")
)

print(
    "TIMESTAMP massimo:",
    max_timestamp,
    "->",
    pd.to_datetime(max_timestamp, unit="s")
)