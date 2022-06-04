#!/usr/bin/python
# -*- encoding: utf-8 -*-
############################################################################################
import os

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
        cur.execute("SELECT id_osebe FROM uporabnik WHERE username=%s",
                    [username])
        r = cur.fetchone()[0]
        if r is not None:
            # uporabnik obstaja, vrnemo njegove podatke
            return r
    # Če pridemo do sem, uporabnik ni prijavljen, naredimo redirect
    if auto_login:
        redirect('/login/')
    else:
        return None


def get_my_profile(id):
    """Funkcija glede na vlogo vrača podatke za kartico osebe."""
    cur.execute(
        "SELECT ime, priimek, emso, stalno_prebivalisce FROM oseba WHERE id_osebe = %s", [id])
    return cur.fetchone()


def get_id_from(emso):
    """Funkcija vraca emso stevilko glede na id osebe."""
    cur.execute("SELECT id_osebe FROM oseba WHERE emso = %s", [emso])
    return cur.fetchone()[0]


def is_doctor(id):
    """Funkcija za danega uporabnika preveri, če je zdravnik"""
    cur.execute(
        "SELECT exists (SELECT 1 FROM zdravstveni_delavec WHERE id_osebe = %s LIMIT 1);", [id])
    return cur.fetchone()[0]


def is_vaxed(id):
    """Funkcija za danega uporabnika preveri, če je cepljen"""
    cur.execute(
        "SELECT exists (SELECT * FROM cepljenje WHERE id_osebe = %s)", [id])
    return cur.fetchone()[0]


def is_tested(id):
    """Funkcija za danega uporabnika preveri, če je testiran"""
    cur.execute(
        "SELECT exists (SELECT * FROM testiranje WHERE id_osebe = %s)", [id])
    return cur.fetchone()[0]


def add_to_hospital(pacient_id, hospital_id):
    """Funkcija v bazo vstavlja novega pacienta za sprejem v bolnišnico."""
    cur.execute("INSERT INTO pacient VALUES (%s, %s)",
                [pacient_id, hospital_id])
    baza.commit()


def vax_id(id):
    """Funkcija vrne ime cepiva, če ji podamo id cepiva"""
    if is_vaxed(id):
        cur.execute(
            "SELECT ime_cepiva FROM cepivo WHERE id_cepiva = (SELECT DISTINCT id_cepiva FROM cepljenje WHERE id_osebe=%s)", [id])
        return cur.fetchone()[0]
    else:
        return False


def hospital_id(id):
    """Funkcija vrača id bolnice v kateri dela trenutni uporabnik"""
    cur.execute(
        "SELECT id_bolnisnice FROM zdravstveni_delavec WHERE id_osebe = %s", [id])
    return cur.fetchone()[0]


def hospital_name(id):
    """Funkcija vrača ime bolnisnice v kateri je uporabnik z idjem"""
    if is_doctor(id):
        cur.execute("SELECT ime_bolnisnice FROM bolnisnica WHERE id_bolnisnice=%s", [hospital_id(id)])
        return cur.fetchone()[0]


def remove_pacient(id):
    """Funkcija poisce pacienta v doloceni bolnicni in ga odstrani iz tabele. Pravice imajo samo zdravstveni delavci."""
    hospital = hospital_id(id)
    cur.execute(
        "SELECT ime, priimek, emso FROM odstrani_pacienta WHERE id_bolnisnice = %s", [hospital])
    return cur.fetchall()


def vax_pacient(ime, priimek, cepivo):
    """Funkcija v bazi popravi podatek o cepljenu dolocenega pacienta. Ce osebe ni v bolnici, je nemoremo cepiti. Pravice ima samo zdravnik."""
    # TODO

def test_last_date(id):
    if is_tested(id):
        cur.execute(
            "SELECT datum_testa FROM testiranje WHERE id_osebe=%s ORDER BY datum_testa DESC", [id])
        return cur.fetchone()[0]
    else:
        return False

def delete_pacient(id):
    """ Funkcija izbriše bolnika id-jem"""
    cur.execute("DELETE FROM pacient WHERE id_osebe = %s", [id])
    baza.commit()



def test_result(id):
    if is_tested(id):
        cur.execute(
            "SELECT rezultat_testa FROM testiranje WHERE id_osebe=%s ORDER BY datum_testa DESC", [id])
        return cur.fetchone()[0]
    else:
        return False


def verify_user(ime, priimek, emso):
    cur.execute(
        "SELECT exists (SELECT * FROM oseba WHERE ime=%s AND priimek=%s AND emso=%s)", [ime, priimek, emso])
    return cur.fetchone()[0]


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
    id = get_user()
    # TODO dodaj še eno polje, ki prikaže ime bolnice, če je oseba zdravstveni delavec
    return template("user.html", get_my_profile(id), is_doctor=is_doctor(id), is_vaxed=is_vaxed(id), is_tested=is_tested(id), hospital_name=hospital_name(id))


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
            id = get_id_from(emso)
            cur.execute("INSERT INTO uporabnik (username, password, id_osebe) VALUES (%s, %s, %s)", [
                        username, password, id])
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
    ime = request.forms.ime
    priimek = request.forms.priimek
    emso = request.forms.emso
    doctor_id = get_user()
    if verify_user(ime, priimek, emso):
        add_to_hospital(get_id_from(emso), hospital_id(doctor_id))
        redirect('/remove_pacient/')
    else:
        return template("add_pacient.html", ime=None, priimek=None, emso=None, napaka="Podatki pacienta se ne ujemajo")


@route('/pct_certificate/')
def pct_certificate():
    """Serviraj formo za PCT potrdilo"""
    id = get_user()
    if is_vaxed(id) or is_tested(id):
        return template("pct_certificate.html", get_my_profile(id), datum_testiranja=test_last_date(id), rezultat_test=test_result(id), cepivo=vax_id(id))
    else:
        # TODO naredi napako na vrhu htmlja
        return

@route('/pct_certificate/<x>')
def pacient_certificate(x):
    """Serviraj formo za pacientovo PCT potrdilo"""
    id = get_user()
    id_pacienta = get_id_from(x)
    if is_doctor(id):
        return template("pct_certificate.html", get_my_profile(id_pacienta),  datum_testiranja=test_last_date(id_pacienta), rezultat_test=test_result(id_pacienta), cepivo=vax_id(id_pacienta))


@route("/remove_pacient/")
def remove_get():
    """Serviraj formo za odstranitev pacienta"""
    id = get_user()
    if is_doctor(id):
        return template('remove_pacient.html', pacienti=remove_pacient(id))
    else:
        # TODO naredi napako na vrhu htmlja
        return


@route("/remove_pacient/<x>/")
def remove_post(x):
    """Odstrani uporabnika"""
    id_uporabnika = get_user()
    if is_doctor(id_uporabnika):
        id = get_id_from(x)
        delete_pacient(id)
        redirect(url("remove_get"))
    else:
        # TODO naredi napako na vrhu htmlja
        return



# @get('/vpogledextra')
# def vpogledextra():
#     emso = request.query.emso
#     ime = request.query.ime
#     priimek = request.query.priimek

#     cur.execute("""SELECT emso, ime, priimek FROM oseba
#     WHERE emso = %s and ime = %s and priimek = %s""", [emso, ime, priimek])
#     return template('pacient.html', osebe=cur)


# @get('/vpogled')
# def vpogled():
#     return template('vpogled.html', napaka="", ime="", priimek="", emso="")

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
