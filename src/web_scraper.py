from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random
import logging
from fake_useragent import UserAgent
from retrying import retry

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Optional: Proxy list (you can use a proxy service like BrightData, Oxylabs, or free proxies)
PROXIES = [
    # Example: 'http://proxy1:port',
    # Add proxies here or use a proxy service API
]

def get_random_proxy():
    return random.choice(PROXIES) if PROXIES else None

def retry_if_exception(exception):
    """Retry on specific exceptions."""
    return isinstance(exception, (Exception,))

@retry(retry_on_exception=retry_if_exception, stop_max_attempt_number=3, wait_fixed=2000)
def get_page():
    """Fetch the page using Selenium with anti-detection measures."""
    # Initialize User-Agent rotator
    ua = UserAgent()
    user_agent = ua.random
    logger.info(f"Using User-Agent: {user_agent}")

    # Set up Selenium with Chrome
    options = Options()
    options.add_argument('--headless')  # Run in headless mode
    options.add_argument(f'--user-agent={user_agent}')
    options.add_argument('--disable-blink-features=AutomationControlled')  # Avoid detection
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')  # Set a realistic window size
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    # Optional: Add proxy
    proxy = get_random_proxy()
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
        logger.info(f"Using proxy: {proxy}")

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user_agent})

        url = "https://www.boerse-duesseldorf.de/etc/DE000A4AJWY5/encore-issuances-s-a-comp-102-oend-z-25-unl-swissone-idx/#instrument-historie"
        logger.info(f"Fetching URL: {url}")

        # Load the page
        driver.get(url)

        # Wait for the table to load (adjust selector as needed)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'instrument-historie'))
        )

        # Random delay to mimic human behavior
        time.sleep(random.uniform(3, 7))

        # Scroll to ensure all dynamic content loads (optional)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1, 3))

        # Get the page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        return soup
    except Exception as e:
        logger.error(f"Error loading page: {e}")
        raise
    finally:
        if driver:
            driver.quit()
            logger.info("Browser closed")

def extract_historical_prices():
    """Extract historical price data from the page."""
    soup = get_page()
    if not soup:
        logger.error("Failed to retrieve page content")
        return []

    historical_data = []
    try:
        # Find the historical section by id
        hist_section = soup.find('div', id='instrument-historie')
        if not hist_section:
            logger.warning("Historical section not found")
            return []

        # Find the table within the section
        table = hist_section.find('table', class_='kurs-table') or hist_section.find('table')
        if not table:
            logger.warning("Table not found in historical section")
            return []

        # Extract headers
        headers = [th.text.strip() for th in table.find('thead').find_all('th')]
        logger.info(f"Found headers: {headers}")

        # Extract rows
        tbody = table.find('tbody')
        if not tbody:
            logger.warning("Table body not found")
            return []

        for tr in tbody.find_all('tr'):
            cells = [td.text.strip() for td in tr.find_all('td')]
            if len(cells) == len(headers):
                row = dict(zip(headers, cells))
                historical_data.append(row)
            else:
                logger.warning(f"Skipping row with mismatched columns: {cells}")

        logger.info(f"Extracted {len(historical_data)} rows of historical data")
        return historical_data
    except Exception as e:
        logger.error(f"Error extracting data: {e}")
        return []

def main():
    """Main function to run the scraper."""
    # Check robots.txt (manually or programmatically)
    logger.info("Please ensure scraping complies with the website's terms of service and robots.txt")
    
    # Run the scraper
    data = extract_historical_prices()
    if data:
        for row in data:
            print(row)
    else:
        logger.error("No data extracted")

if __name__ == "__main__":
    main()