import argparse
import os
import platform
import re
import signal
import sys
from datetime import datetime
from pathlib import Path
from urllib import parse

from webscrape_files import status_codes as sc
from webscrape_files.handle_result import HandleResult
from webscrape_files.start import Start

parser = argparse.ArgumentParser()
verbose = parser.add_argument('-d', '--debug',
                              action='store_true',
                              help='[OPTIONAL] debugging mode')

no_headless = parser.add_argument('--no-headless',
                                  action='store_false',
                                  help='[OPTIONAL] start chrome in non-headless mode')

max_consecutive_error = parser.add_argument('--max-error',
                                            type=int,
                                            default=5,
                                            help='[OPTIONAL] number of maximum consecutive errors before exiting')

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
                           choices=['tokopedia', 'bukalapak', 'shopee', 'lazada'],
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

scrapeurl_parser.add_argument('-q',
                              '--query',
                              help='[OPTIONAL] keyword for search',
                              metavar='',
                              default='',
                              type=str,
                              required=False)

retry_parser = subparsers.add_parser('retry', help="Command to retry errors from xxx_errors.json", usage="""

The following arguments are required:
-f / --filename         [REQUIRED] name of the file containing the errors
-r / --result           [REQUIRED] the file format for the results {csv, json}

Either -f or -r has to be present

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

merge_parser = subparsers.add_parser('merge', help="Command to merge two files csv/json", usage="""

The following arguments are required:
-f1 / --file-1         [REQUIRED] name of the first file
-f2 / --file-2         [REQUIRED] name of the second file

""")
merge_parser.add_argument('-f1',
                          '--file-1',
                          help='[REQUIRED] name of the first file',
                          type=str,
                          metavar='',
                          required=True)

merge_parser.add_argument('-f2',
                          '--file-2',
                          help='[REQUIRED] name of the second file',
                          type=str,
                          metavar='',
                          required=True)

current_path = (Path(__file__).resolve()).parent


class Main:
    operating_system = platform.system()
    original_sigint = signal.getsignal(signal.SIGINT)

    def __init__(self, arguments):
        self.args = vars(arguments)
        self.check_args()

    def get_final_path(self):
        if self.args['command'].casefold() == 'merge'.casefold():
            path1 = Path(f"Output/{self.args['file_1']}")
            path2 = Path(f"Output/{self.args['file_2']}")

            return [str(current_path.joinpath(path1)), str(current_path.joinpath(path2))]
        else:
            path = Path(f"Output/{self.args['filename']}")
            return str(current_path.joinpath(path))

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

    def save_data(self, error=None, interrupted=False):
        try:
            driver = self.process.get_driver()
            driver.quit()
        except AttributeError:
            pass

        proc = self.process.get_process()

        data = proc.data
        errors = proc.errors
        id = self.process.get_ID()

        if self.args["debug"]:
            print("*******************************************\n")
            print("Last Four Exceptions")
            import traceback
            traceback.print_exc()
            print("\n*******************************************")

        if len(data) > 0:
            if self.args['filename'] == '':
                # Filename argument is not specified, so filename will be generated
                self.args['filename'] = f"{self.args['query']}_{id}_{str(datetime.now()).replace(':', '-')}"

            else:
                if self.args['command'] != 'scrape':
                    self.args['filename'] = self.args['filename'].replace('.' + self.args['result'],
                                                                          '') + f"_{self.args['command']}"

            print("Process is interrupted, results might not be complete")
            if error is not None:
                print(error)

            handle_class = HandleResult(file_name=self.args['filename'], file_type=self.args['result'], args=self.args)
            handle_class.handle_scrape(data, errors, interrupted=interrupted)
        else:
            if self.args["debug"]:
                print(f"Exit code is {sc.SUCCESS_NORESULTS}")
            sys.exit(sc.SUCCESS_NORESULTS)

    def handle_sigint(self, signum, frame):
        self.save_data(interrupted=True)

    def main(self):
        try:
            if self.args['command'] == 'scrapeurl':
                if not self.args["debug"]:
                    # Changes stdout to null
                    f = open(os.devnull, 'w')
                    sys.stdout = f
                start = Start(args=self.args)
                self.process = start
                start.start()

            else:
                self.clear_console()

                if self.args['command'] == 'scrape':
                    """
                        scrape takes 4 required parameters and 2 optional
                            Required:
                                - marketplace
                                - query
                                - endpage
                                - result
                            Optional:
                                - startpage (Default = 1)
                                - filename 
                    """
                    start = Start(args=self.args)
                    self.process = start
                    start.start()

                elif self.args['command'] in ['continue', 'retry', 'convert', 'merge']:
                    self.args['path'] = self.get_final_path()
                    start = Start(args=self.args)
                    self.process = start
                    start.start()

                else:
                    if self.args["debug"]:
                        print(f"Exit code is {sc.ERROR_ARGUMENT}")
                    sys.exit(sc.ERROR_ARGUMENT)
        except Exception as error:
            self.save_data(error=error)

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
