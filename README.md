# COVID-19 portal
## Projektna nalogi pri predmetu Osnove podatkovnih baz

* [![bottle.py](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/BlackPhoenixSlo/projektna-naloga-Covid-19/main?urlpath=proxy/8080/) Aplikacija `bottle.py`
* [![Jupyter](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/BlackPhoenixSlo/projektna-naloga-Covid-19/main) Jupyter

Aplikacija je preprost primer uporabe podatkovnih baz, pri čemer imajo uporabniki glede na različne vloge tudi različne pravice. Na portalu imamo **zdravstvene delavce** in **paciente**. V celotni populaciji so nekateri cepljeni in/ali testirani.
Ker podatkov ni mogoče pridobiti, sva podatke generirala preko spletnih virov na način, da se najbolje opiše slovensko prebivalstvo. Seveda zelo poenostavljeno.

## Dostopi pri uporabi aplikacije

### zdravstveni delavec
uporabniško ime: `admin`

geslo: `admin`

### pacient
uporabniško ime: `tadej`

geslo: `tadej`


### Opomba
Svojih računov z lastnimi podatki ni mogoče kreirati, saj aplikacija v odzadju preverja ali so dani podatki res v bazi prebivalstva.

### ER diagram
![ER DIAGRAM](ER_diagram.png)