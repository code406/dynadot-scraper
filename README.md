# Dynadot Scraper (domain search tool)

A simple Python scraper to **find available domain extensions for a given domain name**.
It uses Selenium to interact with the Dynadot search page and
BeautifulSoup to parse the HTML.

## Usage

Install the requirements with pipenv (```pipenv install```) and then run the script with:

    pipenv run python dynadot.py -n [DOMAIN_NAME]

The script will click the 'View More Extensions' button repeatedly to load all the results,
which may take a couple minutes. Once it's done, the available domains will be printed out
(or written to a JSON file, if specified).

### Arguments

Only the "-n" ("--name") argument is required, but here are all the possible arguments
the script can take:

* **```-n NAME```**, **```--name NAME```**:
Name (subdomain) to search for. This is the part before the first "."
(e.g. "amazon" to get "amazon.com", "amazon.de", "amazon.fr"...).
* **```-o OUTPUT_FILE```**, **```--output-file OUTPUT_FILE```**:
File to write results to (in JSON format).
If not specified, results will be printed to stdout in a somewhat readable format.
* **```-p MAX_PRICE```**, **```--max-price MAX_PRICE```**:
Maximum price to filter results (if given).
* **```-r MAX_RENEWAL```**, **```--max-renewal MAX_RENEWAL```**:
Maximum renewal price to filter results (if given).
* **```-l MAX_TLD_LEN```**, **```--max-tld-len MAX_TLD_LEN```**:
Maximum length of TLD to filter results (if given).
* **```-t TLDS```**, **```--tlds TLDS```**:
Comma-separated list of TLDs to show. If not given, all TLDs will be shown.
* **```--slds```**:
If given, show also domains from SLDs (second-level domains, e.g. ".co.uk").
By default, the script only shows domains from TLDs (with a single "." in them).
* **```--non-ascii```**:
If given, show also domains from non-ASCII TLDs (e.g. "amazon.닷컴").
By default, the script only shows ASCII domain extensions.

## Disclaimer

The script only searches for domains in the Dynadot search page.
If the domain you're looking for is not available there (this happens with ".es" domains,
for instance), it won't be found by this script.

Also, I'm not encouraging or trying to promote the purchase of domains through Dynadot.
I've found some bad reviews, so do your own research and take the results as an indicator
of availability only.

I'm open to suggestions or improvements, and you can adapt the script however you like!
