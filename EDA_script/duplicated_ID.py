import pandas as pd

FILE_NAME = "../porto/porto.csv"
CHUNK_SIZE = 100000

trip_id_counts = {}

# Primo passaggio: troviamo tutti i TRIP_ID duplicati
for chunk in pd.read_csv(
    FILE_NAME,
    usecols=["TRIP_ID"],
    chunksize=CHUNK_SIZE
):
    counts = chunk["TRIP_ID"].value_counts()

    for trip_id, count in counts.items():
        trip_id_counts[trip_id] = trip_id_counts.get(trip_id, 0) + count


duplicate_ids = {
    trip_id
    for trip_id, count in trip_id_counts.items()
    if count > 1
}


# Secondo passaggio:
# prendiamo solo le righe che hanno un TRIP_ID duplicato
duplicate_rows = []

for chunk in pd.read_csv(
    FILE_NAME,
    chunksize=CHUNK_SIZE
):
    rows = chunk[chunk["TRIP_ID"].isin(duplicate_ids)]
    duplicate_rows.append(rows)


duplicate_df = pd.concat(duplicate_rows)


# Liste degli ID
identical_duplicate_ids = []
different_duplicate_ids = []


# Controlliamo ogni TRIP_ID duplicato
for trip_id, group in duplicate_df.groupby("TRIP_ID"):

    # Se eliminando le righe identiche ne rimane una sola,
    # tutte le occorrenze di quel TRIP_ID sono uguali
    if len(group.drop_duplicates()) == 1:
        identical_duplicate_ids.append(trip_id)
    else:
        different_duplicate_ids.append(trip_id)


# ==================================================
# OUTPUT
# ==================================================

print("=== DUPLICATI TRIP_ID ===")

print(
    "\nID duplicati con righe identiche:",
    len(identical_duplicate_ids)
)

for trip_id in identical_duplicate_ids:
    print("  ", trip_id)


print(
    "\nID duplicati con righe diverse:",
    len(different_duplicate_ids)
)

for trip_id in different_duplicate_ids:
    print("  ", trip_id)