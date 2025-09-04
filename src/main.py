from web_scraper import extract_historical_prices
from currency_convert import convert_eur_to_usd
from chart import plot_historical_prices

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


def main():
    historical_prices = extract_historical_prices()
    closing_prices_eur = string_to_float(historical_prices)

    dates = [row['Datum'] for row in historical_prices]
    closing_price_usd = convert_eur_to_usd(closing_prices_eur) 

    plot_historical_prices(dates, closing_price_usd) 

if __name__ == "__main__":
    main()