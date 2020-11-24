import re
from typing import List, Dict
from .. import city_list as cl


class Shopee:
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

        print(f"{duplicates} Duplicates skipped")
        return self.clean_data

    def process_row(self, data):
        clean_row = {
            'KEYWORD': data['KEYWORD'],
            'PRODUK': data['PRODUK'],  # Empty
            'FARMASI': data['FARMASI'],  # Empty
            'E-COMMERCE': 'SHOPEE',
            'TOKO': data['TOKO'],
            'ALAMAT': data['ALAMAT'],
            'KOTA': data['KOTA'],  # Processed below
            'BOX': data['KOTA'],  # Processed below
            'RANGE': data['RANGE'],
            'JUAL (UNIT TERKECIL)': data['JUAL (UNIT TERKECIL)'],  # Processed below
            'HARGA UNIT TERKECIL': data['HARGA UNIT TERKECIL'],  # Processed below
            'VALUE': data['VALUE'],  # Empty
            '% DISC': data['% DISC'],  # Processed below
            'KATEGORI': data['KATEGORI'],
            'SOURCE': data['SOURCE'],
            'NAMA PRODUK E-COMMERCE': data['NAMA PRODUK E-COMMERCE'],
            'RATING (Khusus shopee dan toped dikali 20)': data['RATING (Khusus shopee dan toped dikali 20)'],
            # Processed below
            'JML ULASAN': data['JML ULASAN'],  # Processed below
            'DILIHAT': data['DILIHAT'],
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
        sol = str(clean_row['JUAL (UNIT TERKECIL)'])
        if 'RB' in sol:
            sol = sol.replace('RB', '').replace(',', '').replace('+', '')
            sol = int(sol) * 100
        clean_row['JUAL (UNIT TERKECIL)'] = int(sol) if int(sol) != 0 else ""
        # END

        # Start Processing "HARGA UNIT TERKECIL"
        prices = clean_row['HARGA UNIT TERKECIL'].split()
        prices = [val.replace('.', '').replace('Rp', '') for val in prices]
        try:
            prices.remove('-')
        except ValueError:
            pass

        if len(prices) == 1:
            clean_row['HARGA UNIT TERKECIL'] = int(prices[0])
        else:
            clean_row['HARGA UNIT TERKECIL'] = f"{prices[0]} - {prices[1]}"

        # END

        # Start Processing "% DISC"
        disc = clean_row['% DISC']
        if '%' in disc:
            disc_float = disc[:disc.index('%'):]
            disc = float(disc_float) / 100

        clean_row['% DISC'] = disc
        # END

        # Start Processing "RATING (Khusus shopee dan toped dikali 20)"
        rating = clean_row['RATING (Khusus shopee dan toped dikali 20)']
        if rating != '':
            rating = float(rating) * 20
        clean_row['RATING (Khusus shopee dan toped dikali 20)'] = rating
        # END

        # Start Processing "JML ULASAN"
        rat = str(clean_row['JML ULASAN'])
        if 'RB' in rat:
            rat = rat.replace('RB', '').replace(',', '').replace('+', '')
            rat = int(rat) * 1000
        clean_row['JML ULASAN'] = rat
        # END


        return clean_row