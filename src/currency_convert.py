import json
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, date

def get_conversion_rate():
    """
    Fetches the live conversion rate from EUR to USD using Currencylayer API.
    Returns the conversion rate as a float or None if the request fails.
    """
    load_dotenv()
    api_key = os.getenv("CURRENCYLAYER_API_KEY")  # Replace with your Currencylayer API key
    url = f"https://api.currencylayer.com/live?access_key={api_key}&source=EUR&currencies=USD"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        
        if data.get("success"):
            return data["quotes"]["EURUSD"]
        else:
            print(data)
            print(f"API error: {data.get('error', {}).get('info', 'Unknown error')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def get_historical_conversion_rate(date: date):
    load_dotenv()
    api_key = os.getenv("CURRENCYLAYER_API_KEY")
    date_string = date.strftime("%Y-%m-%d")
    url = f"https://api.currencylayer.com/historical?access_key={api_key}&date={date_string}&source=EUR&currencies=USD"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data.get("success"):
            return data["quotes"]["EURUSD"]
        else:
            print(data)
            print(f"API error: {data.get('error', {}).get('info', 'Unknown error')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# def convert_eur_to_usd(amount, date):
#     rate = get_historical_conversion_rate(date)
#     return float(amount) * rate

def convert_eur_to_usd(amount_eur, date):
    load_dotenv()
    api_key = os.getenv("CURRENCYLAYER_API_KEY")
    url = f"https://api.currencylayer.com/convert?access_key={api_key}&from=EUR&to=EUR&amount={amount_eur}&date={date}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data.get("success"):
            return data["result"]
        else:
            print("API ERROR:")
            print(data)
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None
    

if __name__=="__main__":
    print(convert_eur_to_usd(100, datetime.today()))