import re
from typing import List
from datetime import datetime
from selenium import webdriver
import json
from . import city_list as cl
from selenium.webdriver.remote import webelement
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


class Shopee:
    NEXT_PAGE_DEAD = 0
    NEXT_PAGE_EXISTS = 1
    timeout_limit = 10

    def __init__(self, args, driver, config=dict(), completed_urls=[]):
        self.args = args
        self.data = []
        self.errors = []
        self.completed_urls = completed_urls
        self.scraped_count = 0
        self.config = config

        self.driver = driver
        self.wait = WebDriverWait(driver, self.timeout_limit)

    def retry_errors(self, urls):
        driver = self.driver

        consecutive_error_count = 0
        for url in urls:
            try:
                driver.get(url)
                self.scrape_product_page(driver)
            except TimeoutException as err:
                consecutive_error_count += 1
                print(err)
                continue
            except WebDriverException as err:
                consecutive_error_count += 1
                print(err)
                continue
            else:
                consecutive_error_count = 0

            # There has been 5 errors in a row, exits
            if consecutive_error_count > self.args['max_error']:
                raise TimeoutError(f"Job ran into error {self.args['max_error']} consecutive times.")

        driver.quit()

    def get_urls_from_search_results(self, start_page) -> List[str]:
        c = self.config
        try:
            has_results = self.driver.find_element_by_css_selector(
                c["extras"]["search_page_has_results"]).text()
            if "Kami tidak dapat menemukan" in has_results:
                print("No results found, try another query?")
                return []
        except NoSuchElementException:
            pass

        try:
            # self.wait.until(ec.presence_of_element_located(
            #     (By.CSS_SELECTOR, 'div[class="row shopee-search-item-result__items"]')), "No items found on this page")
            # self.wait.until(ec.presence_of_element_located(
            #     (By.CSS_SELECTOR, 'div[class="row shopee-search-item-result__items"] div[class*="shopee-search-item-result__item"]')), "No items found on this page")

            self.wait.until(ec.presence_of_element_located(
                (By.CSS_SELECTOR, c["extras"]["search_page_data"])), "No items found on this page")

        except:
            return []

        else:
            print(f"Page {start_page}", flush=True)
            # search_results = self.driver.find_element_by_css_selector(
            #     'div[class="row shopee-search-item-result__items"]')
            #
            # products = search_results.find_elements_by_css_selector('div.shopee-search-item-result__item')
            self.wait.until(lambda driver: len(
                driver.find_elements_by_css_selector(c["extras"]["search_page_data"])) > 1)

            products: List[webdriver] = self.driver.find_elements_by_css_selector(
                c["extras"]["search_page_data"])

            # For Shop Search
            # search_results = self.driver.find_element_by_css_selector(
            #     'div[class="shop-search-result-view"]')
            # products = search_results.find_elements_by_css_selector('div.shop-search-result-view__item')

            list_of_url = []

            for product in products:  # type: webelement
                # try:
                #     product_url = product.find_element_by_tag_name('a').get_attribute('href')
                #     list_of_url.append(product_url)
                # except Exception as err:
                #     print(f"Error in def get_urls_from_search_results\n{err}", flush=True)
                #     if self.args["debug"]:
                #         import traceback
                #         traceback.print_exc(limit=4)

                try:
                    data = json.loads(product.get_attribute('innerHTML').strip())
                    if (data['@type'].casefold() != 'product'.casefold()):
                        if self.args["debug"]:
                            print("Data is not of product type, skipping")
                        continue

                    list_of_url.append(data['url'])

                    # product_url = product.find_element_by_tag_name('a').get_attribute('href')
                    # list_of_url.append(product_url)
                except Exception as err:
                    print(f"Error in def get_urls_from_search_results\n{err}", flush=True)
                    if self.args["debug"]:
                        print("*******************************************\n")
                        print("Last Four Exceptions")
                        import traceback
                        traceback.print_exc()
                        print("\n*******************************************")

            return list_of_url

    def get_data(self):
        return self.data

    def get_errors(self):
        return self.errors

    def scrape_product_page(self, driver: WebDriver):
        c: dict = self.config

        try:
            self.wait.until(ec.text_to_be_present_in_element((By.CSS_SELECTOR, c["extras"]["page_is_valid"]), ""),
                            "Page product not found")

        except Exception as err:
            print(err)
            self.errors.append(driver.current_url)
            return

        else:
            product_doesnt_exist = driver.find_elements_by_css_selector(c["extras"]["product_doesnt_exist"])
            if len(product_doesnt_exist) > 0:
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

            self.wait.until(ec.text_to_be_present_in_element((By.CSS_SELECTOR, c["seller_info"]["seller_name"]), ""),
                            "Shop name not found")
            d['TOKO'] = driver.find_element_by_css_selector(c["seller_info"]["seller_name"]).text.strip()

            product_specs = driver.find_element_by_css_selector(c["extras"]["product_specs"]).find_elements_by_css_selector(
                c["extras"]["product_specs_child"])
            location = None
            for loc in product_specs:
                if "Dikirim Dari".casefold() in loc.text.strip().casefold():
                    location = loc.text.strip()
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

            d['KOTA'] = kota or ""

            self.wait.until(lambda driver: driver.find_element_by_css_selector(c["product_info"]["title"]).text.strip() != '')
            nama_produk = driver.find_element_by_css_selector(c["product_info"]["title"]).text.strip()

            box_patt = "(?i)((?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule\b)[ ]+[0-9,]*[ ]?(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule|gr|gram|kg\b))|([0-9,]{1,6}[ ]?(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule|gr|gram|kg\b))|((?:(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule\b)[ ]?)+[0-9,]{1,6})"
            rbox = re.findall(box_patt, nama_produk)

            reg = []
            for tuple in rbox:
                reg.append([var for var in tuple if var != ''])

            d['BOX'] = ', '.join([item for sublist in reg for item in sublist]) if len(reg) > 0 else ""

            range_container = driver.find_element_by_css_selector(c["product_info"]["options"]["all_options_containers"])
            indiv_container = range_container.find_elements_by_css_selector(c["product_info"]["options"]["individual_container"])

            all_options = []

            for i in range(0, len(indiv_container) - 1):
                indiv_container_title = indiv_container[i].find_element_by_css_selector(
                    c["product_info"]["options"]["individual_container_title"]).text.strip()
                indiv_container_options = indiv_container[i].find_element_by_css_selector(
                    c["product_info"]["options"]["individual_container_items_container"])
                options = indiv_container_options.find_elements_by_css_selector(
                    c["product_info"]["options"]["individual_container_items_container_items"]
                )
                textoptions = [a.text.strip() for a in options]
                text = indiv_container_title + ': ' + ', '.join(textoptions)
                all_options.append(text)

            d['RANGE'] = '; '.join(all_options) if len(all_options) > 0 else ""

            sold_count_val = driver.find_elements_by_css_selector(c["product_info"]["sold_count"])
            if len(sold_count_val) > 0:
                sol = sold_count_val[0].text.strip()
                if 'RB' in sol:
                    sol = sol.replace('RB', '').replace('+', '')
                    if (',' in sol):
                        sol = sol.replace(',', '')
                        sol = int(sol) * 100
                    else:
                        sol = int(sol) * 1000
                d['JUAL (UNIT TERKECIL)'] = int(sol) if int(sol) != 0 else ""

            else:
                d['JUAL (UNIT TERKECIL)'] = ""

            prices = driver.find_elements_by_css_selector(c["product_info"]["price"]["price_before_discount"])
            self.wait.until(
                lambda driver: driver.find_element_by_css_selector(c["product_info"]["price"]["original"]).text.split() != '')

            if len(prices) > 0:
                prices = prices[0].text.split()
            else:
                prices = (driver.find_element_by_css_selector(c["product_info"]["price"]["original"]).text.split())

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
                raise NoSuchElementException("    Price not found")

            d['VALUE'] = ""

            disc = driver.find_elements_by_css_selector(c["product_info"]["price"]["discount_percentage"])
            if len(disc) > 0:
                disc_float = (disc[0].text.strip())[:(disc[0].text.strip()).index('%'):]
                disc = float(disc_float) / 100
            else:
                disc = ""

            d['% DISC'] = disc

            shop_cat = driver.find_elements_by_css_selector(c["extras"]["shop_category_container"])
            if len(shop_cat) > 0:
                mall = len(shop_cat[0].find_elements_by_css_selector(c["seller_info"]["category"])) > 0
                if mall:
                    cat = "OFFICIAL STORE"
                else:
                    cat = shop_cat[0].text.strip()
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

            rating_val = driver.find_elements_by_css_selector(c["product_info"]["rating"]["rating_value"])
            d['RATING (Khusus shopee dan toped dikali 20)'] = float(rating_val[0].text.strip()) * 20 if len(
                rating_val) > 0 else ""

            rating_count_val = driver.find_elements_by_css_selector(c["product_info"]["rating"]["rating_count"])
            if len(rating_count_val) > 0:
                rat = rating_count_val[0].text.strip()
                if 'RB' in rat:
                    rat = rat.replace('RB', '').replace(',', '').replace('+', '')
                    rat = int(rat) * 1000
                d['JML ULASAN'] = int(rat)

            else:
                d['JML ULASAN'] = ""

            d['DILIHAT'] = ""

            d['DESKRIPSI'] = driver.find_element_by_css_selector(c["product_info"]["description"]).text.strip()

            d['TANGGAL OBSERVASI'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # TODO MORE SPECIFIC EXCEPTION HANDLING
        except (NoSuchElementException, WebDriverException) as err:
            print(err)
            self.errors.append(driver.current_url)
            if self.args["debug"]:
                print("*******************************************\n")
                print("Last Four Exceptions")
                import traceback
                traceback.print_exc()
                print("\n*******************************************")

        else:
            self.completed_urls.append(d['SOURCE'])
            self.data.append(d)
            self.scraped_count += 1
            print(f"    Item #{self.scraped_count} completed")

    def next_search_page(self, driver: WebDriver) -> int:
        c = self.config
        try:

            self.wait.until(ec.presence_of_element_located(
                (By.CSS_SELECTOR, c["extras"]["next_page_btn"])),
                "No next page")

            next_button = driver.find_element_by_css_selector(
                c["extras"]["next_page_btn"])

            if next_button.is_enabled():
                print("Next page")
                next_button.click()
                return self.NEXT_PAGE_EXISTS
            else:
                return self.NEXT_PAGE_DEAD

        except TimeoutException as err:
            print(err)
            if self.args["debug"]:
                print("*******************************************\n")
                print("Last Four Exceptions")
                import traceback
                traceback.print_exc()
                print("\n*******************************************")

            return self.NEXT_PAGE_DEAD

        except NoSuchElementException:
            if self.args["debug"]:
                print("*******************************************\n")
                print("Last Four Exceptions")
                import traceback
                traceback.print_exc()
                print("\n*******************************************")

            return self.NEXT_PAGE_DEAD
