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


class Tokopedia:
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
        try:
            has_results = self.driver.find_element_by_css_selector('button[data-testid="btnSRPChangeKeyword"]').text
            if "Ganti kata kunci" in has_results:
                print("No results found, try another query?")
                return []
        except NoSuchElementException:
            pass

        print(f"Page {start_page}", flush=True)
        search_results = self.driver.find_element_by_css_selector('div[data-testid="divSRPContentProducts"]')
        products = search_results.find_elements_by_class_name('pcv3__info-content')
        
        list_of_url = []

        for product in products:
            try:
                product_url = product.get_attribute('href')
                if "ta.tokopedia.com" in product_url:
                    product_url = self.get_url_from_ad_link(product_url)
                list_of_url.append(product_url)
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
        # try:
        #     self.wait.until_not(ec.url_contains("ta.tokopedia"))
        #
        # except TimeoutException as err:
        #     print(err)
        #     self.errors.append(driver.current_url)
        #     return

        # try:
        #     self.wait.until(
        #         ec.text_to_be_present_in_element((By.CSS_SELECTOR, 'div[data-testid="pdpDescriptionContainer"]'), ""),
        #         "pdpDescriptionContainer not found")
        # except TimeoutException as err:
        #     print(err)
        #     print("timed out, skipping")
        #     self.errors.append(driver.current_url)
        #     return
        #
        # else:
        is_page_valid = driver.find_elements_by_css_selector(
            'h1[class="css-6hac5w-unf-heading e1qvo2ff1"]')  # Required to check if product page is valid

        if len(is_page_valid) > 0:
            return

        """
        Starts scraping process here
        """

        try:
            # self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[aria-label="unf-overlay"]')))
            # overlay = driver.find_elements_by_css_selector('div[aria-label="unf-overlay"]')
            # print(overlay.__str__())
            # if len(overlay) > 0:
            #     overlay_parent = overlay[0].find_element_by_xpath('..')
            #     print(overlay_parent)


            driver.implicitly_wait(0)
            d = dict()

            d['KEYWORD'] = self.args['query']


            d['PRODUK'] = ""
            d['FARMASI'] = ""
            d['E-COMMERCE'] = 'TOKOPEDIA'

            # self.wait.until(ec.text_to_be_present_in_element((By.CSS_SELECTOR, 'a[data-testid="llbPDPFooterShopName"]'), "Shop name not found"))
            self.wait.until(lambda driver:driver.find_element_by_css_selector('a[data-testid="llbPDPFooterShopName"]').text.split() != '', "Shop name not found")
            d['TOKO'] = driver.find_element_by_css_selector('a[data-testid="llbPDPFooterShopName"]').text.strip()
            driver.implicitly_wait(0)

            # self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="lblPDPSellerOrigin"]')))
            # self.wait.until(ec.presence_of_element_located((By.ID, 'pdp_comp-shipping')))
            # location = driver.find_element_by_css_selector('div[data-testid="lblPDPSellerOrigin"]').text
            # location = location[13::]  # Removes "Dikirim Dari"
            location = driver.find_element_by_css_selector('meta[name="twitter:data2"]').get_attribute('content')
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

            nama_produk = driver.find_element_by_css_selector('h1[data-testid="lblPDPDetailProductName"]').text.strip()

            box_patt = "(?i)((?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule\b)[ ]+[0-9,]*[ ]?(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule|gr|gram|kg\b))|([0-9,]{1,6}[ ]?(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule|gr|gram|kg\b))|((?:(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule\b)[ ]?)+[0-9,]{1,6})"
            rbox = re.findall(box_patt, nama_produk)

            reg = []
            for tuple in rbox:
                reg.append([var for var in tuple if var != ''])

            d['BOX'] = ', '.join([item for sublist in reg for item in sublist]) if len(reg) > 0 else ""

            range_data = []
            ignored_containers = ['HARGA', 'JUMLAH', 'PROMO', 'INFO PRODUK', 'ONGKOS KIRIM']
            range_containers = driver.find_elements_by_css_selector('div[class="css-8atqhb"]')

            """
            Selenium are not able to get text of elements not displayed (e.g dropdowns)
            This script clicks on all dropdowns making them visible
            """
            driver.execute_script("""
            document.querySelectorAll('[data-testid*="btnProductVariantLevel"]').forEach((el) => {
                el.querySelector('button').click()
            })
            """)

            for i in range(0, len(range_containers)):
                range_title = range_containers[i].find_elements_by_css_selector('div[data-testid*="pdpVariantTitle"] span')
                if len(range_title) > 0:
                    if range_title[0].text.strip() in ignored_containers:
                        continue
                    else:
                        title = range_title[0].text.strip()
                        range_options_container = range_containers[i].find_elements_by_css_selector('[data-testid*="pdpVariantItemLevel"]')

                        options = []
                        for j in range(0, len(range_options_container)):
                            range_options = range_options_container[j].find_elements_by_css_selector('img')

                            if len(range_options) > 0:
                                range_element = range_options[0].get_attribute('alt')
                            else:
                                range_element = range_options_container[j].find_element_by_tag_name('span').text.strip()

                            options.append(range_element)

                        range_final = title + ': ' + ', '.join(options)
                        range_data.append(range_final)

            d['RANGE'] = '; '.join(range_data)

            sold_count_valid = driver.find_elements_by_css_selector(
                'div[data-testid="lblPDPDetailProductSoldCounter"]')
            sold_count = sold_count_valid[0].text.strip() if len(sold_count_valid) > 0 else ""
            if ("barang berhasil terjual".casefold() in sold_count.casefold()):
                x = re.search('(\d+)', sold_count)
                sold_count = x.group(1)
            else:
                sold_count = sold_count[8::].replace(',','').replace('.', '')
                if "rb" in sold_count:
                    sold_count = sold_count.replace('rb', '')
                    sold_count = int(sold_count) * 100

            d['JUAL (UNIT TERKECIL)'] = int(sold_count) if len(sold_count_valid) > 0 else ""


            discount = driver.find_elements_by_css_selector('span[data-testid="lblPDPDetailOriginalPrice"]')
            if len(discount) > 0:
                d['HARGA UNIT TERKECIL'] = int((discount[0].text.strip()[2::]).replace(".", ""))
            else:
                price = driver.find_element_by_css_selector('div[data-testid="lblPDPDetailProductPrice"]').text.strip()
                d['HARGA UNIT TERKECIL'] = int((price[2::]).replace(".", ""))

            d['VALUE'] = ""

            discount = driver.find_elements_by_css_selector('span[data-testid="lblPDPDetailDiscountPercentage"]')
            d['% DISC'] = float(discount[0].text.strip().replace('%',''))/100 if len(discount) > 0 else ""

            shop_container = driver.find_element_by_css_selector('a[data-testid="llbPDPFooterShopName"]')
            shop_category = shop_container.find_elements_by_css_selector('img[data-testid*="pdpShopBadge"]')
            if len(shop_category) > 0:
                shop_category = shop_category[0].get_attribute('alt')
                if shop_category.casefold() == "Official Store".casefold():
                    cat = "OFFICIAL STORE"
                elif shop_category.casefold() == "Power Merchant".casefold():
                    cat = "STAR SELLER"
                elif shop_category.casefold() == "".casefold():
                    cat = "TOKO BIASA"
                else:
                    cat = "TOKO BIASA"
            else:
                cat = "TOKO BIASA"
            d['KATEGORI'] = cat

            url = driver.current_url
            if '?' in url:
                url = url[:str(driver.current_url).index('?')]
            d['SOURCE'] = url

            d['NAMA PRODUK E-COMMERCE'] = nama_produk

            rating = driver.find_elements_by_css_selector('span[data-testid="lblPDPDetailProductRatingNumber"]')
            d['RATING (Khusus shopee dan toped dikali 20)'] = float(rating[0].text.strip())*20 if len(rating) > 0 else ""

            rating_total = driver.find_elements_by_css_selector(
                'span[data-testid="lblPDPDetailProductRatingCounter"]')
            rating_total = rating_total[0].text.strip().replace('(','').replace(',','').replace('.', '').replace(' ulasan)', '') if len(rating_total) > 0 else ""
            if "rb" in rating_total:
                rating_total = rating_total.replace('rb','')
                rating_total = int(rating_total) * 100

            d['JML ULASAN'] = int(rating_total) if len(str(rating_total)) > 0 else ""

            # seen_by = (
            #     driver.find_elements_by_css_selector('span[data-testid="lblPDPDetailProductSeenCounter"]'))
            # seen_by = seen_by[0].text[:seen_by[0].text.index("x"):].replace('(','').replace(')', '').replace(',','').replace('.', '')
            # if "rb" in seen_by:
            #     seen_by = seen_by.replace('rb', '')
            #     seen_by = int(seen_by) * 100

            # d['DILIHAT'] = int(seen_by)
            d['DILIHAT'] = ''

            # self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="lblPDPDescriptionProduk"]')), "Description not found, skipping")

            desc = driver.find_elements_by_css_selector(
                'div[data-testid="lblPDPDescriptionProduk"]')
            d['DESKRIPSI'] = desc[0].text if len(desc) > 0 else "Tidak ada Deskripsi"

            d['TANGGAL OBSERVASI'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        except (NoSuchElementException, WebDriverException) as err:
            # raise err
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
        try:
            driver.implicitly_wait(3)
            next_button = driver.find_element_by_css_selector('button[aria-label="Halaman berikutnya"]')

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

    def get_url_from_ad_link(self, product_url) -> str:
        url = product_url[product_url.rindex("https")::]
        return uq(url)
