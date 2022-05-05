import hashlib


###########################################################
# Pomozne funkcije 


def geslo_md5(s):
    """Funkcija zgoscevanja gesel, ki so v UTF-8 encodingu. To potem spravimo v bazo"""
    h = hashlib.md5()
    h.update(s.encode('utf-8'))
    return h.hexdigest()