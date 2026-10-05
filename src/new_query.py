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
        print(tabulate(rows, headers="average_trips_per_taxi"))


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


    def query4b(self):

        # 1. Average trip duration

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
        print(
            tabulate(
                average_rows,
                headers=self.cursor.column_names
            )
        )


        # 2. Average distance per call type

        query_distance = """
            SELECT
                call_type,
                ROUND(AVG(distance_km), 2) AS avg_distance_km
            FROM Trip
            WHERE distance_km IS NOT NULL
            GROUP BY call_type
            ORDER BY call_type;
        """

        self.cursor.execute(query_distance)
        distance_rows = self.cursor.fetchall()

        print("\nQUERY 4b - Average distance per call type\n")
        print(
            tabulate(
                distance_rows,
                headers=self.cursor.column_names
            )
        )


        # 3. Share of trips in the four time bands

        query_time_bands = """
            SELECT
                call_type,

                ROUND(
                    100.0 * SUM(
                        CASE
                            WHEN HOUR(start_time) >= 0
                            AND HOUR(start_time) < 6
                            THEN 1
                            ELSE 0
                        END
                    ) / COUNT(*),
                    2
                ) AS share_00_06,

                ROUND(
                    100.0 * SUM(
                        CASE
                            WHEN HOUR(start_time) >= 6
                            AND HOUR(start_time) < 12
                            THEN 1
                            ELSE 0
                        END
                    ) / COUNT(*),
                    2
                ) AS share_06_12,

                ROUND(
                    100.0 * SUM(
                        CASE
                            WHEN HOUR(start_time) >= 12
                            AND HOUR(start_time) < 18
                            THEN 1
                            ELSE 0
                        END
                    ) / COUNT(*),
                    2
                ) AS share_12_18,

                ROUND(
                    100.0 * SUM(
                        CASE
                            WHEN HOUR(start_time) >= 18
                            AND HOUR(start_time) < 24
                            THEN 1
                            ELSE 0
                        END
                    ) / COUNT(*),
                    2
                ) AS share_18_24

            FROM Trip
            GROUP BY call_type
            ORDER BY call_type;
        """

        self.cursor.execute(query_time_bands)
        time_band_rows = self.cursor.fetchall()

        print("\nQUERY 4b - Starting time bands\n")
        print(
            tabulate(
                time_band_rows,
                headers=self.cursor.column_names
            )
        )


    def query5(self):

        query = """
            SELECT
                taxi_id,

                ROUND(
                    SUM(
                        CASE
                            WHEN point_count >= 1
                            THEN (point_count - 1) * 15 / 3600.0
                            ELSE 0
                        END
                    ),
                    2
                ) AS total_hours,

                ROUND(
                    SUM(
                        CASE
                            WHEN distance_km IS NOT NULL
                            THEN distance_km
                            ELSE 0
                        END
                    ),
                    2
                ) AS total_distance_km

            FROM Trip

            GROUP BY taxi_id

            ORDER BY total_hours DESC;
        """

        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        print("\nQUERY 5")
        print("Taxis ordered by total hours driven:\n")

        print(
            tabulate(
                rows,
                headers=self.cursor.column_names
            )
        )

        return rows


    def query6(self):

        city_hall = (41.15794, -8.62911)

        # Approximate bounding box of 100 m around Porto City Hall
        lat_min = 41.15794 - 0.0009
        lat_max = 41.15794 + 0.0009
        lon_min = -8.62911 - 0.0012
        lon_max = -8.62911 + 0.0012

        query = """
            SELECT
                trip_id,
                latitude,
                longitude
            FROM GPSPoint
            WHERE latitude BETWEEN %s AND %s
            AND longitude BETWEEN %s AND %s;
        """

        self.cursor.execute(
            query,
            (lat_min, lat_max, lon_min, lon_max)
        )

        trips_near_city_hall = set()

        while True:

            rows = self.cursor.fetchmany(10000)

            if not rows:
                break

            for trip_id, latitude, longitude in rows:

                point = (latitude, longitude)

                distance = haversine(
                    city_hall,
                    point,
                    unit=Unit.METERS
                )

                if distance <= 100:
                    trips_near_city_hall.add(trip_id)

        results = sorted(trips_near_city_hall)

        print("\nQUERY 6")
        print("Trips that passed within 100 m of Porto City Hall:\n")

        for trip_id in results:
            print(trip_id)

        print("\nTotal trips:", len(results))

        return results

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
                t.trip_id,

                g_start.latitude,
                g_start.longitude,

                g_end.latitude,
                g_end.longitude

            FROM Trip t

            JOIN GPSPoint g_start
                ON g_start.trip_id = t.trip_id
                AND g_start.point_index = 0

            JOIN GPSPoint g_end
                ON g_end.trip_id = t.trip_id
                AND g_end.point_index = t.point_count - 1

            WHERE t.point_count >= 2;
        """

        self.cursor.execute(query)

        circular_trips = []

        while True:

            rows = self.cursor.fetchmany(10000)

            if not rows:
                break

            for trip_id, start_lat, start_lon, end_lat, end_lon in rows:

                start_point = (start_lat, start_lon)
                end_point = (end_lat, end_lon)

                distance = haversine(
                    start_point,
                    end_point,
                    unit=Unit.METERS
                )

                if distance <= 50:
                    circular_trips.append(trip_id)


        print("\nQUERY 9")
        print("Circular trips:\n")

        for trip_id in circular_trips:
            print(trip_id)

        print("\nTotal circular trips:", len(circular_trips))

        return circular_trips


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

        program.query1() 

        program.query2() 

        program.query3() 

        program.query4a() 

        program.query4b()  

        print("testo la query 5"); 
        program.query5()

        #new index used 
        print("testo la query 6");     
        program.query6()
        
        print("testo la query 7");           
        program.query7()

        print("testo la query 8");            
        program.query8()

        print("testo la query 9");         
        program.query9()
        
        print("testo la query 10");            
        program.query10()

    except Exception as e:
        print("ERROR: Failed to use database:", e)

    finally:
        if program:
            program.connection.close_connection()


if __name__ == '__main__':
    main()