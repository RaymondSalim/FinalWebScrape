import re
from typing import List, Dict
from .. import city_list as cl


class Tokopedia:

    def __init__(self, input_data):
        self.dirty_data = input_data
        self.clean_data = []
        self.url_completed = []

    def process(self) -> List[Dict]:
        duplicates = 0
        for data in self.dirty_data:
            if (data['SOURCE'] in self.url_completed):
                duplicates += 1
                continue

            clean = self.process_row(data)
            self.clean_data.append(clean)

        print(f"{duplicates} Duplicates skipped", flush=True)
        return self.clean_data

    def process_row(self, data):
        clean_row = {
            'KEYWORD': data['KEYWORD'],
            'PRODUK': data['PRODUK'],  # Empty
            'FARMASI': data['FARMASI'],  # Empty
            'E-COMMERCE': 'TOKOPEDIA',
            'TOKO': data['TOKO'],
            'ALAMAT': data['ALAMAT'],
            'KOTA': data['KOTA'],  # Processed below
            'BOX': data['KOTA'],  # Processed below
            'RANGE': data['RANGE'],
            'JUAL (UNIT TERKECIL)': data['JUAL (UNIT TERKECIL)'],  # Processed below
            'HARGA UNIT TERKECIL': data['HARGA UNIT TERKECIL'],  # Processed below
            'VALUE': data['VALUE'],  # Empty
            '% DISC': data['% DISC'],  # Processed below
            'KATEGORI': data['KATEGORI'],  # Processed below
            'SOURCE': data['SOURCE'],
            'NAMA PRODUK E-COMMERCE': data['NAMA PRODUK E-COMMERCE'],
            'RATING (Khusus shopee dan toped dikali 20)': data['RATING (Khusus shopee dan toped dikali 20)'],
            # Processed below
            'JML ULASAN': data['JML ULASAN'],  # Processed below
            'DILIHAT': data['DILIHAT'],  # Processed below
            'DESKRIPSI': data['DESKRIPSI'],
            'TANGGAL OBSERVASI': data['TANGGAL OBSERVASI']
        }
        self.url_completed.append(clean_row['SOURCE'])

        # Start Processing "KOTA"
        kota = None

        for city in cl.cities:
            if city.casefold() in clean_row['ALAMAT'].casefold():
                kota = city
                break

        if kota is None:
            for regency in cl.regencies:
                if regency.casefold() in clean_row['ALAMAT'].casefold():
                    kota = regency
                    break

        clean_row['KOTA'] = kota
        # END

        # Start Processing "BOX"
        pattern = \
            "(?i)" \
            "((?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule\b)" \
            "[ ]+[0-9,]*[ ]?(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule|gr|gram|kg\b))|" \
            "([0-9,]{1,6}[ ]?(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule|gr|gram|kg\b))|" \
            "((?:(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule\b)[ ]?)+[0-9,]{1,6}) "

        regex_result = re.findall(pattern, clean_row['NAMA PRODUK E-COMMERCE'])
        temp = []
        for tup in regex_result:
            temp.append([var for var in tup if var != ''])

        clean_row['BOX'] = ', '.join([item for sublist in temp for item in sublist]) if len(temp) > 0 else ""
        # END

        # Start Processing "JUAL (UNIT TERKECIL)"
        sold_count = clean_row['JUAL (UNIT TERKECIL)']
        if sold_count != "":
            sold_count = sold_count[8:len(sold_count) - 7:].replace(',', '').replace('.', '').lower()
            if "rb" in sold_count:
                sold_count = sold_count.replace('rb', '')
                sold_count = int(sold_count) * 100

            sold_count = int(sold_count)

            clean_row['JUAL (UNIT TERKECIL)'] = sold_count
        # END

        # Start Processing "HARGA UNIT TERKECIL"
        clean_row['HARGA UNIT TERKECIL'] = int((clean_row['HARGA UNIT TERKECIL'][2::]).replace(".", ""))
        # END

        # Start Processing "% DISC"
        if clean_row['% DISC'] != "":
            clean_row['% DISC'] = float(clean_row['% DISC'].replace('%', '')) / 100
        # END

        # Start Processing "KATEGORI"
        if clean_row['KATEGORI'] != '':
            category = clean_row['KATEGORI']
            if category.casefold() == "Official Store".casefold():
                cat = "OFFICIAL STORE"
            elif category.casefold() == "Power Merchant".casefold():
                cat = "STAR SELLER"
            elif category.casefold() == "".casefold():
                cat = "TOKO BIASA"
            else:
                cat = category

            clean_row['KATEGORI'] = cat
        # END

        # Start Processing "RATING (Khusus shopee dan toped dikali 20)"
        rating = clean_row['RATING (Khusus shopee dan toped dikali 20)']
        if rating != "":
            clean_row['RATING (Khusus shopee dan toped dikali 20)'] = float(rating) * 20
        # END

        # Start Processing 'JML ULASAN'
        rat_total = clean_row['JML ULASAN']
        if rat_total != "":
            rat_total = rat_total.replace('(', '').replace(')', '').replace(',', '').replace('.', '')
            if "rb" in rat_total:
                rat_total = rat_total.replace('rb', '')
                rat_total = int(rat_total) * 100

            clean_row['JML ULASAN'] = rat_total
        # END

        # Start Processing 'DILIHAT'
        seen_by = clean_row['DILIHAT']
        seen_by = seen_by[:seen_by.index("x"):].replace('(', '').replace(')', '').replace(',', '').replace('.', '')
        if "rb" in seen_by:
            seen_by = seen_by.replace('rb', '')
            seen_by = int(seen_by) * 100

        clean_row['DILIHAT'] = seen_by
        # END

        return clean_row
