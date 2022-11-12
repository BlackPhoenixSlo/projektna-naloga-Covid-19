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

# uvozimo generator qr kod
import qrcode

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
    vrni njegov id. Če ni prijavljen, preusmeri
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
        redirect(url("login_get"))
    else:
        return None


def get_my_profile(id):
    """Funkcija vrača splošne podatke osebe"""
    cur.execute(
        "SELECT ime, priimek, emso, stalno_prebivalisce FROM oseba WHERE id_osebe = %s", [id])
    return cur.fetchone()


def get_id_from(emso):
    """Funkcija vraca id glede na emso osebe"""
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
    try:
        cur.execute("INSERT INTO pacient VALUES (%s, %s)",
                    [pacient_id, hospital_id])
        baza.commit()
    except:
        baza.rollback()
        raise Exception("Dan pacient je že v bolnišnici")
        
    
def vax_id(id):
    """Funkcija vrne ime cepiva, če ji podamo id cepljene osebe"""
    if is_vaxed(id):
        cur.execute(
            "SELECT ime_cepiva FROM cepivo WHERE id_cepiva = (SELECT DISTINCT id_cepiva FROM cepljenje WHERE id_osebe=%s)", [id])
        return cur.fetchone()[0]
    else:
        return False


def hospital_id(id):
    """Funkcija vrača id bolnisnice v kateri je oseba s tem id-jem"""
    if is_doctor(id):
        cur.execute(
            "SELECT id_bolnisnice FROM zdravstveni_delavec WHERE id_osebe = %s", [id])
        return cur.fetchone()[0]
    else:    
        cur.execute(
            "SELECT id_bolnisnice FROM pacient WHERE id_osebe = %s", [id])
        return cur.fetchone()[0]
       

def hospital_name(id):
    """Funkcija vrača ime bolnisnice v kateri je uporabnik z idjem"""
    if is_doctor(id):
        cur.execute("SELECT ime_bolnisnice FROM bolnisnica WHERE id_bolnisnice=%s", [
                    hospital_id(id)])
        return cur.fetchone()[0]


def remove_pacient(id):
    """Funkcija poisce pacienta v doloceni bolnisnici in ga odstrani iz tabele. Pravice imajo samo zdravstveni delavci."""
    hospital = hospital_id(id)
    cur.execute(
        "SELECT ime, priimek, emso FROM odstrani_pacienta WHERE id_bolnisnice = %s", [hospital])
    return cur.fetchall()


def vax_pacient(pacient_id, cepivo_id):
    """Funkcija doda nov vnos v tabelo cepljenje. To lahko naredi tudi za že cepljenje paciente."""
    print(pacient_id, cepivo_id)
    today = datetime.today()
    today = today.strftime("%d-%m-%Y")
    try:
        cur.execute("INSERT INTO cepljenje (id_osebe, id_cepiva, datum_cepljenja) VALUES (%s, %s, %s)",
                [pacient_id, cepivo_id, today])
        baza.commit()
    except:
        baza.rollback() 


def test_last_date(id):
    """Funkcija vrača datum zadnjega testiranja, če je bila oseba z id-jem testirana. Drugače vrne False."""
    if is_tested(id):
        cur.execute(
            "SELECT datum_testa FROM testiranje WHERE id_osebe=%s ORDER BY datum_testa DESC", [id])
        return cur.fetchone()[0]
    else:
        return False


def delete_pacient(id):
    """Funkcija izbriše bolnika id-jem"""
    cur.execute("DELETE FROM pacient WHERE id_osebe = %s", [id])
    baza.commit()


def test_result(id):
    """Funkcija vrača rezultat zadnjega testa, če je bila oseba testirana. Drugače vrne False."""
    if is_tested(id):
        cur.execute(
            "SELECT rezultat_testa FROM testiranje WHERE id_osebe=%s ORDER BY datum_testa DESC", [id])
        return cur.fetchone()[0]
    else:
        return False


def verify_user(ime, priimek, emso):
    """Funkcija preverja, če se ime, priimek in emso skladajo s podatki iz baze."""
    cur.execute(
        "SELECT exists (SELECT * FROM oseba WHERE ime=%s AND priimek=%s AND emso=%s)", [ime, priimek, emso])
    return cur.fetchone()[0]


def list_of_vax():
    """Funkcija vrne seznam vseh imen cepiv"""
    cur.execute(
        "SELECT ime_cepiva FROM cepivo"
    )
    cepiva = cur.fetchall()
    # Funkcija mi vraca seznam seznamov -> naredim flat list
    cepiva = [cepivo[0] for cepivo in cepiva]
    return cepiva


def index_of_vax(vax_name : str) -> int:
    cur.execute(
        "SELECT id_cepiva FROM cepivo where ime_cepiva=%s", [vax_name]
    )
    return cur.fetchone()[0]
    


def generate_qr(id):
    """Funkcija ne vrača ničesar, zgenerira pa qr kodo specifično glede na uporabnika"""
    profile = get_my_profile(id)
    if is_vaxed(id):
        qr_pct = "{ime} {priimek} \n{stalno_prebivalisce} \n{cepivo}".format(ime=profile[0], priimek=profile[1], stalno_prebivalisce=profile[3], cepivo=vax_id(id))
        img = qrcode.make(qr_pct)
        img.save('static/user_qrcodes/user_{0}.png'.format(id))
    else:
        # TODO treba je pogledat da je bil vsaj negativen - mogoče nit trenutno ni tako pomembno
        qr_pct = "{ime} {priimek} \n {stalno_prebivalisce} \n {datum}".format(ime=profile[0], priimek=profile[1], stalno_prebivalisce=profile[3], datum=test_last_date(id)) 

        img = qrcode.make(qr_pct)
        img.save('static/user_qrcodes/user_{0}.png'.format(id))


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
    if (is_vaxed(id) or is_tested(id)):
        qr_picture_path = 'static/user_qrcodes/user_{0}.png'.format(id)
        if os.path.isfile(qr_picture_path):
            return template("user.html", get_my_profile(id), is_doctor=is_doctor(id), is_vaxed=is_vaxed(id), is_tested=is_tested(id), hospital_name=hospital_name(id), id=id, vax_id = vax_id(id), napaka=None)
        else:
            generate_qr(id)
            return template("user.html", get_my_profile(id), is_doctor=is_doctor(id), is_vaxed=is_vaxed(id), is_tested=is_tested(id), hospital_name=hospital_name(id), id=id, vax_id = vax_id(id), napaka=None)
    else:
        return template("user.html", get_my_profile(id), is_doctor=is_doctor(id), is_vaxed=is_vaxed(id), is_tested=is_tested(id), hospital_name=hospital_name(id), id="blank", napaka=None)

@route("/login/")
def login_get():
    """Serviraj formo za login."""
    return template("login.html", napaka=None)


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
        redirect(url("main"))


@route("/register/")
def register_get():
    """Serviraj formo za registracijo"""
    return template("register.html",
                    napaka=None,
                    username=None,
                    emso=None,
                    ime=None,
                    priimek=None)


@post("/register/")
def register_post():
    """Registriraj novega uporabnika."""
    ime = request.forms.ime
    priimek = request.forms.priimek
    emso = request.forms.emso
    username = request.forms.username
    password1 = request.forms.password1
    password2 = request.forms.password2
    # Ali uporabnik že obstaja?
    cur.execute("SELECT 1 FROM uporabnik WHERE username=%s", [username])
    if cur.fetchone():
        # Uporabnik že obstaja
        return template("register.html",
                        username=username,
                        emso=emso,
                        ime=ime,
                        priimek=priimek,
                        napaka='To uporabniško ime je že zavzeto')
    elif not password1 == password2:
        # Gesli se ne ujemata
        return template("register.html",
                        username=username,
                        emso=emso,
                        ime=ime,
                        priimek=priimek,
                        napaka='Gesli se ne ujemata')
    else:
        cur.execute("SELECT 1 FROM uporabnik WHERE id_osebe=%s", [get_id_from(emso)])
        if cur.fetchone():
            return template("register.html",
                username=username,
                emso=emso,
                ime=ime,
                priimek=priimek,
                napaka='Ta oseba je že registrirana v portal')
        elif verify_user(ime, priimek, emso):
            password = password_hash(password1)
            try:
                id = get_id_from(emso)
                cur.execute("INSERT INTO uporabnik (username, password, id_osebe) VALUES (%s, %s, %s)", [
                            username, password, id])
                baza.commit()
            except TypeError:
                return template("register.html",
                                username=username,
                                emso=emso,
                                ime=ime,
                                priimek=priimek,
                                napaka='Dane emšo stevilke ni v bazi oseb. Prepričajte se na upravni enoti.')
            # Daj uporabniku cookie
            response.set_cookie('username', username, path='/', secret=secret)
            redirect(url("login_get"))
        else:
            return template("register.html",
                                username=username,
                                emso=emso,
                                ime=ime,
                                priimek=priimek,
                                napaka='Podatki med seboj se ne ujemajo. Prepričajte se na upravni enoti.')


@route("/logout/")
def logout():
    """Pobriši cookie in preusmeri na login."""
    response.delete_cookie('username', path='/')
    redirect(url("login_get"))


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
        try:
            add_to_hospital(get_id_from(emso), hospital_id(doctor_id))
        except:
            return template("add_pacient.html", ime=ime, priimek=priimek, emso=emso, napaka="Pacient je že v bolnišnici")
        else:
            redirect(url("remove_get"))
    else: 
        return template("add_pacient.html", ime=None, priimek=None, emso=None, napaka="Podatki pacienta se ne ujemajo")



@route('/pct_certificate/<x>')
def pacient_certificate(x):
    """Serviraj formo za pacientovo PCT potrdilo"""
    id = get_user()
    id_pacienta = get_id_from(x)
    if is_doctor(id):
        qr_picture_path = 'static/user_qrcodes/user_{0}.png'.format(id_pacienta)
        if os.path.isfile(qr_picture_path):
            return template("pct_certificate.html", get_my_profile(id_pacienta),  datum_testiranja=test_last_date(id_pacienta), rezultat_test=test_result(id_pacienta), cepivo=vax_id(id_pacienta), id=id_pacienta)
        else:
            generate_qr(id_pacienta)
            return template("pct_certificate.html", get_my_profile(id_pacienta),  datum_testiranja=test_last_date(id_pacienta), rezultat_test=test_result(id_pacienta), cepivo=vax_id(id_pacienta), id=id_pacienta)
    else:
        return template("user.html", get_my_profile(id), is_doctor=is_doctor(id), is_vaxed=is_vaxed(id), is_tested=is_tested(id), hospital_name=hospital_name(id), id=id, vax_id = vax_id(id), napaka="Nimate pravic za ogled certifikata")


@route('/pct_certificate/')
def pct_redirect():
    """Preusmerjamo uporabnika na glavno stran, če v urlju ni podatkov za koncno osebo"""
    redirect(url("remove_get"))       


@route("/my_pacients/")
def remove_get():
    """Serviraj formo za akcijo pri svojih pacientih"""
    id = get_user()
    if is_doctor(id):
        pacienti = remove_pacient(id)
        for i in range(len(pacienti)):
            (ime, priimek, emso) = pacienti[i]
            id_pacienta = get_id_from(emso)
            if is_vaxed(id_pacienta):
                pacienti[i] = [ime, priimek, emso, False]
            else:
                pacienti[i] = [ime, priimek, emso, True]
        #return template('remove_pacient.html', pacienti=pacienti)
        return template("my_pacients.html", pacienti=pacienti)
    else:
        return template("user.html", get_my_profile(id), is_doctor=is_doctor(id), is_vaxed=is_vaxed(id), is_tested=is_tested(id), hospital_name=hospital_name(id), id="blank", napaka="Nimate pravic za dostop do te strani.")


@route("/remove_pacient/<x>/")
def remove_post(x):
    """Odstrani pacienta"""
    id_uporabnika = get_user()
    if is_doctor(id_uporabnika):
        id = get_id_from(x)
        try:
            delete_pacient(id)
        except:
            redirect(url('remove_get'))
        else:
            redirect(url("remove_get"))
    else:
        # TODO naredi napako na vrhu htmlja
        return


@route("/vax_pacient/<x>")
def vax_get(x):
    """Serviraj formo za cepljenje danega pacienta"""
    id_uporabnika = get_user()
    id_pacienta = get_id_from(x)
    ime, priimek, emso  = get_my_profile(id_pacienta)[0], get_my_profile(id_pacienta)[1], get_my_profile(id_pacienta)[2]
    cepiva = list_of_vax()
    if is_doctor(id_uporabnika):
        return template("vax.html", ime=ime, priimek=priimek, emso=emso, cepiva=cepiva, napaka=None)



@route("/vax_pacient/<x>/<cepivo>")
def vax_post(x, cepivo):
    id_pacienta = get_id_from(x)
    id_zdravnika = get_user()
    id_cepiva = index_of_vax(cepivo)
    if (hospital_id(id_pacienta) == hospital_id(id_zdravnika) and is_doctor(id_zdravnika)):
        # Pacienta lahko cepimo tudi če je že cepljen
        vax_pacient(id_pacienta, id_cepiva)
        redirect(url("pacient_certificate", x=x))
    # TODO pohendlaj kaj se zgodi če nemoreš cepit pacienta   
    # elif not is_doctor(id_zdravnika):
    #   return template("vax.html", ime=ime, priimek=priimek, emso=emso, cepiva=id_cepiva, napaka="Nimate ustrezne avtorizacije za cepljenje.")
    # else:
    #    return template("vax.html", ime=ime, priimek=priimek, emso=emso, cepiva=id_cepiva, napaka="Nimate ustrezne avtorizacije za cepljenje tega pacienta.")

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
