#!/usr/bin/env python3
"""Build the fictional offline walkthrough with existing EDGY tools (stdlib only).
No skill or presenter template is changed. Generated index.html is committed so
reviewers can open it without installing anything.
"""
import base64
import hashlib
import html
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DIAGRAM = ROOT / 'skills/documentation/edgy-diagram/scripts'


def digest(text):
    return "'sha256-" + base64.b64encode(hashlib.sha256(text.encode()).digest()).decode() + "'"


def build():
    env = {**os.environ, 'EDGY_TEXT_TABLE_ONLY': '1'}
    with tempfile.TemporaryDirectory(prefix='edgy-walkthrough-') as work:
        work = Path(work)
        drawio = work / 'model.drawio'
        subprocess.run([sys.executable, str(DIAGRAM / 'edgy_generator.py'),
                        str(HERE / 'model.txt'), '--output', str(drawio),
                        '--graph', str(work / 'graph.json')], check=True, env=env)
        subprocess.run([sys.executable, str(DIAGRAM / 'edgy_lint.py'),
                        '--warnings-as-errors', str(drawio)], check=True, env=env)
        subprocess.run([sys.executable, str(DIAGRAM / 'edgy_render.py'),
                        str(drawio), '--no-png', '--out', str(work)], check=True, env=env)
        subprocess.run([sys.executable, str(DIAGRAM / 'edgy_present.py'),
                        str(drawio), '--graph', str(work / 'graph.json'),
                        '-o', str(work / 'atlas.html'), '--title', 'Acme Oy – EDGY-kaavioatlas',
                        '--lang', 'fi'], check=True, env=env)
        atlas = (work / 'atlas.html').read_text(encoding='utf-8')
        graph = json.loads((work / 'graph.json').read_text(encoding='utf-8'))
        figures = [p.read_text(encoding='utf-8') for p in sorted(work.glob('model-*.svg'))
                   if 'trace-' not in p.name]
    data = {
        'atlas': base64.b64encode(atlas.encode()).decode(), 'graph': graph,
        'sources': [
            {'id': 'S-01', 'title': 'Palvelulupauksen luonnos',
             'content': 'Acme Oy haluaa, että asiakas tietää työn etenemisen ja seuraavan askeleen.',
             'scope': 'Keksitty tavoite; toteutumista ei ole mitattu.'},
            {'id': 'S-02', 'title': 'Kaksi palveluluovutuksen esimerkkitapausta',
             'content': 'Molemmissa keksityissä tapauksissa asiakkaan piti kysyä, kuka jatkaa asian käsittelyä.',
             'scope': 'Keksityt tapaukset; eivät tilastollinen otos.'},
            {'id': 'S-03', 'title': 'Työnohjauskuvauksen esimerkki',
             'content': 'Kuvitteellinen organisaatio käyttää yhteistä työjonoa. Luovutuksen vahvistamisesta ei tässä aineistossa ole kuvausta.',
             'scope': 'Aineiston puute; ei näyttö käytännön puuttumisesta.'}],
        'capabilities': [
            {'id': 'CAP-01', 'name': 'Palvelutarpeen hallinta', 'why': 'Tunnistetaan tarve ja sovitaan oikea palvelun rajaus.'},
            {'id': 'CAP-02', 'name': 'Palvelun koordinointi', 'why': 'Vastuu, työ ja asiakkaan seuraava askel kohtaavat.'},
            {'id': 'CAP-03', 'name': 'Palvelun palautuminen', 'why': 'Toiminta jatkuu turvallisesti poikkeustilanteessa.'},
            {'id': 'CAP-04', 'name': 'Asiakastiedon hallinta', 'why': 'Tieto on ymmärrettävää ja ajantasaista eri toimijoille.'}],
        'journey': [
            {'name': 'Pyydän apua', 'task': 'Saan tarpeeni ymmärretyksi.', 'handover': 'Mitä asiakas kertoi ja mitä luvattiin?', 'check': 'Yhteinen käsitys tarpeesta ja palvelun rajasta.'},
            {'name': 'Sovin toteutuksen', 'task': 'Tiedän milloin ja miten apu tulee.', 'handover': 'Kuka vahvistaa työn siirtymisen toteuttajalle?', 'check': 'Omistaja, ajankohta ja asiakkaan seuraava askel.'},
            {'name': 'Saan avun', 'task': 'Laitteeni palautuu käyttöön.', 'handover': 'Miten poikkeama muutetaan yhteiseksi päätökseksi?', 'check': 'Toimintaohje ja vastuu myös tiedon puuttuessa.'},
            {'name': 'Varmistan tuloksen', 'task': 'Tiedän, että asia on ratkaistu.', 'handover': 'Vahvistaako asiakas lopputuloksen?', 'check': 'Ratkaisu ja mahdollinen jatkotoimi näkyviin.'}],
        'options': [
            {'id': 'A', 'title': 'Nykykäytännön täsmennys', 'description': 'Päivitetään ohje ja säilytetään nykyinen vastuunjako.',
             'pros': 'Rajattu muutos ja pieni valmistelutarve.', 'cons': 'Yhteinen luovutusvastuu voi jäädä epäselväksi.', 'unknown': 'Riittääkö ohje nykyisessä työnjaossa?'},
            {'id': 'B', 'title': 'Yhteinen vastuumalli', 'description': 'Kokeillaan vahvistettua vastuunvaihtoa ja asiakkaalle näkyvää seuraavaa askelta.',
             'pros': 'Kohdistuu luovutukseen ja tekee vastuun näkyväksi.', 'cons': 'Vaatii yhteisen omistajan, harjoittelun ja ylläpidon.', 'unknown': 'Auttaako malli asiakkaan arjessa ja millä työkuormalla?'},
            {'id': 'C', 'title': 'Uusi työnohjausratkaisu', 'description': 'Selvitetään järjestelmän uusimista laajempana muutoksena.',
             'pros': 'Voi mahdollistaa uudenlaisia työnkulkuja.', 'cons': 'Laajempi muutos, riippuvuudet ja investointitarve.', 'unknown': 'Onko nykyisessä järjestelmässä todellinen este vai onko kyse toimintatavasta?'}]
    }
    text = (HERE / 'walkthrough.template.html').read_text(encoding='utf-8')
    safe = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    text = text.replace('__DATA__', safe).replace('__FIGURES__', ''.join(figures).replace('`', '&#96;').replace('${', '&#36;{'))
    script = re.search(r'<script id="walkthrough-script">(.*?)</script>', text, re.S).group(1)
    style = re.search(r'<style>(.*?)</style>', text, re.S).group(1)
    atlas_script = re.search(r'<script>(.*?)</script>', atlas, re.S).group(1)
    atlas_style = re.search(r'<style>(.*?)</style>', atlas, re.S).group(1)
    # srcdoc inherits the parent policy, so permit only the two known applications' hashes.
    csp = ("default-src 'none'; script-src " + digest(script) + ' ' + digest(atlas_script)
           + '; style-src ' + digest(style) + ' ' + digest(atlas_style)
           + "; img-src data: blob:; font-src data:; connect-src 'none'; frame-src 'self'; "
             "object-src 'none'; base-uri 'none'; form-action 'none'")
    text = text.replace('__CSP__', html.escape(csp, quote=True))
    (HERE / 'index.html').write_text(text, encoding='utf-8')
    print('Built', HERE / 'index.html', '—', len(text.encode()), 'bytes')


if __name__ == '__main__':
    build()
