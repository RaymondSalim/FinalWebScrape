import re
from typing import List, Dict
from .. import city_list as cl


class Bukalapak:

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
            'E-COMMERCE': 'BUKALAPAK',
            'TOKO': data['TOKO'],
            'ALAMAT': data['ALAMAT'],
            'KOTA': data['KOTA'],  # Processed below
            'BOX': data['KOTA'],  # Processed below
            'RANGE': data['RANGE'],  # Empty for bukalapak
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
            'DILIHAT': data['DILIHAT'],  # Empty for bukalapak
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
        nama_produk = clean_row['NAMA PRODUK E-COMMERCE']
        box_patt = "(?i)((?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule\b)[ ]+[0-9,]*[ ]?(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule|gr|gram|kg\b))|([0-9,]{1,6}[ ]?(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule|gr|gram|kg\b))|((?:(?:\bbox|isi|dus|eceran|strip|bundle|paket|pack|tablet|kapsul|capsule\b)[ ]?)+[0-9,]{1,6})"
        rbox = re.findall(box_patt, nama_produk)

        reg = []
        for tuple in rbox:
            reg.append([var for var in tuple if var != ''])

        clean_row['BOX'] = ', '.join([item for sublist in reg for item in sublist]) if len(reg) > 0 else ""
        # END

        # Start Processing "JUAL (UNIT TERKECIL)"
        mpr = clean_row['JUAL (UNIT TERKECIL)']
        mpr_arr = mpr.split()

        ratingc = None
        soldc = None

        if len(mpr_arr) == 4:
            ratingc = int(mpr_arr[0].replace('.', ''))
            soldc = int(mpr_arr[2].replace('.', ''))

        elif len(mpr_arr) == 2:
            soldc = int(mpr_arr[0].replace('.', ''))

        clean_row['JUAL (UNIT TERKECIL)'] = int(soldc) if len(mpr) > 0 else ""
        # END

        # Start Processing "HARGA UNIT TERKECIL"
        price = clean_row['HARGA UNIT TERKECIL']
        price = price.split('\n')
        clean_row['HARGA UNIT TERKECIL'] = float((price[0][2::]).replace(".", ""))
        # END

        # Start Processing "% DISC"
        discount = clean_row['% DISC']
        if discount != "":
            discount = discount.split()
            clean_row['% DISC'] = float(discount[-1].replace('%', '')) / 100
        # END

        # Start Processing "KATEGORI"
        shop_category = clean_row['KATEGORI']
        shop_category = shop_category.replace('\n', '').replace(' ', '')
        q = ['super', 'recommended', 'good', 'juragan']
        if any(a in shop_category.casefold() for a in q):
            shop_category = "STAR SELLER"
        elif "Resmi".casefold() == shop_category.casefold() or "bukamall".casefold() == shop_category.casefold():
            shop_category = "OFFICIAL STORE"
        elif "Pedagang".casefold() == shop_category.casefold():
            shop_category = "TOKO BIASA"
        clean_row['KATEGORI'] = shop_category
        # END

        # Start Processing "JML ULASAN"
        clean_row['JML ULASAN'] = int(ratingc) if len(mpr_arr) == 4 else ""
        # END

        return clean_row