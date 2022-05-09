################################################
from datetime import datetime
import pandas as pd
import numpy as np
from scipy import rand
from sqlalchemy import true

################################################
# Osnovni konfiguracija podatkov

prebivalstvo_slovenije = 2 ** 6
precepljenost_prebivalstva = 0.582
delez_zensk = 0.511
julijana_zakrajsek = '28-10-1912'

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

def random_date_generator(start_date = julijana_zakrajsek):
    """Funkcija vraca nakljucni datum, glede ustrezne vhodne parametre"""
    num_of_days = (datetime.now() - datetime.strptime(start_date, '%d-%m-%Y')).days
    days = np.random.choice(num_of_days)
    random_date = pd.to_datetime(start_date) + pd.DateOffset(days=days)
    str_date = random_date.strftime('%d%m%Y')
    return str_date[:4] + str_date[5:]

def generiraj_emso(zenska):
    """Funkcija generira emso stevilko"""
    if zenska:
        # Malce pretirana poenostavitev zadnjih treh cifer, lahko se zgodi da pridejo iste + zanemarjam take, ki imajo dve nicli npr. 015,...
        return (random_date_generator() + '505' + str(np.random.randint(100, 999)))
    else:
        return (random_date_generator() + '500' + str(np.random.randint(100, 999)))


def generiraj_osebo(zenska):
    """Funkcija izbere nakljucno ime in nakljucni priimek, nakljucni emso in zgenerira osebo."""
    if zenska:
        ime = zenska_imena["ime"].sample(n=1, weights=zenska_imena["delez"]).values[0]
        priimek = priimki["priimek"].sample(n=1, weights=zenska_imena["delez"]).values[0]
        emso = generiraj_emso(True)
    else :
        ime = moska_imena["ime"].sample(n=1, weights=moska_imena["delez"]).values[0]
        priimek = priimki["priimek"].sample(n=1, weights=zenska_imena["delez"]).values[0]
        emso = generiraj_emso(False)
    stalno_prebivalisce = "Ljubljanska ulica 15"
    datum_testiranja = "15-05-2020"
    rezultat_test = True
    cepivo = 1
    return {"ime": ime, 
            "priimek": priimek,
            "emso": emso,
            "stalno_prebivalisce": stalno_prebivalisce,
            "datum_testiranja": datum_testiranja,
            "rezultat_test": rezultat_test,
            "cepivo": cepivo}



# TODO popravi še za cepiva, za stalni naslov se verjetno ne splača. Bolj koristno bi bilo nabrati par naslovov in jih random razporediti
# TODO for zanka za 5k uporabnikov in push v bazo
# TODO naredi zdravnika, upravo, in bolnika
# TODO 



