import csv
import json
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

from DbConnector import DbConnector


PORTO_TZ = ZoneInfo("Europe/Lisbon")


class PopulateDatabase:

    def __init__(self):
        self.connection = DbConnector()
        self.db_connection = self.connection.db_connection
        self.cursor = self.connection.cursor

        self.file_name = "../porto/porto.csv"

        self.trip_batch_size = 2000
        self.gps_batch_size = 20000

        self.expected_columns = [
            "TRIP_ID",
            "CALL_TYPE",
            "ORIGIN_CALL",
            "ORIGIN_STAND",
            "TAXI_ID",
            "TIMESTAMP",
            "DAY_TYPE",
            "MISSING_DATA",
            "POLYLINE"
        ]


    # =========================================================
    # UTILITY
    # =========================================================

    def int_or_none(self, value):
        if value is None or value.strip() == "":
            return None
        return int(value)

    def parse_boolean(self, value):
        value = value.strip().lower()

        if value == "true":
            return True

        if value == "false":
            return False

        raise ValueError( f"Boolean value not valid: {value}")

    def parse_polyline(self, polyline_string):

        if ( polyline_string is None
            or polyline_string.strip() == "" ):
            return []

        points = json.loads(polyline_string)

        if not isinstance(points, list):
            raise ValueError(
                "POLYLINE is not a list" )

        cleaned_points = []

        for point in points:

            if (
                not isinstance(point, list)
                or len(point) != 2
            ):
                raise ValueError(
                    f"Malformed GPS point: {point}"
                )

            longitude = float(point[0])
            latitude = float(point[1])

            if not -180 <= longitude <= 180:
                raise ValueError(
                    f"Invalid longitude: {longitude}"
                )

            if not -90 <= latitude <= 90:
                raise ValueError(
                    f"Invalid latitude: {latitude}"
                )

            cleaned_points.append(
                (longitude, latitude)
            )

        return cleaned_points


    # =========================================================
    # DUPLICATE ANALYSIS
    # =========================================================

    def row_signature(self, row):

        value = "\x1f".join(
            row[column]
            for column in self.expected_columns
        )

        return hashlib.blake2b(
            value.encode("utf-8"),
            digest_size=8
        ).digest()


    def find_duplicate_trip_ids(self):

        print("Analyzing duplicate TRIP_ID values...")
        first_signature = {}
        duplicated_ids = set()
        conflicting_ids = set()

        with open(
            self.file_name,
            "r",
            encoding="utf-8",
            newline=""
        ) as file:
            reader = csv.DictReader(file)
            for row in reader:

                trip_id = int(
                    row["TRIP_ID"] )

                signature = self.row_signature(row)

                if trip_id not in first_signature:
                    first_signature[trip_id] = (
                        signature)
                else:
                    duplicated_ids.add(
                        trip_id)

                    if ( first_signature[trip_id]
                        != signature ):
                        conflicting_ids.add(trip_id)
        identical_ids = ( duplicated_ids - conflicting_ids )
        print()
        print("=== DUPLICATES ===")
        print(  "Identical duplicate TRIP_IDs:", len(identical_ids))
        print("Conflicting duplicate TRIP_IDs:", len(conflicting_ids))

        return (identical_ids, conflicting_ids)

    # =========================================================
    # SAVE CONFLICTING IDS
    # =========================================================

    def save_conflicting_ids( self, conflicting_ids ):

        with open(
            "conflicting_trip_ids.csv",
            "w",
            encoding="utf-8",
            newline=""
        ) as file:

            writer = csv.writer(file)
            writer.writerow(["TRIP_ID"])

            for trip_id in sorted( conflicting_ids):
                writer.writerow([ trip_id])

    # =========================================================
    # INSERT BATCH
    # =========================================================

    def flush_batches(
        self,
        taxi_ids,
        trip_rows,
        gps_rows
    ):

        if not trip_rows:
            return
        try:
            # -----------------------------------------
            # TAXI
            # -----------------------------------------
            if taxi_ids:
                taxi_values = [
                    (taxi_id,)
                    for taxi_id in taxi_ids
                ]

                query = """
                    INSERT IGNORE INTO Taxi (
                        taxi_id
                    )
                    VALUES (%s)
                """
                self.cursor.executemany(
                    query,
                    taxi_values
                )
            # -----------------------------------------
            # TRIP
            # -----------------------------------------
            query = """
                INSERT INTO Trip (
                    trip_id,
                    taxi_id,
                    call_type,
                    origin_call,
                    origin_stand,
                    start_time,
                    day_type,
                    missing_data,
                    point_count
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
            """
            self.cursor.executemany(
                query,
                trip_rows
            )
            # -----------------------------------------
            # GPS POINT
            # -----------------------------------------
            if gps_rows:

                query = """
                    INSERT INTO GPSPoint (
                        trip_id,
                        point_index,
                        longitude,
                        latitude
                    )
                    VALUES (
                        %s, %s, %s, %s
                    )
                """
                self.cursor.executemany(
                    query,
                    gps_rows
                )
            self.db_connection.commit()
        except Exception:
            self.db_connection.rollback()
            raise
    # =========================================================
    # POPULATE DATABASE
    # =========================================================

    def populate_database(
        self,
        conflicting_ids
    ):

        taxi_ids = set()

        trip_rows = []
        gps_rows = []

        processed_trip_ids = set()

        inserted_trips = 0
        inserted_points = 0

        skipped_identical_duplicates = 0
        skipped_conflicting_rows = 0

        rejected_rows = 0

        rejected_file = open(
            "rejected_rows.csv",
            "w",
            encoding="utf-8",
            newline=""
        )

        rejected_writer = csv.writer(
            rejected_file
        )

        rejected_writer.writerow([
            "TRIP_ID",
            "reason"
        ])

        print()
        print(
            "Inserting data into database..."
        )

        with open(
            self.file_name,
            "r",
            encoding="utf-8",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            for row_number, row in enumerate(
                reader,
                start=2
            ):

                try:

                    trip_id = int(
                        row["TRIP_ID"]
                    )

                    # =====================================
                    # CONFLICTING DUPLICATES
                    # =====================================

                    if trip_id in conflicting_ids:

                        skipped_conflicting_rows += 1
                        continue

                    # =====================================
                    # IDENTICAL DUPLICATES
                    # =====================================

                    if (
                        trip_id
                        in processed_trip_ids
                    ):

                        skipped_identical_duplicates += 1
                        continue

                    processed_trip_ids.add(
                        trip_id
                    )

                    # =====================================
                    # TAXI
                    # =====================================

                    taxi_id = int(
                        row["TAXI_ID"]
                    )

                    # =====================================
                    # CALL TYPE
                    # =====================================

                    call_type = (
                        row["CALL_TYPE"]
                        .strip()
                    )

                    if (
                        call_type
                        not in {"A", "B", "C"}
                    ):
                        raise ValueError(
                            f"Invalid CALL_TYPE: "
                            f"{call_type}"
                        )

                    # =====================================
                    # DAY TYPE
                    # =====================================

                    day_type = (
                        row["DAY_TYPE"]
                        .strip()
                    )

                    if (
                        day_type
                        not in {"A", "B", "C"}
                    ):
                        raise ValueError(
                            f"Invalid DAY_TYPE: "
                            f"{day_type}"
                        )

                    # =====================================
                    # ORIGIN FIELDS
                    # =====================================

                    origin_call = (
                        self.int_or_none(
                            row["ORIGIN_CALL"]
                        )
                    )

                    origin_stand = (
                        self.int_or_none(
                            row["ORIGIN_STAND"]
                        )
                    )

                    if (
                        origin_call is not None
                        and call_type != "A"
                    ):
                        raise ValueError(
                            "ORIGIN_CALL is not NULL "
                            "but CALL_TYPE is not A"
                        )

                    if (
                        origin_stand is not None
                        and call_type != "B"
                    ):
                        raise ValueError(
                            "ORIGIN_STAND is not NULL "
                            "but CALL_TYPE is not B"
                        )

                    # =====================================
                    # MISSING DATA
                    # =====================================

                    missing_data = (
                        self.parse_boolean(
                            row["MISSING_DATA"]
                        )
                    )

                    # =====================================
                    # TIMESTAMP
                    # =====================================

                    unix_timestamp = int(
                        row["TIMESTAMP"]
                    )

                    # Porto local time (Europe/Lisbon, UTC+1 in summer),
                    # so HOUR()/DATE() in the queries match local hours.
                    start_time = (
                        datetime.fromtimestamp(
                            unix_timestamp,
                            tz=PORTO_TZ
                        ).replace(
                            tzinfo=None
                        )
                    )

                    # =====================================
                    # POLYLINE
                    # =====================================

                    points = (
                        self.parse_polyline(
                            row["POLYLINE"]
                        )
                    )

                    point_count = len(
                        points
                    )

                    # =====================================
                    # ADD TAXI
                    # =====================================

                    taxi_ids.add(
                        taxi_id
                    )

                    # =====================================
                    # ADD TRIP
                    # =====================================

                    trip_rows.append((
                        trip_id,
                        taxi_id,
                        call_type,
                        origin_call,
                        origin_stand,
                        start_time,
                        day_type,
                        missing_data,
                        point_count
                    ))

                    # =====================================
                    # ADD GPS POINTS
                    # =====================================

                    for (
                        point_index,
                        point
                    ) in enumerate(points):

                        longitude = point[0]
                        latitude = point[1]

                        gps_rows.append((
                            trip_id,
                            point_index,
                            longitude,
                            latitude
                        ))

                    inserted_trips += 1

                    inserted_points += (
                        point_count
                    )

                except Exception as error:

                    rejected_rows += 1

                    rejected_writer.writerow([
                        row.get(
                            "TRIP_ID",
                            ""
                        ),
                        (
                            f"Row {row_number}: "
                            f"{error}"
                        )
                    ])

                # =====================================
                # FLUSH BATCH
                # =====================================
                # Flushed outside the per-row try: a database error must stop
                # the import instead of being logged as a rejected row (which
                # left the buffers full and retried the same batch forever).

                if (
                    len(trip_rows)
                    >= self.trip_batch_size
                    or
                    len(gps_rows)
                    >= self.gps_batch_size
                ):

                    self.flush_batches(
                        taxi_ids,
                        trip_rows,
                        gps_rows
                    )

                    taxi_ids.clear()
                    trip_rows.clear()
                    gps_rows.clear()

                    print(
                        f"\rTrips inserted: "
                        f"{inserted_trips:,} | "
                        f"GPS points inserted: "
                        f"{inserted_points:,}",
                        end=""
                    )

        # Last batch
        self.flush_batches(
            taxi_ids,
            trip_rows,
            gps_rows
        )

        rejected_file.close()

        print("\n")
        print(
            "=== IMPORT COMPLETED ==="
        )

        print(
            "Trips inserted:",
            f"{inserted_trips:,}"
        )

        print(
            "GPS points inserted:",
            f"{inserted_points:,}"
        )

        print(
            "Identical duplicate rows skipped:",
            skipped_identical_duplicates
        )

        print(
            "Conflicting duplicate rows skipped:",
            skipped_conflicting_rows
        )

        print(
            "Rows rejected for other reasons:",
            rejected_rows
        )


    # =========================================================
    # DATABASE CONTROL
    # =========================================================

    def print_database_counts(self):

        print()
        print(
            "=== DATABASE CONTROL ==="
        )

        self.cursor.execute(
            "SELECT COUNT(*) FROM Taxi"
        )

        taxi_count = (
            self.cursor.fetchone()[0]
        )

        print(
            "Taxi:",
            taxi_count
        )


        self.cursor.execute(
            "SELECT COUNT(*) FROM Trip"
        )

        trip_count = (
            self.cursor.fetchone()[0]
        )

        print(
            "Trip:",
            trip_count
        )


        self.cursor.execute(
            "SELECT COUNT(*) FROM GPSPoint"
        )

        gps_count = (
            self.cursor.fetchone()[0]
        )

        print(
            "GPSPoint:",
            gps_count
        )


def main():

    program = None

    try:

        program = PopulateDatabase()

        # -----------------------------------------
        # Analyze duplicate IDs first
        # -----------------------------------------

        (
            identical_ids,
            conflicting_ids
        ) = program.find_duplicate_trip_ids()

        # -----------------------------------------
        # Save conflicting IDs for documentation
        # -----------------------------------------

        program.save_conflicting_ids(
            conflicting_ids
        )

        # -----------------------------------------
        # Populate the database
        # -----------------------------------------

        program.populate_database(
            conflicting_ids
        )

        # -----------------------------------------
        # Final control
        # -----------------------------------------

        program.print_database_counts()

    except Exception as error:

        print(
            "ERROR: Failed to populate database:",
            error
        )

    finally:

        if program:
            program.connection.close_connection()


if __name__ == "__main__":
    main()