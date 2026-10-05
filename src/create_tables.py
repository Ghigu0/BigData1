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

            FOREIGN KEY (taxi_id)
                REFERENCES Taxi(taxi_id),

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
