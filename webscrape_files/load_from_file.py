import csv
import json
import sys
from urllib import parse
from . import handle_result, status_codes as sc


class LoadFromFile:
    process = None
    start = []

    def __init__(self, args, path=None):
        self.path = path
        self.args = args
        self.data = []
        self.errors = []
        self.result = args.get('result', "")
        self.check_file()

    def check_file(self):
        if self.args['command'] != 'scrapeurl':
            if "csv" in self.path[-4::]:
                self.filetype = "csv"

            elif "json" in self.path[-4::]:
                self.filetype = "json"

            else:
                sys.exit(sc.ERROR_INVALID_FILE)

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
            sys.exit(sc.ERROR_FILE_NOT_FOUND)

    def load_urls_from_scraped_file(self, data):
        urls = [values['SOURCE'] for values in data]
        self.args['query'] = data[0]['KEYWORD']
        self.args['query_parsed'] = parse.quote(data[0]['KEYWORD'])
        return urls

