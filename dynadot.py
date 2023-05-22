import argparse
import json
import logging
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
driver.get("https://www.dynadot.com/domain/search.html")

# Find the domain search input element and enter your domain name
driver.find_element(By.ID, "domain_search_input").send_keys(args.name)

# Find and click the search button
logging.info('Clicking the "search-submit" button...')
driver.find_element(By.CSS_SELECTOR, ".btn.search-submit").click()

# Find and click the "accept_button" button (to dismiss the privacy policy popup)
logging.info('Clicking the "accept-privacy" button...')
try:
    WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "accept_button"))).click()
except TimeoutException:
    logging.info('"accept-privacy" button not found. Continuing...')

# Wait for the "view-more-button" element to be visible. While it's visible, click it
logging.info('Clicking the "view-more-button" button until all domains are loaded...')
while True:
    try:
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "view-more-button"))).click()
    except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
        break

# Save contents and close the WebDriver
page_contents = driver.page_source
driver.quit()

# Parse the HTML. We want to find the "tab-result" div
logging.info("Done with Selenium! Parsing the HTML with BeautifulSoup...")
soup = BeautifulSoup(page_contents, "html.parser")
tab_result = soup.find(id="tab-result")
assert isinstance(tab_result, Tag)

# Build the list of available domains
domains = []
currency = None

# Each domain is in a div.class="s-row transition-all"
for div in tab_result.find_all("div", {"class": "s-row transition-all"}):
    # If the div contains the "fa-cart-plus" icon, it's available
    if div.find("i", {"class": "fa-cart-plus"}):
        # Get domain name, TLD, price and renewal price from spans in the div
        name = div.find("span", {"class": "result-idn-name"}).text
        tld = div.find("span", {"class": "result-idn-tld"}).text
        price = div.find("span", {"class": "s-current-price"}).text
        renewal = div.find("span", {"class": "s-renewal-price"}).text
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
            domains.append({"name": f"{name}.{tld}", "price": price, "renewal": renewal})

# Sort by domain length, then by renewal, then by price
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
