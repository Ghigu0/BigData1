import pandas as pd

FILE_NAME = "../porto/porto.csv"
CHUNK_SIZE = 100000

count_0_points = 0
count_1_point = 0
count_2_points = 0
count_valid = 0

total_rows = 0

for chunk in pd.read_csv(
    FILE_NAME,
    usecols=["POLYLINE"],
    chunksize=CHUNK_SIZE
):
    for polyline in chunk["POLYLINE"]:

        total_rows += 1

        # Caso POLYLINE vuota
        if polyline == "[]":
            n_points = 0

        else:
            # Ogni "],[" separa due punti
            n_points = polyline.count("],[") + 1

        if n_points == 0:
            count_0_points += 1

        elif n_points == 1:
            count_1_point += 1

        elif n_points == 2:
            count_2_points += 1

        else:
            count_valid += 1


invalid_trips = (
    count_0_points
    + count_1_point
    + count_2_points
)

print("\n=== RISULTATI ===")

print("Totale viaggi:", total_rows)

print("\nViaggi con 0 punti:", count_0_points)
print("Viaggi con 1 punto:", count_1_point)
print("Viaggi con 2 punti:", count_2_points)

print("\nViaggi con almeno 3 punti:", count_valid)

print("\n=== INVALID TRIPS ===")

print("Totale viaggi invalidi:", invalid_trips)

print(
    "Percentuale invalidi:",
    f"{(invalid_trips / total_rows) * 100:.4f}%"
)