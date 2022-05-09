################################################
from datetime import datetime
import pandas as pd
import numpy as np


################################################
# Osnovni konfiguracija podatkov

prebivalstvo_slovenije = 10** 3
precepljenost_prebivalstva = 0.582
stevilo_cepiv = 5
delez_zensk = 0.511
julijana_zakrajsek = '28-10-1912'
verjetnost_testa = 0.15

seed = 1
rng = np.random.default_rng(seed)


################################################
# Dataframe-i iz katerih bom generiral podatke

header_names = ["ime", "stevilo"]
header_surnames = ["priimek", "stevilo"]

# Podatke iz sursa
moska_imena = pd.read_csv("uvoz/moska_imena.csv", names=header_names, encoding='cp1250', header=0)
zenska_imena = pd.read_csv("uvoz/zenska_imena.csv", names=header_names, encoding='cp1250', header=0)
priimki_af = pd.read_csv("uvoz/priimki_af.csv", names=header_surnames, encoding='cp1250', header=0)
priimki_gl = pd.read_csv("uvoz/priimki_gl.csv", names=header_surnames, encoding='cp1250', header=0)
priimki_mr = pd.read_csv("uvoz/priimki_mr.csv", names=header_surnames, encoding='cp1250', header=0)
priimki_sž = pd.read_csv("uvoz/priimki_sž.csv", names=header_surnames, encoding='cp1250', header=0)


# Zdruzevanje priimkov
priimki = pd.concat([priimki_af, priimki_gl, priimki_sž])

# Odstranjevanje takih imen in priimkov, ki jih v letosnjem letu ni vec
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

def random_date_generator(start_date):
    """Funkcija vraca nakljucni datum, glede na zaceteke. Zadnji datum je danasnji."""
    num_of_days = (datetime.now() - datetime.strptime(start_date, '%d-%m-%Y')).days
    days = rng.choice(num_of_days, replace=False)
    random_date = pd.to_datetime(start_date) + pd.DateOffset(days=days)
    str_date = random_date.strftime('%d%m%Y')
    # Prvo števko leta odstranim
    return str_date


def generiraj_emso(zenska):
    """Funkcija generira emso stevilko"""
    rojstvo = random_date_generator(julijana_zakrajsek)
    emso_stevke = rojstvo[:4] + rojstvo[5:]
    if zenska:
        # Malce pretirana poenostavitev zadnjih treh cifer, lahko se zgodi da pridejo iste + zanemarjam take, ki imajo dve nicli npr. 015,...
        return (emso_stevke + '505' + str(np.random.randint(100, 999)))
    else:
        return (emso_stevke + '500' + str(np.random.randint(100, 999)))


def cepi_osebo():
    # Stevilo 0 uporabljam kot da oseba ni cepljena
    vrednosti = np.arange(0, stevilo_cepiv)
    verjetnosti_cepiva = [prebivalstvo_slovenije / stevilo_cepiv for i in range(stevilo_cepiv)]
    verjetnosti = [(1 - precepljenost_prebivalstva)] + verjetnosti_cepiva
    cepivo = rng.choice(vrednosti, 1, verjetnosti)[0]
    return cepivo


def testiraj_osebo(verjetnost_testa=verjetnost_testa):
    rezultat_testa = np.random.binomial(1, verjetnost_testa)
    return rezultat_testa
    

def generiraj_osebo(zenska):
    """Funkcija izbere nakljucno ime in nakljucni priimek, nakljucni emso in zgenerira osebo."""
    if zenska:
        ime = zenska_imena["ime"].sample(n=1, weights=zenska_imena["delez"]).values[0]
        priimek = priimki["priimek"].sample(n=1, weights=zenska_imena["delez"]).values[0]
        emso = generiraj_emso(zenska)
    else :
        ime = moska_imena["ime"].sample(n=1, weights=moska_imena["delez"]).values[0]
        priimek = priimki["priimek"].sample(n=1, weights=zenska_imena["delez"]).values[0]
        emso = generiraj_emso(zenska)
    return {"ime": ime, 
            "priimek": priimek,
            "emso": emso,
            "stalno_prebivalisce": "Ljubljanska cesta 15",
            "datum_testiranja": random_date_generator("04-03-2020"),
            "rezultat_test": testiraj_osebo(),
            "cepivo": cepi_osebo()}


def generiraj_prebivalstvo(prebivalci=prebivalstvo_slovenije):
    """Funkcija generira ljudi, glede na procent spolov in jim priredi ustrezne podatke"""
    spoli = np.random.binomial(1, delez_zensk, size=prebivalci) > 0
    prebivalci = []
    for spol in spoli:
        prebivalci.append(generiraj_osebo(spol))
    return pd.DataFrame(prebivalci)





###################################################################################
# Generiranje datotek in prenos na server



def main():
    print(generiraj_prebivalstvo())
    


if __name__ == "__main__":
    main()

