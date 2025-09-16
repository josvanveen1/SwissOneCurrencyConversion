from web_scraper import extract_historical_prices
from database_client import DatabaseClient
from currency_convert import convert_eur_to_usd
from chart import plot_historical_prices
from file_reader import parse_stock_data
import datetime
import os
from dotenv import load_dotenv

def string_to_float(historical_prices):
    closing_prices_eur = []
    for row in historical_prices:
        if 'Schluss [EUR]' in row:
            value = row['Schluss [EUR]'].replace('.', '').replace(',', '.')
            try:
                closing_prices_eur.append(float(value))
            except ValueError:
                print(f"Warning: Could not convert value '{row['Schluss [EUR]']}' to float.")

    return closing_prices_eur

def reverse_array(arr):
    reverse_array = []
    for i in range(len(arr)-1, -1, -1):
        reverse_array.append(arr[i])

    return reverse_array

def serialize_chart_data(chart_data):
    for item in chart_data["labels"]:
        item = str(item)
    return chart_data

def populate_database():
    load_dotenv()
    db = DatabaseClient(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        sslmode="allow"
    )
    db.connect()

    historical_prices = extract_historical_prices()
    closing_prices_eur = string_to_float(historical_prices)
    # dates, opens, highs, lows, closing_prices_eur, volumes = parse_stock_data("src/stock_data.txt")

    dates = ([row['Datum'] for row in historical_prices])
    new_dates = []
    for date_str in dates:
        day, month, year = map(int, date_str.split('.'))
        date_object = datetime.date(int(year), int(month), int(day))
        new_dates.append(date_object)


    closing_price_usd = convert_eur_to_usd(closing_prices_eur)
    print(new_dates)

    for date, price, price_eur in zip(new_dates, closing_price_usd, closing_prices_eur):
        db.insert_price(price, price_eur, date)

    db.disconnect()

def get_dates_from(date):
    today = datetime.date.today()
    delta = today - date
    dates = [date + datetime.timedelta(days=i) for i in range(delta.days + 1)]
    return dates

def create_finance_schema_and_table():
    load_dotenv()
    db = DatabaseClient(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    db.connect()
    try:
        db.cursor.execute("""
            CREATE SCHEMA IF NOT EXISTS finance;
            CREATE TABLE IF NOT EXISTS finance.daily_prices (
                price_date DATE PRIMARY KEY,
                price FLOAT
            );
        """)
        db.connection.commit()
        print("Schema and table created or already exist.")
    except Exception as e:
        print(f"Error creating schema/table: {e}")
    finally:
        db.disconnect()

def update_values_on_currency_change():
    load_dotenv()
    db = DatabaseClient(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    db.connect()
    try:
        db.cursor.execute("SELECT price_date, price_eur FROM finance.daily_prices;")
        rows = db.cursor.fetchall()

        date = [row[0] for row in rows]
        price_eur = [row[1] for row in rows]
        price_usd = convert_eur_to_usd(price_eur)
        for d, p in zip(date, price_usd):
            try:
                db.cursor.execute("""
                        UPDATE finance.daily_prices
                        SET price = %s
                        WHERE price_date = %s;
                    """, (p, d))
            except Exception as e:
                print(f"Error updating price for {d}: {e}")

    except Exception as e:
        print(f"Error updating prices: {e}")
    finally:
        db.disconnect()

if __name__ == "__main__":
    update_values_on_currency_change()