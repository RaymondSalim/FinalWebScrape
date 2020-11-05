import os
import platform
import re
from typing import List
from datetime import datetime
from selenium import webdriver
from webscrape_files.handle_result import HandleResult
from . import city_list as cl
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class Bukalapak:
    operating_system = platform.system()
    NEXT_PAGE_DEAD = 0
    NEXT_PAGE_EXISTS = 1
    ID = "bukalapak"
    timeout_limit = 10

    def __init__(self, args):
        self.args = args
        self.data = []
        self.errors = []
        self.scraped_count = 0
        self.driver_dir = str(os.path.dirname(os.path.realpath(__file__)))

        if str(self.operating_system) == 'Linux':
            self.driver_dir = self.driver_dir.replace('/webscrape_files', '/Files/chromedriver')
        elif str(self.operating_system) == 'Windows':
            self.driver_dir = self.driver_dir.replace('\\webscrape_files', '\\Files\\chromedriver.exe')

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

        self.wait = WebDriverWait(driver, self.timeout_limit)

        return driver

    def clear_console(self):
        if str(self.operating_system) == 'Windows':
            os.system('cls')
        else:
            os.system('clear')

    def start_scrape(self):
        print("Start")
        self.start_time = datetime.now()

        start_page = self.args['startpage'] or 1
        self.args['endpage'] = self.args['endpage'] if self.args['endpage'] != 0 else 9999

        url = f"https://www.bukalapak.com/products?page={start_page}&search%5Bkeywords%5D={self.args['query_parsed']}"

        try:
            driver = self.start_driver()

            driver.get(url)

            while start_page <= self.args['endpage']:
                urls = self.get_urls_from_search_results(driver, start_page)
                self.scrape_from_url_list(driver, urls)

                has_next = self.next_search_page(driver)
                if has_next == self.NEXT_PAGE_EXISTS:
                    start_page += 1
                elif has_next == self.NEXT_PAGE_DEAD:
                    break
        except Exception as err:
            print(err)
            driver.quit()

        finally:
            driver.quit()

            self.handle_data()

    def continue_scrape(self, completed_urls):
        print("Start")
        self.start_time = datetime.now()

        start_page = self.args['startpage'] or 1
        self.args['endpage'] = self.args['endpage'] if self.args['endpage'] != 0 else 9999

        driver = self.start_driver()

        url = f"https://www.bukalapak.com/products?page={start_page}&search%5Bkeywords%5D={self.args['query']}"

        driver.get(url)

        while start_page <= self.args['endpage']:
            urls = self.get_urls_from_search_results(driver, start_page)
            self.scrape_from_url_list(driver, urls, completed_url=completed_urls)

            has_next = self.next_search_page(driver)
            if has_next == self.NEXT_PAGE_EXISTS:
                start_page += 1
            elif has_next == self.NEXT_PAGE_DEAD:
                break

        driver.quit()

        self.handle_data()

    def retry_errors(self, urls):
        print("Start")
        self.start_time = datetime.now()
        driver = self.start_driver()

        for url in urls:
            driver.get(url)
            self.scrape_product_page(driver)

        driver.quit()

        self.handle_data()

    def get_urls_from_search_results(self, driver: WebDriver, start_page) -> List[str]:
        try:
            has_results = driver.find_element_by_css_selector('p[class="mb-8 bl-text bl-text--subheading-1"]').text
            if "Maaf, barangnya tidak ketemu" in has_results:
                print("Tidak ada hasil")
                return []
        except NoSuchElementException:
            pass

        finally:
            try:
                self.wait.until(
                    ec.presence_of_element_located((By.XPATH, '//div[@class="bl-product-card__thumbnail"]//*//a')),
                    "No items found on this page")

            except:
                return []

            else:
                print(f"Page {start_page}")
                products = driver.find_elements_by_css_selector('div[class="bl-product-card__description"]')

                list_of_url = []

                for product in products:
                    try:
                        product_url = product.find_element_by_tag_name('a').get_attribute('href')
                        list_of_url.append(product_url)
                    except Exception as err:
                        print(f"Error in def get_urls_from_search_results\n{err}")

                return list_of_url

    def scrape_from_url_list(self, driver: WebDriver, urls: List[str], completed_url=[]):
        for product in urls:
            if any(completed in product for completed in completed_url):
                print("Item skipped")
                continue

            # Opens a new tab
            driver.execute_script("window.open('');")

            # Gets a list of open tabs
            handle = driver.window_handles

            # Change focus to new tab
            driver.switch_to.window(handle[-1])
            driver.get(product)

            self.scrape_product_page(driver)

            # Closes and switch focus to the main tab
            driver.execute_script("window.close();")
            handle = driver.window_handles
            driver.switch_to.window(handle[0])

    def scrape_product_page(self, driver: WebDriver):
        try:
            self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[id="section-informasi-barang"]')),
                            "Page timeout")

        except Exception as err:
            print(err)
            self.errors.append(driver.current_url)
            return

        else:
            is_page_valid = driver.find_elements_by_css_selector('h1[class="u-fg--ash-light u-txt--bold"]')
            if len(is_page_valid) > 0:
                return

            """
            Starts scraping process here
            """

            try:
                d = dict()

                d['KEYWORD'] = self.args['query']

                d['PRODUK'] = ""
                d['FARMASI'] = ""
                d['E-COMMERCE'] = 'BUKALAPAK'

                shop = driver.find_element_by_class_name('c-seller__info')
                d['TOKO'] = shop.find_element_by_css_selector('a[class="c-link--primary--black"]').text

                location = driver.find_element_by_css_selector('a[class="c-seller__city u-mrgn-bottom--2"]').text
                d['ALAMAT'] = location

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

                d['KOTA'] = kota or ""

                nama_produk = driver.find_element_by_css_selector(
                    'h1[class="c-main-product__title u-txt--large"]').text

                box_patt = "(?i)((?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule\b)[ ]+[0-9,]*[ ]+(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule\b))|([0-9,]{1,6}[ ]?(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule\b))|((?:(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule\b)[ ]?)+[0-9,]{1,6})"
                rbox = re.findall(box_patt, nama_produk)

                d['BOX'] = ', '.join(rbox) if len(rbox) > 0 else ""

                d['RANGE'] = ''

                mpr = driver.find_element_by_class_name("c-main-product__reviews").text
                mpr_arr = mpr.split()

                ratingc = None
                soldc = None

                if len(mpr_arr) == 4:
                    ratingc = int(mpr_arr[0].replace('.', ''))
                    soldc = int(mpr_arr[2].replace('.', ''))

                elif len(mpr_arr) == 2:
                    soldc = int(mpr_arr[0].replace('.', ''))

                d['JUAL (UNIT TERKECIL)'] = int(soldc) if len(mpr) > 0 else ""

                price = driver.find_element_by_css_selector('div.c-main-product__price').text.split('\n')
                d['HARGA UNIT TERKECIL'] = float((price[0][2::]).replace(".", ""))

                d['VALUE'] = ""

                discount = driver.find_elements_by_css_selector(
                    'span[class="c-main-product__price__discount-percentage"]')
                if len(discount) > 0:
                    text_disc = discount[0].text.split()
                d['% DISC'] = float(text_disc[-1].replace('%', '')) / 100 if len(discount) > 0 else ""

                shop_category = driver.find_element_by_css_selector('div[class="c-seller__badges"]')
                cat = shop_category.text.replace('\n', '').replace(' ', '')
                q = ['super', 'recommended', 'good', 'juragan']
                if any(a in cat.casefold() for a in q):
                    cat = "STAR SELLER"
                elif "Resmi".casefold() == cat.casefold() or "bukamall" in shop_category.get_attribute('innerHTML'):
                    cat = "OFFICIAL STORE"
                elif "Pedagang".casefold() == cat.casefold():
                    cat = "TOKO BIASA"
                else:
                    cat = "TOKO BIASA"

                d['KATEGORI'] = cat

                url = driver.current_url
                if '?' in url:
                    url = url[:str(driver.current_url).index('?')]
                d['SOURCE'] = url

                d['NAMA PRODUK E-COMMERCE'] = nama_produk

                rating = driver.find_elements_by_css_selector('span[class="summary__score"]')
                d['RATING (Khusus shopee dan toped dikali 20)'] = float(rating[0].text) if len(rating) > 0 else ""

                d['JML ULASAN'] = int(ratingc) if len(mpr_arr) == 4 else ""

                d['DILIHAT'] = ""

                d['DESKRIPSI'] = driver.find_element_by_css_selector(
                    'div[class="c-information__description-txt"]').text

                d['TANGGAL OBSERVASI'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            except Exception as err:
                print(err)
                self.errors.append(driver.current_url)

            else:
                self.data.append(d)
                self.scraped_count += 1
                print(f"    Item #{self.scraped_count} completed")

    def next_search_page(self, driver: WebDriver) -> int:
        try:
            next_button = driver.find_element_by_css_selector("a[class*='pagination__next']")

            if next_button.is_enabled():
                print("Next page")
                next_button.click()
                return self.NEXT_PAGE_EXISTS
            else:
                return self.NEXT_PAGE_DEAD

        except TimeoutException as err:
            print(err)
            return self.NEXT_PAGE_DEAD

        except NoSuchElementException as err:
            return self.NEXT_PAGE_DEAD

    def handle_data(self):
        end_time = str(datetime.now() - self.start_time).replace(':', '꞉')
        print("Time taken: " + end_time)

        if self.args['command'] == "scrape":
            if self.args['filename'] == '':
                # Filename argument is not specified, so filename will be generated
                self.args['filename'] = f"{self.args['query']}_{self.ID}_{str(datetime.now()).replace(':', '꞉')}"

            else:
                self.args['filename'] = self.args['filename']

            handle_class = HandleResult(file_name=self.args['filename'], file_type=self.args['result'])
            handle_class.handle_scrape(self.data, self.errors)

        elif self.args['command'] == "continue":
            handle_class = HandleResult(file_name=self.args['filename'], file_type=self.args['result'])
            handle_class.handle_continue(self.data, self.errors)

        elif self.args['command'] == "retry":
            handle_class = HandleResult(file_name=self.args['filename'], file_type=self.args['result'])
            handle_class.handle_retry(self.data, self.errors)
