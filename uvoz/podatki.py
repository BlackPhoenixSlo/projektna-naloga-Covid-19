# uvozimo ustrezne podatke za povezavo
import auth

# uvozimo psycopg2
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s šumniki

import csv

def ustvari_tabelo():
    cur.execute("""
        CREATE TABLE obcina (
            id SERIAL PRIMARY KEY,
            ime TEXT NOT NULL,
            povrsina NUMERIC NOT NULL,
            prebivalstvo INTEGER NOT NULL,
            gostota NUMERIC NOT NULL,
            naselja INTEGER NOT NULL,
            ustanovitev INTEGER,
            pokrajina TEXT NOT NULL,
            stat_regija TEXT NOT NULL,
            odcepitev TEXT
        );
    """)
    conn.commit()

def pobrisi_tabelo():
    cur.execute("""
        DROP TABLE obcina;
    """)
    conn.commit()

conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) 

pobrisi_tabelo()

