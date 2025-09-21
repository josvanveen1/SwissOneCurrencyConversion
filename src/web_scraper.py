from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
import random
import logging
import json
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_page_with_retries(max_retries=3):
    ua = UserAgent()  # For random user agents
    options = Options()
    options.add_argument('--headless')  # Headless mode
    options.add_argument('--no-sandbox')  # Required for Render
    options.add_argument('--disable-dev-shm-usage')  # Avoid memory issues in containers
    options.add_argument(f'--user-agent={ua.random}')  # Random user agent
    options.add_argument('--disable-blink-features=AutomationControlled')  # Hide Selenium
    options.add_experimental_option('excludeSwitches', ['enable-automation'])  # Hide automation flags
    options.add_argument('accept-language=en-US,en;q=0.9')
    options.add_argument('accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')

    # Optional: Proxy setup (use a paid residential proxy service like BrightData or Smartproxy)
    # proxy = "http://username:password@proxy_host:port"
    # options.add_argument(f'--proxy-server={proxy}')

    driver = None
    url = "https://www.boerse-duesseldorf.de/etc/DE000A4AJWY5/encore-issuances-s-a-comp-102-oend-z-25-unl-swissone-idx/#instrument-historie"

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries} to load page")
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(30)  # Prevent hanging

            # Navigate and handle potential cookie banner
            driver.get(url)
            time.sleep(random.uniform(3, 7))  # Random delay for JS to load

            # Check for cookie consent (adjust selector based on site)
            try:
                cookie_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.accept-cookies, [id*="cookie-accept"]'))
                )
                cookie_button.click()
                logger.info("Accepted cookie banner")
                time.sleep(random.uniform(1, 3))
            except:
                logger.info("No cookie banner found")

            # Check for paywall/402
            if "402" in driver.page_source or "Payment Required" in driver.page_source:
                logger.error("Encountered 402 Payment Required")
                return None

            # Wait for the history section to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'instrument-historie'))
            )

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            return soup
        except Exception as e:
            logger.error(f"Error loading page: {e}")
            if attempt < max_retries - 1:
                time.sleep(random.uniform(5, 10))  # Wait before retry
            continue
        finally:
            if driver:
                driver.quit()
    logger.error("Failed to load page after max retries")
    return None

def extract_historical_prices():
    soup = get_page_with_retries()
    if not soup:
        logger.error("No page content to parse")
        return []

    historical_data = []
    cache_file = 'historical_data.json'

    # Check cache to avoid unnecessary scraping
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            cached_data = json.load(f)
        last_cached_date = max(cached_data, key=lambda x: x.get('Date', ''), default={}).get('Date', '')
        if last_cached_date >= time.strftime('%Y-%m-%d'):  # Cache valid for today
            logger.info("Using cached data")
            return cached_data

    # Find the historical section
    hist_section = soup.find('div', id='instrument-historie')
    if hist_section:
        table = hist_section.find('table', class_='kurs-table') or hist_section.find('table')
        if table:
            headers = [th.text.strip() for th in table.find('thead').find_all('th')]
            tbody = table.find('tbody')
            if tbody:
                for tr in tbody.find_all('tr'):
                    cells = [td.text.strip() for td in tr.find_all('td')]
                    if len(cells) == len(headers):
                        row = dict(zip(headers, cells))
                        historical_data.append(row)
                logger.info(f"Extracted {len(historical_data)} rows")
                
                # Cache results
                with open(cache_file, 'w') as f:
                    json.dump(historical_data, f)
            else:
                logger.error("No table body found")
        else:
            logger.error("No table found in history section")
    else:
        logger.error("No instrument-historie section found")
    
    return historical_data

if __name__ == "__main__":
    data = extract_historical_prices()
    if data:
        print(json.dumps(data, indent=2))
    else:
        print("No data extracted")