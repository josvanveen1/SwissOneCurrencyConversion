import json
import requests

def get_conversion_rate():
    """
    Fetches the live conversion rate from EUR to USD using Currencylayer API.
    Returns the conversion rate as a float or None if the request fails.
    """
    api_key = "bbc1a75d1d2515f03d362082e32fadc5"  # Replace with your Currencylayer API key
    url = f"https://api.currencylayer.com/live?access_key={api_key}&source=EUR&currencies=USD"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        
        if data.get("success"):
            return data["quotes"]["EURUSD"]
        else:
            print(f"API error: {data.get('error', {}).get('info', 'Unknown error')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def convert_eur_to_usd(amount):
    rate = get_conversion_rate()
    amount_usd = []
    for i in amount:
        amount_usd.append(i * rate)
    return amount_usd

if __name__=="__main__":
    print(convert_eur_to_usd([100, 200, 300, 400, 11]))  # Example usage