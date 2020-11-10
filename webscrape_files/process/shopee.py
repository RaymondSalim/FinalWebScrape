import re
from typing import List, Dict
from .. import city_list as cl


class Shopee:
    def __init__(self, input_data):
        self.dirty_data = input_data
        self.clean_data = []

    def process(self) -> List[Dict]:
        for data in self.dirty_data:
            clean = self.process_row(data)
            self.clean_data.append(clean)

        return self.clean_data

    def process_row(self, data):
        clean_row = {
            'KEYWORD': data['KEYWORD'],
            'PRODUK': '',  # Empty
            'FARMASI': '',  # Empty
            'E-COMMERCE': 'SHOPEE',
            'TOKO': data['TOKO'],
            'ALAMAT': data['ALAMAT'],
            'KOTA': None,  # Processed below
            'BOX': None,  # Processed below
            'RANGE': data['RANGE'],
            'JUAL (UNIT TERKECIL)': data['JUAL (UNIT TERKECIL)'],  # Processed below
            'HARGA UNIT TERKECIL': data['HARGA UNIT TERKECIL'],
            'VALUE': '',  # Empty
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
        sol = clean_row['JUAL (UNIT TERKECIL)']
        if 'RB' in sol:
            sol = sol.replace('RB', '').replace(',', '').replace('+', '')
            sol = int(sol) * 100
        clean_row['JUAL (UNIT TERKECIL)'] = int(sol) if int(sol) != 0 else ""
        # END

        # Start Processing "% DISC"
        disc = clean_row['% DISC']
        if '%' in disc:
            disc_float = disc[:disc.index('%'):]
            disc = float(disc_float) / 100

        clean_row['% DISC'] = disc
        # END

        # Start Processing "JML ULASAN"
        rat = clean_row['JML ULASAN']
        if 'RB' in rat:
            rat = rat.replace('RB', '').replace(',', '').replace('+', '')
            rat = int(rat) * 1000
        clean_row['JML ULASAN'] = rat
        # END


        return clean_row