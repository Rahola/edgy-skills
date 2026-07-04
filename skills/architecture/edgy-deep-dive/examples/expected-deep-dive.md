# EDGY Syväanalyysi: Capability × Organisation

**Yritys:** Globex Oy
**Linssi:** dependency
**Analysoitu:** 25.04.2026
**Konteksti:** Yleinen EDGY-analyysi tunnisti coherence-luokituksen **Weak** organisation × capability -suhteelle. Tämä syväanalyysi porautuu kyseiseen elementtipariin.

---

## Linkkartta

| Polku | Hyppyjä | Status | Verbi(t) |
|-------|---------|--------|----------|
| organisation → capability | 1 (suora) | **Aktiivinen** | omistaa |
| organisation → process → capability | 2 | **Osittainen** (molemmat linkit aktiivisia) | suorittaa / toteuttaa |
| product → capability | 1 (sivupolku) | Aktiivinen | vaatii |
| process → capability | 1 (sivupolku) | Aktiivinen | toteuttaa |

**Huomio puuttuvista linkeistä:** Virallisessa EDGY 23 -viitekehyksessä ei ole suoraa linkkiä `organisation → capability` (vain epäsuoran polun kautta process). Mallissa oleva `organisation omistaa capability` -linkki on kuitenkin validi sovellettu tulkinta organisaation omistajuussuhteesta.

---

## Riippuvuusanalyysi: Capability ↔ Organisation

### Kriittiset riippuvuudet

**1. Organisaatio omistaa kyvykkyydet — mutta omistajuus on epätasainen**

Mallissa on neljä kyvykkyyttä, joista organisaatio omistaa ne rakenteellisesti:
- **Cloud-arkkitehtuuri (AWS/Azure)** → omistaja: Arkkitehtuuri & Konsultointi -tiimi (15 hlö) — selkeä
- **Räätälöity ohjelmistokehitys** → omistaja: Kehitys-tiimi (45 hlö) — selkeä
- **DevOps ja jatkuva toimitus** → omistajuus epäselvä: käytetään sisäisesti, mutta asiakasprojekteissa vaihteleva
- **Myynti ja asiakkuudenhallinta (Ruotsi)** → omistaja: yksi rekrytoitu henkilö ilman tukiprosessia

Kriittisin puute: **Ruotsin myyntikyvykkyys on olemassa henkilötasolla mutta ei organisatorisella tasolla** — ei tiimiä, ei prosessia, ei playbooka.

**2. Prosessit toteuttavat kyvykkyyksiä — osittain**

2-hop-polku `organisation → process → capability`:
- `Projektitoimitusmalli (agile)` toteuttaa `Räätälöity ohjelmistokehitys` → toimii
- `Projektitoimitusmalli (agile)` toteuttaa `Cloud-arkkitehtuuri` → toimii osittain (arkkitehti ei aina mukana)
- `Myyntiprosessi` pitäisi toteuttaa `Myynti ja asiakkuudenhallinta (Ruotsi)` → **puuttuu kokonaan**
- `Rekrytointiprosessi` toteuttaa kyvykkyyksien kasvua → toimii

### Riippuvuuden suunta

**Yksisuuntainen: Kyvykkyydet ovat riippuvaisia organisaatiorakenteesta.**

Jos organisaatiorakenne muuttuu (esim. tiimijako tai roolitus), kyvykkyyksien omistajuus muuttuu. Jos kyvykkyys kasvaa (esim. AI-kyvykkyys lisätään), organisaation täytyy luoda uusi omistajuusrakenne.

### Pullonkaulat

1. **Ruotsin laajentuminen** — kyvykkyys (myynti/asiakkuudenhallinta Ruotsissa) odottaa organisaatiorakenteen syntymistä. Yksittäinen rekrytoitu henkilö ei muodosta kyvykkyyttä ilman prosessia ja tukea.

2. **DevOps-kyvykkyyden leviäminen** — DevOps on Enablingtason kyvykkyys, mutta organisaation toiminnallinen rakenne (erillinen kehitystiimi ilman yhteistä delivery-omistajuutta) hidastaa sen käyttöönottoa asiakasprojekteissa.

3. **Uusien kyvykkyyksien skaalaus** — 20 rekrytointia 2026 kasvattaa ohjelmistokehityskyvykkyyttä, mutta kyvykkyyden laatu ja homogeenisuus on riski: ei kyvykkyyskarttaa, ei eksplisiittisiä tasomäärittelyjä uusille osaajille.

### Vaihtoehtoiset polut

- **Product → capability** -polku: Tuotteet vaativat kyvykkyyksiä, mikä luo epäsuoran vetofunktion. Jos arkkitehtuuri­konsultointi-tuotetta myydään aktiivisesti, se vetää arkkitehtuurikyvykkyyttä. Tätä voisi vahvistaa eksplisiittisesti.
- **Asiakkuuspäällikkö-rooli** voisi toimia kyvykkyyssillan rakentajana Ruotsissa — ei vielä olemassa mallissa.

---

## Yhteenveto

Globexin organisaatiorakenne omistaa pääkyvykkyydet selkeästi (kehitys, arkkitehtuuri), mutta kolme kriittistä kohtaa vaativat toimenpiteitä: (1) Ruotsin myyntikyvykkyys tarvitsee organisatorisen kodin ja prosessin, ei vain henkilöä; (2) DevOps-kyvykkyyttä ei ole rakennettu asiakastoimitusten prosessiin; (3) kasvavaa kehittäjäjoukkoa ei ohjaa kyvykkyyskartta. Kaikki kolme ovat `organisation → capability` -linkin toteutumisen esteitä.

---

## Seuraava jatkoanalyysi

Tämän analyysin löydösten perusteella suositellaan:

| Elementtipari | Linssi | Perustelu |
|---------------|--------|-----------|
| capability × process | gaps | Myynti- ja DevOps-kyvykkyydet eivät ole prosesseissa. Tarkista puuttuvat `process → capability` -linkit. |
| organisation × product | alignment | Ei tuote-/palveluomistajuutta organisaatiossa. Ruotsin tuotetarjooma epäselvä. |
