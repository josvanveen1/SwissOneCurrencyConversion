from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

def get_page():
    # Set up Selenium with Chrome
    options = Options()
    options.add_argument('--headless')  # Run in headless mode (no browser window)
    driver = webdriver.Chrome(options=options)  # Assume chromedriver is in PATH

    url = "https://www.boerse-duesseldorf.de/etc/DE000A4AJWY5/encore-issuances-s-a-comp-102-oend-z-25-unl-swissone-idx/#instrument-historie"

    # Load the page
    driver.get(url)
    time.sleep(5)  # Wait for JavaScript to load content (adjust if needed)

    # Get the page source and parse with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    # Close the driver
    driver.quit()

    return soup

# Function to extract historical price data
def extract_historical_prices():
    soup = get_page()
    historical_data = []
    # Find the historical section by id
    hist_section = soup.find('div', id='instrument-historie')
    if hist_section:
        # Find the table within the section
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
    return historical_data
