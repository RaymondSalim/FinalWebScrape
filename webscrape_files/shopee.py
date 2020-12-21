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


class Shopee:
    operating_system = platform.system()
    NEXT_PAGE_DEAD = 0
    NEXT_PAGE_EXISTS = 1
    ID = "shopee"
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

        print(f"Browser PID: {driver.service.process.pid}")

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

        url = f"https://shopee.co.id/search?page={start_page-1}&keyword={self.args['query_parsed']}"

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

        try:

            driver = self.start_driver()

            url = f"https://shopee.co.id/search?page={start_page-1}&keyword={self.args['query_parsed']}"

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
            print(err)

        finally:
            driver.quit()

            self.handle_data()

    def retry_errors(self, urls):
        print("Start")
        self.start_time = datetime.now()

        try:
            driver = self.start_driver()

            for url in urls:
                driver.get(url)
                self.scrape_product_page(driver)

        except Exception as err:
            print(err)

        finally:
            driver.quit()

            self.handle_data()

    def get_urls_from_search_results(self, driver: WebDriver, start_page) -> List[str]:
        try:
            has_results = driver.find_element_by_css_selector('div[class="shopee-search-result-header__text"]').text
            if "Kami tidak dapat menemukan" in has_results:
                print("Tidak ada hasil")
                return []
        except NoSuchElementException:
            pass

        finally:
            try:
                self.wait.until(ec.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div[class="row shopee-search-item-result__items"]')), "No items found on this page")
            except:
                return []

            else:
                print(f"Page {start_page}")
                search_results = driver.find_element_by_css_selector(
                    'div[class="row shopee-search-item-result__items"]')
                products = search_results.find_elements_by_css_selector('div.shopee-search-item-result__item')

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
            if product in completed_url or any(completed in product for completed in completed_url):
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
            self.wait.until(ec.text_to_be_present_in_element((By.CSS_SELECTOR, 'div.page-product'), ""),
                            "Page product not found")
            self.wait.until(ec.text_to_be_present_in_element((By.CLASS_NAME, 'qaNIZv'), ""), "Title not found")

        except Exception as err:
            print(err)
            self.errors.append(driver.current_url)
            return

        else:
            is_page_valid = driver.find_elements_by_css_selector('div[class="product-not-exist__content"]')
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
            d['E-COMMERCE'] = 'SHOPEE'

            self.wait.until(ec.text_to_be_present_in_element((By.CSS_SELECTOR, 'div._3Lybjn'), ""), "Shop name not found")
            d['TOKO'] = driver.find_element_by_css_selector('div._3Lybjn').text

            info = driver.find_elements_by_css_selector('div[class="kIo6pj"]')
            location = None
            for loc in info:
                if "Dikirim Dari".casefold() in loc.text.casefold():
                    location = loc.text
            if location is not None:
                location = location.replace("Dikirim Dari", "").replace('\n', '')
            else:
                location = "Location Not Found"
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

            d['KOTA'] =kota or ""

            self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[class="qaNIZv"]')),"Product name not found")
            nama_produk = driver.find_element_by_css_selector('div[class="qaNIZv"]').text

            box_patt = "(?i)((?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule\b)[ ]+[0-9,]*[ ]?(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule|gr|gram|kg\b))|([0-9,]{1,6}[ ]?(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule|gr|gram|kg\b))|((?:(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule\b)[ ]?)+[0-9,]{1,6})"
            rbox = re.findall(box_patt, nama_produk)

            reg = []
            for tuple in rbox:
                reg.append([var for var in tuple if var != ''])

            d['BOX'] = ', '.join([item for sublist in reg for item in sublist]) if len(reg) > 0 else ""

            range_container = driver.find_element_by_css_selector('div[class="flex _3dRJGI _3a2wD-"]')
            indiv_container = range_container.find_elements_by_css_selector('div[class="flex items-center"]')

            all_options = []

            for i in range(0, len(indiv_container) - 1):
                indiv_container_title = indiv_container[i].find_element_by_css_selector('label[class="_2iNrDS"]').text
                indiv_container_options = indiv_container[i].find_element_by_css_selector('div[class="flex items-center crl7WW"]')
                options = indiv_container_options.find_elements_by_css_selector('button[class*="product-variation"]')
                textoptions = [a.text for a in options]
                text = indiv_container_title + ': ' + ', '.join(textoptions)
                all_options.append(text)

            d['RANGE'] = '; '.join(all_options) if len(all_options) > 0 else ""

            sold_count_val = driver.find_elements_by_css_selector('div[class="_22sp0A"]')
            if len(sold_count_val) > 0:
                sol = sold_count_val[0].text
                if 'RB' in sol:
                    sol = sol.replace('RB', '').replace(',', '').replace('+', '')
                    sol = int(sol) * 100
                d['JUAL (UNIT TERKECIL)'] = int(sol) if int(sol) != 0 else ""

            else:
                d['JUAL (UNIT TERKECIL)'] = ""

            prices = driver.find_elements_by_css_selector('div[class="_3_ISdg"]')
            if len(prices) > 0:
                prices = prices[0].text.split()
            else:
                prices = (driver.find_element_by_css_selector('div[class="_3n5NQx"]').text.split())

            prices = [val.replace('.', '').replace('Rp', '') for val in prices]
            try:
                prices.remove('-')
            except ValueError:
                pass

            if len(prices) == 1:
                d['HARGA UNIT TERKECIL'] = int(prices[0])
            elif len(prices) == 2:
                d['HARGA UNIT TERKECIL'] = f"{prices[0]} - {prices[1]}"
            else:
                raise Exception("    Price not found")

            d['VALUE'] = ""

            disc = driver.find_elements_by_css_selector('div[class="MITExd"]')
            if len(disc) > 0:
                disc_float = (disc[0].text)[:(disc[0].text).index('%'):]
                disc = float(disc_float) / 100
            else:
                disc = ""

            d['% DISC'] = disc

            shop_cat = driver.find_elements_by_css_selector('div[class="_1oAxCI"]')
            if len(shop_cat) > 0:
                mall = shop_cat[0].find_elements_by_css_selector('img[class="official-shop-new-badge--all"]')
                if len(mall) > 0:
                    cat = "OFFICIAL STORE"
                else:
                    cat = shop_cat[0].text
                    if "Star".casefold() in cat.casefold():
                        cat = "STAR SELLER"

            else:
                cat = "TOKO BIASA"
            d['KATEGORI'] = cat


            url = driver.current_url
            if '?' in url:
                url = url[:str(driver.current_url).index('?')]
            d['SOURCE'] = url

            if nama_produk.startswith('Star+'):
                nama_produk = nama_produk[6::]
            elif nama_produk.startswith('Star'):
                nama_produk = nama_produk[5::]

            d['NAMA PRODUK E-COMMERCE'] = nama_produk

            rating_val = driver.find_elements_by_css_selector('div[class="_3Oj5_n _2z6cUg"]')
            d['RATING (Khusus shopee dan toped dikali 20)'] = float(rating_val[0].text) * 20 if len(
                rating_val) > 0 else ""

            rating_count_val = driver.find_elements_by_css_selector('div[class="_3Oj5_n"]')
            if len(rating_count_val) > 0:
                rat = rating_count_val[0].text
                if 'RB' in rat:
                    rat = rat.replace('RB', '').replace(',', '').replace('+', '')
                    rat = int(rat) * 1000
                d['JML ULASAN'] = int(rat)

            else:
                d['JML ULASAN'] = ""

            d['DILIHAT'] = ""

            d['DESKRIPSI'] = driver.find_element_by_css_selector('div[class="_2u0jt9"]').text

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
            driver.implicitly_wait(3)
            next_button = driver.find_element_by_css_selector(
                'button[class="shopee-button-outline shopee-mini-page-controller__next-btn"')

            if next_button.is_enabled():
                print("Next page")
                next_button.click()
                self.wait.until(ec.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div.shopee-search-item-result__item')),
                    f'Items not found in this page')
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

        elif self.args['command'] == 'scrapeurl':
            import sys
            sys.stdout = sys.__stdout__
            print(self.data)
            sys.stdout = open(os.devnull, 'w')
            sys.exit(0)