import re
from typing import List
from datetime import datetime
from . import city_list as cl
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


class Bukalapak:
    timeout_limit = 10
    NEXT_PAGE_DEAD = 0
    NEXT_PAGE_EXISTS = 1

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
        try:
            has_results = self.driver.find_element_by_css_selector('p[class="mb-8 bl-text bl-text--subheading-1"]').text
            if "Maaf, barangnya tidak ketemu" in has_results:
                print("No results found, try another query?")
                return []
        except NoSuchElementException:
            pass

        try:
            self.wait.until(
                ec.presence_of_element_located((By.XPATH, '//div[@class="bl-product-card__thumbnail"]//*//a')),
                "No items found on this page")

        except TimeoutException:
            return []

        else:
            print(f"Page {start_page}", flush=True)
            products = self.driver.find_elements_by_css_selector('div[class="bl-product-card__description"]')

            list_of_url = []

            for product in products:
                try:
                    product_url = product.find_element_by_tag_name('a').get_attribute('href')
                    list_of_url.append(product_url)
                except NoSuchElementException:
                    pass
            return list_of_url

    def get_data(self):
        return self.data

    def get_errors(self):
        return self.errors

    def scrape_product_page(self, driver: WebDriver):
        try:
            self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[id="section-informasi-barang"]')),
                            "Page timeout")

        except TimeoutException as err:
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

                box_patt = "(?i)((?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule\b)[ ]+[0-9,]*[ ]?(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule|gr|gram|kg\b))|([0-9,]{1,6}[ ]?(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule|gr|gram|kg\b))|((?:(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule\b)[ ]?)+[0-9,]{1,6})"
                rbox = re.findall(box_patt, nama_produk)

                reg = []
                for tuple in rbox:
                    reg.append([var for var in tuple if var != ''])

                d['BOX'] = ', '.join([item for sublist in reg for item in sublist]) if len(reg) > 0 else ""

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
                mall = len(driver.find_element_by_class_name('c-main-product__head').find_elements_by_class_name('bukamall')) > 0
                super_seller = len(shop_category.find_elements_by_css_selector('div[class*="c-badges__new-super-seller"]')) > 0
                cat = shop_category.text.replace('\n', '').replace(' ', '')
                q = ['super', 'trusted']
                if any(a in cat.casefold() for a in q) or super_seller:
                    cat = "STAR SELLER"
                elif "Resmi".casefold() == cat.casefold() or "bukamall" in shop_category.get_attribute('innerHTML') or mall:
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

            except (NoSuchElementException, WebDriverException) as err:
                print(err)
                self.errors.append(driver.current_url)

            else:
                self.completed_urls.append(d['SOURCE'])
                self.data.append(d)
                self.scraped_count += 1
                print(f"    {self.ID} {self.args['query']} Item #{self.scraped_count} completed")

    def next_search_page(self, driver: WebDriver) -> int:
        try:
            next_button = driver.find_element_by_css_selector("a[class*='pagination__next']")

            if next_button.is_enabled():
                print(f"{self.ID} {self.args['query']} Next page")
                next_button.click()
                return self.NEXT_PAGE_EXISTS
            else:
                return self.NEXT_PAGE_DEAD

        except TimeoutException as err:
            print(err)
            return self.NEXT_PAGE_DEAD

        except NoSuchElementException as err:
            return self.NEXT_PAGE_DEAD
