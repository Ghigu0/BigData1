from DbConnector import DbConnector


# =========================================================
# SCHEMA
# =========================================================
# Taxi 1 : N Trip 1 : N GPSPoint
#
# Tables are created in dependency order and dropped in
# reverse order (children first, because of the foreign keys).

TABLES = {

    "Taxi": """
        CREATE TABLE Taxi (
            taxi_id BIGINT PRIMARY KEY
        )
    """,

    "Trip": """
        CREATE TABLE Trip (
            trip_id BIGINT PRIMARY KEY,
            taxi_id BIGINT NOT NULL,
            call_type CHAR(1) NOT NULL,
            origin_call BIGINT NULL,
            origin_stand INT NULL,
            start_time DATETIME NOT NULL,
            day_type CHAR(1) NOT NULL,
            missing_data BOOLEAN NOT NULL,
            point_count INT NOT NULL,

            -- Per-trip summary computed while populating, so the
            -- queries do not have to re-read all GPS points.
            duration_s INT NOT NULL,            -- (point_count - 1) * 15, 0 if no points
            end_time DATETIME NOT NULL,         -- start_time + duration_s
            distance_km DOUBLE NOT NULL,        -- sum of haversine between consecutive points
            start_lat DOUBLE NULL,              -- NULL if the trip has no points
            start_lon DOUBLE NULL,
            end_lat DOUBLE NULL,
            end_lon DOUBLE NULL,

            -- Deleting a taxi removes its trips (and, through the
            -- GPSPoint foreign key, their points): a trip without its
            -- taxi has no meaning in this dataset.
            FOREIGN KEY (taxi_id)
                REFERENCES Taxi(taxi_id)
                ON DELETE CASCADE
                ON UPDATE CASCADE,

            CHECK (call_type IN ('A', 'B', 'C')),
            CHECK (day_type IN ('A', 'B', 'C')),
            CHECK (origin_call IS NULL OR call_type = 'A'),
            CHECK (origin_stand IS NULL OR call_type = 'B')
        )
    """,

    "GPSPoint": """
        CREATE TABLE GPSPoint (
            trip_id BIGINT NOT NULL,
            point_index INT NOT NULL,
            longitude DOUBLE NOT NULL,
            latitude DOUBLE NOT NULL,

            PRIMARY KEY (trip_id, point_index),

            FOREIGN KEY (trip_id)
                REFERENCES Trip(trip_id)
                ON DELETE CASCADE,

            CHECK (longitude BETWEEN -180 AND 180),
            CHECK (latitude BETWEEN -90 AND 90)
        )
    """
}


# =========================================================
# INDEXES
# =========================================================
# Secondary indexes are created AFTER populate, not in CREATE TABLE:
# building an index once on the loaded data takes minutes, while
# keeping it updated during ~80M inserts (in random latitude order)
# makes populate several times slower.

INDEXES = {

    # Used by query 6: the box around City Hall is a range on
    # latitude, so MySQL reads only that slice of the index
    # instead of scanning every GPS point.
    "idx_gps_lat_lon": "CREATE INDEX idx_gps_lat_lon ON GPSPoint (latitude, longitude)"
}


def create_indexes(cursor):
    cursor.execute("""
        SELECT DISTINCT index_name
        FROM information_schema.statistics
        WHERE table_schema = DATABASE()
    """)
    existing = {row[0] for row in cursor.fetchall()}

    for index_name, query in INDEXES.items():
        if index_name in existing:
            print("Index already exists:", index_name)
            continue
        print("Creating index (may take a few minutes):", index_name)
        cursor.execute(query)
        print("Created index:", index_name)


class CreateTables:

    def __init__(self):
        self.connection = DbConnector()
        self.db_connection = self.connection.db_connection
        self.cursor = self.connection.cursor

    def drop_tables(self):
        for table_name in reversed(list(TABLES)):
            self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            print("Dropped (if existing):", table_name)

    def create_tables(self):
        for table_name, query in TABLES.items():
            self.cursor.execute(query)
            print("Created:", table_name)
        self.db_connection.commit()


def main():
    program = None

    try:
        program = CreateTables()

        answer = input(
            "This DROPS Taxi, Trip and GPSPoint (all data is lost) "
            "and recreates them. Continue? [y/N]: "
        )

        if answer.strip().lower() != "y":
            print("Aborted.")
            return

        program.drop_tables()
        program.create_tables()

    except Exception as error:
        print("ERROR: Failed to create tables:", error)

    finally:
        if program:
            program.connection.close_connection()


if __name__ == "__main__":
    main()
