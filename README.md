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
- **Vorbestellung:** `VORBESTELL_TAGE` in `build.py` (Standard 14 Tage; 0 = nur heute). Angeboten werden nur Öffnungstage im 15-Minuten-Raster; die Nachricht heißt dann „Vorbestellung“ und nennt Wochentag und Datum.

## Verfügbarkeit („heute kein Hähnchen“, „Nuggets ab 17 Uhr“)

Tagesaktuelle Sperren stehen in **`docs/status.json`**. Die Seite lädt die Datei bei jedem Aufruf neu; `build.py` überschreibt sie nicht.

```json
{"regeln": [
  {"was": "huhn", "datum": "2026-10-21"},
  {"was": "nuggets", "ab": "17:00"},
  {"was": "baguette", "laden": "altenberg"},
  {"was": ["80", "81"], "bis": "14:00", "tage": [1, 2, 3, 4, 5]}
]}
```

| Feld | Bedeutung |
|---|---|
| `was` | Gruppe oder Gerichtsnummer, auch als Liste. Gruppen: jede Kategorie (`doener`, `duerum`, `teller`, `pizza`, `lahmacun`, `baguette`, `salate`, `schnitzel`, `kinder`) und Zutaten (`huhn`, `nuggets`, `falafel`, `halloumi`, `schnitzel-fleisch`, `fisch`) |
| `ab` / `bis` | erst ab / nur bis Uhrzeit. Ohne beides: nicht verfügbar |
| `datum` | nur an diesem Tag (oder Liste von Tagen) – verfällt danach von selbst |
| `tage` | nur an diesen Wochentagen (0 = Sonntag) |
| `laden` | nur `freital` oder `altenberg`; ohne: beide Läden |

Auf der Seite: Hinweis am Gericht („heute nicht verfügbar“, „erst ab 17 Uhr“, „Altenberg: …“), ganz gesperrte Gerichte sind ausgegraut. Im Bestellzettel wird gegen Laden **und Abholzeit** geprüft – Nuggets um 15 Uhr für 17:30 Uhr vorbestellen geht, für „so schnell wie möglich“ nicht. Solange etwas nicht passt, ist der WhatsApp-Knopf ausgeblendet.

Feste Regeln, die immer gelten, können stattdessen in `VERFUEGBARKEIT` in `build.py` stehen.

## WhatsApp-Bestellung

Die Nummern stehen bei `whatsapp` in `STANDORTE` (`build.py`), international ohne `+`, z. B. `4917612345678`. Zurzeit ist dort zum Testen **Michaels Nummer** eingetragen – vor dem Livegang durch die Nummer des jeweiligen Ladens ersetzen. Ist das Feld leer, wird der WhatsApp-Knopf ausgeblendet; Anrufen und „Zettel kopieren“ funktionieren immer.

Optional nur lokal: `lokal.json` (steht in `.gitignore`) überschreibt die Nummern für die Einzeldatei-Vorschau (`--einzeln`):
```json
{"whatsapp": {"freital": "4917612345678", "altenberg": "4917612345678"}}
```

## Vor dem Wechsel auf saraydöner.de

- `VORSCHAU = False` in `build.py`. Das entfernt das Band „Nicht freigeschaltet“, das Wasserzeichen, den Titel-Zusatz, den TEST-Hinweis in der WhatsApp-Nachricht, `noindex` und die Sperre in `robots.txt`.
- `CNAME` in `build.py` auf die endgültige Domain setzen und den DNS-Eintrag umstellen.
- Testnummer bei `whatsapp` durch die Nummern der Läden ersetzen.
- Datenschutzerklärung fertigstellen (inkl. Hinweis auf WhatsApp/Meta).
- Allergen- und Zusatzstoff-Legende vom Inhaber einarbeiten.
