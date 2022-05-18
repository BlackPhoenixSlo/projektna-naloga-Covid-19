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
    emso TEXT PRIMARY KEY,
    ime TEXT NOT NULL,
    priimek TEXT NOT NULL,
    stalno_prebivalisce TEXT NOT NULL,
    datum_testiranja DATE,
    rezultat_test BOOLEAN,
    cepivo INTEGER REFERENCES cepivo(id_cepiva)
);

CREATE TABLE IF NOT EXISTS uporabnik (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    emso TEXT REFERENCES oseba(emso)
);


CREATE TABLE IF NOT EXISTS pacient (
    emso TEXT PRIMARY KEY REFERENCES oseba(emso),
    id_bolnisnice INTEGER REFERENCES bolnisnica(id_bolnisnice)
);


CREATE TABLE IF NOT EXISTS zdravstveni_delavec (
    emso TEXT PRIMARY KEY REFERENCES oseba(emso),
    id_bolnisnice INTEGER REFERENCES bolnisnica(id_bolnisnice)
);


CREATE TABLE IF NOT EXISTS bolnisnica (
    id_bolnisnice SERIAL PRIMARY KEY,
    ime_bolnisnice TEXT NOT NULL,
    stevilo_postelj INTEGER NOT NULL
    
);


CREATE VIEW odstrani_pacienta AS
SELECT pacient.emso, oseba.ime, oseba.priimek, pacient.id_bolnisnice 
FROM pacient JOIN oseba ON oseba.emso = pacient.emso;



GRANT ALL ON ALL TABLES IN SCHEMA public TO tinm WITH GRANT OPTION;
GRANT ALL ON ALL TABLES IN SCHEMA public TO jakab WITH GRANT OPTION;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO tinm WITH GRANT OPTION;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO jakab WITH GRANT OPTION;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO javnost;

--- Dovolimo vsakemu obiskovalcu spletne strani, da se registrira v portal
GRANT INSERT ON uporabnik TO javnost;
GRANT INSERT ON pacient TO javnost;


