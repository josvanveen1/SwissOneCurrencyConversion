import json
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, date
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_frankfurter_conversion_rate(amount_eur: float, date: date) -> float:
    """Fetches conversion rate from EUR to USD using Frankfurter API."""
    date_string = date.strftime("%Y-%m-%d")
    url = f"https://api.frankfurter.app/{date_string}?from=EUR&to=USD"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        rate = data.get("rates", {}).get("USD")
        if rate:
            logger.info(f"Frankfurter API: Fetched rate {rate} for {date_string}")
            return amount_eur * rate
        logger.warning(f"Frankfurter API: No USD rate found for {date_string}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Frankfurter API error for {date_string}: {e}")
        return None

def get_currencylayer_historical_rate(date: date) -> float:
    """Fetches historical conversion rate from EUR to USD using Currencylayer API."""
    load_dotenv()
    api_key = os.getenv("CURRENCYLAYER_API_KEY")
    if not api_key:
        logger.error("Currencylayer API key not found")
        return None
    
    date_string = date.strftime("%Y-%m-%d")
    url = f"https://api.currencylayer.com/historical?access_key={api_key}&date={date_string}&source=EUR&currencies=USD"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            rate = data["quotes"]["EURUSD"]
            logger.info(f"Currencylayer historical: Fetched rate {rate} for {date_string}")
            return rate
        logger.warning(f"Currencylayer historical API error: {data.get('error', {}).get('info', 'Unknown error')}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Currencylayer historical error for {date_string}: {e}")
        return None

def get_currencylayer_live_rate() -> float:
    """Fetches live conversion rate from EUR to USD using Currencylayer API."""
    load_dotenv()
    api_key = os.getenv("CURRENCYLAYER_API_KEY")
    if not api_key:
        logger.error("Currencylayer API key not found")
        return None
    
    url = f"https://api.currencylayer.com/live?access_key={api_key}&source=EUR&currencies=USD"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            rate = data["quotes"]["EURUSD"]
            logger.info(f"Currencylayer live: Fetched rate {rate}")
            return rate
        logger.warning(f"Currencylayer live API error: {data.get('error', {}).get('info', 'Unknown error')}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Currencylayer live error: {e}")
        return None

def convert_eur_to_usd(amount_eur: float, date: date) -> float:
    """
    Converts EUR to USD using multiple APIs with fallback strategy.
    Returns the converted amount or None if all attempts fail.
    """
    # Try Frankfurter API first
    result = get_frankfurter_conversion_rate(amount_eur, date)
    if result is not None:
        return result
    
    logger.warning(f"Falling back to Currencylayer historical rate for {date.strftime('%Y-%m-%d')}")
    # Fallback to Currencylayer historical rate
    rate = get_currencylayer_historical_rate(date)
    if rate is not None:
        return amount_eur * rate
    
    # If the date is today, try Currencylayer live rate as a last resort
    if date.date() == datetime.today().date():
        logger.warning("Falling back to Currencylayer live rate")
        rate = get_currencylayer_live_rate()
        if rate is not None:
            return amount_eur * rate
    
    logger.error(f"Failed to fetch conversion rate for {date.strftime('%Y-%m-%d')}")
    return None

if __name__ == "__main__":
    amount = 100
    today = datetime.today()
    result = convert_eur_to_usd(amount, today)
    if result is not None:
        print(f"{amount} EUR on {today.strftime('%Y-%m-%d')} = {result:.2f} USD")
    else:
        print(f"Could not convert {amount} EUR on {today.strftime('%Y-%m-%d')}")