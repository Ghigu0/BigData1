import mysql.connector as mysql


class DbConnector:
    """
    this code has been modified, so the program can be runned both on the VM or in local if a docker container is been used.
    The container was created like this:
    docker run --name porto-mysql \
        -e MYSQL_ROOT_PASSWORD=root \
        -e MYSQL_DATABASE=gruppo_25 \
        -p 3306:3306 \
        -v porto-mysql-data:/var/lib/mysql \
        -d mysql:8.0

    """

    def __init__(self):

        print("Choose where to run the program:")
        print("1 - Local MySQL")
        print("2 - NTNU VM")

        choice = input("Enter 1 or 2: ")

        if choice == "1":
            HOST = "localhost"
            DATABASE = "gruppo_25"
            USER = "root"
            PASSWORD = "root"

        elif choice == "2":
            HOST = "tdt4225-25.idi.ntnu.no"
            DATABASE = "gruppo_25"
            USER = "gruppo25"
            PASSWORD = "gruppo25"

        else:
            raise ValueError("Invalid choice. Please enter 1 or 2.")

        # Connect to the database
        try:
            self.db_connection = mysql.connect(host=HOST, database=DATABASE, user=USER, password=PASSWORD, port=3306)
        except Exception as e:
            print("ERROR: Failed to connect to db:", e)

        # Get the db cursor
        self.cursor = self.db_connection.cursor()

        print("Connected to:", self.db_connection.get_server_info())
        # get database information
        self.cursor.execute("select database();")
        database_name = self.cursor.fetchone()
        print("You are connected to the database:", database_name)
        print("-----------------------------------------------\n")

    def close_connection(self):
        # close the cursor
        self.cursor.close()
        # close the DB connection
        self.db_connection.close()
        print("\n-----------------------------------------------")
        print("Connection to %s is closed" % self.db_connection.get_server_info())
