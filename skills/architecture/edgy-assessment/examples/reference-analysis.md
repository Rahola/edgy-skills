# Acme Oy — EDGY 23 Enterprise Design -analyysi

**Lähde:** acme.example (julkinen verkkosivusto, maaliskuu 2026)
**Menetelmä:** EDGY 23 Enterprise Design
**Analysoija:** Claude (Anthropic)

---

## 1. Ylätason yhteenveto

Acme on 2017 perustettu 30 hengen ohjelmistoasiantuntijatalo Otaniemessä. Yritys positioituu pitkäaikaiseksi teknologiakumppaniksi, joka painottaa ylläpidettäviä järjestelmiä, suoraa viestintää ja eurooppalaista infrastruktuuria.

EDGY-analyysi paljastaa vahvan koherenssin Identity- ja Architecture-fasettien välillä, mutta tunnistaa kehityskohteita Experience-fasetin ja leikkauselementtien välisessä koherenssissa.

---

## 2. Identity-fasetti — Miksi Acme on olemassa?

### Purpose (Tarkoitus)
**Kestävä teknologiakumppanuus** — "Rakennamme järjestelmiä, joita joku oikeasti jaksaa ylläpitää."

Acmen tarkoitus ei ole teknologian myynti vaan pitkäaikainen kumppanuus. Tämä erottaa yrityksen konsulttitaloista, jotka keskittyvät projektitoimituksiin.

### Story (Tarina)
**Otaniemestä 200+ projektiin** — Perustettu 2017 Suomen teknologiakeskuksessa, kasvanut intohimoisella porukalla 30 ammattilaiseen. 141 vuotta yhdistettyä kokemusta.

Tarina on aito ja erottava: startup-henkinen kasvu ilman ulkoista rahoitusta, korostaa itsenäisyyttä ja autenttisuutta.

### Content (Sisältö)
**Suora ja rehellinen viestintä** — "Underpromise, overdeliver" -filosofia. Viestintä myös silloin kun on epämukavaa. Blogi, asiakasreferenssit ja lupaukset kuten "emme myy tekoälyä tuotteena".

**Vahvuus:** Content ilmaisee tarkoitusta johdonmukaisesti — lupaukset ja tarina puhuvat samaa kieltä.

---

## 3. Architecture-fasetti — Miten Acme toimii?

### Capability (Kyvykkyydet)
Acme tarjoaa laajan palveluvalikoiman:

| Kyvykkyys | Luonne | Taso |
|-----------|--------|------|
| Ohjelmistokehitys (web/mobiili) | Differentiating, in-house | Ydin |
| UI/UX-suunnittelu | In-house | Tukeva |
| Pilvi-infrastruktuuri (UpCloud) | Differentiating, in-house | Ydin |
| QA ja testaus | In-house | Tukeva |
| DevOps ja ylläpito (First Line AI) | Differentiating, in-house | Ydin |
| Kasvuhakkerointi | In-house | Tukeva |

**Huomio:** Kyvykkyysvalikoima on laaja 30 hengen yritykselle. Tämä voi olla sekä vahvuus (kokonaispalvelu) että riski (fokuksen puute).

### Asset (Resurssit)
- **React/Vue/Node/TypeScript -teknologiapino** — moderni ja yleinen
- **Google Cloud + UpCloud -infrastruktuuri** — eurooppalainen painotus on erottuva
- **First Line AI-valvontatyökalu** — oma tuote, joka tukee ylläpitopalvelua

### Process (Prosessit)
- **Ketterä kehitys** — MVP-lähestyminen, iteratiivinen toimitus
- **Jatkuva ylläpito** — proaktiiviset päivitykset ja korjaukset AI-avusteisesti
- **Tiimivuokraus** — embedded-kehittäjät asiakkaan tiimissä

**Vahvuus:** Prosessit toteuttavat kyvykkyyksiä suoraan — ketterä kehitys → ohjelmistokehitys, jatkuva ylläpito → DevOps.

---

## 4. Experience-fasetti — Mikä rooli Acmella on asiakkaiden elämässä?

### Task (Tehtävät)
Asiakkaiden ydintehtävät Acmen kanssa:

1. **Uuden sovelluksen kehittäminen** — suurin palvelualue
2. **Olemassa olevan palvelun ylläpito** — First Line -palvelun kautta
3. **Kehitystiimin skaalaaminen** — tiimivuokraus
4. **Teknologianeuvonta** — konsultointi
5. **MVP/prototyypin rakentaminen** — nopea validointi (5-7k EUR)

### Channel (Kanavat)
| Kanava | Tyyppi | Rooli |
|--------|--------|-------|
| acme.example | Digitaalinen, asynkroninen | Ensimmäinen kontaktipiste |
| Puhelin/WhatsApp | Digitaalinen, synkroninen | Nopea yhteydenotto |
| Sähköposti | Digitaalinen, asynkroninen | Tarjoukset ja sopimukset |
| LinkedIn/some | Digitaalinen, asynkroninen | Brändin rakennus |
| Otaniemen toimisto | Fyysinen, synkroninen | Syvälliset keskustelut |

### Journey (Asiakasmatka)
```
Yhteydenotto → Tarvekartoitus → Suunnittelu → MVP/Proto → Kehitys → Julkaisu → Ylläpito
```

**Vahvuus:** Asiakasmatka kattaa koko elinkaaren ideasta ylläpidettyyn palveluun, mikä vastaa Purpose-lupausta pitkäaikaisesta kumppanuudesta.

---

## 5. Leikkauselementit — Fasettien väliset sillat

### Organisation (Identity ↔ Architecture)
**30 hengen tiimipohjainen organisaatio** — CEO Atte Pohjanmaa, myynti/markkinointi Timo Moilanen. Embedded-tiimimallit asiakasprojekteissa.

- **tavoittelee** Purpose (kestävä kumppanuus)
- **omistaa** kyvykkyydet (ohjelmistokehitys, UI/UX, DevOps)
- **suorittaa** prosessit (ketterä kehitys, ylläpito)
- **rakentaa** brändiä (luotettava kumppani)

**Koherenssi:** Vahva. Organisaatiorakenne tukee sekä identiteettiä (tiimipohjainen, ei hierarkkinen) että arkkitehtuuria (embedded-tiimit mahdollistavat ketterän kehityksen).

### Product (Architecture ↔ Experience)
Kolme tuotelinjaa:

1. **Web/mobiilisovellukset** — räätälöidyt ratkaisut
2. **First Line ylläpitopalvelu** — AI-pohjainen valvonta ja ylläpito
3. **UpCloud-infrapalvelu** — eurooppalainen pilvi-infra

- **palvelee** asiakkaan tehtäviä (kehitys, ylläpito)
- **esiintyy** asiakasmatkan eri vaiheissa

**Koherenssi:** Hyvä. Tuotteet vastaavat suoraan asiakkaan tehtäviin. First Line on erityisen koherentti — se yhdistää DevOps-kyvykkyyden ylläpitotehtävään.

### Brand (Identity ↔ Experience)
**"Luotettava eurooppalainen ohjelmistotalo"** — "jokaiseen muottiin soveltuva", "ei bullshit-pönötystä".

- **edustaa** tarkoitusta (kestävä kumppanuus)
- **herättää** tarinan (kasvutarina ilman hypeä)
- **tukee** asiakkaan tehtäviä (luottamus vähentää riskiä)

**Koherenssi:** Hyvä. Anti-hype-brändi on uskottava 30 hengen yritykselle ja resonoi erityisesti suomalaisten B2B-asiakkaiden kanssa.

---

## 6. Vahvuudet

1. **Purpose-Architecture -koherenssi:** Tarkoitus (kestävä kumppanuus) toteutuu suoraan arkkitehtuurissa (ylläpitopalvelu, jatkuva kehitys, First Line AI).
2. **Erottuva arvolupauksessa:** "Underpromise, overdeliver" ja anti-hype-linja erottaa kilpailijoista.
3. **Eurooppalainen infrastruktuuri:** UpCloud-kumppanuus ja GDPR-painotus on aito erottautumistekijä.
4. **Elinkaaripalvelu:** Harva 30 hengen yritys kattaa koko ketjun suunnittelusta ylläpitoon.
5. **First Line AI:** Oma tuote, joka tukee Purpose-lupausta konkreettisesti.

---

## 7. Kehityskohteet ja aukot

### 7.1 Kyvykkyysfokus
14 palvelualuetta 30 hengen yrityksessä on laaja. EDGY-analyysi suosittelee erottelua:
- **Differentiating** (panostettavat): ohjelmistokehitys, DevOps/First Line, pilvi-infra
- **Commodity** (ulkoistettavat tai vähennettävät): graafinen suunnittelu, verkkokauppa, kasvuhakkerointi

### 7.2 Experience-fasetin selkeys
Asiakasmatka on implisiittinen mutta ei eksplisiittisesti kuvattu verkkosivuilla. Suositus: visualisoi asiakasmatka selkeämmin markkinointimateriaalissa.

### 7.3 Content-strategia
Blogi on olemassa mutta sisältöstrategia vaikuttaa reaktiiviselta. "Underpromise, overdeliver" -filosofia voisi näkyä vahvemmin case studyissa, jotka todistavat lupauksen.

### 7.4 Brand-Experience -yhteys
Brändi "luotettava kumppani" on vahva mutta yleinen. Suositus: konkretisoi brändilupausta asiakaskokemuksessa — esim. SLA-takuut, läpinäkyvät prosessit, automaattiset raportit.

### 7.5 Organisation-skaalautuvuus
30 hengen organisaatiossa embedded-tiimimalli skaalautuu rajallisesti. Kumppanuusverkosto (25+ yritystä) kompensoi tätä, mutta ei näy EDGY-mallissa.

---

## 8. Suositukset

| # | Suositus | EDGY-elementti | Prioriteetti |
|---|----------|----------------|-------------|
| 1 | Priorisoi 3-4 ydinkyvykkyyttä, ulkoista loput | Capability | Korkea |
| 2 | Kuvaa asiakasmatka eksplisiittisesti verkkosivuille | Journey | Keskitaso |
| 3 | Luo case study -sarja joka todistaa "underpromise, overdeliver" | Content | Keskitaso |
| 4 | Konkretisoi brändilupausta mitattavilla SLA-tasoilla | Brand | Keskitaso |
| 5 | Mallinna kumppanuusverkosto EDGY:n People/Organisation -elementeillä | Organisation | Matala |
| 6 | Kehitä First Line omaksi tuotebrändiksi | Product/Brand | Matala |

---

## 9. Kaaviot

Täysi assessment tuottaa seuraavat EDGY 23 -kaaviot (draw.io-muodossa). Tämän
esimerkin mukana toimitetaan näytteenä vain Identity-kartta
(`acme-identity.drawio`):

| Tiedosto | Sisältö |
|----------|---------|
| `acme-all-facets.drawio` | Ylätason kokonaiskaavio kaikista faceteista ja leikkauselementeistä |
| `acme-identity.drawio` | Identity-fasetin tarkka kartta (Purpose, Story, Content, Brand, Organisation) |
| `acme-architecture.drawio` | Architecture-fasetin tarkka kartta (6 kyvykkyyttä, 3 resurssia, 3 prosessia, 4 tuotetta) |
| `acme-experience.drawio` | Experience-fasetin tarkka kartta (5 tehtävää, 5 kanavaa, 6 matkaelementtiä, 3 tuotetta) |

Kaaviot noudattavat EDGY 23 -standardin virallista väripalettia ja elementtimuotoja. Avaa `.drawio`-tiedostot draw.io-sovelluksessa tai app.diagrams.net-sivustolla.

---

*Analyysi perustuu julkisesti saatavilla oleviin tietoihin osoitteessa acme.example. Yrityksen sisäinen tieto voi tuoda lisää syvyyttä erityisesti Architecture- ja Organisation-elementteihin.*
