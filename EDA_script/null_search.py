import pandas as pd

FILE_NAME = "../porto/porto.csv"
CHUNK_SIZE = 100000

required_columns = [
    "TRIP_ID",
    "CALL_TYPE",
    "TAXI_ID",
    "TIMESTAMP",
    "DAY_TYPE",
    "MISSING_DATA",
    "POLYLINE"
]

total_rows = 0

missing_counts = {col: 0 for col in required_columns}

invalid_call_types = 0
invalid_day_types = 0

missing_origin_call_for_A = 0
missing_origin_stand_for_B = 0

empty_polylines = 0

valid_call_types = {"A", "B", "C"}
valid_day_types = {"A", "B", "C"}

for chunk in pd.read_csv(FILE_NAME, chunksize=CHUNK_SIZE):

    total_rows += len(chunk)

    for col in required_columns:
        missing_counts[col] += chunk[col].isnull().sum()

    invalid_call_types += (
        chunk["CALL_TYPE"].notna()
        & ~chunk["CALL_TYPE"].isin(valid_call_types)
    ).sum()

    invalid_day_types += (
        chunk["DAY_TYPE"].notna()
        & ~chunk["DAY_TYPE"].isin(valid_day_types)
    ).sum()

    missing_origin_call_for_A += (
        (chunk["CALL_TYPE"] == "A")
        & chunk["ORIGIN_CALL"].isnull()
    ).sum()

    missing_origin_stand_for_B += (
        (chunk["CALL_TYPE"] == "B")
        & chunk["ORIGIN_STAND"].isnull()
    ).sum()

    empty_polylines += (
        chunk["POLYLINE"].isna()
        | (chunk["POLYLINE"] == "[]")
        | (chunk["POLYLINE"].str.strip() == "")
    ).sum()


print("\n=== RISULTATI ===")
print("Numero totale di righe:", total_rows)

print("\n=== VALORI MANCANTI ===")

for col in required_columns:
    percentage = (missing_counts[col] / total_rows) * 100

    print(
        f"{col}: {missing_counts[col]} "
        f"({percentage:.4f}%)"
    )

print("\nCALL_TYPE non validi:", invalid_call_types)
print("DAY_TYPE non validi:", invalid_day_types)

print(
    "CALL_TYPE A con ORIGIN_CALL mancante:",
    missing_origin_call_for_A
)

print(
    "CALL_TYPE B con ORIGIN_STAND mancante:",
    missing_origin_stand_for_B
)

print("POLYLINE vuote:", empty_polylines)