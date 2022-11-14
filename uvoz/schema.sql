--- Shema za COVID portal
GRANT ALL ON DATABASE sem2022_tinm TO jakab WITH GRANT OPTION;

GRANT ALL ON SCHEMA public TO jakab WITH GRANT OPTION;

GRANT CONNECT ON DATABASE sem2022_tinm TO javnost;

GRANT USAGE ON SCHEMA public TO javnost;

CREATE TABLE IF NOT EXISTS cepivo (
    id_cepiva SERIAL PRIMARY KEY,
    ime_cepiva TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS oseba (
    id_osebe SERIAL PRIMARY KEY,
    emso TEXT UNIQUE NOT NULL,
    ime TEXT NOT NULL,
    priimek TEXT NOT NULL,
    stalno_prebivalisce TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bolnisnica (
    id_bolnisnice SERIAL PRIMARY KEY,
    ime_bolnisnice TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS uporabnik (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    id_osebe INTEGER UNIQUE REFERENCES oseba(id_osebe)
);

CREATE TABLE IF NOT EXISTS pacient (
    id_osebe INTEGER PRIMARY KEY REFERENCES oseba(id_osebe),
    id_bolnisnice INTEGER REFERENCES bolnisnica(id_bolnisnice)
);

CREATE TABLE IF NOT EXISTS zdravstveni_delavec (
    id_osebe INTEGER PRIMARY KEY REFERENCES oseba(id_osebe),
    id_bolnisnice INTEGER REFERENCES bolnisnica(id_bolnisnice)
);

CREATE TABLE IF NOT EXISTS cepljenje (
    id_osebe INTEGER REFERENCES oseba(id_osebe),
    id_cepiva INTEGER REFERENCES cepivo(id_cepiva),
    datum_cepljenja DATE NOT NULL,
    PRIMARY KEY (id_osebe, datum_cepljenja)
);

CREATE TABLE IF NOT EXISTS testiranje (
    id_osebe INTEGER PRIMARY KEY REFERENCES oseba(id_osebe),
    datum_testa DATE NOT NULL,
    rezultat_testa BOOLEAN NOT NULL
);

CREATE
OR REPLACE VIEW odstrani_pacienta AS
SELECT
    oseba.ime,
    oseba.priimek,
    oseba.emso,
    pacient.id_bolnisnice
FROM
    pacient
    JOIN oseba ON oseba.id_osebe = pacient.id_osebe;

GRANT ALL ON ALL TABLES IN SCHEMA public TO tinm WITH GRANT OPTION;

GRANT ALL ON ALL TABLES IN SCHEMA public TO jakab WITH GRANT OPTION;

GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO tinm WITH GRANT OPTION;

GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO jakab WITH GRANT OPTION;

GRANT
SELECT
    ON ALL TABLES IN SCHEMA public TO javnost;

--- Dovolimo vsakemu obiskovalcu spletne strani, da se registrira v portal
GRANT
INSERT
    ON uporabnik TO javnost;

--- Namenjeno zdravnikom, da lahko dodajajo nove paciente v bolnisnice
GRANT
INSERT
    ON pacient TO javnost;

GRANT DELETE ON pacient TO javnost;

--- Namenjeno zdravnikom, da lahko cepijo svoje paciente, verifikacija zdravnikov poteka preko 
GRANT
INSERT
    ON cepljenje TO javnost;