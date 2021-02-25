import re
from urllib.parse import unquote as uq
from typing import List
from datetime import datetime
from . import city_list as cl
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


class Marketplace_Base_Class:
    NEXT_PAGE_DEAD = 0
    NEXT_PAGE_EXISTS = 1
    timeout_limit = 10

    def __init__(self, args, driver, completed_urls=[]):
        self.args = args
        self.data = []
        self.errors = []
        self.completed_urls = completed_urls
        self.scraped_count = 0

        self.driver = driver
        self.wait = WebDriverWait(driver, self.timeout_limit)

    def retry_errors(self, urls):
        driver = self.driver

        for url in urls:
            try:
                driver.get(url)
                self.scrape_product_page(driver)
            except WebDriverException as err:
                print(err)

        driver.quit()


    def get_urls_from_search_results(self, start_page) -> List[str]:
        # Checks if search results produces output of at least one product
        try:
            has_results = self.driver.find_element_by_css_selector('button[data-testid="btnSRPChangeKeyword"]').text
            if "Ganti kata kunci" in has_results:
                print("No results found, try another query?")
                return []
        except NoSuchElementException:
            pass

        print(f"Page {start_page}", flush=True)

        # Selects all the product
        search_results = self.driver.find_element_by_css_selector('div[data-testid="divSRPContentProducts"]')
        products = search_results.find_elements_by_class_name('pcv3__info-content')
        
        list_of_url = []

        # Gets all the URL to the individual products
        for product in products:
            try:
                product_url = product.get_attribute('href')
                if "ta.tokopedia.com" in product_url:
                    product_url = self.get_url_from_ad_link(product_url)
                list_of_url.append(product_url)
            except Exception as err:
                print(f"Error in def get_urls_from_search_results\n{err}", flush=True)

        return list_of_url

    def get_data(self):
        return self.data

    def get_errors(self):
        return self.errors

    def scrape_product_page(self, driver: WebDriver):
        # Waits for redirect (if URL is not the final URL)
        try:
            self.wait.until_not(ec.url_contains("ta.tokopedia"))

        except TimeoutException as err:
            print(err)
            self.errors.append(driver.current_url)
            return

        # Checks if URL exists and doesn't return 404
        is_page_valid = driver.find_elements_by_css_selector(
            'h1[class="css-6hac5w-unf-heading e1qvo2ff1"]')  # Required to check if product page is valid

        if len(is_page_valid) > 0:
            return

        """
        Starts scraping process here
        """

        try:
            driver.implicitly_wait(0)
            d = dict()

            d['KEYWORD'] = self.args['query']


            d['PRODUK'] = ""
            d['FARMASI'] = ""
            d['E-COMMERCE'] = "" # TODO

            d['TOKO'] = "" # TODO

            d['ALAMAT'] = "" # TODO

            kota = None

            for city in cl.cities:
                if city.casefold() in location.casefold():
                    kota = city
                    break

            if kota is None:
                for regency in cl.regencies:
                    if regency.casefold() in location.casefold():
                        kota = regency
                        break

            d['KOTA'] = "" # TODO

            nama_produk = driver.find_element_by_css_selector('h1[data-testid="lblPDPDetailProductName"]').text # TODO

            box_patt = "(?i)((?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule\b)[ ]+[0-9,]*[ ]?(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule|gr|gram|kg\b))|([0-9,]{1,6}[ ]?(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule|gr|gram|kg\b))|((?:(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule\b)[ ]?)+[0-9,]{1,6})"
            rbox = re.findall(box_patt, nama_produk)

            reg = []
            for tuple in rbox:
                reg.append([var for var in tuple if var != ''])

            d['BOX'] = ', '.join([item for sublist in reg for item in sublist]) if len(reg) > 0 else "" # TODO

            d['RANGE'] = "" # TODO

            d['JUAL (UNIT TERKECIL)'] = "" # TODO

            d['HARGA UNIT TERKECIL'] = "" # TODO

            d['VALUE'] = ""

            d['% DISC'] = "" # TODO

            d['KATEGORI'] = "" # TODO

            url = driver.current_url
            if '?' in url:
                url = url[:str(driver.current_url).index('?')]
            d['SOURCE'] = url

            d['NAMA PRODUK E-COMMERCE'] = nama_produk

            d['RATING (Khusus shopee dan toped dikali 20)'] = "" # TODO

            d['JML ULASAN'] = "" # TODO

            d['DILIHAT'] = "" # TODO

            d['DESKRIPSI'] = "" # TODO

            d['TANGGAL OBSERVASI'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        except (NoSuchElementException, WebDriverException) as err:
            # raise err
            print(err)
            self.errors.append(driver.current_url)

        else:
            self.completed_urls.append(d['SOURCE'])
            self.data.append(d)
            self.scraped_count += 1
            print(f"    Item #{self.scraped_count} completed")

    def next_search_page(self, driver: WebDriver) -> int:
        # Checks if "next page" button exists
        try:
            driver.implicitly_wait(3)
            next_button = driver.find_element_by_css_selector('button[aria-label="Halaman berikutnya"]')

            # Checks if button is not disabled
            if next_button.is_enabled():
                print("Next page")
                next_button.click()

                self.wait.until(ec.presence_of_element_located((By.CLASS_NAME, 'pcv3__info-content')),
                                'Items not found in this page')

                return self.NEXT_PAGE_EXISTS
            else:
                return self.NEXT_PAGE_DEAD

        except TimeoutException as err:
            print(err)
            return self.NEXT_PAGE_DEAD

        except NoSuchElementException as err:
            return self.NEXT_PAGE_DEAD

    def get_url_from_ad_link(self, product_url) -> str:
        url = product_url[product_url.rindex("https")::]
        return uq(url)
