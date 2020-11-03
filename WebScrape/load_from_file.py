import csv
import json

from WebScrape import shopee, tokopedia, bukalapak, handle_result

class LoadFromFile:
    def __init__(self, args, path=None):
        self.path = path
        self.args = args
        self.result = args['result'] or ""
        self.check_file()

    def check_file(self):
        if "tokopedia" in self.path:
            self.marketplace = "tokopedia"

        elif "bukalapak" in self.path:
            self.marketplace = "bukalapak"

        elif "shopee" in self.path:
            self.marketplace = "shopee"

        if "csv" in self.path:
            self.filetype = "csv"

        elif "json" in self.path:
            self.filetype = "json"

    def load_file(self):
        if "json" in self.path:
            with open(self.path, 'r') as openFile:
                data = json.load(openFile)

        elif "csv" in self.path:
            with open(self.path, 'r') as openFile:
                data = [{key: (int(value) if value.isnumeric() else value) for key, value in row.items()}
                             for row in csv.DictReader(openFile, skipinitialspace=True)]
        return data

    def load_urls_from_scraped_file(self, data):
        urls = [values['SOURCE'] for values in data]
        self.args['query'] = data[0]['KEYWORD']
        print(urls)
        return urls

    def continue_scrape(self):
        data = self.load_file()
        urls = self.load_urls_from_scraped_file(data)
        self.marketplace = data[0]['E-COMMERCE']

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
        print(urls[0])
        if "tokopedia" in urls[0]:
            self.process = tokopedia.Tokopedia(self.args)
            self.process.retry_errors(urls)

        elif "bukalapak" in urls[0]:
            self.process = bukalapak.Bukalapak(self.args)
            self.process.retry_errors(urls)

        elif "shopee" in urls[0]:
            self.process = shopee.Shopee(self.args)
            self.process.continue_scrape(urls)

    def convert(self):
        data = self.load_file()
        hr = handle_result.HandleResult(file_path=self.path)
        hr.handle_convert(data)