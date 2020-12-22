import os
import platform
import sys
from typing import List
from datetime import datetime
from selenium import webdriver
from . import status_codes as sc
from webscrape_files import load_from_file as lff
from webscrape_files.handle_result import HandleResult
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class Tokopedia:
    operating_system = platform.system()
    NEXT_PAGE_DEAD = 0
    NEXT_PAGE_EXISTS = 1
    ID = "tokopedia"
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
        self.driver = driver

        print(f"Browser PID: {driver.service.process.pid}", flush=True)

        self.wait = WebDriverWait(driver, self.timeout_limit)

        return driver

    def clear_console(self):
        if str(self.operating_system) == 'Windows':
            os.system('cls')
        else:
            os.system('clear')

    def start_scrape(self):
        print("Start", flush=True)
        self.start_time = datetime.now()

        start_page = self.args['startpage'] or 1
        self.args['endpage'] = self.args['endpage'] if self.args['endpage'] != 0 else 9999

        url = f"https://www.tokopedia.com/search?page={start_page}&q={self.args['query_parsed']}"

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
            print(err, flush=True)

        finally:
            driver.quit()

            self.handle_data()

    def continue_scrape(self, completed_urls):
        print("Start", flush=True)
        self.start_time = datetime.now()

        start_page = self.args['startpage'] or 1
        self.args['endpage'] = self.args['endpage'] if self.args['endpage'] != 0 else 9999

        try:
            driver = self.start_driver()

            url = f"https://www.tokopedia.com/search?page={start_page}&q={self.args['query_parsed']}"

            driver.get(url)

            while start_page <= self.args['endpage']:
                urls = self.get_urls_from_search_results(driver, start_page)
                self.scrape_from_url_list(driver, urls, completed_url=completed_urls)

                has_next = self.next_search_page(driver)
                if has_next == self.NEXT_PAGE_EXISTS:
                    start_page += 1
                elif has_next == self.NEXT_PAGE_DEAD:
                    break

        except Exception as err:
            print(err, flush=True)

        finally:
            driver.quit()

            self.handle_data()


    def retry_errors(self, urls):
        print("Start", flush=True)
        self.start_time = datetime.now()

        try:
            driver = self.start_driver()

            for url in urls:
                driver.get(url)
                self.scrape_product_page(driver)

        except Exception as err:
            print(err, flush=True)

        finally:
            driver.quit()

            self.handle_data()

    def get_urls_from_search_results(self, driver: WebDriver, start_page) -> List[str]:
        try:
            has_results = driver.find_element_by_css_selector('button[data-testid="btnSRPChangeKeyword"]').text
            if "Ganti kata kunci" in has_results:
                print("Tidak ada hasil", flush=True)
                return []
        except NoSuchElementException:
            pass

        print(f"Page {start_page}", flush=True)
        search_results = driver.find_element_by_css_selector('div[data-testid="divSRPContentProducts"]')
        products = search_results.find_elements_by_class_name('pcv3__info-content')
        list_of_url = []

        for product in products:
            try:
                product_url = product.get_attribute('href')
                list_of_url.append(product_url)
            except Exception as err:
                print(f"Error in def get_urls_from_search_results\n{err}", flush=True)

        return list_of_url

    def scrape_from_url_list(self, driver: WebDriver, urls: List[str], completed_url=[]):
        for product in urls:
            if any(completed in product for completed in completed_url):
                print("Item skipped", flush=True)
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
            self.wait.until_not(ec.url_contains("ta.tokopedia"))

        except Exception as err:
            print(err, flush=True)
            self.errors.append(driver.current_url)
            return

        try:
            self.wait.until(
                ec.text_to_be_present_in_element((By.CSS_SELECTOR, 'div[data-testid="pdpDescriptionContainer"]'), ""),
                "pdpDescriptionContainer not found")
        except Exception as err:
            print(err, flush=True)
            print("timed out, skipping" ,flush=True)
            self.errors.append(driver.current_url)
            return

        else:
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
                d['E-COMMERCE'] = 'TOKOPEDIA'

                self.wait.until(ec.text_to_be_present_in_element((By.CSS_SELECTOR, 'a[data-testid="llbPDPFooterShopName"]'), ""))
                d['TOKO'] = driver.find_element_by_css_selector('a[data-testid="llbPDPFooterShopName"]').text

                location = driver.find_element_by_css_selector('span[data-testid="lblPDPFooterLastOnline"]').text
                location = location.split('•')[0]
                d['ALAMAT'] = location

                d['KOTA'] = ""

                d['BOX'] = ""

                range_data = []
                ignored_containers = ['HARGA', 'JUMLAH', 'PROMO', 'INFO PRODUK', 'ONGKOS KIRIM']
                range_containers = driver.find_elements_by_css_selector('div[class="css-eyzclq"]')
                for i in range(0, len(range_containers)):
                    range_title = range_containers[i].find_elements_by_css_selector('p[class="css-1k51u5l-unf-heading e1qvo2ff8"]')
                    if len(range_title) > 0:
                        if range_title[0].text in ignored_containers:
                            continue
                        else:
                            title = range_title[0].text
                            range_options = range_containers[i].find_elements_by_css_selector('div[data-testid="lblPDPProductVariantukuran"]')

                            if len(range_options) < 0:
                                range_options = range_containers[i].find_elements_by_css_selector('div[data-testid="lblPDPProductVariantwarna"]')

                            ranges = [a.text for a in range_options]
                            range_final = title + ': ' + ', '.join(ranges)
                            range_data.append(range_final)
                d['RANGE'] = '; '.join(range_data)

                sold_count_valid = driver.find_elements_by_css_selector(
                    'span[data-testid="lblPDPDetailProductSuccessRate"]')
                d['JUAL (UNIT TERKECIL)'] = sold_count_valid[0].text if len(sold_count_valid) > 0 else ""


                ori_price = driver.find_elements_by_css_selector('p[data-testid="lblPDPDetailOriginalPrice"]')

                price = driver.find_elements_by_css_selector('h3[data-testid="lblPDPDetailProductPrice"]')

                d['HARGA UNIT TERKECIL'] = ori_price[0].text if len(ori_price) > 0 else price[0].text


                d['VALUE'] = ""

                discount = driver.find_elements_by_css_selector('div[data-testid="lblPDPDetailDiscountPercentage"]')
                d['% DISC'] = discount[0].text if len(discount) > 0 else ""

                shop_category = driver.find_elements_by_css_selector('p[data-testid="imgPDPDetailShopBadge"]')
                d['KATEGORI'] = shop_category[0].text if len(shop_category) > 0 else ""

                url = driver.current_url
                if '?' in url:
                    url = url[:str(driver.current_url).index('?')]
                d['SOURCE'] = url

                d['NAMA PRODUK E-COMMERCE'] = driver.find_element_by_css_selector('h1[data-testid="lblPDPDetailProductName"]').text

                rating = driver.find_elements_by_css_selector('span[data-testid="lblPDPDetailProductRatingNumber"]')
                d['RATING (Khusus shopee dan toped dikali 20)'] = rating[0].text if len(rating) > 0 else ""

                rating_total = driver.find_elements_by_css_selector(
                    'span[data-testid="lblPDPDetailProductRatingCounter"]')

                d['JML ULASAN'] = rating_total[0].text if len(rating_total) > 0 else ""

                seen_by = (
                    driver.find_elements_by_css_selector('span[data-testid="lblPDPDetailProductSeenCounter"]'))

                d['DILIHAT'] = seen_by[0].text if len(seen_by) > 0 else ""

                d['DESKRIPSI'] = driver.find_element_by_css_selector(
                    'div[data-testid="pdpDescriptionContainer"]').text

                d['TANGGAL OBSERVASI'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            except Exception as err:
                print(err, flush=True)
                self.errors.append(driver.current_url)

            else:
                self.data.append(d)
                self.scraped_count += 1
                print(f"    Item #{self.scraped_count} completed", flush=True)

    def next_search_page(self, driver: WebDriver) -> int:
        try:
            driver.implicitly_wait(3)
            next_button = driver.find_element_by_css_selector('button[aria-label="Halaman berikutnya"]')

            if next_button.is_enabled():
                print("Next page", flush=True)
                next_button.click()

                self.wait.until(ec.presence_of_element_located((By.CLASS_NAME, 'pcv3__info-content')),
                                'Items not found in this page')

                return self.NEXT_PAGE_EXISTS
            else:
                return self.NEXT_PAGE_DEAD

        except TimeoutException as err:
            print(err, flush=True)
            return self.NEXT_PAGE_DEAD

        except NoSuchElementException as err:
            return self.NEXT_PAGE_DEAD

    def handle_data(self):
        end_time = str(datetime.now() - self.start_time)
        print("Time taken: " + end_time, flush=True)

        if self.args['command'] == "scrape":
            if self.args['filename'] == '':
                # Filename argument is not specified, so filename will be generated
                self.args['filename'] = f"{self.args['query']}_{self.ID}_{str(datetime.now()).replace(':', '-')}"

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

        elif self.args['command'] == 'scrapeurl':
            if (len(self.data) == 0 or len(self.errors) != 0):
                sys.exit(sc.SUCCESS_NORESULTS)
            else:
                lf = lff.LoadFromFile(args=self.args)
                lf.process(self.data)
