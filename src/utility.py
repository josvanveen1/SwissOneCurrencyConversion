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

    closing_price_usd = []
    for i in len(closing_prices_eur):
        closing_price_usd.append(convert_eur_to_usd(closing_prices_eur[i], new_dates[i]))

    print(new_dates)

    for date, price, price_eur in zip(new_dates, closing_price_usd, closing_prices_eur):
        db.insert_price(price, price_eur, date)

    db.disconnect()

def populate_new_data_database():
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

    dates = ([row['Datum'] for row in historical_prices])
    new_dates = []
    for date_str in dates:
        day, month, year = map(int, date_str.split('.'))
        date_object = datetime.date(int(year), int(month), int(day))
        new_dates.append(date_object)

    print(new_dates)

    for date, price_eur in zip(new_dates, closing_prices_eur):
        if not db.price_exists(date):
            price_usd = convert_eur_to_usd(price_eur, date)
            db.insert_price(price_usd, price_eur, date)

    db.disconnect()

def update_conversion_rates():
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

    prices = db.read_all_prices()
    for price_date, price, price_eur in prices:
        usd = convert_eur_to_usd(float(price_eur), price_date)
        db.update_price(price_date=price_date, price=usd)

    db.disconnect()

# New function to populate EURtoUSD_fx_rate column
def populate_fx_rate_column():
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

    import csv

    # Load FX rates from ECB CSV file into a dictionary
    fx_rates = {}
    csv_path = os.path.join(os.path.dirname(__file__), '../EuropeanCentralBank_Euro_FX - eurofxref-hist.csv')
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            date_str = row['Date']
            usd_rate = row['USD']
            if usd_rate and usd_rate != 'N/A':
                fx_rates[date_str] = float(usd_rate)

    prices = db.read_all_prices()
    for price_date, price, price_eur in prices:
        # Convert price_date to string in YYYY-MM-DD format
        date_str = price_date.strftime('%Y-%m-%d')
        fx_rate = fx_rates.get(date_str)
        if fx_rate is not None:
            try:
                query = """
                    UPDATE finance.daily_prices
                    SET EURtoUSD_fx_rate = %s
                    WHERE price_date = %s;
                """
                db.cursor.execute(query, (fx_rate, price_date))
                db.connection.commit()
                print(f"Updated EURtoUSD_fx_rate for {price_date}: {fx_rate}")
            except Exception as e:
                print(f"Error updating EURtoUSD_fx_rate for {price_date}: {e}")
        else:
            print(f"No FX rate found for {price_date}")
    db.disconnect()

def get_dates_from(start_date):
    today = datetime.date.today()
    delta = today - start_date
    dates = [start_date + datetime.timedelta(days=i) for i in range(delta.days + 1)]
    return dates

def update_price_with_fx_rate():
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

    # Read all prices and FX rates
    query = """
        SELECT price_date, price_eur, EURtoUSD_fx_rate
        FROM finance.daily_prices;
    """
    db.cursor.execute(query)
    rows = db.cursor.fetchall()

    for price_date, price_eur, fx_rate in rows:
        if price_eur is not None and fx_rate is not None:
            new_price = float(price_eur) * float(fx_rate)
            try:
                update_query = """
                    UPDATE finance.daily_prices
                    SET price = %s
                    WHERE price_date = %s;
                """
                db.cursor.execute(update_query, (new_price, price_date))
                db.connection.commit()
                print(f"Updated price for {price_date}: {new_price}")
            except Exception as e:
                print(f"Error updating price for {price_date}: {e}")
        else:
            print(f"Missing price_eur or EURtoUSD_fx_rate for {price_date}")
    db.disconnect()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Utility functions for SwissOneCurrencyConversion")
    parser.add_argument("--function", type=str, required=True, choices=[
        "update_conversion_rates",
        "populate_database",
        "populate_new_data_database",
        "populate_fx_rate_column",
        "update_price_with_fx_rate"
    ], help="Function to execute")
    args = parser.parse_args()

    if args.function == "update_conversion_rates":
        update_conversion_rates()
    elif args.function == "populate_database":
        populate_database()
    elif args.function == "populate_new_data_database":
        populate_new_data_database()
    elif args.function == "populate_fx_rate_column":
        populate_fx_rate_column()
    elif args.function == "update_price_with_fx_rate":
        update_price_with_fx_rate()