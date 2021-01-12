import json
import platform
import sys
from datetime import datetime
from typing import List
from urllib import parse

from .bukalapak import Bukalapak
from .tokopedia import Tokopedia
from .shopee import Shopee
from pathlib import Path

from . import status_codes as sc

from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from .handle_result import HandleResult
from .load_from_file import LoadFromFile


class Start:
    operating_system = platform.system()
    args = []
    driver_dir = None
    process = None

    NEXT_PAGE_DEAD = 0
    NEXT_PAGE_EXISTS = 1

    def __init__(self, args):
        self.args = args
        marketplace = args.get('marketplace', None)
        self.ID = marketplace.lower() if marketplace is not None else ""
        self.get_driver_dir()

    def get_process(self):
        return self.process

    def get_driver(self):
        return self.driver

    def get_ID(self):
        return self.ID

    def get_driver_dir(self):
        curr_path = (Path(__file__).resolve()).parent.parent

        if str(self.operating_system) == 'Windows':
            chromedriver = Path('Files/chromedriver.exe')
        else:
            chromedriver = Path('Files/chromedriver')

        self.driver_dir = str(curr_path.joinpath(chromedriver))

    def start_driver(self) -> webdriver:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.headless = True
        chrome_options.add_argument('--log-level=3')
        chrome_options.page_load_strategy = 'eager'
        chrome_options.add_argument('--window-size=1080,3840')
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0')
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2
        })  # Prevents annoying "Show notifications" request

        driver = webdriver.Chrome(self.driver_dir, options=chrome_options)

        print(f"Browser PID: {driver.service.process.pid}")

        self.driver = driver

        return driver

    def start(self):
        driver = self.start_driver()

        if self.args['command'].casefold() == 'scrape'.casefold():
            self.scrape(driver=driver)

        elif self.args['command'].casefold() == 'continue'.casefold():
            self.continue_scrape(driver=driver)

        elif self.args['command'].casefold() == 'convert'.casefold():
            self.convert()

        elif self.args['command'].casefold() == 'retry'.casefold() or self.args['command'].casefold() == 'scrapeurl'.casefold():
            self.retry(driver=driver)

    # Scrape functions
    def scrape(self, driver, completed_url=[]):
        print("Start")
        start_page = self.args['startpage'] or 1

        if (self.ID.casefold() == 'bukalapak'.casefold()):
            # Max page is limited to 100 as pages > 100 are duplicates of page 100
            end_page = self.args['endpage'] if self.args['endpage'] != 0 else 100
            if end_page > 100:
                end_page = 100

            url = f"https://www.bukalapak.com/products?page={start_page}&search%5Bkeywords%5D={self.args['query_parsed']}"
            self.process = Bukalapak(args=self.args, driver=driver, completed_urls=completed_url)

        else:
            end_page = self.args['endpage'] if self.args['endpage'] != 0 else 9999
            if (self.ID.casefold() == 'shopee'.casefold()):
                url = f"https://shopee.co.id/search?page={start_page - 1}&keyword={self.args['query_parsed']}"
                self.process = Shopee(args=self.args, driver=driver, completed_urls=completed_url)

            else:
                url = f"https://www.tokopedia.com/search?page={start_page}&q={self.args['query_parsed']}"
                self.process = Tokopedia(args=self.args, driver=driver, completed_urls=completed_url)

        if start_page > end_page:
            driver.quit()
            print("Start page should be less than end page")
            sys.exit(-1)

        self.start_time = datetime.now()

        try:
            driver.get(url)
        except WebDriverException as err:
            print(err)
            driver.quit()
            sys.exit(sc.ERROR_NETWORK)
        else:
            while start_page <= end_page:
                search_result_urls = self.process.get_urls_from_search_results(start_page=start_page)
                self.scrape_from_url_list(urls=search_result_urls, driver=driver, completed_url=completed_url)

                has_next = self.process.next_search_page(driver)
                if has_next == self.NEXT_PAGE_EXISTS:
                    start_page += 1
                elif has_next == self.NEXT_PAGE_DEAD:
                    break

            driver.quit()

            data = self.process.get_data()
            errors = self.process.get_errors()

            self.handle_data(data, errors)

    def scrape_from_url_list(self, driver, urls: List[str], completed_url=[]):
        try:
            for product in urls:
                if any(completed in product for completed in completed_url):
                    print("Item Skipped")
                    continue

                # Opens a new tab
                driver.execute_script("window.open('');")

                # Gets a list of open tabs
                handle = driver.window_handles

                # Change focus to new tab
                driver.switch_to.window(handle[-1])
                driver.get(product)

                self.process.scrape_product_page(driver)

                # Closes and switch focus to the main tab
                driver.execute_script("window.close();")
                handle = driver.window_handles
                driver.switch_to.window(handle[0])
        except WebDriverException as err:
            # raise err
            print(err)


    # Continue functions
    def continue_scrape(self, driver):
        lff = LoadFromFile(path=self.args['path'], args=self.args)
        data = lff.load_file()

        self.args['marketplace'] = self.ID = data[0]['E-COMMERCE']
        urls = lff.load_urls_from_scraped_file(data=data)
        self.scrape(driver=driver, completed_url=urls)

    # Retry functions
    def retry(self, driver):
        print("Start", flush=True)
        self.start_time = datetime.now()

        if self.args.get('url') is None:
            lff = LoadFromFile(args=self.args, path=self.args['path'])
            data = lff.load_file()
            errors = data['ERRORS']
            keyword = data['KEYWORD']
            self.args['query'] = keyword
            self.args['query_parsed'] = parse.quote(keyword)
        else:
            errors = [self.args['url']]
            self.args['query'] = ''

    # TODO CATCH EXCEPTIONS
        if "tokopedia" in errors[0]:
            self.ID = 'tokopedia'
            self.process = Tokopedia(self.args, driver=driver)

        elif "bukalapak" in errors[0]:
            self.ID = 'bukalapak'
            self.process = Bukalapak(self.args, driver=driver)

        elif "shopee" in errors[0]:
            self.ID = 'shopee'
            self.process = Shopee(self.args, driver=driver)
        else:
            sys.exit(sc.ERROR_INVALID_FILE)

        try:
            print(errors)
            self.process.retry_errors(urls=errors)
        except WebDriverException as err:
            print(err)

        data = self.process.get_data()
        errors = self.process.get_errors()

        self.handle_data(data=data, errors=errors)

    def handle_data(self, data, errors):
        end_time = str(datetime.now() - self.start_time)
        print("Time taken: " + end_time, flush=True)

        if self.args['command'].casefold() == "scrape".casefold():
            if self.args['filename'] == '':
                # Filename argument is not specified, so filename will be generated
                self.args['filename'] = f"{self.args['query']}_{self.ID}_{str(datetime.now()).replace(':', '-')}"

            handle_class = HandleResult(file_name=self.args['filename'], file_type=self.args['result'])
            handle_class.handle_scrape(data, errors)

        elif self.args['command'].casefold() == 'scrapeurl'.casefold():
            sys.stdout = sys.__stdout__
            if len(data) == 0 or len(errors) != 0:
                sys.exit(sc.SUCCESS_NORESULTS)
            else:
                print(json.dumps(data))
                sys.exit(sc.SUCCESS_COMPLETE)
        else:
            handle_class = HandleResult(file_name=self.args['filename'], file_type=self.args['result'])

            if self.args['command'].casefold() == "continue".casefold():
                handle_class.handle_continue(data, errors)

            elif self.args['command'].casefold() == "retry".casefold():
                handle_class.handle_retry(data, errors)

    def convert(self):
        lff = LoadFromFile(args=self.args, path=self.args['path'])
        data = lff.load_file()
        hr = HandleResult(file_path=self.args['path'])
        hr.handle_convert(data)