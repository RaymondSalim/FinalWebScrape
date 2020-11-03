import csv
import json
import os
import platform
import sys
from . import status_codes as sc


class HandleResult:
    def __init__(self,
                 file_name=None,
                 file_type=None,
                 file_path=None
                 ):
        self.file_name = file_name
        self.file_type = file_type
        self.file_path = file_path
        operating_system = platform.system()

        self.output_dir = str(os.path.dirname(os.path.realpath(__file__)))

        if str(operating_system) == 'Linux':
            self.output_dir = self.output_dir.replace('/webscrape_files', '/Output/')

        elif str(operating_system) == 'Windows':
            self.output_dir = self.output_dir.replace('\\webscrape_files', '\\Output\\')

        if not os.path.exists(os.path.normpath(self.output_dir)):
            os.mkdir(os.path.normpath(self.output_dir))

    def handle_scrape(self, data, errors):
        if self.file_type == "csv":
            self.file_name += ".csv"
            file_path = self.output_dir + self.file_name

            self.save_csv(file_path, data, errors)

        elif self.file_type == "json":
            self.file_name += ".json"
            file_path = self.output_dir + self.file_name

            self.save_json(file_path, data, errors)

    def save_csv(self, path, data, errors):
        if len(data) > 0:
            try:
                keys = data[0].keys()
                with open(path, 'w', newline='', encoding='utf-8') as csvFile:
                    dict_writer = csv.DictWriter(csvFile, keys)
                    dict_writer.writeheader()
                    dict_writer.writerows(data)

                print(f"Saved to {path}")

            except Exception as err:
                print(err)
                print("\nSaving error occured, saving as json instead")

                with open(path.replace('.csv', '.json'), 'w') as outFile:
                    json.dump(data, outFile)

                print(f"Saved to {path.replace('.csv', '.json')}")

            finally:
                self.save_errors(path, errors)

        else:
            print("Nothing scraped")
            sys.exit(sc.SUCCES_NORESULTS)

    def save_json(self, path, data, errors):
        if len(data) > 0:
            try:
                with open(path, 'w') as outFile:
                    json.dump(data, outFile)

                print(f"Saved to {path}")

            except Exception as err:
                print(err)
                print("\nSaving error occured, saving as csv instead")
                keys = data[0].keys()

                with open(path.replace('.json', '.csv'), 'w', newline='', encoding='utf-8') as csvFile:
                    dict_writer = csv.DictWriter(csvFile, keys)
                    dict_writer.writeheader()
                    dict_writer.writerows(data)

            finally:
                self.save_errors(path, errors)

        else:
            print("Nothing scraped")
            sys.exit(sc.SUCCES_NORESULTS)

    def save_errors(self, path, errors):
        if len(errors) > 0:
            path = path.replace('.json', '_errors.json')
            with open(path, 'w') as outFile:
                json.dump(errors, outFile)

        sys.exit(sc.SUCCESS_COMPLETE)

    def handle_retry(self, data, errors):
        ## FROM ERRORS.json
        if "csv" in self.file_name:
            file_path = self.output_dir + self.file_name.replace('.csv', '_retry.csv')
            self.save_csv(file_path, data, errors)

        elif "json" in self.file_name:
            file_path = self.output_dir + self.file_name.replace('.json', '_retry.json')

            self.save_json(file_path, data, errors)

    def handle_continue(self, data, errors):
        if "csv" in self.file_name:
            file_path = self.output_dir + self.file_name.replace('.csv', '_continued.csv')
            self.save_csv(file_path, data, errors)

        elif "json" in self.file_name:
            file_path = self.output_dir + self.file_name.replace('.json', '_continued.json')
            self.save_json(file_path, data, errors)

    def handle_convert(self, data):
        if "csv" in self.file_path:
            file_path = self.file_path.replace('.csv', '.json')
            self.save_json(file_path, data, errors=[])

        elif "json" in self.file_path:
            file_path = self.file_path.replace('.json', '.csv')
            self.save_csv(file_path, data, errors=[])

