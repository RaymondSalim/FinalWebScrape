import argparse
import os
import re
import signal
import sys
import platform
from urllib import parse
from WebScrape import Shopee, Tokopedia, Bukalapak

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(required=True, dest='command')

scrape_parser = subparsers.add_parser('scrape', help="Command to scrape", usage="""

The following arguments are required:
-m / --marketplace      [REQUIRED] the marketplace
-q / --query            [REQUIRED] keyword for search
-sp / --startpage       [REQUIRED] start scraping from this page number
-ep / --endpage         [REQUIRED] scrape until this page number
-r / --result           [REQUIRED] the file format for the results
-f / --filename         [OPTIONAL] the name of the final output

""")
scrape_parser.add_argument('-m',
                           '--marketplace',
                           help='[REQUIRED] the marketplace',
                           metavar='',
                           type=str,
                           required=True)

scrape_parser.add_argument('-q',
                           '--query',
                           help='[REQUIRED] keyword for search',
                           metavar='',
                           type=str,
                           required=True)

scrape_parser.add_argument('-sp',
                           '--startpage',
                           help='[OPTIONAL] start scraping from this page number (Default is 1)',
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
                           type=str,
                           required=True)

scrape_parser.add_argument('-f',
                           '--filename',
                           help='[OPTIONAL] the name of the final output',
                           type=str,
                           metavar='',
                           required=False)

load_parser = subparsers.add_parser('load', help="Command to load from file or retry errors", usage="""

The following arguments are required:
-f / --filename         [REQUIRED] name of the file
-r / --result           [REQUIRED] the file format for the results

""")
load_parser.add_argument('-f',
                         '--filename',
                         help='[REQUIRED] name of the file',
                         type=str,
                         metavar='',
                         required=True)
load_parser.add_argument('-r',
                         '--result',
                         help='[REQUIRED] the file format for the results',
                         metavar='',
                         type=str,
                         required=True)

continue_parser = subparsers.add_parser('continue', help="Command to continue scraping", usage="""

The following arguments are required:
-f / --filename         [REQUIRED] name of the file
-sp / --startpage      [REQUIRED] start scraping from this page number
-ep / --endpage        [REQUIRED] scrape until this page number
-r / --result           [REQUIRED] the file format for the results

""")
continue_parser.add_argument('-f',
                             '--filename',
                             help='[REQUIRED] name of the file',
                             type=str,
                             metavar='',
                             required=True)

continue_parser.add_argument('-sp',
                             '--startpage',
                             help='[OPTIONAL] start scraping from this page number (Default is 1)',
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
                             type=str,
                             required=True)


class Main:
    operating_system = platform.system()
    original_sigint = signal.getsignal(signal.SIGINT)

    def __init__(self, arguments):
        arguments.query = self.fix_key_word(arguments.query)
        self.args = vars(arguments)
        self.check_name()

    def check_name(self):
        query = r"^[ .]|[/<>:\"\\|?*]+|[ .]$"
        illegal_char = re.findall(query, self.args['filename'])
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

    def fix_key_word(self, keyword):
        # Replaces any characters to HTML Charset
        return parse.quote(keyword)

    def handle_sigint(self, signum, frame):
        signal.signal(signal.SIGINT, self.original_sigint)

        try:
            if input("Are you sure you want to quit? [y/n]").lower().startswith('y'):
                sys.exit(0)

        except KeyboardInterrupt:
            sys.exit(1)

        else:
            signal.signal(signal.SIGINT, self.handle_sigint)

    def main(self):
        self.clear_console()
        if self.args['command'] == 'scrape':
            # scrape
            if self.args['marketplace'].lower() == 'tokopedia':
                self.process = Tokopedia.Tokopedia(self.args)
                self.process.start_scrape()

            elif self.args['marketplace'].lower() == 'bukalapak':
                self.process = Bukalapak.Bukalapak(self.args)
                self.process.start_scrape()

            elif self.args['marketplace'].lower() == 'shopee':
                self.process = Shopee.Shopee(self.args)
                self.process.start_scrape()

        elif self.command == 'continue':
            #continue

        elif self.command == 'load':
            #load
        else:
            sys.exit(1)


try:
    args = parser.parse_args()
except TypeError as err:
    parser.print_help()
    exit()
else:
    if __name__ == "__main__":
        main = Main(args)
        signal.signal(signal.SIGINT, main.handle_sigint)
        main.main()
