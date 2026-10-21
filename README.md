# Saray Döner – Website

Neue Website für **Saray Döner** in Freital und Altenberg: Speisekarte mit Suche, Bestellzettel mit Wünschen je Gericht, Abholzeit, Öffnungsstatus live, Deutsch/Englisch.

Live (Vorschau): **https://saray.micana.de**

Statische Seite ohne Framework, ohne externe Anfragen und ohne Cookies. Was im Browser gespeichert wird (Bestellzettel, Abholung, Sprache, letzte Bestellung), bleibt in `localStorage` auf dem Gerät des Gastes.

## Aufbau

| Pfad | Inhalt |
|---|---|
| `menu.py` | Speisekarte: alle Gerichte, Preise, Größen |
| `englisch.py` | Englische Namen und Beschreibungen |
| `build.py` | Standorte, Öffnungszeiten, Hinweis-Band, Vorlage, CSS und JS; baut die Seite |
| `maskottchen.py` | Zeichnet das Koch-Maskottchen als SVG (`maskottchen/`) |
| `png_export.py` | PNG-Fassungen und Favicon aus den SVGs |
| `assets/` | Schriften (Roboto Slab, Lato), Ladenfoto, Kartenausschnitte (© OpenStreetMap-Mitwirkende) |
| `docs/` | **Fertige Seite** – wird von GitHub Pages ausgeliefert, nicht von Hand ändern |

## Bauen

```bash
python3 build.py            # docs/: index.html, css/style.css, js/main.js, fonts/, img/
python3 build.py --einzeln  # index.html als einzelne Datei mit allem eingebettet (Vorschau, nicht im Repo)
```

Nur Python 3, keine Pakete nötig. Nach jeder Änderung `python3 build.py` laufen lassen und `docs/` mit committen.

## Häufige Änderungen

- **Preise oder Gerichte:** `menu.py`, bei neuen Gerichten auch `englisch.py`.
- **Öffnungszeiten, Telefon:** `STANDORTE` in `build.py`.
- **Hinweis oben (Urlaub, Feiertag, Angebot):** `HINWEISE` in `build.py`, mit `von`/`bis` als Datum. Außerhalb des Zeitraums blendet sich das Band von selbst aus.
- **Empfehlung und „Beliebt“:** `EMPFEHLUNG` und `BELIEBT` in `build.py`.

## WhatsApp-Bestellung

Die Nummern stehen bewusst **nicht** im Repo. Solange `whatsapp` in `STANDORTE` leer ist, ist der WhatsApp-Knopf ausgeblendet; Anrufen und „Zettel kopieren“ funktionieren immer.

- Für den Livegang die echte Nummer des Ladens bei `whatsapp` eintragen (international ohne `+`, z. B. `4917612345678`).
- Zum Testen nur lokal: `lokal.json` anlegen (steht in `.gitignore`), wirkt nur auf `--einzeln`:
  ```json
  {"whatsapp": {"freital": "4917612345678", "altenberg": "4917612345678"}}
  ```

## Vor dem Wechsel auf saraydöner.de

- `VORSCHAU = False` in `build.py` (entfernt `noindex` und die Sperre in `robots.txt`).
- `CNAME` in `build.py` auf die endgültige Domain setzen und den DNS-Eintrag umstellen.
- Datenschutzerklärung fertigstellen (inkl. Hinweis auf WhatsApp/Meta, sobald die Bestellung per WhatsApp aktiv ist).
- Allergen- und Zusatzstoff-Legende vom Inhaber einarbeiten.
