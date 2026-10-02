from DbConnector import DbConnector
from tabulate import tabulate


class Task2:

    def __init__(self):
        self.connection = DbConnector()
        self.db_connection = self.connection.db_connection
        self.cursor = self.connection.cursor

    def query1(self): #query number 1
      

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

        return rows


def main():
    program = None

    try:
        program = Task2()

        #execute query number 1 
        program.query1()

        #execute query number 2

    except Exception as e:
        print("ERROR: Failed to use database:", e)

    finally:
        if program:
            program.connection.close_connection()


if __name__ == '__main__':
    main()