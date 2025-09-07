import psycopg2
from psycopg2 import Error
from datetime import date

class DatabaseClient:
    def __init__(self, host, port, dbname, user, password, sslmode="require"):
        """Initialize the database connection."""
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.sslmode = sslmode
        self.connection = None
        self.cursor = None
        

    def connect(self):
        """Establish a connection to the PostgreSQL database."""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                sslmode=self.sslmode  # Ensure SSL connection
            )
            self.cursor = self.connection.cursor()
            print("Database connection established.")
        except Error as e:
            print(f"Error connecting to database: {e}")
            raise

    def disconnect(self):
        """Close the database connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            print("Database connection closed.")
        
    def insert_price(self, price: float, price_date: date):
        """Insert a new price for a given date"""
        try:
            query = """
            INSERT INTO finance.daily_prices (price_date, price)
            VALUES (%s, %s)
            ON CONFLICT (price_date) DO NOTHING;
            """
            self.cursor.execute(query, (price_date, price))
            self.connection.commit()
            print(f"Inserted/Updated price {price} for date {price_date}.")
        except Error as e:
            print(f"Error inserting price: {e}")
            self.connection.rollback()

    def read_price(self, price_date: date):
        """Read the price for a given date"""
        try:
            query = "SELECT price FROM finance.daily_prices WHERE price_date = %s;"
            self.cursor.execute(query, (price_date,))
            result = self.cursor.fetchone()
            if result:
                return result[0]
            else:
                print(f"No price found for date {price_date}.")
                return None
        except Error as e:
            print(f"Error reading price: {e}")
            return None

    def read_price_range(self, start_date: date, end_date: date):
        """Read prices for a date range, inclusive."""
        try:
            query = """
                SELECT price_date, price
                FROM finance.daily_prices
                WHERE price_date BETWEEN %s AND %s
                ORDER BY price_date;
            """
            self.cursor.execute(query, (start_date, end_date))
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error reading price range: {e}")
            return []


    def __enter__(self):
        """Support for context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Support for context manager exit."""
        self.disconnect()


if __name__ == "__main__":
    # Example usage
    db = DatabaseClient(
        host="127.0.0.1",
        port="5432",
        dbname="swiss_one",
        user="postgres",
        password="SillyTwit222"
    )
    try:
        db.connect()
        db.insert_price(100.5, date(2023, 10, 1))
        price = db.read_price(date(2023, 10, 1))
    finally:
        db.disconnect()