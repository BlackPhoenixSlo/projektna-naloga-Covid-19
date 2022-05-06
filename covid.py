#!/usr/bin/python
# -*- encoding: utf-8 -*-
############################################################################################
from bottle import *
from bottleext import get, post, run, request, template, redirect, static_file, url
import bottle
import hashlib # računanje kriptografski hash za gesla


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
        cur.execute("SELECT username, emso FROM uporabnik WHERE username=%s",
                  [username])
        r = cur.fetchone()
        if r is not None:
            # uporabnik obstaja, vrnemo njegove podatke
            return r
    # Če pridemo do sem, uporabnik ni prijavljen, naredimo redirect
    if auto_login:
        bottle.redirect('/login/')
    else:
        return None


def get_my_profile():
    """Funkcija glede na vlogo vrača podatke za kartico osebe."""



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
# Funkcije, ki obdelajo zahteve odjemalcev

@route("/static/<filename:path>")
def static(filename):
    """Splošna funkcija, ki servira vse statične datoteke iz naslova
       /static/..."""
    return static_file(filename, root=static_dir)

@route("/")
def main():
    """Glavna stran."""
    (username, ime) = get_user()
    # Morebitno sporočilo za uporabnika

@route("/login/")
def login_get():
    """Serviraj formo za login."""
    return template("login.html",
                    napaka = None,
                    username = None)

@post("/login/")
def login_post():
    """Obdelaj izpolnjeno formo za prijavo"""
    # Uporabniško ime, ki ga je uporabnik vpisal v formo
    username = request.forms.username
    # Izračunamo hash gesla, ki ga bomo spravili
    password = password_hash(request.forms.password)
    # Preverimo, ali se je uporabnik pravilno prijavil
    cur.execute("SELECT 1 FROM uporabnik WHERE username=%s AND password=%s",
              [username, password])
    if cur.fetchone() is None:
        # Username in geslo se ne ujemata
        return template("login.html",
                        napaka="Nepravilna prijava",
                        username=username)
    else:
        # Vse je v redu, nastavimo cookie in preusmerimo na glavno stran
        response.set_cookie('username', username, path='/', secret=secret)
        redirect("/")


@route("/register/")
def register_get():
    """Serviraj formo za registracijo"""
    return template("register.html",
                    napaka = None,
                    username = None,
                    emso = None)

@post("/register/")
def register_post():
    """Registriraj novega uporabnika."""
    username = request.forms.username
    emso = request.forms.emso
    password1 = request.forms.password1
    password2 = request.forms.password2
    # Ali uporabnik že obstaja?
    cur.execute("SELECT 1 FROM uporabnik WHERE username=%s", [username])
    if cur.fetchone():
        # Uporabnik že obstaja
        return template("register.html",
                               username=username,
                               emso=emso,
                               napaka='To uporabniško ime je že zavzeto')
    elif not password1 == password2:
        # Gesli se ne ujemata
        return template("register.html",
                               username=username,
                               emso=emso,
                               napaka='Gesli se ne ujemata')
    else:
        # Vse je v redu, vstavi novega uporabnika v bazo
        password = password_hash(password1)
        try:
            cur.execute("INSERT INTO uporabnik (username, emso, password) VALUES (%s, %s, %s)",
                    (username, emso, password))
            baza.commit()
        except psycopg2.errors.ForeignKeyViolation:
            print("Uporabnika ni v bazi registriranih oseb")
            return template("register.html",
                            username = username,
                            emso = emso,
                            napaka = 'Dane emso stevilke ni v bazi oseb. Posvetujte se z zdravnikom.')
        # Daj uporabniku cookie
        response.set_cookie('username', username, path='/', secret=secret)
        redirect("/login/")


@route("/user/<username>")
def user_wall(username):
    """"Osebna izkaznica osebe."""

    






    














######################################################################
# Glavni program

# priklopimo se na bazo
baza = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password, port=DB_PORT)
#conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # onemogočimo transakcije
cur = baza.cursor(cursor_factory=psycopg2.extras.DictCursor)

# poženemo strežnik na podanih vratih, npr. http://localhost:8080/
if __name__ == "__main__":
    bottle.run(host='localhost', port=SERVER_PORT, reloader=RELOADER)
