#!/usr/bin/python
# -*- encoding: utf-8 -*-
############################################################################################
import os

from sqlalchemy import false
from bottle import *
from bottleext import get, post, run, request, template, redirect, static_file, url
import bottle
import hashlib  # računanje kriptografski hash za gesla


# uvozimo ustrezne podatke za povezavo
import auth_public as auth


# uvozimo psycopg2
import psycopg2
import psycopg2.extensions
import psycopg2.extras
# se znebimo problemov s šumniki
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)

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
    vrni njegov emso. Če ni prijavljen, preusmeri
    na stran za prijavo ali vrni None (advisno od auto_login).
    """
    # Dobimo username iz piškotka
    username = request.get_cookie('username', secret=secret)
    # Preverimo, ali ta uporabnik obstaja
    if username is not None:
        cur.execute("SELECT emso FROM uporabnik WHERE username=%s",
                    [username])
        r = cur.fetchone()
        if r is not None:
            # uporabnik obstaja, vrnemo njegove podatke
            return r
    # Če pridemo do sem, uporabnik ni prijavljen, naredimo redirect
    if auto_login:
        redirect('/login/')
    else:
        return None


def get_my_profile(emso):
    """Funkcija glede na vlogo vrača podatke za kartico osebe."""
    cur.execute("SELECT * FROM oseba WHERE emso = %s", emso)
    return cur.fetchone()


def is_doctor(emso):
    """Funkcija za danega uporabnika preveri, če je zdravnik"""
    cur.execute(
        "SELECT exists (SELECT 1 FROM zdravstveni_delavec WHERE emso = %s LIMIT 1);", emso)
    return cur.fetchone()


def is_vaxed(emso):
    """Funkcija za danega uporabnika preveri, če je cepljen"""
    cur.execute(
        "SELECT exists (SELECT 1 FROM oseba WHERE emso = %s AND cepivo IS NOT NULL)", emso)
    return cur.fetchone()


def add_to_hospital(emso_zdravnika, emso_pacienta):
    """Funkcija v bazo vstavlja novega pacienta za sprejem v bolnišnico."""
    # TODO naredi insert


def vax_id(emso):
    """Funkcija vrne ime cepiva, če ji podamo id cepiva"""
    cur.execute("SELECT ime_cepiva FROM cepivo WHERE oseba(emso) = %s", emso)
    return cur.fetchone()


def hospital_id(emso):
    """Funkcija vrača id bolnice v kateri dela trenutni uporabnik"""
    cur.execute("SELECT id_bolnisnice FROM zdravstveni_delavec WHERE emso = %s", emso)
    return cur.fetchone() 

    
def remove_pacient(emso):
    """Funkcija poisce pacienta v doloceni bolnicni in ga odstrani iz tabele. Pravice imajo samo zdravstveni delavci."""
    print(emso)
    hospital = hospital_id(emso)
    print(hospital)
    cur.execute("SELECT ime, priimek, emso FROM odstrani_pacienta WHERE id_bolnisnice = %s", hospital)
    return cur.fetchall()


def vax_pacient(ime, priimek, cepivo):
    """Funkcija v bazi popravi podatek o cepljenu dolocenega pacienta. Ce osebe ni v bolnici, je nemoremo cepiti. Pravice ima samo zdravnik."""


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
    emso = get_user()
    profil = get_my_profile(emso)
    return template("user.html", profil, is_doctor=is_doctor(emso), is_vaxed=is_vaxed(emso))


@route("/login/")
def login_get():
    """Serviraj formo za login."""
    return template("login.html",
                    napaka=None,
                    username=None)


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
                    napaka=None,
                    username=None,
                    emso=None)


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
                            username=username,
                            emso=emso,
                            napaka='Dane emso stevilke ni v bazi oseb. Posvetujte se z zdravnikom.')
        # Daj uporabniku cookie
        response.set_cookie('username', username, path='/', secret=secret)
        redirect("/login/")


@route("/logout/")
def logout():
    """Pobriši cookie in preusmeri na login."""
    response.delete_cookie('username', path='/')
    redirect('/login/')


@route("/add_pacient/")
def add_pacient_get():
    """Forma za dodajanje pacientov"""
    if is_doctor(get_user()):
        return template("add_pacient.html", ime=None, priimek=None, emso=None, napaka=None)
    else:
        return template("add_pacient.html", ime=None, priimek=None, emso=None, napaka="Nimate pravic za dodajanje pacienta.")


@post("/add_pacient/")
def add_pacient_post():
    """Dodajanje novega pacienta"""

    redirect('/')


@route('/pct_certificate/')
def pct_certificate():
    """Serviraj formo za PCT potrdilo"""
    emso = get_user()
    if is_vaxed(emso):
        return template("pct_certificate.html", get_my_profile(emso))
    else:
        # TODO naredi napako na vrhu htmlja
        return

@route("/remove_pacient/")
def remove_get():
    """Serviraj formo za odstranitev pacienta"""
    emso = get_user()
    if is_doctor(emso):
        return template('remove_pacient.html', pacienti=remove_pacient(emso))
    else:
        # TODO naredi napako na vrhu htmlja
        return

@post("/remove_pacient")
def remove_post():
    """Odstrani uporabnika"""
    # TODO preglej podatke iz forme odstranitev pacienta in jih preko funkcije remove_pacient odstrani
    redirect('/')


@get('/vpogledextra')
def vpogledextra():
    emso = request.query.emso
    ime = request.query.ime
    priimek = request.query.priimek

    cur.execute("""SELECT emso, ime, priimek FROM oseba
    WHERE emso = %s and ime = %s and priimek = %s""", [emso, ime, priimek])
    return template('pacient.html', osebe=cur)


@get('/vpogled')
def vpogled():
    return template('vpogled.html', napaka="", ime="", priimek="", emso="")

######################################################################
# Glavni program


# priklopimo se na bazo
baza = psycopg2.connect(database=auth.db, host=auth.host,
                        user=auth.user, password=auth.password, port=DB_PORT)
# conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # onemogočimo transakcije
cur = baza.cursor(cursor_factory=psycopg2.extras.DictCursor)

# poženemo strežnik na podanih vratih, npr. http://localhost:8080/
if __name__ == "__main__":
    bottle.run(host='localhost', port=SERVER_PORT, reloader=RELOADER)
