import argparse
import json
import logging
from time import sleep
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Argparse
parser = argparse.ArgumentParser(description="Get available domains from Dynadot")
parser.add_argument("-n", "--name", type=str, help="Domain name (before the dot)", required=True)
parser.add_argument("-o", "--output-file", type=str, help="Output file (JSON)")
parser.add_argument("-p", "--max-price", type=float, help="Maximum price")
parser.add_argument("-r", "--max-renewal", type=float, help="Maximum renewal price")
parser.add_argument("-l", "--max-tld-len", type=int, help="Maximum length of TLD")
parser.add_argument("-t", "--tlds", type=str, help="TLDs to search for (comma separated)")
parser.add_argument("--slds", action="store_true", help="Include SLDs (like .co.uk)", default=False)
parser.add_argument("--non-ascii", action="store_true", help="Include non-ASCII TLDs", default=False)
args = parser.parse_args()

# Set up the WebDriver
logging.info("Setting up the WebDriver...")
chrome_options = Options()
chrome_options.add_argument("--headless")  # Ensure GUI is off
driver = webdriver.Chrome(options=chrome_options)

# Navigate to the Dynadot search page
logging.info("Navigating to the Dynadot search page...")
driver.get("https://www.dynadot.com/domain/search")

# Find the domain search input element and enter your domain name
logging.info("Looking for the domain search input element...")
driver.find_element(By.ID, "search-domain-input").send_keys(args.name)

# Find and click the search button
logging.info('Clicking the search button...')
driver.find_element(By.ID, "search-button").click()

# Find and click the "accept_button" button (to dismiss the privacy policy popup)
logging.info('Clicking the "accept-privacy" button...')
try:
    WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CLASS_NAME, "accept_button"))).click()
except TimeoutException:
    logging.info('"accept-privacy" button not found. Continuing...')

# Wait for the "view-more-button" element to be visible. While it's visible, click it
logging.info('Clicking the "view-more-button" button until all domains are loaded...')
attempts_left = 2
while attempts_left > 0:
    try:
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "see-more-group"))).click()
    except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
        logging.info("That's it? Will retry in 5 seconds, just in case...")
        sleep(5)
        attempts_left -= 1

        # Check if search quota exceeded (class "domain-search-result-error" is visible)
        if driver.find_element(By.CLASS_NAME, "domain-search-result-error").is_displayed():
            logging.info("Search quota exceeded. Maybe try again later? Exiting...")
            driver.quit()
            exit(1)

# Save contents and close the WebDriver
page_contents = driver.page_source
driver.quit()

# Parse the HTML. We want to find the first div with class="domain-search-result"
logging.info("Done with Selenium! Parsing the HTML with BeautifulSoup...")
soup = BeautifulSoup(page_contents, "html.parser")
search_result = soup.find("div", {"class": "domain-search-result"})
assert isinstance(search_result, Tag)

# Build the list of available domains
domains = {}
currency = None

# Each domain is in a div.class="search-row"
for div in search_result.find_all("div", {"class": "search-row"}):

    # If the div contains the "search-shop-cart" icon, it's available
    if div.find("div", {"class": "search-shop-cart"}):
        
        # Get TLD from the "row-tld" attribute of the search-row div
        tld = div["row-tld"]

        # Get name, price, renewal from classes search-domain, search-price & search-renewal
        name = div.find("div", {"class": "search-domain"}).text
        price = div.find("div", {"class": "search-price"}).text

        # Divs come twice, 1 with and 1 without renewal. If there's no renewal, skip
        try: renewal = div.find("div", {"class": "search-renewal"}).text
        except AttributeError: continue

        if not currency:
            currency = price[0]

        # Convert price and renewal to floats
        price = float("".join([c for c in price if c.isdigit() or c == "."]))
        renewal = float("".join([c for c in renewal if c.isdigit() or c == "."]))

        # If conditions are met, add the domain to the list
        if (
            (not args.max_price or price <= args.max_price)
            and (not args.max_renewal or renewal <= args.max_renewal)
            and (not args.tlds or tld in args.tlds.split(","))
            and (not args.max_tld_len or len(tld) <= args.max_tld_len)
            and (args.non_ascii or tld.isascii())
            and (args.slds or "." not in tld)
        ):
            domains[name] = {"name": f"{name}", "price": price, "renewal": renewal}

# Sort by domain length, then by renewal, then by price
domains = list(domains.values())
domains.sort(key=lambda x: (len(x["name"]), x["renewal"], x["price"]))

# If output_file given, write the available domains to it. Otherwise, print to console
if args.output_file:
    logging.info(f"Writing available domains to {args.output_file}...")
    
    with open(args.output_file, "w", encoding="utf-8") as file:
        json.dump(domains, file, ensure_ascii=False, indent=4)
else:
    logging.info("Printing available domains to the console...")
    
    name_len = max([len(domain['name']) for domain in domains]) + 3
    price_len = max([len(f"{domain['price']}") for domain in domains]) + 3
    renewal_len = max([len(f"{domain['renewal']}") for domain in domains]) + 3

    print(f'{"Domain":<{name_len}}{"Price":<{price_len}}{"Renewal":<{renewal_len}}')
    for domain in domains[::-1]:
        name, price, renewal = domain['name'], domain['price'], domain['renewal']
        print(f'{name:<{name_len}}{price:>{price_len}.2f}{currency}{renewal:>{renewal_len}.2f}{currency}')

logging.info("Done!")
