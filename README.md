# WebScraping

Program to scrape products from Tokopedia, Bukalapak, Shopee

## First Run
```shell
git clone https://github.com/RaymondSalim/FinalWebScrape
cd FinalWebScrape
python setup.py
```
Executing setup.py will automatically download and prepare the required files. 
If an error happens here, do the following:
  1. Get the chromedriver file <a href="https://chromedriver.chromium.org/">Here</a>
  2. Unzip the downloaded archive and place it in ```./Files/``` folder


## Using the program
The following help document can be obtained by ```python main.py -h```
```shell
usage: main.py [-h] {scrape,retry,convert,continue} ...

positional arguments:
  {scrape,retry,convert,continue}
    scrape              Command to scrape
    retry               Command to retry errors from xxx_errors.json
    convert             Command to convert from/to csv/json
    continue            Command to continue scraping

optional arguments:
  -h, --help            show this help message and exit
```


### Scraping
```shell
usage: 

The following arguments are required:
-m / --marketplace      [REQUIRED] the marketplace {tokopedia, bukalapak, shopee}
-q / --query            [REQUIRED] keyword for search
-sp / --startpage       [OPTIONAL] (DEFAULT = 1) start scraping from this page number
-ep / --endpage         [REQUIRED] (0 TO SCRAPE ALL PAGES) scrape until this page number
-r / --result           [REQUIRED] the file format for the results {csv, json}
-f / --filename         [OPTIONAL] the name of the final output
````
Example:
* Tokopedia, "masker bagus", from page 5 to page 25, save as csv
```shell
python main.py scrape -m tokopedia -q "masker bagus" -sp 5 -ep 25 -r csv
```
* Shopee, "obat batuk", all results, save as json
```shell
python main.py scrape -m shopee -q "obat batuk" -ep 0 -r json
```


### Retrying Errors
The program will automatically save a file ending with ```_errors.json``` which contains url of all the pages that had failed. This program allows you to retry all the failed urls. All retried urls will be saved in a new file with the same file name ending with ```_retry```
```shell
usage: 

The following arguments are required:
-f / --filename         [REQUIRED] name of the file containing the errors
-r / --result           [REQUIRED] the file format for the results {csv, json}
```


### Continuing Interrupted Job
This program allows you to continue interrupted jobs. This process will skip all scraped product and only scrape products that has been skipped. A new file will be saved in a new file with the same file name ending with ```_continued```
```shell
usage:

The following arguments are required:
-f / --filename         [REQUIRED] name of the incomplete job file
-sp / --startpage       [OPTIONAL] (DEFAULT = 1) start scraping from this page number
-ep / --endpage         [REQUIRED] scrape until this page number
-r / --result           [REQUIRED] the file format for the results {csv, json}
```


### Converting Result
This program allows you to convert file from JSON to CSV and vice versa. The converted file will have the same name
```shell
usage: 

The following arguments are required:
-f / --filename         [REQUIRED] name of the file
```

<hr>

### To Do List
- [x] Merge similar functions in different classes
- [ ] Improve exit code based on exception