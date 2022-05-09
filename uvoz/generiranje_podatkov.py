################################################
from datetime import datetime
import pandas as pd
import numpy as np
from scipy import rand

################################################
# Osnovni konfiguracija podatkov

prebivalstvo_slovenije = 2 ** 6
precepljenost_prebivalstva = 0.582
delez_zensk = 0.511

seed = 1
rng = np.random.default_rng(seed)

################################################
# Dataframe-i iz katerih bom generiral podatke

header_names = ["ime", "stevilo"]
header_surnames = ["priimek", "stevilo"]

moska_imena = pd.read_csv("uvoz/moska_imena.csv", names=header_names, encoding='cp1250', header=0)
zenska_imena = pd.read_csv("uvoz/zenska_imena.csv", names=header_names, encoding='cp1250', header=0)
priimki_af = pd.read_csv("uvoz/priimki_af.csv", names=header_surnames, encoding='cp1250', header=0)
priimki_gl = pd.read_csv("uvoz/priimki_gl.csv", names=header_surnames, encoding='cp1250', header=0)
priimki_mr = pd.read_csv("uvoz/priimki_mr.csv", names=header_surnames, encoding='cp1250', header=0)
priimki_sž = pd.read_csv("uvoz/priimki_sž.csv", names=header_surnames, encoding='cp1250', header=0)


# Zdruzevanje zadnjih treh
priimki = pd.concat([priimki_af, priimki_gl, priimki_sž])

# Odstranjevanje takih, ki jih ni
priimki = priimki[priimki["stevilo"] != "-"]
moska_imena = moska_imena[moska_imena["stevilo"] != "-"]
zenska_imena = zenska_imena[zenska_imena["stevilo"] != "-"]

# Spreminjanje tipa stolpca 'stevilo'
moska_imena["stevilo"] = pd.to_numeric(moska_imena["stevilo"])
zenska_imena["stevilo"] = pd.to_numeric(zenska_imena["stevilo"])
priimki["stevilo"] = pd.to_numeric(priimki["stevilo"])

# Izracunavanje deleza kot cenilka za slovensko populacijo
moska_imena["delez"] = (moska_imena['stevilo'] / moska_imena['stevilo'].sum())
zenska_imena["delez"] = (zenska_imena['stevilo'] / zenska_imena['stevilo'].sum())
priimki["delez"] = (priimki['stevilo'] / priimki['stevilo'].sum())


###################################################################################
# Pomozne funkcije

def random_date_generator(start_date=datetime(1900,1,1)):
    """Funkcija vraca nakljucni datum, glede ustrezne vhodne parametre"""
    days_to_add = (datetime.now() - start_date).days
    random_date = np.datetime64(start_date) + np.random.choice(days_to_add).days
    date = pd.to_datetime(str(random_date))
    str_date = date.strftime('%d%m%Y')
    return str_date

def generiraj_emso(zenska):
    """Funkcija generira emso stevilko"""
    stevec_m = 0
    stevec_z = 0
    if zenska:
        return
        

print(random_date_generator())






