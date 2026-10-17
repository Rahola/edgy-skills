# Cursor Adapter

Tämä adapteri integroi edgy-skills -skillit Cursoriin.

## Miten Cursor käyttää skillejä

Cursor lukee ohjeet `.cursorrules`-tiedostosta projektin juuresta. Install-skripti yhdistää valittujen skillien sisällöt tähän tiedostoon.

## Asennus

```bash
# Asenna skillit projektin .cursorrules-tiedostoon
bash adapters/cursor/install.sh edgy-framework edgy-assessment

# Tai aja projektin juuressa
cd your-project/
bash /path/to/edgy-skills/adapters/cursor/install.sh edgy-framework
```

## Mitä install.sh tekee

1. Lataa valittujen skillien `SKILL.md`-tiedostot (riippuvuudet `requires:` ensin)
2. Yhdistää ne `.cursorrules`-tiedostoon projektin juureen
3. Lisää selkeät osioiden erottimet
4. Skillit, jotka tarvitsevat koko hakemistonsa (`install: directory`, esim. `edgy-c4`), eivät
   toimi pelkkänä tekstinä: suora pyyntö päättyy viestiin ja exit 1:een, `--all` ohittaa ne ja
   nimeää ne. Käytä niille claude-code- tai generic-adapteria.
5. Epäonnistunut skilli tai tyhjä / lukukelvoton skillilista → exit 1

## Vaatimukset

- `curl`
- `python3` + `pyyaml`
