#!/usr/bin/python
# -*- encoding: utf-8 -*-
############################################################################################
from bottle import *
import sqlite3
import bottle
import hashlib # računanje kriptografski hash za gesla
from datetime import datetime


# uvozimo ustrezne podatke za povezavo
import auth_public as auth


# uvozimo psycopg2
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s šumniki

import os
############################################################################################
# Konfiguracija

# Vklopimo debug
bottle.debug(True)

# Datoteka, kjer je spravljena baza
baza_datoteka = "covid.sqlite"

# Mapa s statičnimi datotekami
static_dir = "./static"

# Skrivnost za kodiranje cookijev
secret = "6752c0f942dcb7d45bc947a79636f9ccbc59efc319c4024daf1163b00ea757ce"

# Strezniske nastavitve
SERVER_PORT = os.environ.get('BOTTLE_PORT', 8080)
RELOADER = os.environ.get('BOTTLE_RELOADER', True)
DB_PORT = os.environ.get('POSTGRES_PORT', 5432)


###############################################################
# Pomozne funkcije

def password_hash(s):
    """Vrni SHA-512 hash danega UTF-8 niza. Gesla vedno spravimo v bazo
       kodirana s to funkcijo."""
    h = hashlib.sha512()
    h.update(s.encode('utf-8'))
    return h.hexdigest()

def get_user(auto_login=True):
    """Poglej cookie in ugotovi, kdo je prijavljeni uporabnik,
    vrni njegov username in ime. Če ni prijavljen, presumeri
    na stran za prijavo ali vrni None (advisno od auto_login).
    """
    # Dobimo username iz piškotka
    username = bottle.request.get_cookie('username', secret=secret)
    # Preverimo, ali ta uporabnik obstaja
    if username is not None:
        c = baza.cursor()
        c.execute("SELECT username, ime, vloga, bolnisnica FROM uporabnik WHERE username=?",
                  [username])
        r = c.fetchone()
        c.close ()
        if r is not None:
            # uporabnik obstaja, vrnemo njegove podatke
            return r
    # Če pridemo do sem, uporabnik ni prijavljen, naredimo redirect
    if auto_login:
        bottle.redirect('/login/')
    else:
        return None

def get_pacients():
    """Funkcija pogleda če ima uporabnik pravice, če jih ima potem vrne vse paciente v bolnici kjer smo prijavljeni."""
    (username, ime, vloga, bolnisnica) = get_user()
    # Preverimo vlogo uporabnika
    if vloga == "zdravstveni_delavec":
        c = baza.cursor()
        # TODO izberem vse paciente v bolnici kjer je tisti zdravnik
        c.execute()
    else:
        return None


def get_my_profile():
    """Funkcija glede na vlogo vrača podatke za kartico osebe."""
    if get_user() == None:
        return None
    else:    
        (username, ime, vloga, bolnisnica) = get_user()
        c = baza.cursor()
        if vloga == "zdravstveni delavec":
            # TODO poglej bazo in vrni podatke zdravstvenega delavca
            c.close()
        elif vloga == "pacient":
            # TODO poglej bazo in vrni podatke pacienta
            c.close()
            return None
        elif vloga == "uprava":
            # TODO poglej bazo in vrni podatke za vse bolnike in delavce tiste bolnice
            c.close
            return None


def transfer_medic(name):
    """Funkcija zamenja lokacijo zdravstvenega delavca. Pravice ima samo uprava """
    return None


def add_pacient(ime, priimek, cepivo=None):
    """Funkcija v bazo vstavlja novega pacienta za sprejem v bolnišnico."""
    return None


def remove_pacient(ime, priimek):
    """Funkcija poisce pacienta v doloceni bolnicni in ga odstrani iz baze. Pravice imajo samo zdravstveni delavci."""
    return None


def vax_pacient(ime, priimek, cepivo):
    """Funkcija v bazi popravi podatek o cepljenu dolocenega pacienta. Ce osebe ni v bolnici, je nemoremo cepiti. Pravice ima samo zdravnik."""
    return None

###############################################################
@get('/static/<filename:path>')
def static(filename):
    return static_file(filename, root='static' )    

### Izkaznica pacienta
@get('/pacient')
def pacient():
    cur.execute("SELECT emso, ime, priimek FROM oseba")
    return template('pacient.html', osebe = cur)

### TODO izkaznica bolnice
### TODO izkaznica zdravstvenega delavca
### TODO možnost da zdravnik sprejema in odpušča bolnike, možnost bolnice da prestavi zdravnika v drugo bolnico
### TODO možnost cepljenega bolnika, da si lahko ogleda svojo COVID izkaznico




@get('/vpogled')
def vpogled():
    return template('normal_person.html', napaka = "" , ime="" , priimek="", emso="" )

######################################################################
# Glavni program

# priklopimo se na bazo
baza = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password, port=DB_PORT)
#conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # onemogočimo transakcije
cur = baza.cursor(cursor_factory=psycopg2.extras.DictCursor)

# poženemo strežnik na podanih vratih, npr. http://localhost:8080/
if __name__ == "__main__":
    bottle.run(host='localhost', port=SERVER_PORT, reloader=RELOADER)
