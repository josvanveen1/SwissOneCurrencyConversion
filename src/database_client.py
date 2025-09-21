import psycopg2
from psycopg2 import Error
from datetime import date

class DatabaseClient:
    def __init__(self, host, port, dbname, user, password, sslmode="allow"):
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

    def insert_price(self, price: float, price_eur: float, price_date: date):
        """Insert a new price for a given date"""
        try:
            query = """
            INSERT INTO finance.daily_prices (price_date, price, price_eur)
            VALUES (%s, %s, %s)
            ON CONFLICT (price_date) DO NOTHING;
            """
            self.cursor.execute(query, (price_date, price, price_eur))
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
                SELECT price_date, price, price_eur
                FROM finance.daily_prices
                WHERE price_date BETWEEN %s AND %s
                ORDER BY price_date;
            """
            self.cursor.execute(query, (start_date, end_date))
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error reading price range: {e}")
            return []

    def read_all_prices(self):
        """Retrieve all price entries from the database."""
        try:
            query = """
                SELECT price_date, price, price_eur
                FROM finance.daily_prices
                ORDER BY price_date;
            """
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error reading all prices: {e}")
            return []
    
    def update_price(self, price_date: date, price: float = None, price_eur: float = None):
        """Update price and/or price_eur for a given date."""
        try:
            fields = []
            values = []
            if price is not None:
                fields.append("price = %s")
                values.append(price)
            if price_eur is not None:
                fields.append("price_eur = %s")
                values.append(price_eur)
            if not fields:
                print("No fields to update.")
                return
            query = f"""
                UPDATE finance.daily_prices
                SET {', '.join(fields)}
                WHERE price_date = %s;
            """
            values.append(price_date)
            self.cursor.execute(query, tuple(values))
            self.connection.commit()
            print(f"Updated price entry for date {price_date}.")
        except Error as e:
            print(f"Error updating price: {e}")
            self.connection.rollback()


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