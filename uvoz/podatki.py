# uvozimo ustrezne podatke za povezavo
import auth

# uvozimo psycopg2
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s šumniki


def ustvari_tabelo():
    cur.execute("""
        CREATE TABLE oseba (
            emso TEXT PRIMARY KEY,
            ime TEXT NOT NULL,
            priimek TEXT NOT NULL,
            stalno_prebivalisce TEXT NOT NULL,
            datum_testiranja DATE NOT NULL,
            rezultat_testa BOOLEAN NOT NULL
        );
    """)
    conn.commit()

def pobrisi_tabelo():
    cur.execute("""
        DROP TABLE oseba;
    """)
    conn.commit()

conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) 

ustvari_tabelo()



