################################################
import requests
from io import StringIO
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from requests import request
import auth
import psycopg2
import psycopg2.extensions
import psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)

################################################
# Osnovni konfiguracija podatkov

prebivalstvo_slovenije = 10**3
stevilo_cepiv = 5
delez_zensk = 0.511
julijana_zakrajsek = '28-10-1912'
verjetnost_testa = 0.15
# Verjetnost hospitalizacije ob pogoju, da je oseba pozitivna
verjetnost_hospitalizacije = 0.3
delez_zdravstvenih_delavcev = 31 / (2 * (10 ** 3))
cepiva = "https://api.sledilnik.org/api/vaccinations"


seed = 1
rng = np.random.default_rng(seed)

conn = psycopg2.connect(database=auth.db, host=auth.host,
                        user=auth.user, password=auth.password)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

################################################
# Dataframe-i iz katerih bom generiral podatke

header_names = ["ime", "stevilo"]
header_surnames = ["priimek", "stevilo"]

# Podatke iz sursa za imena in priimke
moska_imena = pd.read_csv("uvoz/moska_imena.csv",
                          names=header_names, encoding='cp1250', header=0)
zenska_imena = pd.read_csv("uvoz/zenska_imena.csv",
                           names=header_names, encoding='cp1250', header=0)
priimki_af = pd.read_csv("uvoz/priimki_af.csv",
                         names=header_surnames, encoding='cp1250', header=0)
priimki_gl = pd.read_csv("uvoz/priimki_gl.csv",
                         names=header_surnames, encoding='cp1250', header=0)
priimki_mr = pd.read_csv("uvoz/priimki_mr.csv",
                         names=header_surnames, encoding='cp1250', header=0)
priimki_sž = pd.read_csv("uvoz/priimki_sž.csv",
                         names=header_surnames, encoding='cp1250', header=0)


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
zenska_imena["delez"] = (zenska_imena['stevilo'] /
                         zenska_imena['stevilo'].sum())
priimki["delez"] = (priimki['stevilo'] / priimki['stevilo'].sum())

# Podatki iz sledilnika
response = requests.get(cepiva)
cepljenje = pd.DataFrame(response.json())
prva_doza = cepljenje["administered"]
druga_doza = cepljenje["administered2nd"]
tretja_doza = cepljenje["administered3rd"]

# Pogledamo najnovejše podatke (podatki so kumulativni)
prva_doza = prva_doza[len(prva_doza) - 2]
druga_doza = druga_doza[len(druga_doza) - 2]
tretja_doza = tretja_doza[len(tretja_doza) - 2]

# Izracunam kaksen delez populacije je cepljen kolikokrat
delez_tretje = (tretja_doza["toDate"] / (2107180))
delez_druge = ((druga_doza["toDate"] - tretja_doza["toDate"]) / (2107180))
delez_prve = ((prva_doza["toDate"] - druga_doza["toDate"]) / (2107180))

precepljenost_prebivalstva = delez_prve + delez_druge + delez_tretje
###################################################################################
# Pomozne funkcije


def random_date_generator(start_date):
    """Funkcija vraca nakljucni datum, glede na zaceteke. Zadnji datum je danasnji."""
    num_of_days = (datetime.now() -
                   datetime.strptime(start_date, '%d-%m-%Y')).days
    days = rng.choice(num_of_days, replace=False)
    random_date = pd.to_datetime(start_date) + pd.DateOffset(days=days)
    # String je v takšni obliki zaradi generiranja emso stevilke
    str_date = random_date.strftime('%d%m%Y')

    return str_date


def pristej_datum(start_date, stevilo_dni):
    """Funkcija vzame začetni datum v obliki stringa in vrne datum v obliki stringa, ki je zamaknjen za stevilo dni"""
    start_date = datetime.strptime(start_date, '%d-%m-%Y')
    new_date = start_date + timedelta(days=stevilo_dni)
    return new_date.strftime('%d-%m-%Y')


def generiraj_emso(zenska):
    """Funkcija generira emso stevilko"""
    rojstvo = random_date_generator(julijana_zakrajsek)
    # Odstranim prvo števko leta
    emso_stevke = rojstvo[:4] + rojstvo[5:]
    if zenska:
        # Malce pretirana poenostavitev zadnjih treh cifer, lahko se zgodi da pridejo iste + zanemarjam take, ki imajo niclo na zacetku,...
        return (emso_stevke + '505' + str(np.random.randint(100, 999)))
    else:
        return (emso_stevke + '500' + str(np.random.randint(100, 999)))


def izberi_cepivo():
    # Stevilo 0 uporabljam kot da oseba ni cepljena
    vrednosti = np.arange(0, stevilo_cepiv)
    verjetnosti_cepiva = [prebivalstvo_slovenije * precepljenost_prebivalstva /
                          stevilo_cepiv for _ in range(stevilo_cepiv)]
    verjetnosti = [(1 - precepljenost_prebivalstva)] + verjetnosti_cepiva
    cepivo = rng.choice(vrednosti, 1, verjetnosti)[0]
    return cepivo


def potek_cepljenja(id):
    cepivo = izberi_cepivo()
    stevilo_odmerkov = rng.choice(
        [1, 2, 3], 1, [delez_prve, delez_druge, delez_tretje])
    datum_cepljenja = datetime.strptime(random_date_generator("27-12-2020"), '%d%m%Y').strftime("%d-%m-%Y")
    evidenca_osebe = []
    if cepivo > 0:
        evidenca_osebe.append(
            {"id_osebe": id, "id_cepiva": cepivo, "datum_cepljenja": datum_cepljenja})
        while (stevilo_odmerkov > 1):
            datum_cepljenja = pristej_datum(datum_cepljenja, 180)
            evidenca_osebe.append(
                {"id_osebe": id, "id_cepiva": cepivo, "datum_cepljenja": datum_cepljenja})
            stevilo_odmerkov -= 1
    return evidenca_osebe


def testiraj_osebo(verjetnost_testa=verjetnost_testa):
    rezultat_testa = np.random.binomial(1, verjetnost_testa) > 0
    return rezultat_testa


def generiraj_osebo(zenska):
    """Funkcija izbere nakljucno ime in nakljucni priimek, nakljucni emso in zgenerira osebo."""
    if zenska:
        ime = zenska_imena["ime"].sample(
            n=1, weights=zenska_imena["delez"]).values[0]
        priimek = priimki["priimek"].sample(
            n=1, weights=zenska_imena["delez"]).values[0]
        emso = generiraj_emso(zenska)
    else:
        ime = moska_imena["ime"].sample(
            n=1, weights=moska_imena["delez"]).values[0]
        priimek = priimki["priimek"].sample(
            n=1, weights=zenska_imena["delez"]).values[0]
        emso = generiraj_emso(zenska)

    return {"emso": emso,
            "ime": ime,
            "priimek": priimek,
            "stalno_prebivalisce": "Ljubljanska cesta 15"
            }


def generiraj_prebivalstvo(prebivalci=prebivalstvo_slovenije):
    """Funkcija generira ljudi, glede na procent spolov in jim priredi ustrezne podatke"""
    spoli = np.random.binomial(1, delez_zensk, size=prebivalci) > 0
    prebivalci = []
    for spol in spoli:
        prebivalci.append(generiraj_osebo(spol))
    return pd.DataFrame(prebivalci)


def copy_from_stringio(conn, df, table):
    """
    Here we are going save the dataframe in memory 
    and use copy_from() to copy it to the table
    """
    # save dataframe to an in memory buffer
    buffer = StringIO()
    df.to_csv(buffer, header=False)
    buffer.seek(0)
    cursor = conn.cursor()
    try:
        cursor.copy_from(buffer, table, sep=",", null="")
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        conn.rollback()
        cursor.close()
        return 1
    print("Prenos na bazo uspešen")
    cursor.close()


###################################################################################
# 1. tabela - cepiva
cepivo = pd.Series(["Pfizer-BioNTech", "Moderna",
                    "Johnson & Johnson", "Novavax", "Oxford-AstraZeneca"])


# 2. tabela - osebe
oseba = generiraj_prebivalstvo()


# 3. tabela - bolnisnice
bolnisnica = pd.Series(["Splošna bolnišnica Celje", "Bolnišnica Postojna", "Splošna bolnišnica Izola",
                        "Klinični center Ljubljana", "Splošna bolnišnica Maribor", "Splošna bolnišnica Slovenj Gradec"])


# 4. tabela - uporabniki
# Se polni sproti ob registraciji uporabnika

# 5. tabela in 6. tabela - pacienti in zdravstveni delavci
# Zaradi preprostosti dolocim da je procent hospitaliziranih 20% - veliko več kot dejansko
id_oseb = pd.Series(oseba.sample(frac=0.4).index.values)
id_bolnisnice = pd.Series(rng.integers(len(bolnisnica), size=len(id_oseb)))
bolnisnicni = pd.concat([id_oseb, id_bolnisnice], axis=1)
bolnisnicni = bolnisnicni.rename(columns={0: "id_osebe", 1: "id_bolnisnice"})

pacient = bolnisnicni.sample(frac=0.8)


# Tisti, ki so v bolnici in niso pacienti, so zdravstveni delavci
zdravstveni_delavec = bolnisnicni[bolnisnicni["id_osebe"].isin(pacient["id_osebe"]) == False]

pacient.set_index("id_osebe", drop=True, inplace=True)
zdravstveni_delavec.set_index("id_osebe", drop=True, inplace=True)



# 8. tabela - cepljenje
seznam_oseb = []
for id_osebe in oseba.index.values:
    seznam_oseb = seznam_oseb + potek_cepljenja(id_osebe)
cepljenje = pd.DataFrame(seznam_oseb)
cepljenje.set_index("id_osebe", drop=True, inplace=True)
    
# 9. tabela - testiranje
seznam_testiranj = []
testirana_populacija = oseba.sample(frac=0.4).index.values
for id_osebe in testirana_populacija:
    seznam_testiranj.append({"id_osebe": id_osebe, "datum_testa": datetime.strptime(random_date_generator("27-12-2020"), '%d%m%Y').strftime("%d-%m-%Y"), "rezultat_testa": testiraj_osebo()})
testiranje = pd.DataFrame(seznam_testiranj)
testiranje.set_index("id_osebe", drop=True, inplace=True)




def main():
    copy_from_stringio(conn=conn, df=cepivo, table="cepivo")
    copy_from_stringio(conn=conn, df=oseba, table="oseba")
    copy_from_stringio(conn=conn, df=bolnisnica, table="bolnisnica")
    copy_from_stringio(conn=conn, df=pacient, table="pacient")
    copy_from_stringio(conn=conn, df=zdravstveni_delavec, table="zdravstveni_delavec")
    copy_from_stringio(conn=conn, df=cepljenje, table="cepljenje")
    copy_from_stringio(conn=conn, df=testiranje, table="testiranje")
    


if __name__ == '__main__':
    main()
