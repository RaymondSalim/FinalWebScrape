import argparse
import os
import re
import signal
import sys
import platform
from datetime import datetime
from urllib import parse
from webscrape_files import status_codes as sc
from webscrape_files import load_from_file as lff
from webscrape_files import shopee, tokopedia, bukalapak
from webscrape_files.handle_result import HandleResult
from urllib3.connection import NewConnectionError
from http.client import HTTPException

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(required=True, dest='command')

scrape_parser = subparsers.add_parser('scrape', help="Command to scrape", usage="""

The following arguments are required:
-m / --marketplace      [REQUIRED] the marketplace {tokopedia, bukalapak, shopee}
-q / --query            [REQUIRED] keyword for search
-sp / --startpage       [OPTIONAL] (DEFAULT = 1) start scraping from this page number
-ep / --endpage         [REQUIRED] (0 TO SCRAPE ALL PAGES) scrape until this page number
-r / --result           [REQUIRED] the file format for the results {csv, json}
-f / --filename         [OPTIONAL] the name of the final output

""")
scrape_parser.add_argument('-m',
                           '--marketplace',
                           help='[REQUIRED] the marketplace',
                           metavar='',
                           type=str.lower,
                           choices=['tokopedia', 'bukalapak', 'shopee'],
                           required=True)

scrape_parser.add_argument('-q',
                           '--query',
                           help='[REQUIRED] keyword for search',
                           metavar='',
                           type=str,
                           required=True)

scrape_parser.add_argument('-sp',
                           '--startpage',
                           help='[OPTIONAL] (DEFAULT = 1) start scraping from this page number',
                           metavar='',
                           type=int,
                           required=False,
                           default=1)

scrape_parser.add_argument('-ep',
                           '--endpage',
                           help='[REQUIRED] scrape until this page number',
                           metavar='',
                           type=int,
                           required=True)

scrape_parser.add_argument('-r',
                           '--result',
                           help='[REQUIRED] the file format for the results',
                           metavar='',
                           type=str.lower,
                           required=True,
                           choices=['csv', 'json']
                           )

scrape_parser.add_argument('-f',
                           '--filename',
                           help='[OPTIONAL] the name of the final output',
                           type=str,
                           metavar='',
                           default='',
                           required=False)

scrapeurl_parser = subparsers.add_parser('scrapeurl', help="Command to scrape URL", usage="""

The following arguments are required:
-u / --url         [REQUIRED] The URL to be scraped

""")
scrapeurl_parser.add_argument('-u',
                              '--url',
                              help='[REQUIRED] URL to be scraped',
                              type=str,
                              metavar='',
                              required=True
                              )

retry_parser = subparsers.add_parser('retry', help="Command to retry errors from xxx_errors.json", usage="""

The following arguments are required:
-f / --filename         [REQUIRED] name of the file containing the errors
-r / --result           [REQUIRED] the file format for the results {csv, json}

""")
retry_parser.add_argument('-f',
                         '--filename',
                          help='[REQUIRED] name of the file',
                          type=str,
                          metavar='',
                          required=True)
retry_parser.add_argument('-r',
                          '--result',
                          help='[REQUIRED] the file format for the results',
                          metavar='',
                          type=str.lower,
                          required=True,
                          choices=['csv', 'json']
                          )

convert_parser = subparsers.add_parser('convert', help="Command to convert from/to csv/json", usage="""

The following arguments are required:
-f / --filename         [REQUIRED] name of the file

""")
convert_parser.add_argument('-f',
                         '--filename',
                         help='[REQUIRED] name of the file',
                         type=str,
                         metavar='',
                         required=True)

continue_parser = subparsers.add_parser('continue', help="Command to continue scraping", usage="""

The following arguments are required:
-f / --filename         [REQUIRED] name of the incomplete job file
-sp / --startpage       [OPTIONAL] (DEFAULT = 1) start scraping from this page number
-ep / --endpage         [REQUIRED] scrape until this page number
-r / --result           [REQUIRED] the file format for the results {csv, json}

""")
continue_parser.add_argument('-f',
                             '--filename',
                             help='[REQUIRED] name of the file',
                             type=str,
                             metavar='',
                             required=True)

continue_parser.add_argument('-sp',
                             '--startpage',
                             help='[OPTIONAL] (DEFAULT = 1) start scraping from this page number',
                             metavar='',
                             type=int,
                             required=False,
                             default=1)

continue_parser.add_argument('-ep',
                             '--endpage',
                             help='[REQUIRED] scrape until this page number',
                             metavar='',
                             type=int,
                             required=True)

continue_parser.add_argument('-r',
                             '--result',
                             help='[REQUIRED] the file format for the results',
                             metavar='',
                             type=str.lower,
                             required=True,
                             choices=['csv', 'json']
                             )

process_parser = subparsers.add_parser('process', help="Command to process raw data", usage="""

The following arguments are required:
-f / --filename         [REQUIRED] name of the file to be processed

""")
process_parser.add_argument('-f',
                             '--filename',
                             help='[REQUIRED] name of the file',
                             type=str,
                             metavar='',
                             required=True)

current_path = str(os.path.dirname(os.path.realpath(__file__)))


class Main:
    operating_system = platform.system()
    original_sigint = signal.getsignal(signal.SIGINT)

    def __init__(self, arguments):
        self.args = vars(arguments)
        self.check_args()

    def get_final_path(self):
        if str(self.operating_system) == 'Windows':
            return current_path + '\\Output\\' + self.args['filename']
        else:
            return current_path + '/Output/' + self.args['filename']

    def check_args(self):
        arguments = self.args.keys()

        if "filename" in arguments:
            self.check_name()

        if "query" in arguments:
            self.fix_key_word()

    def check_name(self):
        query = r"^[ .]|[/<>:\"\\|?*]+|[ .]$"
        illegal_char = re.findall(query, self.args['filename'] or '')
        if len(illegal_char) == 0:
            return
        else:
            print(f"filename contains illegal characters:\n {illegal_char}\n replacing with \"_\"")
            self.args['filename'] = re.sub(query, "", self.args['filename'])

    def clear_console(self):
        if str(self.operating_system) == 'Windows':
            os.system('cls')
        else:
            os.system('clear')

    def fix_key_word(self):
        # Replaces any characters to HTML Charset
        self.args['query_parsed'] = parse.quote(self.args['query'])

    def handle_sigint(self, signum, frame):
        try:
            driver = self.process.driver
            driver.quit()
        except AttributeError:
            pass

        data = self.process.data
        errors = self.process.errors
        id = self.process.ID
        if len(data) > 0:
            if self.args['filename'] == '':
                # Filename argument is not specified, so filename will be generated
                self.args['filename'] = f"{self.args['query']}_{id}_{str(datetime.now()).replace(':', '꞉')}"

            else:
                if self.args['command'] != 'scrape':
                    self.args['filename'] = self.args['filename'].replace('.' + self.args['result'], '') + f"_{self.args['command']}"


            print("Process is interrupted, results might not be complete")
            handle_class = HandleResult(file_name=self.args['filename'], file_type=self.args['result'])
            handle_class.handle_scrape(data, errors)
        else:
            sys.exit(sc.SUCCESS_NORESULTS)


    def main(self):
        # pass
        # self.clear_console()
        try:
            if self.args['command'] == 'scrapeurl':
                # f = open(os.devnull, 'w')
                # sys.stdout = f

                self.process = lff.LoadFromFile(args=self.args)
                self.process.retry(urls=[self.args['url']])

            else:
                self.clear_console()

                if self.args['command'] == 'scrape':
                    # scrape
                    if self.args['marketplace'].lower() == 'tokopedia':
                        self.process = tokopedia.Tokopedia(self.args)
                        self.process.start_scrape()

                    elif self.args['marketplace'].lower() == 'bukalapak':
                        self.process = bukalapak.Bukalapak(self.args)
                        self.process.start_scrape()

                    elif self.args['marketplace'].lower() == 'shopee':
                        self.process = shopee.Shopee(self.args)
                        self.process.start_scrape()

                elif self.args['command'] == 'continue':
                    path = self.get_final_path()
                    self.process = lff.LoadFromFile(path=path, args=self.args)
                    self.process.continue_scrape()

                elif self.args['command'] == 'retry':
                    path = self.get_final_path()

                    self.process = lff.LoadFromFile(path=path, args=self.args)
                    self.process.retry()

                elif self.args['command'] == 'convert':
                    path = self.get_final_path()
                    self.args['result'] = ''
                    self.process = lff.LoadFromFile(path=path, args=self.args)
                    self.process.convert()

                elif self.args['command'] == 'process':
                    path = self.get_final_path()
                    self.args['result'] = 'csv' if "csv" in path else "json"
                    self.process = lff.LoadFromFile(path=path, args=self.args)
                    self.process.process()


                else:
                    sys.exit(sc.ERROR_ARGUMENT)
        except (NewConnectionError, HTTPException):
            sys.exit(sc.ERROR_GENERAL)
            pass

        except KeyboardInterrupt:
            pass

        except Exception as err:
            try:
                driver = self.process.driver
                driver.quit()
            except AttributeError:
                pass
            finally:
                print(err)
                self.handle_sigint(None, None)


try:
    args = parser.parse_args()
except TypeError as err:
    parser.print_help()
    sys.exit(sc.ERROR_ARGUMENT)
else:
    if __name__ == "__main__":
        main = Main(args)
        signal.signal(signal.SIGINT, main.handle_sigint)
        main.main()
