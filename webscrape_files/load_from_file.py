import csv
import json
import sys
from urllib import parse
from webscrape_files import shopee, tokopedia, bukalapak, handle_result, status_codes as sc
from webscrape_files.process import tokopedia as proc_tp, shopee as proc_shopee

class LoadFromFile:
    def __init__(self, args, path=None):
        self.path = path
        self.args = args
        self.result = args['result'] or ""
        self.check_file()

    def check_file(self):
        if "csv" in self.path[-4::]:
            self.filetype = "csv"

        elif "json" in self.path[-4::]:
            self.filetype = "json"

        else:
            sys.exit(sc.ERROR_GENERAL)

    def load_file(self):
        try:
            if self.filetype == "json":
                with open(self.path, 'r') as openFile:
                    data = json.load(openFile)

            elif self.filetype == "csv":
                with open(self.path, 'r', encoding=('utf-8'), newline='') as openFile:
                    data = [{key: (int(value) if value.isnumeric() else value) for key, value in row.items()}
                            for row in csv.DictReader(openFile, skipinitialspace=True)]

            else:
                raise FileNotFoundError()

            return data
        except FileNotFoundError as err:
            print(err)
            print("File not found")
            sys.exit(sc.ERROR_GENERAL)

    def load_urls_from_scraped_file(self, data):
        urls = [values['SOURCE'] for values in data]
        self.args['query'] = data[0]['KEYWORD']
        self.args['query_parsed'] = parse.quote(data[0]['KEYWORD'])
        return urls

    def continue_scrape(self):
        data = self.load_file()
        urls = self.load_urls_from_scraped_file(data)
        self.marketplace = data[0]['E-COMMERCE']
        self.ID = data[0]['E-COMMERCE']

        if self.marketplace.casefold() == 'tokopedia'.casefold():
            self.process = tokopedia.Tokopedia(self.args)
            self.data = self.process.data
            self.errors = self.process.errors
            self.process.continue_scrape(urls)

        elif self.marketplace.casefold() == 'bukalapak'.casefold():
            self.process = bukalapak.Bukalapak(self.args)
            self.data = self.process.data
            self.errors = self.process.errors
            self.process.continue_scrape(urls)

        elif self.marketplace.casefold() == 'shopee'.casefold():
            self.process = shopee.Shopee(self.args)
            self.data = self.process.data
            self.errors = self.process.errors
            self.process.continue_scrape(urls)

    def retry(self):
        urls = self.load_file()
        self.args['query'] = ''
        if "tokopedia" in urls[0]:
            self.process = tokopedia.Tokopedia(self.args)
            self.data = self.process.data
            self.errors = self.process.errors
            self.process.retry_errors(urls)

        elif "bukalapak" in urls[0]:
            self.process = bukalapak.Bukalapak(self.args)
            self.data = self.process.data
            self.errors = self.process.errors
            self.process.retry_errors(urls)

        elif "shopee" in urls[0]:
            self.process = shopee.Shopee(self.args)
            self.data = self.process.data
            self.errors = self.process.errors
            self.process.retry_errors(urls)

    def convert(self):
        data = self.load_file()
        hr = handle_result.HandleResult(file_path=self.path)
        hr.handle_convert(data)

    def process(self):
        data = self.load_file()
        self.marketplace = data[0]['E-COMMERCE']

        if self.marketplace.casefold() == 'tokopedia'.casefold():
            self.process = proc_tp.Tokopedia(data)

        elif self.marketplace.casefold() == 'shopee'.casefold():
            self.process = proc_shopee.Shopee(data)

        # elif self.marketplace.casefold() == 'bukalapak'.casefold():
        #     self.process = proc_bl.Bukalapak(data)

        clean_data = self.process.process()
        hr = handle_result.HandleResult(file_path=self.path)
        hr.handle_process(clean_data)
        