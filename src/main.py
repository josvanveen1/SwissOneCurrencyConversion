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

def reverse_array(arr):
    reverse_array = []
    for i in range(len(arr)-1, -1, -1):
        reverse_array.append(arr[i])

    return reverse_array


def main():
    historical_prices = extract_historical_prices()
    closing_prices_eur = string_to_float(historical_prices)

    dates = reverse_array([row['Datum'] for row in historical_prices])
    closing_price_usd = reverse_array(convert_eur_to_usd(closing_prices_eur)) 
    return dates, closing_price_usd

    plot_historical_prices(dates, closing_price_usd) 

if __name__ == "__main__":
    print(reverse_array([1, 2, 3, 4, 5]))