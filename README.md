# Saray Döner – Website

Neue Website für **Saray Döner** in Freital und Altenberg: Speisekarte mit Suche, Bestellzettel mit Wünschen je Gericht, Abholzeit, Öffnungsstatus live, Deutsch/Englisch.

Live (Vorschau): **https://saray.micana.de**

Statische Seite ohne Framework, ohne externe Anfragen und ohne Cookies. Was im Browser gespeichert wird (Bestellzettel, Abholung, Sprache, letzte Bestellung), bleibt in `localStorage` auf dem Gerät des Gastes.

## Aufbau

| Pfad | Inhalt |
|---|---|
| `menu.py` | Speisekarte (Standard): alle Gerichte, Preise, Größen |
| `daten/anpassungen.json` | Änderungen aus der Chef-App (leer = Standard) |
| `anpassungen.py` / `chef_app.py` | Änderungen anwenden / Chef-App |
| `qr.py` / `aufsteller.py` | QR-Codes / Druckvorlagen für die Theke |
| `tests/` | automatische Browser-Tests |
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

## Chef-App (für den Inhaber)

Unter **/chef/** (z. B. https://saray.micana.de/chef/) – nicht verlinkt, für Suchmaschinen gesperrt. Große Schaltflächen, fürs Handy gemacht:

- **Heute:** Hähnchen, Nuggets, Falafel, Pizza, Baguette … für heute aus, ab Uhrzeit (heute oder jeden Tag) oder dauerhaft aus – für beide Läden oder nur einen. Dazu ein Hinweis-Band mit Zeitraum.
- **Karte:** Preise, Namen und Beschreibungen ändern, Gerichte löschen (und wieder anzeigen), neue Gerichte anlegen.
- **Zeiten:** Öffnungszeiten je Laden und Wochentag, auch „geschlossen“.
- **Mehr:** „Alles auf Standard zurücksetzen“, Abmelden.

Gespeichert wird nur die Abweichung vom Standard in **`daten/anpassungen.json`** (Aufbau siehe `anpassungen.py`). Danach baut der GitHub-Workflow die Seite neu, testet sie und veröffentlicht sie – nach ca. 2–3 Minuten ist alles online; die App zeigt den Fortschritt an. Ungültige Einträge werden beim Bauen übersprungen (Warnung im Workflow-Log), der Standard bleibt dann stehen. Der Standard selbst steht weiter in `menu.py` und `STANDORTE` in `build.py`.

**Zugang einrichten (einmal pro Gerät):**
1. GitHub → Settings → Developer settings → *Fine-grained personal access tokens* → *Generate new token*
   - Repository access: *Only select repositories* → `saray-doener`
   - Permissions: **Contents: Read and write**, **Actions: Read-only** (für die Fortschrittsanzeige)
   - Ablauf: 1 Jahr (danach neuen Token erzeugen und neu einrichten)
2. Auf dem Handy des Inhabers öffnen: `https://saray.micana.de/chef/#token=<TOKEN>` – der Token wird nur auf dem Gerät gespeichert und sofort aus der Adresse entfernt.
3. „Zum Home-Bildschirm“ → erscheint als App **„Chef“**.

Token verloren oder Handy weg: Token auf GitHub löschen – damit ist der Zugang sofort gesperrt.

## Veröffentlichen

Der Workflow `.github/workflows/pruefen.yml` läuft bei jedem Push: bauen → im Browser testen → `docs/` zurück ins Repo schreiben → auf GitHub Pages veröffentlichen.
Einmalig nötig: **Settings → Pages → Source: „GitHub Actions“**. Schlägt ein Test fehl, wird nichts veröffentlicht.

Tests lokal: `python3 tests/test_seite.py` (braucht `pip install playwright` und `python -m playwright install chromium`).

## QR-Aufsteller

`python3 aufsteller.py` erzeugt `druck/aufsteller-freital.pdf` und `-altenberg.pdf` (A5): oben Speisekarte & vorbestellen (wählt den Laden vor), unten Google-Bewertung. Solange `VORSCHAU = True` mit MUSTER-Streifen. Nach dem Umzug auf saraydöner.de neu erzeugen und vor dem Druck mit dem Handy testen.

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
