from DbConnector import DbConnector
from tabulate import tabulate
from haversine import haversine, Unit


class Task2:

    def __init__(self):
        self.connection = DbConnector()
        self.db_connection = self.connection.db_connection
        self.cursor = self.connection.cursor

    def query1(self): #query number 1   ( FUNZIONA )
      

        query = """
            SELECT
                (SELECT COUNT(*) FROM Taxi) AS number_of_taxis,
                (SELECT COUNT(*) FROM Trip) AS number_of_trips,
                (SELECT COUNT(*) FROM GPSPoint) AS number_of_gps_points;
        """

        #The three counts could also have been obtained using three separate queries, 
        #each with its own SELECT COUNT(*). Here, they are combined into a single query 
        #so that all three results are returned together in one row.
        
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        print("\nQUERY 1")
        print("How many taxis, trips, and total GPS points are there?\n")
        print(tabulate(rows, headers=self.cursor.column_names))


    def query2(self): #query number 2   ( FUNZIONA )
        """
        SELECT AVG(trip_count) AS average_trips_per_taxi
        FROM (
            SELECT taxi_id, COUNT(*) AS trip_count
            FROM Trip
            GROUP BY taxi_id
        ) AS trips_per_taxi;
        """
        query = """
            SELECT COUNT(*) / COUNT(DISTINCT taxi_id)
            FROM Trip;
        """

        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        print("\nQUERY 2")
        print("What is the average number of trips per taxi?\n")
        print(tabulate(rows, headers=["average_trips_per_taxi"]))


    def query3(self): #query number 3   ( FUNZIONA )
    
        query = """
            SELECT
                taxi_id,
                COUNT(*) AS number_of_trips
            FROM Trip
            GROUP BY taxi_id
            ORDER BY number_of_trips DESC
            LIMIT 20;
        """

        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        print("\nQUERY 3")
        print("Top 20 taxis with the most trips:\n")
        print(tabulate(rows, headers=self.cursor.column_names))


    def query4a(self): #query number 4   ( FUNZIONA )
    
        #4a
        query = """
            SELECT taxi_id, call_type, trip_count
            FROM (
                SELECT
                    taxi_id,
                    call_type,
                    COUNT(*) AS trip_count,
                    RANK() OVER (                   
                        PARTITION BY taxi_id
                        ORDER BY COUNT(*) DESC
                    ) AS ranking
                FROM Trip
                GROUP BY taxi_id, call_type
            ) AS ranked_call_types
            WHERE ranking = 1
            ORDER BY taxi_id;
        """
        #in the query, we use RANK and not ROW_NUMBER because it can detect tie cases.

        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        print("\nQUERY 4a")
        print("What is the most used call type per taxi?:\n")
        print(tabulate(rows, headers=self.cursor.column_names))


    def query4b(self): #query number 4   ( FUNZIONA )

        # 1. Average duration and average distance per call type

        # average trip duration 
        query_average = """
            SELECT
                call_type,
                ROUND(AVG((point_count - 1) * 15 / 60.0), 2) AS avg_duration_minutes
            FROM Trip
            WHERE point_count >= 1
            GROUP BY call_type
            ORDER BY call_type;
        """
        self.cursor.execute(query_average)
        average_rows = self.cursor.fetchall()
        print("\nQUERY 4b: Average trip duration\n")
        print(tabulate(average_rows, headers=self.cursor.column_names))

     



     
       # Get call_type for each trip
        query_trip_types = """
            SELECT trip_id, call_type
            FROM Trip;
        """

        self.cursor.execute(query_trip_types)
        trip_rows = self.cursor.fetchall()

        trip_call_type = {}

        for trip_id, call_type in trip_rows:
            trip_call_type[trip_id] = call_type


        # Get GPS points without JOIN
        query_points = """
            SELECT
                trip_id,
                point_index,
                latitude,
                longitude
            FROM GPSPoint
            ORDER BY trip_id, point_index;
        """

        self.cursor.execute(query_points)

        trip_distances = {}
        previous_point = None
        previous_trip_id = None

        while True:

            rows = self.cursor.fetchmany(10000)

            if not rows:
                break

            for trip_id, point_index, latitude, longitude in rows:

                current_point = (latitude, longitude)
                call_type = trip_call_type[trip_id]

                if trip_id != previous_trip_id:

                    previous_trip_id = trip_id
                    previous_point = current_point

                    if call_type not in trip_distances:
                        trip_distances[call_type] = []

                    trip_distances[call_type].append(0)

                else:

                    distance = haversine(
                        previous_point,
                        current_point,
                        unit=Unit.KILOMETERS
                    )

                    trip_distances[call_type][-1] += distance

                    previous_point = current_point

        print("\nQUERY 4b - Average distance per call type\n")
        for call_type, distances in trip_distances.items():
            average_distance = sum(distances) / len(distances)
            print(  call_type, round(average_distance, 2), "km")
 
        # 2. Share of trips in the four time bands
        query_time_bands = """
            SELECT
                call_type,

                ROUND(
                    100.0 * SUM(CASE
                        WHEN HOUR(start_time) >= 0 AND HOUR(start_time) < 6
                        THEN 1 ELSE 0
                    END) / COUNT(*),
                    2
                ) AS share_00_06,

                ROUND(
                    100.0 * SUM(CASE
                        WHEN HOUR(start_time) >= 6 AND HOUR(start_time) < 12
                        THEN 1 ELSE 0
                    END) / COUNT(*),
                    2
                ) AS share_06_12,

                ROUND(
                    100.0 * SUM(CASE
                        WHEN HOUR(start_time) >= 12 AND HOUR(start_time) < 18
                        THEN 1 ELSE 0
                    END) / COUNT(*),
                    2
                ) AS share_12_18,

                ROUND(
                    100.0 * SUM(CASE
                        WHEN HOUR(start_time) >= 18 AND HOUR(start_time) < 24
                        THEN 1 ELSE 0
                    END) / COUNT(*),
                    2
                ) AS share_18_24

            FROM Trip
            GROUP BY call_type
            ORDER BY call_type;
        """

        self.cursor.execute(query_time_bands)
        time_band_rows = self.cursor.fetchall()

        print("\nQUERY 4b - Starting time bands\n")
        print(tabulate(time_band_rows, headers=self.cursor.column_names))


    def query5(self):

        # Total hours driven per taxi
        query_hours = """
            SELECT
                taxi_id,
                SUM(
                    CASE
                        WHEN point_count >= 1
                        THEN (point_count - 1) * 15 / 3600.0
                        ELSE 0
                    END
                ) AS total_hours
            FROM Trip
            GROUP BY taxi_id;
        """

        self.cursor.execute(query_hours)
        hours_rows = self.cursor.fetchall()

        # Dictionary: taxi_id -> total hours
        taxi_hours = {}

        for taxi_id, total_hours in hours_rows:
            taxi_hours[taxi_id] = float(total_hours)

        # Get GPS points ordered by taxi, trip and point index
        query_distance = """
            SELECT
                t.taxi_id,
                g.trip_id,
                g.point_index,
                g.latitude,
                g.longitude
            FROM Trip t
            JOIN GPSPoint g
                ON t.trip_id = g.trip_id
            ORDER BY t.taxi_id, g.trip_id, g.point_index;
        """

        self.cursor.execute(query_distance)
        rows = self.cursor.fetchall()

        # Dictionary: taxi_id -> total distance
        taxi_distance = {}

        previous_trip_id = None
        previous_point = None

        for taxi_id, trip_id, point_index, latitude, longitude in rows:

            current_point = (latitude, longitude)
            if taxi_id not in taxi_distance:
                taxi_distance[taxi_id] = 0

            # If we are still inside the same trip,
            # calculate distance from previous point
            if trip_id == previous_trip_id:

                distance = haversine(previous_point, current_point, unit=Unit.KILOMETERS )
                taxi_distance[taxi_id] += distance

            previous_trip_id = trip_id
            previous_point = current_point

        # Combine hours and distances
        results = []
        for taxi_id, total_hours in taxi_hours.items():
            total_distance = taxi_distance.get(taxi_id, 0)
            results.append(( taxi_id, round(total_hours, 2), round(total_distance, 2)))

        # Sort by total hours, descending
        results.sort( key=lambda row: row[1], reverse=True )

        print("\nQUERY 5")
        print("Taxis ordered by total hours driven:\n")

        print(tabulate(results, headers=["taxi_id","total_hours", "total_distance_km"]))


    def query6(self):

        city_hall = (41.15794, -8.62911)  # (latitude, longitude)

        query = """
            SELECT
                trip_id,
                latitude,
                longitude
            FROM GPSPoint
            ORDER BY trip_id, point_index;
        """

        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        trips_near_city_hall = set()
        for trip_id, latitude, longitude in rows:

            point = (latitude, longitude)
            distance = haversine(city_hall, point, unit=Unit.METERS )

            if distance <= 100: trips_near_city_hall.add(trip_id)

        results = sorted(trips_near_city_hall)
        print("\nQUERY 6")
        print("Trips that passed within 100 m of Porto City Hall:\n")
        for trip_id in results: print(trip_id)
        print("\nTotal trips:", len(results))

    def query7(self):

        query = """
            SELECT COUNT(*) AS invalid_trips
            FROM Trip
            WHERE point_count < 3;
        """

        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        print("\nQUERY 7")
        print("Number of invalid trips:\n")
        print(tabulate(rows, headers=self.cursor.column_names))


    def query8(self):

        query = """
            SELECT
                trip_id,
                start_time,
                TIMESTAMPADD(SECOND, (point_count - 1) * 15, start_time ) AS end_time
            FROM Trip
            WHERE point_count >= 1
            AND DATE(start_time) <> DATE(
                    TIMESTAMPADD( SECOND, (point_count - 1) * 15, start_time ));
        """

        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        print("\nQUERY 8")
        print("Trips that started on one day and ended on the next:\n")
        print(tabulate(rows, headers=self.cursor.column_names))


    def query9(self):

        query = """
            SELECT
                trip_id,
                point_index,
                latitude,
                longitude
            FROM GPSPoint
            ORDER BY trip_id, point_index;
        """

        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        circular_trips = []

        current_trip_id = None
        start_point = None
        end_point = None

        for trip_id, point_index, latitude, longitude in rows:
            current_point = (latitude, longitude)
            if trip_id != current_trip_id:
                # Check the previous trip
                if current_trip_id is not None and start_point is not None and end_point is not None:
                    distance = haversine( start_point, end_point,unit=Unit.METERS)
                    if distance <= 50:
                        circular_trips.append(current_trip_id)
                # Start a new trip
                current_trip_id = trip_id
                start_point = current_point
                end_point = current_point
            else:
                end_point = current_point


        # Check the last trip
        if current_trip_id is not None and start_point is not None and end_point is not None:
            distance = haversine(start_point, end_point,unit=Unit.METERS)
            if distance <= 50:
                circular_trips.append(current_trip_id)

        print("\nQUERY 9")
        print("Circular trips:\n")
        for trip_id in circular_trips: print(trip_id)
        print("\nTotal circular trips:", len(circular_trips))


    def query10(self):

        query = """
            SELECT
                taxi_id,
                ROUND(AVG(idle_seconds) / 60.0, 2) AS avg_idle_minutes
            FROM (
                SELECT
                    taxi_id,
                    TIMESTAMPDIFF(
                        SECOND,
                        TIMESTAMPADD( SECOND, (point_count - 1) * 15, start_time),
                        LEAD(start_time) OVER (PARTITION BY taxi_id ORDER BY start_time)
                    ) AS idle_seconds
                FROM Trip
                WHERE point_count >= 1
            ) AS idle_times

            WHERE idle_seconds >= 0
            GROUP BY taxi_id
            ORDER BY avg_idle_minutes DESC
            LIMIT 20;
        """

        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        print("\nQUERY 10")
        print("Top 20 taxis with the highest average idle time:\n")
        print(tabulate(rows, headers=self.cursor.column_names))

        return rows


def main():
    program = None

    try:
        program = Task2()

        #program.query1() testata funziona 

        #program.query2() worka

        #program.query3() worka

        #program.query4a() worka

        program.query4b()

        program.query5()

        program.query6()

        program.query7()

        program.query8()

        program.query9()

        program.query10()

    except Exception as e:
        print("ERROR: Failed to use database:", e)

    finally:
        if program:
            program.connection.close_connection()


if __name__ == '__main__':
    main()