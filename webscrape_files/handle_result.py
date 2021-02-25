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
        self.interrupted = False
        operating_system = platform.system()

        self.output_dir = str(os.path.dirname(os.path.realpath(__file__)))

        # TODO REPLACE WITH PATHLIB
        if str(operating_system) == 'Linux':
            self.output_dir = self.output_dir.replace('/webscrape_files', '/Output/')

        elif str(operating_system) == 'Windows':
            self.output_dir = self.output_dir.replace('\\webscrape_files', '\\Output\\')

        if not os.path.exists(os.path.normpath(self.output_dir)):
            os.mkdir(os.path.normpath(self.output_dir))

    def save_csv(self, path, data, errors):
        if len(data) > 0:
            keyword = data[0]['KEYWORD']
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
                self.save_errors(path, errors, keyword)

        else:
            print("Nothing scraped")
            sys.exit(sc.SUCCESS_NORESULTS)

    def save_json(self, path, data, errors):
        if len(data) > 0:
            keyword = data[0]['KEYWORD']
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
                self.save_errors(path, errors, keyword)

        else:
            print("Nothing scraped")
            sys.exit(sc.SUCCESS_NORESULTS)

    def save_errors(self, path, errors, keyword):
        error = {
            "KEYWORD": keyword,
            "ERRORS": errors
        }
        if len(errors) > 0:
            path = path.replace('.json', '_errors.json').replace('.csv', '_errors.json')
            with open(path, 'w') as outFile:
                json.dump(error, outFile)

        ec = sc.ERROR_INTERRUPTED if self.interrupted else sc.SUCCESS_COMPLETE
        sys.exit(ec)

    def handle_scrape(self, data, errors, interrupted=False):
        if self.args["debug"]:
            print(json.dumps({
                "data_length": len(data),
                "error_length": len(errors),
                "interrupted": interrupted
            }, indent=4))

        self.interrupted = interrupted
        if self.file_type == "csv":
            self.file_name += ".csv"
            file_path = self.output_dir + self.file_name

            self.save_csv(file_path, data, errors)

        elif self.file_type == "json":
            self.file_name += ".json"
            file_path = self.output_dir + self.file_name

            self.save_json(file_path, data, errors)

    def handle_retry(self, data, errors):
        if self.args["debug"]:
            print(json.dumps({
                "data_length": len(data),
                "error_length": len(errors),
            }, indent=4))
        ## FROM ERRORS.json
        if "csv" in self.file_type:
            file_path = self.output_dir + self.file_name.replace('.csv', '_retry.' + self.file_type).replace('.json', '_retry.' + self.file_type)
            self.save_csv(file_path, data, errors)

        elif "json" in self.file_type:
            file_path = self.output_dir + self.file_name.replace('.json', '_retry.' + self.file_type).replace('.csv', '_retry.' + self.file_type)

            self.save_json(file_path, data, errors)

    def handle_continue(self, data, errors):
        if "csv" in self.file_name:
            file_path = self.output_dir + self.file_name.replace('.csv', '_continue.csv')
            self.save_csv(file_path, data, errors)

        elif "json" in self.file_name:
            file_path = self.output_dir + self.file_name.replace('.json', '_continue.json')
            self.save_json(file_path, data, errors)

    def handle_convert(self, data):
        if "csv" in self.file_path:
            file_path = self.file_path.replace('.csv', '.json')
            self.save_json(file_path, data, errors=[])

        elif "json" in self.file_path:
            file_path = self.file_path.replace('.json', '.csv')
            self.save_csv(file_path, data, errors=[])

    def handle_merge(self, data):
        if "json" in self.file_path[0]:
            file_path = self.file_path[0].replace('_continue.', '.').replace('.json', '_merged.json')
            self.save_json(file_path, data, errors=[])
            print(f"saved to {file_path}")

        elif "csv" in self.file_path[0]:
            file_path = self.file_path[0].replace('_continue.', '.').replace('.csv', '_merged.csv')
            self.save_csv(file_path, data, errors=[])
            print(f"saved to {file_path}")
