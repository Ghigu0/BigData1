# Big Data Assignment – Porto Taxi Trajectories

This repository contains the implementation developed for the Big Data assignment based on the **Porto Taxi Trajectory dataset**.

The project focuses on importing a large CSV dataset into a MySQL relational database, cleaning and validating the data during the import process, and executing a set of analytical queries on taxi trips and GPS trajectories.

## Project structure

The main files of the project are located in the `src` directory.

### `DbConnector.py`

This file manages the connection to MySQL.

When the program starts, the user can choose where to execute the project:

```text
1 - Local MySQL
2 - NTNU VM
```

- **Option 1** connects to a local MySQL instance running inside Docker.
- **Option 2** connects to the MySQL database hosted on the NTNU virtual machine.

This allows the same project code to be tested locally and then executed on the NTNU infrastructure without changing the main scripts.

## Local MySQL with Docker

For local execution, the project expects a MySQL 8.0 container available on:

```text
host: localhost
port: 3306
database: gruppo_25
user: root
password: root
```

A compatible Docker container can be created with:

```bash
docker run --name porto-mysql \
    -e MYSQL_ROOT_PASSWORD=root \
    -e MYSQL_DATABASE=gruppo_25 \
    -p 3306:3306 \
    -v porto-mysql-data:/var/lib/mysql \
    -d mysql:8.0
```

The Docker volume keeps the database persistent even if the container is stopped or removed.
Only one container using host port `3306` should be active at a time.

## Database structure

The database is composed of three main tables:

- `Taxi`
- `Trip`
- `GPSPoint`

`Taxi` contains the taxi identifiers.

`Trip` contains the information associated with each taxi trip, including call type, start time, number of GPS points and the total trip distance.

`GPSPoint` contains the ordered GPS coordinates associated with each trip.

The relationship is:

```text
Taxi 1 ---- N Trip 1 ---- N GPSPoint
```

The `Trip` table also contains several derived fields that are computed during the population phase and stored directly in the database to improve the performance of the analytical queries:

```text
duration_s
end_time
distance_km
start_lat
start_lon
end_lat
end_lon
```

1. `duration_s` stores the trip duration in seconds, computed as `(point_count - 1) * 15`, or `0` when the trip has no GPS points.
2. `end_time` stores the trip end timestamp, computed as `start_time + duration_s`.
3. `distance_km` stores the total trip distance, calculated as the sum of the Haversine distances between consecutive GPS points.
4. `start_lat` and `start_lon` store the coordinates of the first GPS point of the trip.
5. `end_lat` and `end_lon` store the coordinates of the last GPS point of the trip.

## `populate_clean_database.py`

This script imports the Porto CSV dataset into MySQL.

Its main responsibilities are:

- reading the CSV file;
- validating the expected fields;
- parsing the GPS polyline;
- converting UNIX timestamps to MySQL-compatible `DATETIME` values;
- validating coordinates;
- handling missing values;
- detecting duplicated `TRIP_ID` values;
- excluding conflicting duplicated trips;
- avoiding repeated insertion of identical duplicates;
- inserting taxis, trips and GPS points in batches;
- calculating `point_count`;
- calculating the total distance of every trip using the Haversine formula;
- storing rejected rows and conflicting IDs in separate CSV files;
- printing progress information while the database is populated.

The script uses batch insertion for better performance because the original dataset contains a very large number of rows and GPS points.

The total distance is calculated while the polyline is already available in memory. This avoids having to retrieve all GPS points again later when running analytical queries.

## Query script

The query file contains the implementation of the analytical tasks required by the assignment.

SQL is used whenever the calculation can efficiently be performed by MySQL.

Python is used where additional processing is useful, for example for Haversine distance calculations or result formatting.

Some queries originally required scanning the complete `GPSPoint` table. Since this table contains a very large number of rows, several optimizations were introduced.

For example:

- trip distance is precomputed and stored in `Trip.distance_km`;
- queries that only need the first and last GPS point read the precomputed `start_lat`, `start_lon`, `end_lat`, `end_lon` columns of `Trip` instead of the complete trajectory;
- the City Hall proximity query first applies a geographical bounding-box filter;
- trip duration and end time are precomputed in `Trip.duration_s` and `Trip.end_time`.

These changes significantly reduce execution time and memory usage.

## Database indexes

The only secondary index is used by the City Hall proximity query (query 6), so that the bounding box is a range read on the index instead of a full scan of `GPSPoint`:

```sql
CREATE INDEX idx_gps_lat_lon
ON GPSPoint(latitude, longitude);
```

It is defined in `create_tables.py` and created at the end of `populate_clean_database.py`, after all the data has been inserted, because building it once on the loaded data is much faster than keeping it updated during the import.

The `GPSPoint` table also has the composite primary key:

```text
(trip_id, point_index)
```

which is useful for retrieving ordered points belonging to a specific trip.

## EDA scripts

The `EDA` / exploratory analysis scripts contain utilities used before creating and populating the final database.

These scripts were used to inspect the original CSV file and better understand the dataset before defining the relational schema.

The exploratory analysis includes checks such as:

- total number of rows;
- missing values;
- distribution of call types;
- number of taxis;
- number of GPS points per trip;
- trips with fewer than three GPS points;
- empty polylines;
- duplicated `TRIP_ID` values;
- conflicting duplicate rows;
- general characteristics of the dataset.

The results of this analysis were used to decide how invalid, incomplete and duplicated records should be handled during database population.


## Notes

Some queries can take up to 2–3 minutes to run due to the large amount of data stored in the database.