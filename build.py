#!/usr/bin/env python3
"""Baut die Website von Saray Döner.

    python3 build.py            -> docs/ (index.html, css/, js/, fonts/, img/) für GitHub Pages
    python3 build.py --einzeln  -> index.html als eine einzige Datei mit allem eingebettet (Vorschau)

Keine externen Anfragen, keine Cookies. Speisekarte: menu.py · Englisch: englisch.py ·
Standorte/Zeiten: STANDORTE unten · Hinweis-Band: HINWEISE unten.
WhatsApp-Nummern stehen nicht im Repo: optional in lokal.json (siehe README).
"""
import base64, html, json, math, pathlib, re, shutil, sys, urllib.parse
from menu import GRUPPEN, VEGETARISCH, FISCH, VEG_WAEHLBAR, ALLERGENE, ALLERGENE_EN, ZUTATEN, KENNZEICHNUNG, SOSSEN, GERICHT_ALLERGENE
import englisch as EN
import anpassungen as ANP
import sprachen_daten as SP

HIER = pathlib.Path(__file__).parent
A = HIER / "assets"
DOMAIN = "https://xn--saraydner-57a.de/"  # saraydöner.de (Canonical)
CNAME = "saray.micana.de"
REPO = "michael-linuxdev/saray-doener"     # Chef-App speichert Änderungen in diesem Repo (daten/anpassungen.json)                  # Adresse der GitHub Page
VORSCHAU = True                            # True: Suchmaschinen sollen die Vorschau-Adresse nicht aufnehmen
ZAEHLER = "saraymicana"                            # GoatCounter-Kürzel (z. B. "saray-doener" für saray-doener.goatcounter.com); leer = kein Zählen

STANDORTE = [
    {
        "id": "freital", "name": "Freital", "strasse": "Dresdner Str. 87", "plz": "01705", "ort": "Freital",
        "tel": "0351 27676660", "tel_href": "+4935127676660", "tel_ld": "+49 351 27676660",
        "bar": True,  # nur Barzahlung
        "google": "ChIJi62UlB_FCUcRyZITkeCfe8Q",  # Google-Place-ID (Bewertungslink)
        "whatsapp": "4915733729521",  # vorerst Khan privat; später Laden-Handy Freital eintragen; leer: Knopf ausgeblendet
        "zeilen": [("Montag bis Freitag", "10–22 Uhr", [1, 2, 3, 4, 5]), ("Samstag und Sonntag", "11–22 Uhr", [6, 0])],
        "zeilen_en": ["Monday to Friday", "Saturday and Sunday"], "extra_en": "Outdoor seating in good weather.",
        "kurz": "Mo–Fr 10–22 Uhr, Sa–So 11–22 Uhr",
        "extra": "Bei schönem Wetter sitzen Sie draußen.",
        "lage": "an der Dresdner Straße",
    },
    {
        "id": "altenberg", "name": "Altenberg", "strasse": "Dresdner Str. 23", "plz": "01773", "ort": "Altenberg",
        "tel": "035056 23674", "tel_href": "+493505623674", "tel_ld": "+49 35056 23674",
        "bar": True,
        "google": "ChIJ7XWZiUmTCUcRxe2o2WmxkxQ",
        "whatsapp": "491601836249",  # Testnummer (Michael)
        "zeilen": [("Montag bis Samstag", "10–21 Uhr", [1, 2, 3, 4, 5, 6]), ("Sonntag", "11–21 Uhr", [0])],
        "zeilen_en": ["Monday to Saturday", "Sunday"], "extra_en": "Right by the station.",
        "kurz": "Mo–Sa 10–21 Uhr, So 11–21 Uhr",
        "extra": "Direkt am Bahnhof.",
        "lage": "direkt am Bahnhof",
    },
]


# Zug ab Altenberg (Müglitztalbahn RB 72 / RE 19 Richtung Heidenau–Dresden): Abholung passend zur Abfahrt.
# Quelle: DB-Kursbuch 246, gültig 14.12.2025–12.12.2026 (Stand 24.10.2025). Nach "gueltig_bis" blendet sich der
# Vorschlag von selbst aus, bis der neue Fahrplan hier eingetragen ist. Feiertage = Tage in "werktags_nicht".
ZUG = {
    "laden": "altenberg", "gueltig_bis": "2026-12-12", "puffer": 15,
    "taeglich": ["06:18", "08:18", "10:18", "12:18", "18:18", "20:18"],
    "werktags": ["04:18", "05:18", "07:18", "09:18", "11:18", "13:18", "14:18", "15:18", "16:18", "17:18", "19:18", "21:18"],
    "werktags_nicht": ["2025-12-25", "2025-12-26", "2026-01-01", "2026-04-03", "2026-04-06", "2026-05-01", "2026-05-14",
                       "2026-05-25", "2026-11-18"],
    "extra": [  # RE 19 nur am Wochenende in diesen Zeiträumen, dazu an einzelnen Tagen
        {"zeit": "15:18", "wochenende": [["2025-12-14", "2026-02-22"], ["2026-11-07", "2026-12-12"]],
         "auch": ["2025-12-25", "2025-12-26", "2026-01-01", "2026-11-18"]},
        {"zeit": "17:18", "wochenende": [["2026-02-28", "2026-11-01"]],
         "auch": ["2026-04-03", "2026-04-06", "2026-05-01", "2026-05-14", "2026-05-25"]},
    ],
}


def minuten(spanne):
    a, b = spanne.replace(" Uhr", "").split("–")
    return int(a) * 60, int(b) * 60


# Änderungen aus der Chef-App (daten/anpassungen.json) auf Speisekarte und Öffnungszeiten anwenden
import os
ANPASSUNGEN = ANP.laden(pathlib.Path(os.environ.get("SARAY_ANPASSUNGEN") or HIER / "daten" / "anpassungen.json"))
WARNUNGEN = []
STANDARD_GRUPPEN = GRUPPEN
GRUPPEN = ANP.karte(GRUPPEN, ANPASSUNGEN, WARNUNGEN.append)
ANZEIGE_NR = ANP.nummern(GRUPPEN, ANPASSUNGEN, WARNUNGEN.append)


def anz(nr):
    """angezeigte Nummer (Chef-App kann sie ändern); intern bleibt nr der Schlüssel"""
    return ANZEIGE_NR.get(nr, nr)

import datetime as _dt0, zoneinfo as _zi0
HEUTE_ISO = os.environ.get("SARAY_HEUTE") or _dt0.datetime.now(_zi0.ZoneInfo("Europe/Berlin")).date().isoformat()  # Tests setzen das Datum fest
SONDER = ANP.sonderzeiten(ANPASSUNGEN.get("sonderzeiten"), WARNUNGEN.append, HEUTE_ISO)
WARTE = ANP.wartezeit(ANPASSUNGEN.get("wartezeit"), WARNUNGEN.append)
CODES = ANP.codes(ANPASSUNGEN.get("codes"), WARNUNGEN.append, HEUTE_ISO)
WINTER = {"modus": ANP.winter(ANPASSUNGEN.get("winter"), WARNUNGEN.append), "von": ANP.WINTER_STANDARD[0], "bis": ANP.WINTER_STANDARD[1]}

for s in STANDORTE:
    std = {}
    for _, spanne, tage in s["zeilen"]:
        for t in tage:
            std[t] = minuten(spanne)
    s["zeiten_standard"] = std
    s["zeiten"] = ANP.zeiten(std, (ANPASSUNGEN.get("zeiten") or {}).get(s["id"]), WARNUNGEN.append, s["name"])
    s["zeilen_neu"] = ANP.zeilen(s["zeiten"])
    s["kurz"] = ", ".join(f'{z["kurz"]} {z["zeit"]}' for z in s["zeilen_neu"])
    s["sonder"] = [(tag, laeden[s["id"]]) for tag, laeden in SONDER.items() if s["id"] in laeden]
    s["maps"] = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote_plus(
        f"Saray Döner, {s['strasse']}, {s['plz']} {s['ort']}")

e = html.escape


def t(de, en, tag="span", cls=""):
    """Text mit englischer Fassung (wird per Sprachumschalter getauscht)."""
    k = f' class="{cls}"' if cls else ""
    return f'<{tag}{k} data-en="{e(en)}">{e(de)}</{tag}>'


# Dateien werden erst beim Bauen aufgelöst: eingebettet (data:-URL) oder als eigene Datei.
# Platzhalter: %%DATEI:<quelle relativ zu HIER>|<mime>|<ziel relativ zur Seite>%%
def b64(datei, mime):
    ordner = "fonts" if mime.startswith("font/") else "img"
    return f"%%DATEI:assets/{datei}|{mime}|{ordner}/{datei}%%"


MASKOTT = HIER / "maskottchen"   # erzeugt von maskottchen.py


def maskottchen(datei, mime):
    return f"%%DATEI:maskottchen/{datei}|{mime}|img/{datei}%%"


DATEI_RE = re.compile(r"%%DATEI:([^|%]+)\|([^|%]+)\|([^|%]+)%%")


def dateien_aufloesen(text, einzeln, ausgabe=None, praefix=""):
    def ersetze(m):
        quelle, mime, ziel = m.groups()
        if einzeln:
            return f"data:{mime};base64," + base64.b64encode((HIER / quelle).read_bytes()).decode()
        (ausgabe / ziel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(HIER / quelle, ausgabe / ziel)
        return praefix + ziel
    return DATEI_RE.sub(ersetze, text)


# ---------- Speisekarte ----------
def preis(p, klasse="preis", label=""):
    eur, ct = p.split(",")
    pre = f'<span class="sr-only">{e(label)}: </span>' if label else ""
    return (f'<span class="{klasse}">{pre}{eur}<span class="sr-only">,</span>'
            f'<span class="ct">{ct}</span><span class="sr-only"> Euro</span></span>')


O_ = "#3A1531"
_K = f'fill="none" stroke="{O_}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"'
_F = f'stroke="{O_}" stroke-width="2.6" stroke-linejoin="round"'
ICONS = {
    "doener": f'<path d="M8 22 C8 9 32 9 32 22 Z" fill="#C9873A" {_F}/><path d="M7 21 L10 14 L14 18 L17 11 L21 17 L25 11 L28 17 L33 14 L33 22 Z" fill="#5DB44C" {_F}/><path d="M6 21 C6 36 34 36 34 21 C26 24 14 24 6 21 Z" fill="#EFBE6C" {_F}/>',
    "duerum": f'<path d="M10 31 L26 7 C29 5 34 8 33 12 L17 35 C14 38 7 35 10 31 Z" fill="#EFBE6C" {_F}/><path d="M26 7 C29 5 34 8 33 12 C30 13 27 11 26 7 Z" fill="#5DB44C" {_F}/><path d="M14 27 L24 13" {_K}/>',
    "teller": f'<circle cx="20" cy="21" r="14" fill="#fff" {_F}/><path d="M11 22 C11 16 19 14 22 19 C24 24 18 28 13 26 Z" fill="#9C4F2B" {_F}/><path d="M23 14 L27 26 M26 13 L30 24" fill="none" stroke="#FFD21F" stroke-width="3.4" stroke-linecap="round"/>',
    "pizza": f'<path d="M6 10 C14 6 26 6 34 10 L20 35 Z" fill="#FFD27A" {_F}/><path d="M6 10 C14 6 26 6 34 10 L32 14 C24 10 16 10 8 14 Z" fill="#C9873A" {_F}/><circle cx="16" cy="17" r="2.8" fill="#C8371A"/><circle cx="24" cy="18" r="2.8" fill="#C8371A"/><circle cx="20" cy="25" r="2.6" fill="#C8371A"/>',
    "lahmacun": f'<circle cx="20" cy="20" r="14" fill="#E9A15A" {_F}/><circle cx="20" cy="20" r="9.5" fill="#D9603A"/><path d="M15 16 l3 2 M23 15 l-2 3 M24 23 l-3 -1 M16 24 l2 -2" stroke="#5DB44C" stroke-width="2.6" stroke-linecap="round"/>',
    "baguette": f'<path d="M7 27 C4 22 26 7 32 10 C37 13 15 34 7 27 Z" fill="#EFBE6C" {_F}/><path d="M13 23 l3 -5 M19 19 l3 -5 M25 15 l3 -4" {_K}/>',
    "salate": f'<path d="M7 17 C8 12 12 11 15 13 C16 8 23 8 25 12 C28 10 33 13 33 17 Z" fill="#5DB44C" {_F}/><path d="M5 18 H35 C35 28 28 33 20 33 C12 33 5 28 5 18 Z" fill="#fff" {_F}/><circle cx="17" cy="15" r="2.6" fill="#E4472F"/>',
    "schnitzel": f'<rect x="6" y="18" width="13" height="11" rx="5" fill="#E7A84B" {_F}/><rect x="19" y="20" width="14" height="11" rx="5" fill="#E7A84B" {_F}/><rect x="12" y="9" width="14" height="11" rx="5" fill="#E7A84B" {_F}/>',
    "kinder": f'<path d="M20 5 L24.5 14.5 L35 15.6 L27.2 22.6 L29.5 33 L20 27.7 L10.5 33 L12.8 22.6 L5 15.6 L15.5 14.5 Z" fill="#FFD21F" {_F}/><path d="M16.5 20.5 v1 M23.5 20.5 v1 M16.5 24.5 C18 26.5 22 26.5 23.5 24.5" {_K}/>',
    "getraenke": f'<path d="M11 13 H29 L26.5 35 H13.5 Z" fill="#C8371A" {_F}/><path d="M12 19 H28" stroke="#fff" stroke-width="2.6"/><path d="M20 13 L24 4 L29 4" {_K}/>',
}
EMPFEHLUNG = ["87", "1", "3", "26", "91", "125"]   # „Wir empfehlen“: alle gleich groß, ohne Koch
BELIEBT = ["52", "5", "58", "24", "84", "50", "23", "130", "100", "105", "124"]
# nur sichtbar, wenn „Vegetarisch“ oder „Pescetarisch“ eingeschaltet ist (Döner vegetarisch statt Döner Kebap usw.);
# Fischgerichte darunter (Pizza Tonno) erscheinen nur bei „Pescetarisch“
NUR_DIAET = {"87", "3", "52", "5", "58", "24", "84"}   # Reihenfolge wie vom Inhaber gewünscht; 23 = Döner-Teller mit Salat und Pommes
GERICHT = {g[0]: (g, gr, ab) for gr in GRUPPEN for ab in gr["abschnitte"] for g in ab["gerichte"] if g[0]}


D_NR = {"18", "19", "60", "61", "121", "123", "124"}


def gericht_typ(nr, gruppe, abschnitt):
    if abschnitt == "Pizza":
        return {"91": "S", "105": "R"}.get(nr, "P")
    if nr and (gruppe in ("Döner", "Dürüm") or abschnitt in ("Dönerbox", "Dönerteller") or nr in D_NR):
        return "D"
    if gruppe == "Salate":
        return "SA"
    if abschnitt == "Pizzabrötchen":
        return "B"
    return ""


# Fotos der Gerichte (Chef-App lädt sie nach daten/fotos/nr-<Nummer>.jpg hoch); hier verkleinert als WebP
FOTO_QUELLE = HIER / "daten" / "fotos"
FOTO_CACHE = HIER / ".fotos-cache"


def fotos_vorbereiten():
    fertig = set()
    if not FOTO_QUELLE.is_dir():
        return fertig
    try:
        from PIL import Image, ImageOps
    except ImportError:
        print("WARNUNG: Pillow fehlt – Fotos der Gerichte werden übersprungen")
        return fertig
    FOTO_CACHE.mkdir(exist_ok=True)
    for f in sorted(FOTO_QUELLE.glob("nr-*.jpg")):
        nr = f.stem[3:]
        try:
            for breite in (400, 800):
                ziel = FOTO_CACHE / f"nr-{nr}-{breite}.webp"
                if not ziel.exists() or ziel.stat().st_mtime < f.stat().st_mtime:
                    im = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
                    w, h = im.size   # auf 4:3 zuschneiden
                    if w / h > 4 / 3:
                        nw = int(h * 4 / 3); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
                    else:
                        nh = int(w * 3 / 4); im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
                    im.resize((breite, breite * 3 // 4), Image.LANCZOS).save(ziel, "WEBP", quality=78, method=6)
            fertig.add(nr)
        except Exception as fehler:   # ein kaputtes Foto darf die Seite nicht verhindern
            print(f"WARNUNG: Foto {f.name} nicht lesbar ({fehler})")
    return fertig


FOTOS = fotos_vorbereiten()


def foto(nr, breite):
    return f"%%DATEI:.fotos-cache/nr-{nr}-{breite}.webp|image/webp|img/gerichte/nr-{nr}-{breite}.webp%%"


def zettel_daten(nr, name, desc, preise, groessen, typ="", varianten=()):
    ne = (("No. " + anz(nr) + " ") if nr else "") + EN.name(name)
    cent = "|".join(str(int(x.replace(",", ""))) for x in preise)
    v = "|".join(f"{k}: {t}" for k, t in varianten)
    return (f' data-k="{e(nr or name)}" data-n="{e(("Nr. " + anz(nr) + " ") if nr else "")}{e(name)}" data-d="{e(desc)}"'
            f' data-p="{cent}" data-g="{e("|".join(groessen or []))}" data-t="{typ}" data-v="{e(v)}" data-ne="{e(ne)}" data-nen="{e(EN.name(name))}" data-dn="{e(EN.text(desc))}"')


def plus_knopf(name):
    return f'<button type="button" class="plus" aria-label="{e(name)} zur Bestellung hinzufügen" data-en-aria="Add {e(EN.name(name))} to my order">+</button>'


VEG_ICON = (' <svg class="veg" viewBox="0 0 24 24" role="img" aria-label="vegetarisch" data-en-aria="vegetarian"><title>vegetarisch</title>'
            '<path d="M5 19C5 10 11 5 20 4c0 9-5 15-14 15z" fill="#2E7D32"/><path d="M5 19c3-5 6-8 10-10" fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round"/></svg>')


FISCH_ICON = (' <svg class="veg" viewBox="0 0 24 24" role="img" aria-label="mit Fisch" data-en-aria="with fish"><title>mit Fisch</title>'
              '<path d="M2 12c3-5 9-6 14-3l5-3-1 6 1 6-5-3c-5 3-11 2-14-3z" fill="#1565C0"/><circle cx="7" cy="11" r="1.2" fill="#fff"/></svg>')


def gericht_html(g, gruppe, abschnitt, groessen):
    nr, name, desc, preise = g[:4]
    varianten = g[4] if len(g) > 4 else []
    suchtext = " ".join([anz(nr), name, desc, abschnitt, gruppe] + [v for _, v in varianten]
                        + [EN.name(name), EN.text(desc), EN.titel(abschnitt), EN.titel(gruppe)] + [EN.text(v) for _, v in varianten])
    beliebt = nr in BELIEBT and nr not in NUR_DIAET
    empfohlen = nr in EMPFEHLUNG and nr not in NUR_DIAET
    veg = (nr or name) in VEGETARISCH or gruppe == "Getränke" or "vegetarisch" in name.lower()
    fisch = (nr or name) in FISCH
    waehlbar = nr in VEG_WAEHLBAR
    teile = [f'<li class="gericht{" ist-beliebt" if beliebt or empfohlen else ""}"{f' id="nr-{nr}"' if nr else ""} data-s="{e(suchtext)}{" beliebt" if beliebt else ""}{" empfehlung" if empfohlen else ""}{" vegetarisch vegetarian" if veg else ""}{" pescetarisch pescetarian fisch fish" if fisch else ""}"{" data-veg" if veg or waehlbar else ""}{" data-fisch" if fisch else ""}{zettel_daten(nr, name, desc, preise, groessen, gericht_typ(nr, gruppe, abschnitt), varianten)}>']
    teile.append(f'<span class="nr">{chr(60) + "span class=" + chr(34) + "sr-only" + chr(34) + ">Nr. </span>" + e(anz(nr)) if nr else ""}</span>')
    teile.append(f'<span class="zeile"><span class="name">{t(name, EN.name(name))}{VEG_ICON if veg and gruppe != "Getränke" else ""}{FISCH_ICON if fisch else ""}{' <span class="marke-beliebt" data-en="Popular">Beliebt</span>' if beliebt else ""}{' <span class="marke-beliebt marke-empfehlung" data-en="Recommended">Empfehlung</span>' if empfohlen else ""}</span><span class="punkte" aria-hidden="true"></span></span>')
    if groessen:
        for i, p in enumerate(preise):
            teile.append(preis(p, f"preis p{i + 1}", groessen[i]))
    else:
        teile.append(preis(preise[0]))
    teile.append(plus_knopf(name))
    zusatz = GERICHT_ALLERGENE.get(nr)
    zusatz_html = ("".join(f' <span class="allergen-zusatz">{t("enthält " + ALLERGENE[x] + " (" + x + ")", "contains " + ALLERGENE_EN[x].lower() + " (" + x + ")")}</span>'
                           for x in zusatz.split(","))) if zusatz else ""
    bild = (f'<img class="gericht-foto" src="{foto(nr, 400)}" width="400" height="300" loading="lazy" decoding="async" alt="Foto: {e(name)}">'
            if nr in FOTOS else "")
    if desc or varianten or zusatz or bild:
        inner = bild + (t(desc, EN.text(desc)) if desc else "") + zusatz_html
        if varianten:
            inner += '<ul class="varianten">' + "".join(
                f"<li><b>{e(k)}</b> {t(v, EN.text(v))}</li>" for k, v in varianten) + "</ul>"
        teile.append(f'<div class="info">{inner}</div>')
    teile.append("</li>")
    return "".join(teile)


def kennzeichnung_html(zahlen, buchstaben):
    """Kurze Zeile „Inhaltsstoffe 1, 7 · Allergene a, b“ – Kürzel mit Erklärung, Klick führt zur Liste."""
    z = ", ".join(f'<abbr title="{e(ZUTATEN[n][0])}">{n}</abbr>' for n in zahlen.split(","))
    b = ", ".join(f'<abbr title="{e(ALLERGENE[x])}" data-en-title="{e(ALLERGENE_EN[x])}">{x}</abbr>' for x in buchstaben.split(","))
    return (f'<p class="kennz"><a href="#allergene" data-allergene>{t("Inhaltsstoffe", "Ingredients")} {z} · '
            f'{t("Allergene", "Allergens")} {b}</a></p>')


def allergene_html():
    zut = "".join(f'<li><b>{n} {e(name)}</b> – {e(text)}</li>' for n, (name, text) in ZUTATEN.items())
    leg = "".join(f'<li><b>{x}</b> = <span data-en="{e(ALLERGENE_EN[x])}">{e(name)}</span></li>' for x, name in ALLERGENE.items())
    return (
        '<details class="allergene" id="allergene">'
        f'<summary>{t("Zutaten und Allergene", "Ingredients and allergens")}</summary>'
        f'<p>{t("Jede Kategorie der Karte nennt ihre Inhaltsstoffe (Zahlen) und Allergene (Buchstaben).", "Each menu category lists its ingredients (numbers) and allergens (letters).")}</p>'
        f'<h4>{t("Allergene", "Allergens")}</h4><ul class="leg">{leg}</ul>'
        f'<h4>{t("Soßen", "Sauces")}</h4><p>{t("Alle Gerichte mit Soße nach Wahl: " + SOSSEN[0], "All dishes with sauce of your choice: garlic, herbs, chili")} – '
        f'{t("Inhaltsstoffe", "Ingredients")} {SOSSEN[1]} · {t("Allergene", "Allergens")} {", ".join(SOSSEN[2].split(","))}</p>'
        f'<h4>{t("Inhaltsstoffe", "Ingredients")}</h4><ul class="zut" lang="de">{zut}</ul>'
        f'<p>{t("Fragen Sie an der Theke nach Zutaten, Allergenen und Zusatzstoffen – unsere Allergiker-Speisekarte können Sie jederzeit einsehen.", "Ask at the counter about ingredients, allergens and additives – you can see our allergen menu at any time.")}</p>'
        '</details>')


def gruppe_html(gr):
    out = [f'<section class="gruppe" id="{gr["id"]}" aria-labelledby="g-{gr["id"]}">',
           f'<h3 class="band" id="g-{gr["id"]}"><svg class="band-icon" viewBox="0 0 40 40" aria-hidden="true">{ICONS[gr["id"]]}</svg>{t(gr["titel"], EN.titel(gr["titel"]))}</h3>']
    for ab in gr["abschnitte"]:
        groessen = ab.get("groessen")
        n = len(ab["gerichte"])
        out.append('<div class="abschnitt">')
        info = t(ab["info"], EN.titel(ab["info"]), cls="abschnitt-info") if ab.get("info") else ""
        if ab["titel"] == gr["titel"]:
            if info:
                out.append(f'<p class="abschnitt-titel solo">{info}</p>')
        else:
            out.append(f'<h4 class="abschnitt-titel">{t(ab["titel"], EN.titel(ab["titel"]))}{info}</h4>')
        if ab["titel"] in KENNZEICHNUNG:
            out.append(kennzeichnung_html(*KENNZEICHNUNG[ab["titel"]]))
        if groessen:
            kopf = "".join(f"<span>{e(x)}</span>" for x in groessen) + "<span></span>"
            out.append(f'<div class="groessen-kopf" aria-hidden="true"><div class="groessen"><span></span><span></span>{kopf}</div>'
                       f'<div class="groessen nur-breit"><span></span><span></span>{kopf}</div></div>')
        klasse = "liste zwei" if groessen else "liste"
        if not any(g[0] for g in ab["gerichte"]):
            klasse += " ohne-nr"
        out.append(f'<ul class="{klasse}" style="--zeilen:{math.ceil(n / 2)}">')
        zeilen = [gericht_html(g, gr["titel"], ab["titel"], groessen) for g in ab["gerichte"]]
        out += zeilen
        out.append("</ul>")
        if ab.get("notiz"):
            out.append(f'<p class="notiz" data-en="{e(EN.titel(ab["notiz"]))}">{e(ab["notiz"])}</p>')
        out.append("</div>")
    out.append("</section>")
    return "\n".join(out)


KARTE = "\n".join(gruppe_html(g) for g in GRUPPEN)


def beliebt_karte(nr, gross=False, koch=True):
    g, gr, ab = GERICHT[nr]
    name, desc, preise = g[1], g[2], g[3]
    zusatz = f" ({ab['groessen'][0]})" if ab.get("groessen") else ""
    veg = nr in VEGETARISCH or nr in VEG_WAEHLBAR or "vegetarisch" in name.lower()
    return (f'<li class="tipp{" tipp-gross" if gross else ""}{" ohne-koch" if gross and not koch else ""}"{" data-veg" if veg else ""}{" data-fisch" if nr in FISCH else ""}{" data-nur-diaet hidden" if nr in NUR_DIAET else ""}{zettel_daten(nr, name, desc, preise, ab.get("groessen"), gericht_typ(nr, gr["titel"], ab["titel"]), g[4] if len(g) > 4 else ())}><a href="#nr-{nr}">'
            + (f'<img class="tipp-foto" src="{foto(nr, 800)}" srcset="{foto(nr, 400)} 400w, {foto(nr, 800)} 800w" sizes="(min-width: 900px) 260px, 50vw" width="800" height="600" loading="lazy" decoding="async" alt="">' if nr in FOTOS else "") +
            f'<span class="tipp-nr"><span data-en="No.">Nr.</span> {e(anz(nr))}</span><b class="tipp-name" data-en="{e(EN.name(name))}">{e(name)}</b>'
            f'<span class="tipp-info" data-en="{e(EN.text(desc))}">{e(desc)}</span>'
            f'<span class="tipp-preis">{t("ab ", "from ") if zusatz else ""}{preis(preise[0])}</span>'
            + (f'<img class="tipp-koch" src="{maskottchen("saray-koch.svg", "image/svg+xml")}" width="430" height="470" alt="">' if gross and koch else "")
            + '</a>' + plus_knopf(name) + '</li>')


# gelöschte Gerichte fallen aus Empfehlung und „Beliebt“ heraus
BELIEBT = [n for n in BELIEBT if n in GERICHT]
BELIEBT_HTML = ('<section class="beliebt" aria-label="Empfehlungen">'
                + ('<h3 class="beliebt-titel" data-en="Our recommendation">Wir empfehlen</h3><ul class="tipps tipps-empfehlung">'
                   + "".join(beliebt_karte(n, True, False) for n in EMPFEHLUNG if n in GERICHT) + '</ul>'
                   if any(n in GERICHT for n in EMPFEHLUNG) else "") +
                '<h3 class="beliebt-titel" data-en="Popular with our guests">Beliebt bei unseren Gästen</h3>'
                '<ul class="tipps">' + "".join(beliebt_karte(n) for n in BELIEBT) + '</ul></section>')
NAV = "".join(f'<li><a href="#{g["id"]}" data-en="{e(EN.titel(g["titel"]))}">{e(g["titel"])}</a></li>' for g in GRUPPEN)
ANZAHL = sum(len(ab["gerichte"]) for g in GRUPPEN for ab in g["abschnitte"])
DOENER_PREIS = next((g[3][0] for gr in GRUPPEN for ab in gr["abschnitte"] for g in ab["gerichte"] if g[0] == "1"), None)

# ---------- Standorte ----------
TEL_ICON = ('<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 '
            '19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 '
            '2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></svg>')
PIN_ICON = ('<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>'
            '<circle cx="12" cy="10" r="3"/></svg>')
BAR_ICON = ('<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><rect x="2.5" y="6" width="19" height="12" rx="2"/>'
            '<circle cx="12" cy="12" r="2.6"/><path d="M6 9.5v5M18 9.5v5"/></svg>')
SUCH_ICON = ('<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/>'
             '<path d="M20 20l-4-4"/></svg>')


def status_html(s, klasse="status"):
    return (f'<p class="{klasse}" data-status="{s["id"]}"><span class="punkt" aria-hidden="true"></span>'
            f'<span class="status-text">{e(s["kurz"])}</span></p>')


STATUS_KARTEN = "\n".join(
    f'''<li class="schild">
  <p class="schild-ort"><a class="schild-link" href="#ort-{s["id"]}" data-en-aria="{e(s["name"])}: opening hours and directions" aria-label="{e(s["name"])}: Öffnungszeiten und Anfahrt">{e(s["name"])}</a></p>
  <p class="schild-adresse">{e(s["strasse"])}{t(" · nur Barzahlung", " · cash only") if s.get("bar") else ""}</p>
  {status_html(s)}
  <a class="schild-tel" href="tel:{s["tel_href"]}" aria-label="{e(s["name"])} anrufen: {e(s["tel"])}" title="{e(s["tel"])}">{TEL_ICON}</a>
</li>''' for s in STANDORTE)

def karte_html(s):
    alt = {"freital": "Stadtplan Freital-Potschappel: Saray Döner an der Dresdner Straße, Ecke Turnerstraße",
           "altenberg": "Stadtplan Altenberg: Saray Döner an der Dresdner Straße am Bahnhof"}[s["id"]]
    return (f'<figure class="karte-bild"><a href="{e(s["maps"])}" target="_blank" rel="noopener" aria-label="Route zu Saray Döner {e(s["name"])} planen">'
            f'<img src="{b64("karte_" + s["id"] + ".webp", "image/webp")}" srcset="{b64("karte_" + s["id"] + "_480.webp", "image/webp")} 480w, {b64("karte_" + s["id"] + ".webp", "image/webp")} 940w" sizes="(min-width: 900px) 460px, 100vw" width="940" height="680" loading="lazy" decoding="async" alt="{alt}">'
            f'<svg class="pin" viewBox="0 0 40 52" aria-hidden="true"><path d="M20 50 C20 50 4 31 4 19 a16 16 0 0 1 32 0 C36 31 20 50 20 50 Z" fill="#C8371A" stroke="#3A1531" stroke-width="3"/><circle cx="20" cy="19" r="6.5" fill="#fff"/></svg></a>'
            f'<figcaption>{t("Karte", "Map")}: © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>{t("-Mitwirkende", " contributors")}</figcaption></figure>')


def sonder_html(s):
    if not s["sonder"]:
        return ""
    zeilen = []
    for tag, wert in s["sonder"]:
        d = _dt0.date.fromisoformat(tag)
        de = f'{ANP.KURZ[(d.weekday() + 1) % 7]}, {d.day:02d}.{d.month:02d}.'
        en = f'{ANP.TAGE_EN[(d.weekday() + 1) % 7][:3]} {d.day} {d.strftime("%b")}'
        zeit = (f"{ANP.uhr(wert[0])}–{ANP.uhr(wert[1])} Uhr", f"{ANP.uhr(wert[0], True)}–{ANP.uhr(wert[1], True)}") if wert else ("geschlossen", "closed")
        zeilen.append(f'<li data-datum="{tag}"><b data-en="{e(en)}">{e(de)}</b> <span data-en="{e(zeit[1])}">{e(zeit[0])}</span></li>')
    return (f'<div class="sonder"><p>{t("Abweichende Öffnungszeiten", "Special opening hours")}</p><ul>' + "".join(zeilen) + '</ul></div>')


ORTE = "\n".join(
    f'''<article class="ort" id="ort-{s["id"]}" aria-labelledby="h-{s["id"]}">
  <h3 id="h-{s["id"]}">{e(s["name"])}</h3>
  {status_html(s)}
  <address>Saray Döner<br>{e(s["strasse"])}<br>{e(s["plz"])} {e(s["ort"])}<br>
  {t("Telefon", "Phone")} <a href="tel:{s["tel_href"]}">{e(s["tel"])}</a></address>
  {('<p class="bar">' + BAR_ICON + t("Nur Barzahlung", "Cash only") + '</p>') if s.get("bar") else ""}
  {karte_html(s)}
  <table class="zeiten"><caption class="sr-only">Öffnungszeiten {e(s["name"])}</caption><tbody>
  {"".join(f'<tr data-tage="{",".join(map(str, z["tage"]))}"><th scope="row" data-en="{e(z["en"])}">{e(z["de"])}</th><td data-en="{e(z["zeit_en"])}">{e(z["zeit"])}</td></tr>' for z in s["zeilen_neu"])}
  </tbody></table>
  {sonder_html(s)}
  <p class="ort-extra" data-en="{e(s["extra_en"])}">{e(s["extra"])}</p>
  <div class="knoepfe">
    <a class="knopf knopf-dunkel" href="tel:{s["tel_href"]}">{TEL_ICON}{t("Anrufen", "Call")}</a>
    <a class="knopf knopf-linie" href="{e(s["maps"])}" target="_blank" rel="noopener">{PIN_ICON}{t("Route planen", "Get directions")}</a>
  </div>
</article>''' for s in STANDORTE)

FUSS_ORTE = ('<div class="fuss-ort"><h2 data-en="Call to order ahead">Anrufen und vorbestellen</h2><p>' + "<br>".join(
    f'{e(st["name"])}: <a href="tel:{st["tel_href"]}">{e(st["tel"])}</a>' for st in STANDORTE) +
    '</p><p class="klein"><a href="#standorte" data-en="Addresses and opening hours">Adressen und Öffnungszeiten</a></p></div>')


TAGE_EN = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
LD = {
    "@context": "https://schema.org",
    "@graph": [{
        "@type": "Restaurant",
        "@id": DOMAIN + "#ort-" + s["id"],
        "name": "Saray Döner " + s["name"],
        "url": DOMAIN,
        "telephone": s["tel_ld"],
        "servesCuisine": ["Döner", "Pizza", "Türkisch"],
        "priceRange": "€",
        **({"paymentAccepted": "Cash", "currenciesAccepted": "EUR"} if s.get("bar") else {}),
        "hasMenu": DOMAIN + "#speisekarte",
        "address": {"@type": "PostalAddress", "streetAddress": s["strasse"], "postalCode": s["plz"],
                    "addressLocality": s["ort"], "addressCountry": "DE"},
        "openingHoursSpecification": [{
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": [TAGE_EN[t] for t in z["tage"]],
            "opens": f"{z['wert'][0] // 60:02d}:{z['wert'][0] % 60:02d}", "closes": f"{z['wert'][1] // 60:02d}:{z['wert'][1] % 60:02d}"}
            for z in s["zeilen_neu"] if z["wert"]],
        **({"specialOpeningHoursSpecification": [{
            "@type": "OpeningHoursSpecification", "validFrom": tag, "validThrough": tag,
            "opens": f"{w[0] // 60:02d}:{w[0] % 60:02d}" if w else "00:00",
            "closes": f"{w[1] // 60:02d}:{w[1] % 60:02d}" if w else "00:00"} for tag, w in s["sonder"]]} if s["sonder"] else {}),
    } for s in STANDORTE],
}
JS_ZEITEN = json.dumps({s["id"]: {str(k): list(v) for k, v in s["zeiten"].items()} for s in STANDORTE})
JS_SONDER = json.dumps({s["id"]: {tag: (list(w) if w else None) for tag, w in s["sonder"]} for s in STANDORTE})
JS_WARTE = json.dumps(WARTE)

FAVICON = ("data:image/svg+xml," + urllib.parse.quote(
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><circle cx='32' cy='32' r='30' fill='#C8371A'/>"
    "<circle cx='32' cy='32' r='25' fill='none' stroke='#fff' stroke-width='3'/>"
    "<text x='32' y='43' text-anchor='middle' font-family='Georgia,serif' font-weight='700' font-size='30' fill='#fff'>S</text></svg>"))

CSS = r"""
@font-face{font-family:"Saray Slab";src:url(%%SLAB_B%%) format("woff");font-weight:700;font-display:swap}
@font-face{font-family:"Saray Slab";src:url(%%SLAB_R%%) format("woff");font-weight:400;font-display:swap}
@font-face{font-family:"Saray Text";src:url(%%LATO_R%%) format("woff");font-weight:400;font-display:swap}
@font-face{font-family:"Saray Text";src:url(%%LATO_B%%) format("woff");font-weight:700;font-display:swap}

:root{
  --gelb:#FFD21F; --gelb-blass:#FFF3C2;
  --tinte:#3A1531; --tinte-weich:#6B4A62; --tinte-tief:#2A0E23;
  --paprika:#C8371A; --gruen:#1E7B3C; --weiss:#fff;
  --linie:rgba(58,21,49,.16);
  --slab:"Saray Slab","Roboto Slab",Rockwell,Georgia,serif;
  --text:"Saray Text",Lato,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  --breite:1160px; --rand:16px;
}
@media (min-width:720px){:root{--rand:28px}}
@media (min-width:1100px){:root{--rand:40px}}

*,*::before,*::after{box-sizing:border-box}
[hidden]{display:none!important}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{margin:0;background:var(--weiss);color:var(--tinte);font:400 1.0625rem/1.55 var(--text);
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
img{display:block;max-width:100%;height:auto}
a{color:inherit}
h1,h2,h3,h4{font-family:var(--slab);font-weight:700;line-height:1.1;margin:0}
p{margin:0}
.wrap{max-width:var(--breite);margin-inline:auto;padding-inline:var(--rand)}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.tuete{margin-right:2px}
.zettel-kopf h2{display:flex;align-items:center;gap:8px}
.zettel-kopf h2 .tuete{width:.9em;height:.9em;stroke-width:2.4}
.ico{width:1.15em;height:1.15em;flex:none;fill:none;stroke:currentColor;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}
:focus-visible{outline:3px solid var(--tinte);outline-offset:3px;border-radius:6px}
.skip{position:absolute;left:12px;top:-80px;z-index:50;background:var(--tinte);color:var(--gelb);padding:10px 16px;border-radius:10px;font-weight:700}
.skip:focus{top:12px}

/* Knöpfe */
.knopf{display:inline-flex;align-items:center;justify-content:center;gap:.5em;min-height:50px;padding:0 22px;border-radius:999px;
  font:700 1.02rem/1.1 var(--text);text-decoration:none;border:2px solid transparent;transition:background-color .15s}
.knopf-dunkel{background:var(--tinte);color:var(--gelb)}
.knopf-dunkel:hover{background:var(--tinte-tief)}
.knopf-linie{border-color:var(--tinte);color:var(--tinte);background:transparent}
.knopf-linie:hover{background:var(--gelb-blass)}

/* ---------- Leuchtkasten (Kopf + Bühne) ---------- */
.kopf-band{background:var(--gelb)}
.buehne-band{background-color:var(--gelb);
  background-image:radial-gradient(ellipse 60% 58% at 27% 54%,rgba(255,255,255,.45),rgba(255,255,255,0) 70%);
  border-bottom:6px solid var(--tinte);overflow:hidden}
.seitenkopf{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-block:14px}
.marke{display:flex;align-items:center;gap:10px;text-decoration:none}
.logo{display:block;flex:none;width:58px;height:58px}
.marke-text{display:flex;flex-direction:column}
.marke-text b{font:700 1.12rem/1.1 var(--slab)}
.marke-text small{font-size:.85rem;color:var(--tinte-weich)}
.kopf-nav{display:flex;gap:4px}
.kopf-nav a{font-weight:700;text-decoration:none;padding:10px 12px;border-radius:999px}
.kopf-nav a:hover{background:rgba(255,255,255,.55)}
@media (max-width:479px){.kopf-nav a+a{display:none}}
.kopf-nav{align-items:center}
.sprache-wahl{position:relative;display:inline-block}
.sprachen-menu{position:absolute;right:0;top:calc(100% + 6px);z-index:70;list-style:none;margin:0;padding:6px;min-width:150px;background:#fff;border:2px solid var(--tinte);border-radius:14px;box-shadow:0 10px 24px -10px rgba(58,21,49,.5)}
[dir=rtl] .sprachen-menu{right:auto;left:0}
.sprachen-menu button{display:block;width:100%;min-height:42px;padding:0 12px;border:0;border-radius:10px;background:none;color:var(--tinte);font:700 1rem var(--text);text-align:start;cursor:pointer}
.sprachen-menu button[aria-current=true]{background:var(--gelb)}
.sprachen-menu button:hover{background:var(--gelb-blass)}
.sprache{min-width:44px;min-height:40px;margin-left:4px;border:2px solid var(--tinte);border-radius:999px;background:transparent;color:var(--tinte);
  font:700 .85rem var(--text);letter-spacing:.06em;cursor:pointer}
.sprache:hover{background:rgba(255,255,255,.55)}
.hinweis-band{background:var(--paprika);color:#fff;font-weight:700;text-align:center}
.hinweis-band p{margin:0 auto;padding:10px 16px;line-height:1.4}
.letzte{margin:0 0 22px;padding:18px 20px;border:2px dashed var(--tinte);border-radius:14px;background:var(--gelb-blass)}
.letzte h3{margin:0 0 6px;font:700 1.15rem var(--slab)}
.letzte-liste{margin:0 0 12px;line-height:1.5}

.buehne{display:grid;gap:32px;padding-block:8px 44px}
.buehne h1{font-size:clamp(2.75rem,1.45rem + 6.2vw,5.6rem);line-height:.98;letter-spacing:-.025em;text-wrap:balance;margin-bottom:18px}
.lead{font-size:clamp(1.1rem,1rem + .45vw,1.32rem);line-height:1.45;max-width:34ch;margin-bottom:24px}

.schilder{list-style:none;margin:0 0 24px;padding:0;display:grid;gap:12px}
@media (min-width:560px){.schilder{grid-template-columns:1fr 1fr}}
.schild{display:grid;grid-template-columns:minmax(0,1fr) auto;grid-template-areas:"ort tel" "adr tel" "status status";
  column-gap:12px;background:#fff;border:2px solid var(--tinte);border-radius:16px;padding:14px 14px 14px 16px}
.schild-ort{grid-area:ort;font:700 1.3rem/1.15 var(--slab)}
/* ganze Karte führt zu Öffnungszeiten und Anfahrt (Telefon-Knopf bleibt eigener Link) */
.schild{position:relative;cursor:pointer}
.schild-link{color:inherit;text-decoration:none}
.schild-link::after{content:"";position:absolute;inset:0;border-radius:inherit}
.schild-link:focus-visible{outline:none}
.schild:has(.schild-link:focus-visible){outline:3px solid var(--paprika);outline-offset:3px}
@media (hover:hover){.schild:has(.schild-link:hover){box-shadow:0 8px 20px -10px rgba(58,21,49,.45)}}
.schild-tel{position:relative;z-index:1}
.ort{scroll-margin-top:16px}
.schild-adresse{grid-area:adr;color:var(--tinte-weich);font-size:.98rem}
.schild .status{grid-area:status;margin-top:8px}
.schild-tel{grid-area:tel;align-self:center;display:grid;place-items:center;width:52px;height:52px;border-radius:50%;
  background:var(--tinte);color:var(--gelb);font-size:1.15rem}
.schild-tel:hover{background:var(--tinte-tief)}

.status{display:flex;align-items:center;gap:8px;font-weight:700;font-size:.97rem;line-height:1.3}
.punkt{width:10px;height:10px;border-radius:50%;flex:none;background:var(--tinte-weich)}
.status[data-offen="ja"] .punkt{background:var(--gruen);box-shadow:0 0 0 3px rgba(30,123,60,.22)}
.status[data-offen="nein"] .punkt{background:var(--paprika)}
.status[data-offen="bald"] .punkt{background:#E8A317;box-shadow:0 0 0 3px rgba(232,163,23,.25)}

/* Foto mit Koch */
.bilder{position:relative;max-width:540px;margin:4px 0 30px}
.foto{margin:0;background:#fff;border:5px solid #fff;border-radius:16px;overflow:hidden;
  box-shadow:0 18px 30px -18px rgba(58,21,49,.55),0 0 0 1px rgba(58,21,49,.12)}
.foto img{width:100%;border-radius:11px}
.koch{position:absolute;z-index:2;right:-10px;bottom:-30px;width:40%;filter:drop-shadow(0 8px 9px rgba(58,21,49,.3))}
.sticker{position:absolute;z-index:3;top:-16px;left:-8px;width:92px;height:92px;border-radius:50%;background:var(--paprika);color:#fff;
  display:grid;place-content:center;text-align:center;transform:rotate(-10deg);box-shadow:0 8px 16px -8px rgba(58,21,49,.6);
  animation:klatsch .55s .35s cubic-bezier(.2,.9,.25,1.2) both}
.sticker small{font:700 .72rem/1.1 var(--text);letter-spacing:.01em}
.sticker b{font:700 2.3rem/1 var(--slab);letter-spacing:-.02em}
.sticker .ct{font-size:.46em;position:relative;top:-.95em;margin-left:.04em;text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:2px}
@keyframes klatsch{0%{opacity:0;transform:rotate(-24deg) scale(1.7)}70%{opacity:1;transform:rotate(-8deg) scale(.95)}100%{transform:rotate(-10deg) scale(1)}}

@media (min-width:960px){
  .buehne{grid-template-columns:minmax(0,11fr) minmax(0,10fr);gap:48px;align-items:center;padding-block:28px 72px}
  .bilder{max-width:none;margin:0 0 20px}
  .koch{right:-24px;bottom:-40px;width:45%}
  .sticker{top:-28px;left:-28px;width:112px;height:112px}
  .sticker small{font-size:.8rem}
  .sticker b{font-size:2.85rem}
}

/* ---------- Speisekarte ---------- */
.band-icon{width:1.45em;height:1.45em;flex:none;margin:-4px 0}
.buehne-text{position:relative}
.koch-klein{position:absolute;right:-4px;top:40px;width:100px;filter:drop-shadow(0 6px 7px rgba(58,21,49,.25))}
@media (max-width:959px){.bilder .koch{display:none}}
@media (min-width:600px) and (max-width:959px){.koch-klein{width:150px;top:20px}}
@media (min-width:960px){.koch-klein{display:none}}
[dir=rtl] .koch-klein{right:auto;left:-4px}
@media (max-width:599px){[dir=rtl] .lead{padding-left:92px}}
@media (min-width:600px) and (max-width:959px){[dir=rtl] .lead{padding-left:140px}}
[dir=rtl] address{unicode-bidi:plaintext;text-align:right}
[dir=rtl] .preis,[dir=rtl] .z-preis,[dir=rtl] #zettel-summe,[dir=rtl] .zl-summe,[dir=rtl] a[href^="tel:"]:not(.knopf),[dir=rtl] time{unicode-bidi:isolate;direction:ltr}
[dir=rtl] .koch{right:auto;left:-10px}
[dir=rtl] .sticker{left:auto;right:-8px}
@media (min-width:960px){[dir=rtl] .koch{left:-24px}[dir=rtl] .sticker{right:-28px}}
.marke-beliebt{display:inline-block;vertical-align:2px;margin-left:6px;padding:1px 8px;border-radius:999px;background:var(--paprika);color:#fff;
  font:700 .7rem/1.5 var(--text);letter-spacing:.01em;white-space:nowrap}
.beliebt{margin-bottom:40px;min-width:0;max-width:100vw}
.mittag{margin-bottom:28px;min-width:0;max-width:100vw}.mittag-zeit{margin:-6px 0 10px;color:var(--tinte-weich);font-weight:700}body.sucht .mittag{display:none}
.karte-inhalt{min-width:0}
.tipps{width:calc(100% + 2 * var(--rand));position:relative}
.beliebt-titel{font-size:1.35rem;margin-bottom:12px}
.tipps{list-style:none;margin:0 calc(-1 * var(--rand));padding:4px var(--rand) 12px;display:flex;gap:12px;overflow-x:auto;scroll-snap-type:x mandatory;scroll-padding-inline:var(--rand);scrollbar-width:thin}
.tipp{flex:0 0 200px;scroll-snap-align:start;display:flex;flex-direction:column;border:2px solid var(--tinte);border-radius:16px;background:#fff}
.tipp a{display:flex;flex-direction:column;gap:4px;flex:1;padding:14px 16px;border-radius:14px;text-decoration:none}
.tipp-foto{display:block;width:calc(100% + 32px);max-width:none;height:auto;aspect-ratio:4/3;object-fit:cover;margin:-14px -16px 6px;border-radius:13px 13px 0 0}
.tipps-empfehlung .ohne-koch .tipp-foto{width:calc(100% + 28px);margin:-14px -14px 6px}
.gericht-foto{float:right;width:84px;height:63px;object-fit:cover;border-radius:8px;margin:2px 0 4px 10px}
@media (hover:hover){.tipp:hover{background:var(--gelb-blass)}.tipp-gross:hover{background:#FFDB4D}}
.tipp-gross{flex-basis:100%}
.tipps-empfehlung{overflow:visible;margin-bottom:22px;flex-wrap:wrap}
.tipp-gross.ohne-koch a{padding-right:20px;min-height:0}
.tipps-empfehlung .ohne-koch{flex-basis:calc(50% - 6px);min-width:0}
.tipps-empfehlung .ohne-koch a{padding:14px 14px 16px}
.tipps-empfehlung .ohne-koch .tipp-name{font-size:1.2rem}
.tipps-empfehlung .ohne-koch .tipp-info{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;flex:none;max-height:2.7em;margin-bottom:auto}
.tipp-gross a{position:relative;padding:18px 120px 18px 20px;min-height:150px}
.tipp-koch{position:absolute;right:10px;bottom:6px;width:104px}
@media (min-width:700px){.tipp-gross a{padding-right:190px}.tipp-koch{width:150px;right:24px;bottom:4px}}
.tipp-gross .tipp-preis .preis{font-size:1.7rem}
.marke-empfehlung{background:var(--tinte);color:var(--gelb)}
.tipp-gross{background:var(--gelb)}

.tipp-nr{font-weight:700;font-size:.8rem;color:var(--tinte-weich)}
.tipp-name{font:700 1.1rem/1.2 var(--slab)}
.tipp-gross .tipp-name{font-size:1.6rem}
.tipp-info{font-size:.88rem;line-height:1.35;color:var(--tinte-weich);flex:1}
.tipp-preis .preis{font-size:1.35rem}
.gericht.ist-beliebt{scroll-margin-top:90px}
@media (min-width:1100px){.tipps{width:auto;margin:0;padding:4px 0 12px;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));overflow:visible}
  .tipps-empfehlung{grid-template-columns:repeat(4,minmax(0,1fr))}
  .tipp-gross{grid-column:1/-1}.tipp-gross.ohne-koch{grid-column:auto}.gericht.ist-beliebt{scroll-margin-top:24px}}
@media (max-width:559px){
  .gericht{padding-block:5px}
  .info{font-size:.88rem;line-height:1.35;margin-top:1px}
  .zwei .punkte{display:none}
  .abschnitt+.abschnitt{margin-top:22px}
  .gruppe{margin-bottom:34px}
}
.karte{padding-block:52px 72px}
.abschnitt-kopf h2,.standorte h2{font-size:clamp(2.2rem,1.6rem + 2.4vw,3.4rem);letter-spacing:-.02em;margin-bottom:14px}
.karte-kopf p{max-width:62ch;color:var(--tinte-weich);margin-bottom:6px}
.karte-kopf a{font-weight:700;color:var(--tinte)}
.karte-layout{margin-top:28px}
.suche{margin-bottom:12px}
.suche label{display:block;font-weight:700;margin-bottom:6px}
.suche-feld{position:relative;max-width:520px}
.suche-feld .ico{position:absolute;left:16px;top:50%;transform:translateY(-50%);color:var(--tinte-weich);pointer-events:none}
.suche input{width:100%;min-height:50px;border:2px solid var(--tinte);border-radius:999px;padding:0 18px 0 46px;
  font:400 1.02rem var(--text);color:var(--tinte);background:#fff;-webkit-appearance:none;appearance:none}
.veg-schalter{display:inline-flex;align-items:center;gap:6px;margin-top:10px;min-height:44px;padding:0 16px;border-radius:999px;border:2px solid var(--tinte);
  background:#fff;color:var(--tinte);font:700 .95rem var(--text);cursor:pointer}
.veg-schalter svg{width:18px;height:18px}
.veg-schalter[aria-pressed=true]{background:#2E7D32;border-color:#2E7D32;color:#fff}.veg-schalter[aria-pressed=true] path{fill:#fff}.veg-schalter.pesc[aria-pressed=true]{background:#1565C0;border-color:#1565C0}.diaet{display:flex;flex-wrap:wrap;gap:8px}
@media (max-width:719px){.diaet{display:grid;grid-template-columns:1fr 1fr;gap:10px}.diaet .veg-schalter{justify-content:center;width:100%;min-width:0;padding:0 10px}}
svg.veg{width:.95em;height:.95em;vertical-align:-.1em;margin-left:2px}
.suche input::placeholder{color:#8d7486}
.suche input::-webkit-search-cancel-button{-webkit-appearance:none;appearance:none;width:20px;height:20px;cursor:pointer;background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%233A1531' stroke-width='2.6' stroke-linecap='round'%3E%3Cpath d='M6 6l12 12M18 6L6 18'/%3E%3C/svg%3E") center/contain no-repeat}
.suche input:focus-visible{outline:3px solid var(--tinte);outline-offset:2px;box-shadow:0 0 0 7px var(--gelb)}

.kategorien{position:sticky;top:0;z-index:20;background:#fff;margin-inline:calc(-1 * var(--rand));
  padding:10px 0;border-bottom:1px solid var(--linie);margin-bottom:24px}
/* iOS 26 Safari zeigt über dem Sichtbereich (unter der gläsernen Adressleiste) die Seite durchscheinend.
   Solange das Kategorie-Band oben klebt, deckt eine feste weiße Fläche direkt oberhalb des Sichtbereichs das ab;
   im oberen Teil der Seite (Bild, Läden) darf es durchscheinen. */
.kat-marke{height:0}
/* Safari 26 färbt den Bereich unter der gläsernen Adressleiste nach festen Elementen am oberen Rand ein.
   Solange das Band klebt, liegt deshalb eine feste weiße Fläche genau dahinter. */
.deckel-oben{position:fixed;top:0;left:0;right:0;background:#fff;z-index:19;pointer-events:none}
/* Gegenstück, solange das Band nicht klebt: bildschirmfüllende, praktisch unsichtbare Ebene (wie früher das Wasserzeichen).
   Ohne festes Element nimmt Safari 26 (große Adressleiste) die Hintergrundfarbe – Weiß statt Glas. */
.glas-oben{position:fixed;inset:0;z-index:90;pointer-events:none;opacity:.02;
  background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='420' height='300'%3E%3Ctext x='210' y='160' text-anchor='middle' transform='rotate(-30 210 150)' font-family='Arial,sans-serif' font-weight='700' font-size='30' fill='%23C8371A'%3E%C2%B7%3C/text%3E%3C/svg%3E") repeat}
.app-tipp{opacity:.8}
/* Kontrast: Rot auf Gelb ist zu schwach (3,6:1) – auf gelben Karten dunkleres Rot (5,2:1) */
.tipp-gross .preis,.tipp-gross .tipp-preis{color:#9E2A10}
/* Linkshänder-Modus (nur Handy): Plus und Mengen-Regler der Speisekarte auf die linke Seite.
   Nach-oben-Pfeil ebenfalls links. Karten (Empfehlung/Beliebt) und Bestellzettel bleiben unverändert. */
.hand-knopf{background:none;border:0;padding:6px 0;min-height:32px;color:inherit;font:inherit;text-decoration:underline;text-underline-offset:3px;cursor:pointer}
.fuss-hand{margin:0}
/* Sammelbestellung */
.sammel-start{margin:12px 0 0;text-align:center}
.knopf-sammel{min-height:44px;padding:0 18px;font-size:.98rem;white-space:nowrap}
/* Teilnehmer einer Sammelbestellung: Laden, Tag und Uhrzeit wählt der Sammler */
.im-sammel .abholung legend,.im-sammel .abholung .z-chips,.im-sammel label[for=abhol-tag],.im-sammel #abhol-tag,
.im-sammel label[for=abhol-zeit],.im-sammel #abhol-zeit,.im-sammel #abhol-hinweis,.im-sammel #wa-hinweis,.im-sammel .zettel-hinweis,
.im-sammel #verf-hinweis,.im-sammel [data-anruf]{display:none!important}
.sammel-band{display:flex;gap:10px;align-items:center;justify-content:space-between;margin-top:12px;padding:10px 12px;border-radius:12px;background:var(--gelb-blass);border:2px solid var(--tinte)}
.sammel-band p{margin:0;font-weight:700;line-height:1.35}
.z-fuer{display:inline-block;margin-top:2px;padding:0 8px;border-radius:999px;background:var(--gelb-blass);font-size:.82rem;font-weight:700}
.sammel-dialog{position:fixed;inset:0;z-index:90;background:rgba(58,21,49,.5);display:flex;align-items:center;justify-content:center}
/* Handy: oben statt unten – so verdeckt die Tastatur das Feld nicht und nichts muss nachgeschoben werden */
@media (max-width:719px){.sammel-dialog{align-items:flex-start;padding:calc(12px + env(safe-area-inset-top)) 10px 0}.sammel-box{border-radius:20px!important;max-height:calc(100% - 24px)}}
.sammel-box:focus{outline:none}
.sammel-box{background:#fff;width:100%;max-width:520px;max-height:90%;overflow:auto;border-radius:20px 20px 0 0;padding:20px 18px calc(18px + env(safe-area-inset-bottom))}
@media (min-width:720px){.sammel-box{border-radius:20px}}
.sammel-box h2{margin:0 0 8px;font-size:1.3rem}
.sammel-box label{display:block;font-weight:700;margin:12px 0 4px}
.sammel-box input{width:100%;min-height:46px;border:2px solid var(--tinte);border-radius:12px;padding:0 12px;font:inherit}
.sammel-liste{margin:6px 0;padding-left:18px}
.sammel-summe{font-weight:700}
.sammel-knoepfe{display:flex;flex-wrap:wrap;gap:10px;margin-top:16px}
@media (min-width:720px){.fuss-hand{display:none}}
/* einmaliger Hinweis beim ersten „+“ (nur Handy) */
.hand-tipp{position:fixed;left:10px;right:10px;bottom:calc(80px + env(safe-area-inset-bottom));z-index:71;background:var(--tinte);color:#fff;
  border-radius:16px;padding:12px 14px;box-shadow:0 12px 28px -12px rgba(58,21,49,.7)}
.hand-tipp p{margin:0 0 10px;line-height:1.4}
.hand-tipp p b{color:var(--gelb)}
.hand-tipp div{display:flex;flex-wrap:wrap;gap:8px}
.hand-tipp button{min-height:42px;padding:0 16px;border-radius:999px;border:2px solid var(--gelb);background:var(--gelb);color:var(--tinte);font:700 .95rem var(--text);cursor:pointer}
.hand-tipp button.zweit{background:transparent;color:#fff;border-color:rgba(255,255,255,.55)}
@media (max-width:719px){
  html.links .gericht{grid-template-columns:2.6rem 2.2rem minmax(0,1fr) auto;grid-template-areas:"plus nr zeile p1" ". . info ."}
  html.links .ohne-nr .gericht{grid-template-columns:2.6rem minmax(0,1fr) auto;grid-template-areas:"plus zeile p1" ". info ."}
  html.links .zwei .gericht{grid-template-columns:2.6rem 2.2rem minmax(0,1fr) 3rem 3rem;grid-template-areas:"plus nr zeile p1 p2" ". . info . ."}
  html.links .zwei .groessen{grid-template-columns:2.6rem 2.2rem minmax(0,1fr) 3rem 3rem}
  html.links .plus{justify-self:start}
  html.links .mengen{justify-content:flex-start}
  html.links .nach-oben{right:auto;left:14px}
}
.vorschau-band .stand{opacity:.7;white-space:nowrap}
#debug-info{position:fixed;left:8px;bottom:90px;z-index:95;max-width:70vw;padding:6px 8px;border-radius:8px;background:rgba(0,0,0,.8);color:#0f0;font:11px/1.35 ui-monospace,Menlo,monospace;white-space:pre;pointer-events:none}
/* klebt das Band oben: Bereich darüber (Statusleiste/Notch) weiß statt durchscheinender Seite */

.kategorien ul{list-style:none;margin:0;padding:0 var(--rand);display:flex;gap:8px;overflow-x:auto;scrollbar-width:none;
  scroll-padding-inline:var(--rand);-webkit-mask-image:linear-gradient(90deg,#000 calc(100% - 36px),transparent);
  mask-image:linear-gradient(90deg,#000 calc(100% - 36px),transparent)}
.kategorien ul::-webkit-scrollbar{display:none}
.kategorien li{flex:none}
.kategorien a{display:block;padding:8px 15px;border:2px solid var(--tinte);border-radius:999px;font:700 .95rem/1.2 var(--text);
  text-decoration:none;white-space:nowrap;background:#fff}
.kategorien a[aria-current="true"]{background:var(--tinte);color:var(--gelb)}
.kategorien a.leer{opacity:.35}

.karte-seite{display:contents}
.treffer{font-weight:700;margin-bottom:16px}
.nichts{border:2px dashed var(--linie);border-radius:16px;padding:28px 20px;text-align:center;margin-bottom:24px}
.nichts p{margin-bottom:14px;font-weight:700}

.gruppe{scroll-margin-top:76px;margin-bottom:44px}
.band{display:flex;align-items:center;gap:12px;background:var(--gelb);font-size:clamp(1.5rem,1.3rem + .8vw,2rem);letter-spacing:-.01em;padding:11px 18px 12px;border-radius:12px;margin-bottom:18px}
.abschnitt+.abschnitt{margin-top:30px}
.abschnitt-titel{display:flex;flex-wrap:wrap;align-items:baseline;gap:2px 12px;font-size:1.22rem;margin-bottom:8px}
.abschnitt-titel.solo{margin-bottom:6px}
.abschnitt-info{font:400 .95rem/1.4 var(--text);color:var(--tinte-weich)}
.notiz{margin-top:12px;padding-left:12px;border-left:4px solid var(--gelb);color:var(--tinte-weich);font-size:.97rem}

.liste{list-style:none;margin:0;padding:0}
.gericht{display:grid;grid-template-columns:2.2rem minmax(0,1fr) auto 2.6rem;grid-template-areas:"nr zeile p1 plus" ". info . .";align-content:start;break-inside:avoid;
  column-gap:8px;align-items:baseline;padding-block:8px}
.nr{grid-area:nr;font:700 .82rem/1 var(--text);color:var(--tinte-weich);font-variant-numeric:tabular-nums}
.zeile{grid-area:zeile;display:flex;align-items:baseline;gap:8px;min-width:0}
.name{font:700 1.06rem/1.3 var(--slab)}
.punkte{flex:1 1 auto;min-width:14px;border-bottom:2px dotted rgba(58,21,49,.32);transform:translateY(-.3em)}
.preis{grid-area:p1;font:700 1.28rem/1 var(--slab);color:var(--paprika);white-space:nowrap;text-align:right;letter-spacing:-.01em}
.preis .ct{font-size:.56em;position:relative;top:-.62em;margin-left:.04em;text-decoration:underline;text-decoration-thickness:1.5px;text-underline-offset:2px}
.info{grid-area:info;font-size:.93rem;line-height:1.4;color:var(--tinte-weich);margin-top:3px}
.ohne-nr .gericht{grid-template-columns:minmax(0,1fr) auto 2.6rem;grid-template-areas:"zeile p1 plus" "info . ."}
.ohne-nr .nr{display:none}
.varianten{list-style:none;margin:4px 0 0;padding:0;display:grid;gap:2px}
.varianten b{display:inline-block;min-width:1.3em;font-family:var(--slab);color:var(--tinte)}

.zwei .gericht{grid-template-columns:2.2rem minmax(0,1fr) 3rem 3rem 2.6rem;grid-template-areas:"nr zeile p1 p2 plus" ". info . . ."}
.zwei .p2{grid-area:p2}
.groessen{display:grid;grid-template-columns:2.2rem minmax(0,1fr) 3rem 3rem 2.6rem;column-gap:8px;
  font-weight:700;font-size:.82rem;color:var(--tinte-weich);text-align:right;padding-bottom:6px;border-bottom:2px solid var(--tinte)}
.groessen-kopf .nur-breit{display:none}

.allergene{margin-top:8px;background:var(--gelb-blass);border-radius:14px;padding:4px 18px;max-width:70ch;font-size:.97rem;scroll-margin-top:90px}.allergene summary{cursor:pointer;font-weight:700;padding:12px 0;min-height:44px}.allergene h4{margin:14px 0 4px;font-size:1rem}.allergene ul{margin:0;padding-left:1.1em}.allergene .leg{list-style:none;padding:0;columns:2 14em}.allergene .zut li{margin:0 0 6px;font-size:.92rem}.kennz{margin:-2px 0 8px;font-size:.85rem;color:var(--tinte-weich)}.kennz a{color:inherit;text-decoration:none;border-bottom:1px dotted currentColor}.kennz abbr{text-decoration:none}.allergen-zusatz{font-size:.85em;font-weight:700;color:var(--tinte-weich)}.marke-aktion{background:var(--paprika)!important;color:#fff!important}.preis-alt{text-decoration:line-through;text-decoration-thickness:2px;opacity:.55}.sonder{margin:10px 0 0;padding:10px 14px;border-radius:12px;background:var(--gelb-blass)}.sonder p{margin:0 0 4px;font-weight:700}.sonder ul{margin:0;padding:0;list-style:none}.sonder li.heute{font-weight:700}

@media (min-width:1100px){
  .karte-layout{display:grid;grid-template-columns:220px minmax(0,1fr);gap:52px;align-items:start}
  .karte-seite{display:block;position:sticky;top:24px}
  .suche{margin-bottom:18px}
  .kategorien{position:static;margin:0;padding:0;border:0;background:none}
  .kategorien ul{flex-direction:column;gap:2px;padding:0;overflow:visible;-webkit-mask-image:none;mask-image:none}
  .kategorien a{border-color:transparent;border-radius:10px;padding:8px 14px}
  .kategorien a:hover{background:var(--gelb-blass)}
  .gruppe{scroll-margin-top:24px}
  .liste{columns:2;column-gap:48px}
  .groessen-kopf{display:grid;grid-template-columns:1fr 1fr;column-gap:48px}
  .groessen-kopf .nur-breit{display:grid}
}

/* ---------- Bestellzettel ---------- */
.plus{grid-area:plus;justify-self:end;align-self:start;margin-top:-3px;width:32px;height:32px;padding:0;border-radius:50%;
  border:2px solid var(--tinte);background:#fff;color:var(--tinte);font:700 1.3rem/1 var(--text);cursor:pointer;display:grid;place-items:center}
.plus:hover{background:var(--gelb)}
.plus.ok{background:var(--tinte);color:var(--gelb)}
.mengen{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:8px;justify-content:flex-end;padding-top:6px}
.stepper{display:inline-flex;align-items:center;gap:6px;padding:3px;border-radius:999px;background:var(--gelb);border:2px solid var(--tinte)}
.stepper button{width:30px;height:30px;padding:0;border-radius:50%;border:0;background:#fff;color:var(--tinte);font:700 1.15rem/1 var(--text);cursor:pointer}
.stepper button:hover{background:var(--gelb-blass)}
.st-q{min-width:1.6ch;text-align:center;font-weight:700;font-variant-numeric:tabular-nums}
.st-g{font-size:.82rem;font-weight:700;padding:0 4px 0 8px}
.gericht.im-zettel > .plus{visibility:hidden}
.tipp.im-zettel > .plus{display:none}
.tipp .mengen{position:absolute;right:10px;bottom:10px;padding:0}
.tipp-gross .mengen{right:auto;left:120px;bottom:18px}
.tipp-gross.ohne-koch .mengen{left:auto;right:10px;bottom:10px}
.tipp:has(> .wahl) > .plus{display:none}
.tipp:has(.mengen .st-g) .mengen{position:static;flex-direction:column;align-items:flex-start;gap:6px;padding:0 12px 12px}
.wahl{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:8px;justify-content:flex-end;padding-top:8px}
.wahl button{min-height:40px;padding:0 14px;border-radius:999px;border:2px solid var(--tinte);background:var(--gelb);color:var(--tinte);font:700 .92rem var(--text);cursor:pointer}
.tipp{position:relative}
.tipp .plus{position:absolute;right:12px;bottom:12px;margin:0}
.tipp-gross .plus{right:auto;left:126px;bottom:22px}
.tipp .wahl{padding:0 12px 12px;justify-content:flex-start}
.tipp:has(.mengen .st-g) > .plus{bottom:auto;top:12px}
.zettel-leiste{position:fixed;z-index:35;left:10px;right:10px;bottom:calc(12px + env(safe-area-inset-bottom));display:flex;align-items:center;gap:10px;
  min-height:52px;padding:0 18px;border:2px solid var(--tinte);border-radius:999px;background:var(--gelb);color:var(--tinte);font:700 1rem var(--text);cursor:pointer;
  box-shadow:0 10px 24px -10px rgba(58,21,49,.5)}
.zl-anzahl{display:grid;place-items:center;min-width:28px;height:28px;padding:0 6px;border-radius:999px;background:var(--tinte);color:var(--gelb);font-size:.9rem}
.zl-summe{margin-left:auto}
@media (min-width:720px){.zettel-leiste{left:auto;right:24px;bottom:24px}.zl-summe{margin-left:12px}}
body.mit-zettel .fuss{padding-bottom:calc(100px + env(safe-area-inset-bottom))}
@media (min-width:720px){body.mit-zettel .fuss{padding-bottom:100px}}
/* „Nach oben“: unten rechts, über der Zettel-Leiste bzw. der Anrufleiste */
.nach-oben{position:fixed;z-index:36;right:14px;bottom:calc(16px + env(safe-area-inset-bottom));width:48px;height:48px;display:grid;place-items:center;
  border:2px solid var(--gelb);border-radius:50%;background:var(--tinte);color:var(--gelb);cursor:pointer;box-shadow:0 8px 20px -8px rgba(58,21,49,.55)}
.nach-oben svg{width:24px;height:24px;fill:none;stroke:currentColor;stroke-width:2.6;stroke-linecap:round;stroke-linejoin:round}
.nach-oben:focus-visible{outline:3px solid var(--paprika);outline-offset:3px}
body.mit-zettel .nach-oben{bottom:calc(80px + env(safe-area-inset-bottom))}
@media (min-width:720px){.nach-oben{right:24px;bottom:24px}body.mit-zettel .nach-oben{bottom:94px}}
@media (hover:hover){.nach-oben:hover{background:#56213f}}
@media print{.nach-oben{display:none!important}}
.zettel-huelle{position:fixed;inset:0;height:100vh;height:100dvh;z-index:60;display:flex;justify-content:flex-end;align-items:flex-end}
.zettel-hinter{position:absolute;inset:0;background:rgba(42,14,35,.45)}
/* Höhe am sichtbaren Bereich messen (iPhone: vh zählt die Adressleiste nicht ab) */
.zettel{position:relative;width:100%;max-height:calc(100% - 24px - env(safe-area-inset-top));display:flex;flex-direction:column;background:#fff;border-radius:20px 20px 0 0;
  border-top:6px solid var(--gelb);padding:0 18px calc(18px + env(safe-area-inset-bottom));overflow:auto;overscroll-behavior:contain}
@media (min-width:720px){.zettel-huelle{align-items:stretch}.zettel{width:430px;max-height:none;border-radius:0;border-top:0;border-left:6px solid var(--gelb)}}
/* Kopf mit dem X bleibt beim Scrollen im Zettel immer sichtbar */
.zettel-kopf{position:sticky;top:0;z-index:3;display:flex;align-items:center;justify-content:space-between;margin:0 -18px 10px;padding:14px 18px 10px;background:#fff;border-bottom:1px solid transparent}
.zettel-kopf h2{margin:0}
.zettel-kopf h2{font-size:1.7rem}
.zettel-zu{width:44px;height:44px;border-radius:50%;border:2px solid var(--tinte);background:#fff;color:var(--tinte);font:700 1.5rem/1 var(--text);cursor:pointer}
.zettel-leer{color:var(--tinte-weich);padding:12px 0 20px}
.zettel-liste{list-style:none;margin:0;padding:0}
.z-eintrag{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:6px 12px;padding:12px 0;border-bottom:1px dashed var(--linie)}
.z-name{font:700 1.02rem/1.3 var(--slab)}
.z-info{display:block;font-size:.85rem;color:var(--tinte-weich)}
.z-preis{font:700 1.05rem var(--slab);color:var(--paprika);white-space:nowrap;text-align:right}
.z-steuer{grid-column:1/-1;display:flex;flex-wrap:wrap;align-items:center;gap:8px}
.z-steuer .z-anpassen.z-fertig{background:var(--tinte);color:var(--gelb);min-width:96px}
.z-steuer .z-anpassen{width:auto;height:auto;margin-left:auto;min-height:38px;padding:0 14px;border-radius:999px;border:2px solid var(--tinte);background:var(--gelb);color:var(--tinte);font:700 .9rem var(--text);cursor:pointer}
.z-fehlt{color:var(--paprika);font-weight:700}
.z-optionen{grid-column:1/-1;display:grid;gap:12px;padding:12px;border-radius:14px;background:var(--gelb-blass)}
.z-gruppe-titel{display:block;font-weight:700;font-size:.88rem;margin-bottom:6px}
.z-chips{display:flex;flex-wrap:wrap;gap:6px}
/* Entwurf: Band oben + Wasserzeichen über der ganzen Seite (nur solange VORSCHAU = True) */
.vorschau-band{position:relative;z-index:45;padding:10px 16px;text-align:center;font:400 .9rem/1.4 var(--text);color:#fff;
  background:repeating-linear-gradient(-45deg,#3A1531 0 18px,#5a2350 18px 36px);border-bottom:4px solid var(--paprika)}
.vorschau-band strong{display:inline-block;margin-right:6px;padding:1px 10px;border-radius:999px;background:var(--paprika);letter-spacing:.08em}
/* nicht position:fixed: Safari 26 richtet die Farbe der Adressleiste nach festen Elementen am Rand aus */
body.vorschau{position:relative}
.marke-verf{display:inline-block;margin-left:8px;padding:1px 8px;border-radius:999px;background:var(--paprika);color:#fff;font:700 .72rem/1.6 var(--text);vertical-align:middle;white-space:nowrap}
li.nicht-da .name,li.nicht-da .tipp-name{color:#7a6471}
li.nicht-da .preis,li.nicht-da .tipp-preis,li.nicht-da .beschreibung,li.nicht-da .tipp-info,li.nicht-da .marke-beliebt{opacity:.45}
li.nicht-da .plus{opacity:.35;cursor:not-allowed}
.verf-hinweis{color:var(--paprika);font-weight:700}
.z-gesperrt .z-name{text-decoration:line-through}
.chip:disabled{opacity:.5;cursor:not-allowed}
.chip[data-o=ohne][aria-pressed=false]{text-decoration:line-through;color:#8d7486;border-color:#c9b8c3}
.chip{min-height:36px;padding:0 12px;border-radius:999px;border:2px solid var(--tinte);background:#fff;color:var(--tinte);font:700 .88rem var(--text);cursor:pointer}
.chip[aria-pressed="true"]{background:var(--tinte);color:var(--gelb)}
.chip:disabled{opacity:.35;cursor:not-allowed}.chip.chip-aus:disabled{opacity:.6;border-style:dashed;font-weight:400}
.z-fertig{justify-self:start;min-height:42px}
.z-steuer button{width:36px;height:36px;border-radius:50%;border:2px solid var(--tinte);background:#fff;color:var(--tinte);font:700 1.2rem/1 var(--text);cursor:pointer}
.z-menge{min-width:2ch;text-align:center;font-weight:700;font-variant-numeric:tabular-nums}
.z-notiz{grid-column:1/-1;width:100%;min-height:38px;border:1px solid var(--linie);border-radius:10px;padding:0 10px;font:400 .92rem var(--text);color:var(--tinte)}
.zettel-summe-zeile{display:flex;justify-content:space-between;align-items:baseline;padding:14px 0 6px;font:700 1.3rem var(--slab)}
.zettel-summe-zeile b{color:var(--paprika)}
.abholung{border:0;margin:6px 0 14px;padding:14px;border-radius:14px;background:var(--gelb-blass);display:grid;gap:8px}
.abholung legend{float:left;font:700 1.15rem var(--slab);padding:0;margin-bottom:4px}
.abholung label{font-weight:700;font-size:.9rem;margin-top:4px}
.abholung select,.abholung input{width:100%;min-height:44px;border:2px solid var(--tinte);border-radius:12px;padding:0 12px;font:400 1rem var(--text);color:var(--tinte);background:#fff}
.knopf-whatsapp{background:#1E7B3C;color:#fff}
.knopf-whatsapp:hover{background:#17652F}
.abhol-hinweis{font-size:.88rem;color:var(--paprika);font-weight:700}
.winter{margin-top:16px;padding:14px 16px;border:2px solid var(--tinte);border-radius:18px;background:#EAF4FB;color:var(--tinte)}.winter p{margin:0 0 10px}.winter-titel{font:700 1.2rem var(--slab)}.winter-knoepfe{display:flex;flex-wrap:wrap;gap:8px}.winter-knoepfe .knopf{flex:1 1 200px}
.code-box{margin:-4px 0 12px;font-size:.95rem}.code-box summary{cursor:pointer;color:var(--tinte-weich);font-weight:700;min-height:36px;display:flex;align-items:center}.code-form{display:flex;gap:8px;margin:6px 0}.code-form input{flex:1;min-width:0;min-height:44px;border:2px solid var(--tinte);border-radius:12px;padding:0 12px;font:inherit}.code-info{margin:4px 0;font-weight:700;color:var(--gruen,#2E7D32)}.link-knopf{background:none;border:0;padding:4px 0;color:var(--tinte-weich);text-decoration:underline;font:inherit;cursor:pointer}
[data-offen=bald] .status-text{color:var(--paprika)}
.zug-wahl{margin:12px 0 2px}.zug-titel{margin:0 0 6px;font-weight:700;font-size:.92rem}.zug-chips{display:flex;flex-wrap:wrap;gap:6px}.zug-chips .chip{font-size:.9rem}.zug-quelle{font-size:.78rem;color:var(--tinte-weich);margin:6px 0 0}.wa-nr{margin:0 0 6px;font-size:1.05rem}.wa-nr b{font-size:1.25rem;letter-spacing:.06em}.wa-kalender{margin-top:10px;width:100%}
.wa-gesendet{margin:0;padding:10px 12px;border-radius:12px;background:#E3F3E8;color:#14512A;font-size:.92rem;font-weight:700}.wa-gesendet a{color:inherit}.zettel-bar,.bar{display:flex;align-items:center;gap:8px;font-weight:700;font-size:.92rem}.zettel-bar{margin:6px 0 0}.bar{margin:8px 0 0}.zettel-bar .ico,.bar .ico{width:22px;height:22px;flex:none}
.zettel-hinweis{color:var(--tinte-weich);font-size:.92rem;margin-bottom:14px}
.zettel-knoepfe{display:grid;gap:10px}
.zettel-knoepfe .knopf{width:100%}
.knopf-klein{min-height:40px;font-size:.92rem;border:0;background:none;color:var(--tinte-weich);text-decoration:underline;cursor:pointer}
.zettel-meldung{position:fixed;z-index:70;left:50%;bottom:calc(80px + env(safe-area-inset-bottom));transform:translateX(-50%);max-width:calc(100% - 32px);
  padding:10px 16px;border-radius:12px;background:var(--tinte);color:#fff;font-weight:700;font-size:.95rem;text-align:center;box-shadow:0 8px 20px -8px rgba(0,0,0,.4)}
@media (min-width:720px){.zettel-meldung{bottom:92px;left:auto;right:24px;transform:none}}
@media print{.plus,.zettel-leiste{display:none!important}}

/* ---------- Für Firmen, Vereine und Feiern ---------- */
.gruppen{padding-block:56px 60px;border-top:6px solid var(--gelb)}
.gruppen-wrap{display:grid;gap:24px}
@media (min-width:860px){.gruppen-wrap{grid-template-columns:minmax(0,1.6fr) minmax(0,1fr);align-items:start}}
.gruppen .intro{color:var(--tinte-weich);max-width:60ch}
.schritte{list-style:none;counter-reset:s;margin:18px 0;padding:0;display:grid;gap:12px;max-width:60ch}
.schritte li{counter-increment:s;display:grid;grid-template-columns:2.2rem minmax(0,1fr);column-gap:10px}
.schritte li::before{content:counter(s);grid-row:1 / span 2;display:grid;place-items:center;width:2rem;height:2rem;border-radius:50%;background:var(--gelb);font:700 1rem var(--slab)}
.schritte b{font-family:var(--slab)}
.gruppen .sammel-start{text-align:left}
.gruppen-info{background:var(--gelb-blass);border-radius:16px;padding:18px 20px;display:grid;gap:10px}
.gruppen-info p{margin:0}
.gruppen-info .knopf{justify-content:flex-start}

/* ---------- Standorte ---------- */
.standorte{background:var(--gelb-blass);padding-block:60px 72px}
.standorte .intro{color:var(--tinte-weich);max-width:60ch;margin-bottom:28px}
.orte{display:grid;gap:20px}
@media (min-width:760px){.orte{grid-template-columns:1fr 1fr}}
.ort{background:#fff;border:2px solid var(--tinte);border-radius:18px;padding:22px 22px 24px}
.ort h3{font-size:2rem;letter-spacing:-.015em;margin-bottom:8px}
.ort address{font-style:normal;margin:14px 0 6px}
.ort address a{font-weight:700}
.zeiten{width:100%;border-collapse:collapse;margin:12px 0 10px}
.zeiten th,.zeiten td{padding:9px 0;border-top:1px solid var(--linie);vertical-align:baseline}
.zeiten th{text-align:start;font-weight:400;padding-inline-end:12px}
.zeiten td{text-align:end;font-weight:700;white-space:nowrap;font-variant-numeric:tabular-nums}
html[lang=en] .zeiten tr.heute th::after{content:"today"}
html[lang=cs] .zeiten tr.heute th::after{content:"dnes"}
html[lang=tr] .zeiten tr.heute th::after{content:"bugün"}
html[lang=ru] .zeiten tr.heute th::after{content:"сегодня"}
html[lang=ar] .zeiten tr.heute th::after{content:"اليوم"}
.zeiten tr.heute th::after{content:"heute";display:inline-block;margin-inline-start:8px;padding:1px 8px;border-radius:999px;background:var(--gelb);
  font-weight:700;font-size:.8rem;vertical-align:1px}
.karte-bild{margin:14px 0 4px}
.karte-bild > a{position:relative;display:block;border-radius:12px;overflow:hidden;border:2px solid var(--tinte)}
.karte-bild img{width:100%;display:block}
.pin{position:absolute;left:69.4%;top:64.2%;width:34px;transform:translate(-50%,-100%);filter:drop-shadow(0 3px 3px rgba(58,21,49,.35))}
.karte-bild figcaption{font-size:.8rem;color:var(--tinte-weich);margin-top:4px}
.karte-bild figcaption a{color:inherit}
.ort-extra{color:var(--tinte-weich);margin-bottom:16px}
.knoepfe{display:flex;flex-wrap:wrap;gap:10px}
.knoepfe .knopf{flex:1 1 auto}
.feiertage{margin-top:18px;color:var(--tinte-weich);font-size:.95rem}

/* ---------- Fuß ---------- */
.fuss{background:var(--tinte);color:#F3E6EE;padding-block:48px 28px}
.fuss a{color:var(--gelb)}
.fuss :focus-visible{outline-color:var(--gelb)}
.fuss-raster{display:grid;gap:28px}
@media (min-width:760px){.fuss-raster{grid-template-columns:1.4fr 1fr;align-items:end}}
.fuss .logo{width:76px;height:76px}
.motto{font:700 1.7rem/1.15 var(--slab);color:var(--gelb);margin:16px 0 6px}
.fuss-ort h2{font-size:1.25rem;color:#fff;margin-bottom:6px}
.fuss-ort p{margin-bottom:6px}
.klein{font-size:.9rem;color:#D9C3D2}
.recht{margin-top:36px;padding-top:18px;border-top:1px solid rgba(255,255,255,.18);display:grid;gap:6px}
.recht summary{cursor:pointer;font-weight:700;color:var(--gelb);padding:6px 0;width:fit-content;max-width:100%}.recht{min-width:0}.recht details{min-width:0}
.recht details[open]{background:rgba(255,255,255,.06);border-radius:12px;padding:4px 16px 16px}
.recht details p{margin-bottom:8px;max-width:70ch}
.recht details h3{margin:14px 0 4px;font-size:1rem;color:var(--gelb)}.recht details a{color:inherit}
.platzhalter{background:var(--gelb);color:var(--tinte);padding:0 4px;border-radius:3px}

/* ---------- Anrufleiste (nur Handy) ---------- */
@media (max-width:719px){.fuss{padding-bottom:calc(24px + env(safe-area-inset-bottom))}}

@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}.sticker{animation:none}*{transition:none!important}}
@media print{.kategorien,.suche,.bilder,.kopf-nav,.knoepfe{display:none!important}.kopf-band,.buehne-band{background:none;border:0}
  .gruppe{break-inside:avoid-page}}
"""

ZETTEL_JS = r'''
  /* Bestellzettel mit Wünschen je Gericht */
  var ZK='saray-bestellzettel-2',zettel=[],uidZ=1,offen=null;
  var SOSSEN=['Knoblauch','Kräuter','Chili'],OHNE=['Zwiebeln','Tomaten','Gurken','Rotkohl','Weißkohl','Eisbergsalat'];
  var GEMUESE=['Paprika','Zwiebel','Champignon','Tomate','Peperoni','Ananas','Oliven','Brokkoli','Mais'];
  var FLEISCH=['Schinken','Salami','Dönerfleisch','Hähnchen-Dönerfleisch'],KAESE=['Käse','Halloumikäse','Fetakäse'];
  /* Pizzabrötchen: ein Belag zur Wahl (laut Karte Salami, Schinken, Dönerfleisch oder nach Wahl) */
  var BELAG=['Salami','Schinken','Dönerfleisch','Hähnchen-Dönerfleisch','Käse','Halloumikäse','Fetakäse','Gemüse'];
  var PAARE=[['1','2'],['3','4'],['6','7'],['9','10'],['11','12'],['13','14'],['15','16'],['23','25'],['30','31'],['32','33'],['36','37'],
    ['40','41'],['42','43'],['50','51'],['52','53'],['54','55'],['60','61'],['123','124']],OHNE_K={},MIT_K={};
  PAARE.forEach(function(pq){OHNE_K[pq[0]]=pq[1];MIT_K[pq[1]]=pq[0];});
  /* Varianten: Form, Füllung, extra Fleisch (Super), Käse, Beilage.
     Die Schalter im Zettel suchen damit das passende Gericht der Karte. */
  var VAR={},FUELL=['kalb','huhn','beide','veg','falafel','halloumi','hack','schinken','schinkenananas','hawaii','tonno','bauern','mozzarella'];
  var F_NAME={kalb:['Dönerfleisch','Döner meat'],huhn:['Hähnchen','Chicken'],veg:['ohne Fleisch','No meat'],falafel:['Falafel','Falafel'],
    halloumi:['Halloumi','Halloumi'],hack:['Hackfleisch','Minced meat'],beide:['Döner + Hähnchen (Saray)','Döner + chicken (Saray)'],
    schinken:['Schinken','Ham'],schinkenananas:['Schinken + Ananas','Ham + pineapple'],hawaii:['Ananas','Pineapple'],tonno:['Thunfisch','Tuna'],
    bauern:['Bauernsalat (Käse, Oliven, Peperoni)','Farmer’s (cheese, olives, hot peppers)'],mozzarella:['Mozzarella','Mozzarella']};
  var FLEISCH_F=['kalb','huhn','beide','hack','schinken','schinkenananas'],FISCH_F=['tonno'];
  function erlaubtF(f){return !(DIAET&&FLEISCH_F.indexOf(f)>-1)&&!(DIAET==='veg'&&FISCH_F.indexOf(f)>-1);}
  function ohneFleisch(liste){return DIAET?liste.filter(function(v){return FLEISCH.indexOf(v)<0&&['Salami','Schinken','Dönerfleisch','Hähnchen-Dönerfleisch'].indexOf(v)<0;}):liste;}
  /* Pizza: Zutaten aus Name/Beschreibung (gleiche Namen wie bei den Extras) – zum Abwählen */
  var PZ_WORT=[['thunfisch','Thunfisch'],['dönerfleisch','Dönerfleisch'],['salami','Salami'],['schinken','Schinken'],['champignon','Champignon'],
    ['paprika','Paprika'],['brokkoli','Brokkoli'],['zwiebel','Zwiebel'],['tomate','Tomate'],['ananas','Ananas'],['oliven','Oliven'],['peperoni','Peperoni'],
    ['mais','Mais'],['knoblauch','Knoblauch'],['feta','Fetakäse'],['halloumi','Halloumikäse'],['mozzarella','Mozzarella']];
  function pizzaZutaten(x){
    var t=(x.n+' '+(x.d||'')+' '+((x.o&&x.o.va)||'')).toLowerCase(),r=[];
    if(/hähnchen-?döner/.test(t)){r.push('Hähnchen-Dönerfleisch');t=t.replace(/hähnchen-?dönerfleisch/g,'');}
    PZ_WORT.forEach(function(w){if(t.indexOf(w[0])>-1&&r.indexOf(w[1])<0)r.push(w[1]);});
    if(/(^|[^a-zäöü])ei([^a-zäöü]|$)/.test(t))r.push('Ei');
    r.push('Käse');return r;
  }
  var BEI=['S','P','SP'],BEI_NAME={S:['Salat','Salad'],P:['Pommes','Fries'],SP:['Salat + Pommes','Salad + fries']};
  [ /* k, Form, Füllung, Super, Käse, Beilage */
    ['1','doener','kalb',0,0],['2','doener','kalb',0,1],['6','doener','kalb',1,0],['7','doener','kalb',1,1],
    ['30','doener','huhn',0,0],['31','doener','huhn',0,1],['32','doener','huhn',1,0],['33','doener','huhn',1,1],
    ['3','doener','veg',0,0],['4','doener','veg',0,1],['5','doener','halloumi',0,0],['11','doener','falafel',0,0],['12','doener','falafel',0,1],
    ['50','duerum','kalb',0,0],['51','duerum','kalb',0,1],['54','duerum','kalb',1,0],['55','duerum','kalb',1,1],
    ['40','duerum','huhn',0,0],['41','duerum','huhn',0,1],['42','duerum','huhn',1,0],['43','duerum','huhn',1,1],
    ['52','duerum','veg',0,0],['53','duerum','veg',0,1],['57','duerum','halloumi',0,0],['58','duerum','falafel',0,0],
    ['13','box','kalb',0,0],['14','box','kalb',0,1],['15','box','huhn',0,0],['16','box','huhn',0,1],
    ['21','teller','kalb',0,0,'S'],['22','teller','kalb',0,0,'P'],['23','teller','kalb',0,0,'SP'],['25','teller','kalb',0,1,'SP'],
    ['34','teller','huhn',0,0,'S'],['35','teller','huhn',0,0,'P'],['36','teller','huhn',0,0,'SP'],['37','teller','huhn',0,1,'SP'],
    ['24','teller','veg',0,0,'SP'],['26','teller','beide',0,0,'SPR'],['28','ueber','kalb',0,0],['38','ueber','huhn',0,0],['18','kinder','kalb',0,0],['19','kinder','huhn',0,0],
    ['130','salat','veg',0,0],['132','salat','veg',0,1],['131','salat','kalb',0,0],['133','salat','kalb',0,1],['134','salat','huhn',0,0],['135','salat','huhn',0,1],
    ['136','salat','tonno',0,0],['137','salat','hawaii',0,0],['138','salat','schinken',0,0],['139','salat','schinkenananas',0,0],['140','salat','bauern',0,0],
    ['141','salat','halloumi',0,0],['142','salat','falafel',0,0],['143','salat','mozzarella',0,0],
    ['121','lahmacun','hack',0,0],['123','lahmacun','kalb',0,0],['124','lahmacun','kalb',0,1]
  ].forEach(function(v){VAR[v[0]]={k:v[0],form:v[1],f:v[2],sup:v[3],kae:v[4],bei:v[5]||''};});
  /* bestes Gericht mit den gewünschten Merkmalen; Vorrang: Beilage, Käse, Super */
  function variante(k,wunsch,streng){
    var a=VAR[k];if(!a)return null;var w=Object.assign({},a,wunsch),best=null,bp=-1;
    Object.keys(VAR).forEach(function(kk){var v=VAR[kk];if(v.form!==a.form||v.f!==w.f||!gerichtLi(kk))return;
      if(streng&&(v.sup!==w.sup||v.kae!==w.kae||v.bei!==w.bei))return;
      var pkt=(v.bei===w.bei?4:0)+(v.kae===w.kae?2:0)+(v.sup===w.sup?1:0)+(v.bei==='SP'?.5:0);if(pkt>bp){bp=pkt;best=kk;}});
    return best===k?null:best;
  }
  function kaesePartner(k){return VAR[k]?variante(k,{kae:VAR[k].kae?0:1},true):(OHNE_K[k]||MIT_K[k]||null);}
  /* Verfügbarkeit: feste Regeln aus build.py + tagesaktuelle aus status.json */
  var SPERR=%%SPERR%%,REGELN_FEST=%%REGELN%%,REGELN=REGELN_FEST.slice(),LADEN_N={freital:'Freital',altenberg:'Altenberg'};
  function datumISO(off){return new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Berlin',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(Date.now()+off*864e5));}
  function minAus(t){var q=String(t).split(':');return (+q[0])*60+(+q[1]||0);}
  function trifft(r,k){var w=[].concat(r.was||[]);return w.some(function(v){v=String(v);return v===k||(SPERR[v]&&SPERR[v].nr.indexOf(k)>-1);});}
  /* null = verfügbar, sonst {art:'aus'|'ab'|'bis', zeit} für Laden, Tag (0 = heute) und Uhrzeit (Minuten) */
  function sperre(k,laden,off,min){
    var tag=(jetzt().tag+off)%7,d=datumISO(off),res=null;
    REGELN.forEach(function(r){
      if(res&&res.art==='aus')return;if(!trifft(r,k))return;
      if(r.laden&&r.laden!=='alle'&&r.laden!==laden)return;
      if(r.datum&&[].concat(r.datum).indexOf(d)<0)return;
      if(r.tage&&r.tage.indexOf(tag)<0)return;
      if(r.ab&&min<minAus(r.ab))res={art:'ab',zeit:r.ab};
      else if(r.bis&&min>=minAus(r.bis))res={art:'bis',zeit:r.bis};
      else if(!r.ab&&!r.bis)res={art:'aus',dauer:!r.datum};
    });
    return res;
  }
  function uhrK(t){var m=minAus(t),h=Math.floor(m/60),r=m%60;return SP!=='de'?h+':'+(r<10?'0':'')+r:(r?h+':'+(r<10?'0':'')+r:h)+' Uhr';}
  function sperrText(sp,heute){
    if(sp.art==='aus')return (heute===false||sp.dauer)?L('nicht verfügbar','not available'):L('heute nicht verfügbar','not available today');
    if(sp.art==='ab')return L('erst ab ','only from ')+uhrK(sp.zeit);
    return L('nur bis ','only until ')+uhrK(sp.zeit);
  }
  /* Abholzeitpunkt aus der Auswahl im Zettel */
  var ZINFO={};
  function abholung(){return abh.laden&&ZINFO[abh.zeit]?{laden:abh.laden,off:ZINFO[abh.zeit].off,min:ZINFO[abh.zeit].min}:null;}
  function sperreZettel(k){var a=abholung();return a?sperre(k,a.laden,a.off,a.min):null;}
  /* Speisekarte: Hinweis am Gericht, ausgegraut, wenn heute in keinem Laden zu haben */
  function verfZeigen(){
    var n=jetzt();
    document.querySelectorAll('li[data-k]').forEach(function(li){
      var k=li.dataset.k,sp={};Object.keys(LADEN_N).forEach(function(l){sp[l]=sperre(k,l,0,n.min);});
      var gesperrt=Object.keys(sp).filter(function(l){return sp[l];}),txt='',aus;
      if(abh.laden&&LADEN_N[abh.laden]){ /* Laden gewählt: Karte gilt für diesen Laden */
        var s1=sp[abh.laden];txt=s1?sperrText(s1)+L(' in ',' in ')+LADEN_N[abh.laden]:'';aus=!!s1&&s1.art==='aus';
      }else{
        if(gesperrt.length===2&&sperrText(sp.freital)===sperrText(sp.altenberg))txt=sperrText(sp.freital);
        else txt=gesperrt.map(function(l){return LADEN_N[l]+': '+sperrText(sp[l]);}).join(' · ');
        aus=gesperrt.length===2&&sp.freital.art==='aus'&&sp.altenberg.art==='aus';
      }
      li.classList.toggle('nicht-da',aus);
      var pk=li.querySelector('.plus');if(pk){pk.disabled=aus;}
      var m=li.querySelector('.marke-verf');
      if(!txt){if(m)m.remove();return;}
      if(!m){m=el('span','marke-verf');var ziel=li.querySelector('.name, .tipp-name');if(ziel)ziel.appendChild(m);else return;}
      m.textContent=txt;
    });
  }
  function regelnLaden(){
    if(!window.fetch)return;
    fetch('status.json',{cache:'no-store'}).then(function(r){return r.ok?r.json():{};}).then(function(d){
      REGELN=REGELN_FEST.concat(Array.isArray(d.regeln)?d.regeln:[]);verfZeigen();zeichnen();waAktualisieren();
    }).catch(function(){});
  }
  function wechseln(x,ziel){var li=gerichtLi(ziel);if(!li)return;x.k=li.dataset.k;x.n=li.dataset.n;x.d=li.dataset.d;x.c=+li.dataset.p;}
  function preisDiff(x,ziel){var li=gerichtLi(ziel);if(!li)return '';var d=(+li.dataset.p)-x.c;return d?' ('+(d<0?'−':'+')+euro(Math.abs(d))+')':'';}
  var W={'Knoblauch':'garlic','Thunfisch':'tuna','Mozzarella':'mozzarella','Ei':'egg','Kräuter':'herb','Chili':'chili','Zwiebeln':'onions','Tomaten':'tomatoes','Gurken':'cucumber','Rotkohl':'red cabbage',
    'Weißkohl':'white cabbage','Eisbergsalat':'iceberg lettuce','Paprika':'bell pepper','Zwiebel':'onion','Champignon':'mushrooms','Tomate':'tomato',
    'Gemüse':'vegetables','Peperoni':'hot peppers','Ananas':'pineapple','Oliven':'olives','Brokkoli':'broccoli','Mais':'corn','Schinken':'ham','Salami':'salami',
    'Dönerfleisch':'döner meat','Hähnchen-Dönerfleisch':'chicken döner meat','Käse':'cheese','Halloumikäse':'halloumi','Fetakäse':'feta'};
  function w(v){if(SP==='de'||!W[v])return v;var x=T(W[v]);return x.charAt(0).toUpperCase()+x.slice(1);}
  function gerichtLi(nr){return document.querySelector('li.gericht[data-k="'+nr+'"]');}
  try{zettel=JSON.parse(localStorage.getItem(ZK)||'[]');if(!Array.isArray(zettel))zettel=[];}catch(e){zettel=[];}
  zettel.forEach(function(x){x.u=uidZ++;if(x.o&&!Array.isArray(x.o.s))x.o.s=x.o.s?[x.o.s]:[];});
  /* Bestellnummer: kurz, gut vorzulesen; neu, sobald nach dem Senden etwas geändert wird */
  function neueNr(){var b='ACDEFHKLMNPRTUVWXY';return b.charAt(Math.floor(Math.random()*b.length))+(10+Math.floor(Math.random()*90));}
  var BNR=neueNr(),bnrGesendet=false;
  function speichern(){if(bnrGesendet){BNR=neueNr();bnrGesendet=false;}try{localStorage.setItem(ZK,JSON.stringify(zettel.map(function(x){var y=Object.assign({},x);delete y.u;return y;})));}catch(e){}}
  function euro(c){return (c/100).toFixed(2).replace('.',',')+' €';}
  function grund(t){return {s:(t==='D'||t==='SA')?['Kräuter']:[],ohne:[],ex:[],wahl:[],va:''};}
  function exPreis(o){return (o.ex||[]).reduce(function(a,e){return a+(GEMUESE.indexOf(e)>-1?150:200);},0);}
  function aktionZ(x){var li=gerichtLi(x.k);if(!li)return null;var gs=li.dataset.g?li.dataset.g.split('|'):[''];
    var tag=abh.tag||isoTag(0),zi=ZINFO[abh.zeit],min=zi?zi.min:(tag===isoTag(0)?jetzt().min:null);
    return aktion(x.k,Math.max(0,gs.indexOf(x.g||'')),tag,abh.laden||null,min);}
  /* Beilage (Pommes/Reis) vom Laden ausgeschaltet: Gericht ohne diese Beilage, je 0,50 € weniger */
  var BEILAGEN=%%BEILAGEN%%,BEILAGE_RABATT=%%BEILAGE_RABATT%%;
  function fehlend(x){return (BEILAGEN[x.k]||[]).filter(function(b){return zAus(b);});}
  function stueck(x){var ak=aktionZ(x);return (ak?ak.c:x.c)+exPreis(x.o)-fehlend(x).length*BEILAGE_RABATT;}
  function sig(x){var o=x.o;return [x.k,x.g,o.s.slice().sort().join(','),o.ohne.slice().sort().join(','),o.ex.slice().sort().join(','),o.wahl.slice().sort().join(','),o.va,x.notiz||'',x.fuer||''].join('|');}
  function liste(a,en){var u=en?' '+T('and')+' ':' und ';return a.length<2?a.join(''):a.slice(0,-1).join(', ')+u+a[a.length-1];}
  /* Wünsche als Text; en=true nur für die Anzeige, die Nachricht an den Laden ist immer deutsch */
  function wuensche(x,en){
    var o=x.o,t=[],tr=function(a){return en?a.map(function(v){return W[v]?T(W[v]):v;}):a;};
    if(x.t==='D'||x.t==='SA'){var so=SOSSEN.filter(function(n){return o.s.indexOf(n)>-1;});
      if(en)t.push(!so.length?T('no sauce'):fuell(T('{list} sauce'),{list:liste(tr(so),true)}));
      else t.push(!so.length?'ohne Soße':so.length===1?so[0]+'-Soße':so.slice(0,-1).join('-, ')+'- und '+so[so.length-1]+'-Soße');}
    if(o.ohne.length)t.push(en?fuell(T('no {list}'),{list:liste(tr(o.ohne),en)}):'ohne '+liste(o.ohne,en));
    var fe=fehlend(x);if(fe.length)t.push(en?fuell(T('no {list}'),{list:liste(fe.map(function(b){return T(b==='Pommes'?'fries':'rice');}),en)})+' ('+T('not available')+', −'+euro(fe.length*BEILAGE_RABATT)+')'
      :'ohne '+liste(fe,en)+' (heute aus, −'+euro(fe.length*BEILAGE_RABATT)+')');
    if(x.t==='S')t.push(o.wahl.length<3?(en?T('choose '+(3-o.wahl.length)+' more toppings'):'noch '+(3-o.wahl.length)+(3-o.wahl.length===1?' Zutat wählen':' Zutaten wählen')):(en?fuell(T('with {list}'),{list:liste(tr(o.wahl),en)}):'mit '+liste(o.wahl,en)));
    if(x.t==='R')t.push(o.va?(en?fuell(T('option {x}'),{x:o.va.charAt(0)}):'Variante '+o.va.charAt(0)):(en?T('choose option'):'Variante wählen'));
    if(x.t==='B')t.push(o.va?(en?fuell(T('with {list}'),{list:W[o.va]?T(W[o.va]):o.va}):'mit '+o.va):(en?T('choose topping'):'Belag wählen'));
    tr(o.ex).forEach(function(e){t.push(en?fuell(T('extra {x}'),{x:e}):'extra '+e);});
    return t.join(', ');
  }
  /* Anzeigename/Beschreibung in der gewählten Sprache */
  function nameFremd(li,fallback){if(!li)return fallback;var m=/^Nr\. (\S+) /.exec(li.dataset.n||'');return (m?T('No.')+' '+m[1]+' ':'')+T(li.dataset.nen||'');}
  function nameA(x){if(SP==='de')return x.n;return nameFremd(gerichtLi(x.k),x.n);}
  function beschrA(x){if(SP==='de')return x.d;var li=gerichtLi(x.k);return li&&li.dataset.dn!=null?T(li.dataset.dn):x.d;}
  function zusammenfassen(){
    var neu=[],idx={};
    zettel.forEach(function(x){var k=sig(x);if(idx[k]!=null&&x.u!==offen&&neu[idx[k]].u!==offen){neu[idx[k]].q+=x.q;}else{idx[k]=neu.length;neu.push(x);}});
    zettel=neu;
  }
  var zl=document.getElementById('zettel-leiste'),huelle=document.getElementById('zettel'),zliste=document.getElementById('zettel-liste'),
      zsumme=document.getElementById('zettel-summe'),zmeld=document.getElementById('zettel-meldung'),meldTimer=null,zuletzt=null;
  function anzahl(){return zettel.reduce(function(a,x){return a+x.q;},0);}
  function brutto(){return zettel.reduce(function(a,x){return a+x.q*stueck(x);},0);}
  /* Firmen-Code: Rabatt in Prozent auf alles ohne Aktionspreis; gilt je nach Code nur in einem Laden, zu bestimmten Uhrzeiten, bis zu einem Datum */
  var CODES=%%CODES%%;
  function codeAktiv(){var c=abh.code;if(!c)return null;var d=CODES.filter(function(x){return x.h===c.h;})[0];if(!d)return null;
    var zi=ZINFO[abh.zeit],tag=abh.tag||isoTag(0);
    if(d.bis&&tag>d.bis)return null;if(d.laden&&abh.laden&&d.laden!==abh.laden)return null;
    if(d.za!=null&&zi&&(zi.min<d.za||zi.min>=d.zb))return null;return d;}
  function rabatt(){var d=codeAktiv();if(!d)return 0;
    return Math.round(zettel.reduce(function(a,x){return a+(aktionZ(x)?0:x.q*stueck(x));},0)*d.prozent/100);}
  function summe(){return brutto()-rabatt();}
  function melden(t){zmeld.textContent=t;zmeld.hidden=false;clearTimeout(meldTimer);meldTimer=setTimeout(function(){zmeld.hidden=true;},2400);}
  function el(tag,cls,text){var x=document.createElement(tag);if(cls)x.className=cls;if(text!=null)x.textContent=text;return x;}
  function knopf(text,attrs){var b=el('button',null,text);b.type='button';for(var a in attrs)b.setAttribute(a,attrs[a]);return b;}
  /* Zutat vom Laden ausgeschaltet (Chef-App „Zutaten“)? Gilt für die gewählte Abholung, sonst jetzt */
  var Z_NORM={'Zwiebeln':'Zwiebel','Tomaten':'Tomate'},Z_GRUPPE={'Hähnchen-Dönerfleisch':'huhn','Halloumikäse':'halloumi'};
  function zAus(v){
    var a=abholung()||{laden:abh.laden||null,off:0,min:jetzt().min};
    return sperre('z:'+(Z_NORM[v]||v),a.laden,a.off,a.min)||(Z_GRUPPE[v]?sperre(Z_GRUPPE[v],a.laden,a.off,a.min):null);
  }
  /* ausgeschaltete Zutaten aus Wünschen entfernen (Soße, Extras, Zutaten, Belag) */
  function bereinigen(x){var o=x.o;if(!o)return;
    ['s','ex','wahl'].forEach(function(a){if(Array.isArray(o[a]))o[a]=o[a].filter(function(v){return !zAus(v);});});
    /* „ohne Käse“ und gleichzeitig Käse als Zutat zur Wahl geht nicht */
    if(Array.isArray(o.ohne)&&Array.isArray(o.wahl))o.wahl=o.wahl.filter(function(v){return o.ohne.indexOf(v)<0;});
    if(x.t==='B'&&o.va&&zAus(o.va))o.va='';}
  function chips(titel,werte,gewaehlt,art,uid,extra){
    var g=el('div','z-gruppe');g.appendChild(el('span','z-gruppe-titel',titel));var wb=el('div','z-chips');
    werte.forEach(function(v){var an=gewaehlt.indexOf(v)>-1,sp=art==='va'&&/^[A-D]: /.test(v)?null:zAus(v);
      var b=knopf(w(v)+(extra||'')+(sp?' – '+sperrText(sp):''),{'class':'chip'+(sp?' chip-aus':''),'aria-pressed':String(an&&!sp),'data-o':art,'data-w':v,'data-u':uid});
      if(sp)b.disabled=true;
      if(art==='wahl'&&!an&&gewaehlt.length>=3)b.disabled=true;wb.appendChild(b);});
    g.appendChild(wb);return g;
  }
  function editor(x){
    var box=el('div','z-optionen'),o=x.o;
    if(x.t==='D'||x.t==='SA')box.appendChild(chips(L('Soße (mehrere möglich)','Sauce (choose any)'),SOSSEN,o.s,'s',x.u));
    var va=VAR[x.k];
    if((x.t==='D'||x.t==='SA')&&va){
      var fg=el('div','z-gruppe');fg.appendChild(el('span','z-gruppe-titel',va.form==='salat'?L('Belag','Topping'):L('Füllung','Filling')));var fw=el('div','z-chips');
      FUELL.forEach(function(f){
        if(f!==va.f&&!erlaubtF(f))return;
        var ziel=f===va.f?x.k:variante(x.k,{f:f});if(!ziel)return;
        var spF=f===va.f?null:(sperreZettel(ziel)||(function(){var nn=jetzt();var a=sperre(ziel,'freital',0,nn.min),b=sperre(ziel,'altenberg',0,nn.min);return a&&b&&a.art==='aus'&&b.art==='aus'?a:null;})());
        var fk=knopf(L(F_NAME[f][0],F_NAME[f][1])+(f===va.f?'':spF?' – '+sperrText(spF):preisDiff(x,ziel)),{'class':'chip','aria-pressed':String(f===va.f),'data-fuell':f,'data-u':x.u});
        if(spF)fk.disabled=true;fw.appendChild(fk);
      });
      if(fw.children.length>1){fg.appendChild(fw);box.appendChild(fg);}
      if(va.form==='teller'){ /* Beilage: Salat, Pommes oder beides – wechselt zum passenden Teller */
        var bopt=BEI.filter(function(b){if(b===va.bei)return true;var z=variante(x.k,{bei:b});return z&&VAR[z].bei===b;});
        if(bopt.length>1){var bg=el('div','z-gruppe');bg.appendChild(el('span','z-gruppe-titel',L('Beilage','Side')));var bw=el('div','z-chips');
          bopt.forEach(function(b){var zb=b===va.bei?null:variante(x.k,{bei:b});
            var spB=(b==='P'||b==='SP')&&zAus('Pommes')||(zb?(sperreZettel(zb)||sperre(zb,abh.laden||null,0,jetzt().min)):null);
            var kb2=knopf(L(BEI_NAME[b][0],BEI_NAME[b][1])+(spB?' – '+sperrText(spB):zb?preisDiff(x,zb):''),{'class':'chip'+(spB?' chip-aus':''),'aria-pressed':String(b===va.bei),'data-bei':b,'data-u':x.u});
            if(spB)kb2.disabled=true;bw.appendChild(kb2);});
          bg.appendChild(bw);box.appendChild(bg);}
      }
      var su=variante(x.k,{sup:va.sup?0:1},true);
      if(su){var sg=el('div','z-gruppe');sg.appendChild(el('span','z-gruppe-titel',L('Fleisch','Meat')));var sw=el('div','z-chips');
        sw.appendChild(knopf(L('extra Fleisch (Super)','extra meat (Super)')+(va.sup?'':preisDiff(x,su)),{'class':'chip','aria-pressed':String(!!va.sup),'data-super':x.u}));
        sg.appendChild(sw);box.appendChild(sg);}
    }
    var kp=(x.t==='D'||x.t==='SA')&&kaesePartner(x.k);
    if(kp){
      var mit=VAR[x.k]?!!VAR[x.k].kae:!!MIT_K[x.k];
      var kg=el('div','z-gruppe');kg.appendChild(el('span','z-gruppe-titel',L('Käse','Cheese')));var kw=el('div','z-chips');
      kw.appendChild(knopf(L('mit Käse','with cheese')+(mit?'':preisDiff(x,kp)),{'class':'chip','aria-pressed':String(mit),'data-kaese':x.u}));
      kg.appendChild(kw);box.appendChild(kg);
    }
    if(x.t==='D'||x.t==='SA'){
      /* Gemüse: alles drin, Abgewähltes geht als „ohne …“ an den Laden */
      var gg=chips(L('Gemüse – abwählen, was nicht rein soll','Vegetables – tap to leave out'),OHNE,[],'ohne',x.u);
      gg.querySelectorAll('.chip').forEach(function(c){c.setAttribute('aria-pressed',String(!c.disabled&&o.ohne.indexOf(c.dataset.w)<0));});
      box.appendChild(gg);
    }
    if(x.t==='S'){var wg=chips(L('3 Zutaten Ihrer Wahl (','3 toppings of your choice (')+o.wahl.length+L(' von 3)',' of 3)'),GEMUESE.concat(ohneFleisch(FLEISCH),KAESE).concat(o.wahl.filter(function(v){return ohneFleisch([v]).length===0;})),o.wahl,'wahl',x.u);
      wg.querySelectorAll('.chip').forEach(function(c){if(o.ohne.indexOf(c.dataset.w)>-1){c.disabled=true;c.classList.add('chip-aus');c.setAttribute('aria-pressed','false');
        c.textContent=w(c.dataset.w)+L(' – abgewählt',' – left out');}});
      box.appendChild(wg);}
    if(x.t==='R')box.appendChild(chips(L('Variante','Option'),(x.v||'').split('|').filter(Boolean),[o.va],'va',x.u));
    if(x.t==='B')box.appendChild(chips(L('Belag (einer zur Wahl)','Topping (choose one)'),ohneFleisch(BELAG).concat(o.va&&ohneFleisch([o.va]).length===0?[o.va]:[]),[o.va],'va',x.u));
    if(x.t==='P'||x.t==='R'||x.t==='S'){
      var pz=x.t==='S'?['Käse']:pizzaZutaten(x);
      var pg=chips(L('Zutaten – abwählen, was nicht drauf soll','Toppings – tap to leave out'),pz,[],'ohne',x.u);
      pg.querySelectorAll('.chip').forEach(function(c){c.setAttribute('aria-pressed',String(!c.disabled&&o.ohne.indexOf(c.dataset.w)<0));});
      box.appendChild(pg);
    }
    var nichtExtra=function(v){return o.ohne.indexOf(v)<0;};
    if(x.t==='P'||x.t==='S'||x.t==='R'){
      box.appendChild(chips(L('Extra je Zutat +1,50 €','Extra per topping +1,50 €'),GEMUESE.filter(nichtExtra),o.ex,'ex',x.u));
      box.appendChild(chips(L('Extra je Zutat +2,00 €','Extra per topping +2,00 €'),ohneFleisch(FLEISCH).concat(KAESE).concat(o.ex.filter(function(v){return FLEISCH.indexOf(v)>-1&&DIAET;})).filter(nichtExtra),o.ex,'ex',x.u));
    }
    return box;
  }
  function zeichnen(){
    zettel.forEach(bereinigen);
    var n=anzahl();
    zl.hidden=n===0;document.body.classList.toggle('mit-zettel',n>0);
    zl.querySelector('.zl-anzahl').textContent=n;zl.querySelector('.zl-summe').textContent=euro(summe());
    zl.setAttribute('aria-label',L('Meine Bestellung ansehen: ','View my order: ')+n+(n===1?L(' Gericht, ',' dish, '):L(' Gerichte, ',' dishes, '))+euro(summe()));
    zliste.textContent='';
    zettel.forEach(function(x){
      var li=el('li','z-eintrag'),kopf=el('div');
      var na=nameA(x);
      kopf.appendChild(el('span','z-name',na+(x.g?' ('+x.g+')':'')));
      var wt=x.t?wuensche(x,SP!=='de'):(fehlend(x).length?beschrA(x)+(beschrA(x)?' · ':'')+wuensche(x,SP!=='de'):beschrA(x));if(wt&&SP!=='de')wt=wt.charAt(0).toUpperCase()+wt.slice(1);
      if(x.fuer)kopf.appendChild(el('span','z-fuer',L('für ','for ')+x.fuer));if(wt){var wi=el('span','z-info',wt);if(/wählen|choose/.test(wt))wi.classList.add('z-fehlt');kopf.appendChild(wi);}
      var spZ=sperreZettel(x.k);
      if(spZ){var a0=abholung();kopf.appendChild(el('span','z-info z-fehlt',
        spZ.art==='aus'?L((a0.off?'':'heute ')+'in '+LADEN_N[a0.laden]+' nicht verfügbar – bitte entfernen',(a0.off?'':'today ')+'not available in '+LADEN_N[a0.laden]+' – please remove')
        :sperrText(spZ)+L(' – bitte andere Abholzeit wählen',' – please choose another pickup time')));li.classList.add('z-gesperrt');}
      li.appendChild(kopf);li.appendChild(el('span','z-preis',euro(stueck(x)*x.q)));
      var st=el('div','z-steuer'),q=el('span','z-menge',String(x.q));
      var m=knopf('−',{'data-a':'minus','data-u':x.u,'aria-label':(x.q===1?L('Entfernen: ','Remove: '):L('Eins weniger: ','One less: '))+na});
      var pl=knopf('+',{'data-a':'plus','data-u':x.u,'aria-label':L('Eins mehr: ','One more: ')+na});
      st.appendChild(m);st.appendChild(q);st.appendChild(pl);
      /* „Fertig“ steht beim Anpassen dort, wo vorher „Anpassen“ war – rechts, gut mit dem Daumen erreichbar */
      if(x.t&&offen===x.u)st.appendChild(knopf(L('Fertig','Done'),{'class':'z-anpassen z-fertig','data-fertig':x.u}));
      if(x.t&&offen!==x.u)st.appendChild(knopf(x.q>1?L('Eins davon anpassen','Customize one of them'):L('Anpassen','Customize'),{'class':'z-anpassen','data-anpassen':x.u}));
      li.appendChild(st);
      if(offen===x.u)li.appendChild(editor(x));
      var no=document.createElement('input');no.className='z-notiz';no.type='text';no.value=x.notiz||'';no.dataset.u=x.u;no.id='notiz-'+x.u;
      no.placeholder=L('Weitere Wünsche','Other requests');no.setAttribute('aria-label',L('Weitere Wünsche zu ','Other requests for ')+na);li.appendChild(no);
      zliste.appendChild(li);
    });
    zsumme.textContent=euro(summe());codeZeigen();
    huelle.querySelector('.zettel-leer').hidden=n>0;huelle.querySelector('.zettel-voll').hidden=n===0;
    abgleichen();letzteZeigen();if(typeof sammelZeigen==='function'&&sTeil)sammelZeigen();
  }
  function finde(u){return zettel.find(function(x){return x.u===+u;});}
  function abgleichen(){
    document.querySelectorAll('li[data-k]').forEach(function(li){
      var k=li.dataset.k,mehr=!!li.dataset.g,alt=li.querySelector(':scope > .mengen'),proG={},reihe=[];
      zettel.forEach(function(x){if(x.k!==k)return;if(!(x.g in proG)){proG[x.g]=0;reihe.push(x.g);}proG[x.g]+=x.q;});
      li.classList.toggle('im-zettel',reihe.length>0&&!mehr);
      if(!reihe.length){if(alt)alt.remove();return;}
      var box=alt||el('div','mengen');box.textContent='';
      reihe.forEach(function(g){
        var z=el('span','stepper');if(g)z.appendChild(el('span','st-g',g));
        var nm=(SP!=='de'?nameFremd(li,li.dataset.n):li.dataset.n)+(g?' '+g:'');
        z.appendChild(knopf('−',{'data-st':'minus','data-k':k,'data-g':g,'aria-label':L('Eins weniger: ','One less: ')+nm}));
        z.appendChild(el('span','st-q',String(proG[g])));
        z.appendChild(knopf('+',{'data-st':'plus','data-k':k,'data-g':g,'aria-label':L('Eins mehr: ','One more: ')+nm}));
        box.appendChild(z);
      });
      if(!alt)li.appendChild(box);
    });
  }
  function hinzufuegen(li,g,c,btn){
    var neu={k:li.dataset.k,n:li.dataset.n,d:li.dataset.d,g:g,c:c,q:1,t:li.dataset.t||'',v:li.dataset.v||'',o:grund(li.dataset.t),notiz:'',u:uidZ++};
    var s1=sig(neu),x=zettel.find(function(y){return sig(y)===s1;});
    if(x)x.q++;else zettel.push(neu);
    speichern();zeichnen();
    var hinweis=neu.t==='S'?L(' Zutaten in der Bestellung wählen.',' Choose the toppings in your order.'):neu.t==='R'?L(' Variante in der Bestellung wählen.',' Choose the option in your order.'):neu.t==='B'?L(' Belag in der Bestellung wählen.',' Choose the topping in your order.'):'';
    var meldung=nameA(neu)+(g?' ('+g+')':'')+L(' ist in Ihrer Bestellung.',' added to your order.')+hinweis;
    melden(meldung);
    if(btn){btn.classList.add('ok');btn.textContent='✓';setTimeout(function(){btn.classList.remove('ok');btn.textContent='+';},1200);}
  }
  document.addEventListener('click',function(ev){
    var b=ev.target.closest('.plus');
    if(b){
      var li=b.closest('li[data-k]'),preise=li.dataset.p.split('|').map(Number),gr=li.dataset.g?li.dataset.g.split('|'):[];
      if(preise.length===1){hinzufuegen(li,'',preise[0],b);return;}
      var alt=li.querySelector('.wahl');if(alt){alt.remove();return;}
      var w=el('div','wahl');
      gr.forEach(function(g,i){var k=knopf(g+': '+euro(preise[i]),{});k.addEventListener('click',function(){hinzufuegen(li,g,preise[i],b);w.remove();});w.appendChild(k);});
      li.appendChild(w);w.querySelector('button').focus();return;
    }
    var st=ev.target.closest('[data-st]');
    if(st){
      var li2=st.closest('li[data-k]'),k=st.dataset.k,g=st.dataset.g;
      if(st.dataset.st==='plus'){var pr=li2.dataset.p.split('|').map(Number),gs=li2.dataset.g?li2.dataset.g.split('|'):[''];hinzufuegen(li2,g,pr[Math.max(0,gs.indexOf(g))]);}
      else{for(var i=zettel.length-1;i>=0;i--){if(zettel[i].k===k&&zettel[i].g===g){zettel[i].q--;if(zettel[i].q<1)zettel.splice(i,1);break;}}speichern();zeichnen();}
      var neuB=li2.querySelector('.mengen [data-st="'+st.dataset.st+'"][data-g="'+g+'"]');if(neuB)neuB.focus();else{var pk=li2.querySelector('.plus');if(pk)pk.focus();}
      return;
    }
    if(!zliste.contains(ev.target))return;
    var a=ev.target.closest('[data-a]');
    if(a){var x=finde(a.dataset.u);if(!x)return;
      if(a.dataset.a==='plus')x.q++;else{x.q--;if(x.q<1){zettel.splice(zettel.indexOf(x),1);if(offen===x.u)offen=null;}}
      speichern();zeichnen();if(anzahl()===0)schliessen();return;}
    var an=ev.target.closest('[data-anpassen]');
    if(an){var y=finde(an.dataset.anpassen);if(!y)return;
      if(y.q>1){y.q--;var kopie=JSON.parse(JSON.stringify(y));kopie.q=1;kopie.u=uidZ++;zettel.splice(zettel.indexOf(y)+1,0,kopie);y=kopie;}
      offen=y.u;zeichnen();var erst=zliste.querySelector('.z-optionen .chip');if(erst)erst.focus();return;}
    var ch=ev.target.closest('[data-o]');
    if(ch){var z=finde(ch.dataset.u);if(!z)return;var o=z.o,art=ch.dataset.o,wert=ch.dataset.w;
      if(art==='va')o[art]=wert;
      else{var arr=o[art],i2=arr.indexOf(wert);if(i2>-1)arr.splice(i2,1);else if(!(art==='wahl'&&arr.length>=3))arr.push(wert);
        if(art==='ohne'&&o.ohne.indexOf(wert)>-1){o.ex=o.ex.filter(function(v){return v!==wert;});o.wahl=(o.wahl||[]).filter(function(v){return v!==wert;});}}
      speichern();zeichnen();var wieder=zliste.querySelector('[data-o="'+art+'"][data-w="'+wert+'"]');if(wieder)wieder.focus();return;}
    var fu=ev.target.closest('[data-fuell]');
    if(fu){var zf=finde(fu.dataset.u);if(!zf)return;var zielF=variante(zf.k,{f:fu.dataset.fuell});if(!zielF)return;
      wechseln(zf,zielF);speichern();zeichnen();var fw2=zliste.querySelector('[data-fuell="'+fu.dataset.fuell+'"]');if(fw2)fw2.focus();return;}
    var bb=ev.target.closest('[data-bei]');
    if(bb){var zb2=finde(bb.dataset.u);if(!zb2||!VAR[zb2.k]||VAR[zb2.k].bei===bb.dataset.bei)return;var zielB=variante(zb2.k,{bei:bb.dataset.bei});if(!zielB)return;
      wechseln(zb2,zielB);speichern();zeichnen();var bw2=zliste.querySelector('[data-bei="'+bb.dataset.bei+'"]');if(bw2)bw2.focus();return;}
    var sb=ev.target.closest('[data-super]');
    if(sb){var zs=finde(sb.dataset.super);if(!zs||!VAR[zs.k])return;var zielS=variante(zs.k,{sup:VAR[zs.k].sup?0:1},true);if(!zielS)return;
      wechseln(zs,zielS);speichern();zeichnen();var sw2=zliste.querySelector('[data-super]');if(sw2)sw2.focus();return;}
    var kb=ev.target.closest('[data-kaese]');
    if(kb){var zk=finde(kb.dataset.kaese);if(!zk)return;var zielK=kaesePartner(zk.k);if(!zielK)return;
      wechseln(zk,zielK);speichern();zeichnen();var kw2=zliste.querySelector('[data-kaese]');if(kw2)kw2.focus();return;}
    var f=ev.target.closest('[data-fertig]');
    if(f){offen=null;zusammenfassen();speichern();zeichnen();return;}
  });
  zliste.addEventListener('input',function(ev){var x=finde(ev.target.dataset.u);if(x){x.notiz=ev.target.value;speichern();}});
  zliste.addEventListener('change',function(ev){if(ev.target.classList.contains('z-notiz')){zusammenfassen();speichern();}});
  function oeffnen(){zuletzt=document.activeElement;zmeld.hidden=true;huelle.hidden=false;document.documentElement.style.overflow='hidden';document.getElementById('zettel-titel').focus();}
  function schliessen(){offen=null;zusammenfassen();speichern();zeichnen();huelle.hidden=true;document.documentElement.style.overflow='';if(zuletzt&&zuletzt.focus&&!zl.hidden)zuletzt.focus();}
  zl.addEventListener('click',oeffnen);
  huelle.addEventListener('click',function(ev){if(ev.target.closest('[data-zu]'))schliessen();});
  document.addEventListener('keydown',function(ev){
    if(huelle.hidden)return;
    if(ev.key==='Escape'){schliessen();return;}
    if(ev.key!=='Tab')return;
    /* Tastatur bleibt im offenen Bestellzettel (Dialog) */
    var f=[].filter.call(huelle.querySelectorAll('.zettel a[href],.zettel button,.zettel input,.zettel select,.zettel [tabindex]'),function(x){return !x.disabled&&x.offsetParent!==null;});
    if(!f.length)return;var erst=f[0],letzt=f[f.length-1];
    if(ev.shiftKey&&(document.activeElement===erst||!huelle.contains(document.activeElement))){ev.preventDefault();letzt.focus();}
    else if(!ev.shiftKey&&(document.activeElement===letzt||!huelle.contains(document.activeElement))){ev.preventDefault();erst.focus();}
  });
  /* Abholung: Laden, Uhrzeit, Name */
  var AK='saray-abholung',abh={laden:'',tag:'',zeit:'',name:''},VORBESTELL_TAGE=%%VORBESTELL_TAGE%%;
  try{abh=Object.assign(abh,JSON.parse(localStorage.getItem(AK)||'{}'));}catch(e){}
  /* ?laden=freital (z. B. vom QR-Aufsteller an der Theke) wählt den Laden vor */
  (function(){var m=/[?&]laden=(freital|altenberg)/.exec(location.search);if(m&&abh.laden!==m[1]){abh.laden=m[1];abh.zeit='';}})();
  function abhSpeichern(){try{localStorage.setItem(AK,JSON.stringify(abh));}catch(e){}}
  var selTag=document.getElementById('abhol-tag'),selZeit=document.getElementById('abhol-zeit'),eName=document.getElementById('abhol-name'),hinweisZ=document.getElementById('abhol-hinweis');
  function zeitText(m,en){var h=Math.floor(m/60),r=m%60;return h+':'+(r<10?'0':'')+r+(en?'':' Uhr');}
  /* Datum eines Tages ab heute (deutsche Zeit): ISO-Schlüssel und Anzeige */
  function tagDatum(off,opt,loc){return new Intl.DateTimeFormat(loc||'de-DE',Object.assign({timeZone:'Europe/Berlin'},opt)).format(new Date(Date.now()+off*864e5));}
  function tagKurz(off,en){return tagDatum(off,{weekday:'short',day:'numeric',month:en?'short':'2-digit'},LOC[SP]||'en-GB');}
  function tagLang(off){var t=tagDatum(off,{weekday:'long',day:'2-digit',month:'2-digit'});return /\.$/.test(t)?t:t+'.';}   /* „Freitag, 24.10.“ */
  /* mögliche Abholzeiten eines Tages (Minuten), 15-Minuten-Raster, heute frühestens in 20 Minuten */
  function slots(off){
    var n=jetzt(),h=tagZeit(abh.laden,off),res=[];if(!h)return res;
    var start=h[0]+15;if(off===0)start=Math.max(start,Math.ceil((n.min+20+warte(abh.laden))/15)*15);
    for(var m=start;m<=h[1]-15;m+=15)res.push(m);
    return res;
  }
  /* Zug ab Altenberg: Abfahrten (Minuten) an einem Tag (ISO-Datum) */
  var ZUG=%%ZUG%%;
  function zuege(iso){
    if(!ZUG||iso>ZUG.gueltig_bis)return [];
    var wt=new Date(iso+'T12:00:00Z').getUTCDay(),fei=ZUG.werktags_nicht.indexOf(iso)>-1,z=ZUG.taeglich.slice();
    if(wt>=1&&wt<=5&&!fei)z=z.concat(ZUG.werktags);
    ZUG.extra.forEach(function(x){var we=(wt===0||wt===6)&&x.wochenende.some(function(r){return iso>=r[0]&&iso<=r[1];});
      if(we||x.auch.indexOf(iso)>-1)z.push(x.zeit);});
    return z.map(minAus).sort(function(a,b){return a-b;}).filter(function(m,i,l){return l.indexOf(m)===i;});
  }
  var zugBox=document.getElementById('zug-wahl');
  function zugZeigen(off,sl){
    if(!zugBox)return;zugBox.textContent='';
    var vor=off===0?'heute':off===1?'morgen, '+tagLang(1):tagLang(off),en=SP!=='de';
    if(abh.laden!==ZUG.laden){zugBox.hidden=true;return;}
    var paare=[];zuege(isoTag(off)).forEach(function(d){var s=sl.filter(function(m){return m<=d-ZUG.puffer&&m>=d-45;});if(s.length)paare.push([d,s[s.length-1]]);});
    paare=paare.slice(0,6);zugBox.hidden=!paare.length;if(!paare.length)return;
    zugBox.appendChild(el('p','zug-titel',L('🚆 Mit dem Zug zurück? Abholung passend zur Abfahrt:','🚆 Taking the train? Pickup matched to your departure:')));
    var reihe=el('div','zug-chips');
    paare.forEach(function(p){var v=vor+', '+zeitText(p[1]),dz=zeitText(p[0],true),az=zeitText(p[1],true);
      var b=el('button','chip',L('Zug '+dz+' → abholen '+az,'Train '+dz+' → pickup '+az));b.type='button';
      b.setAttribute('aria-pressed',String(abh.zug===dz&&abh.zeit===v));
      b.addEventListener('click',function(){abh.zeit=v;abh.zug=dz;selZeit.value=v;abhSpeichern();zugZeigen(off,sl);zeichnen();waAktualisieren();});
      reihe.appendChild(b);});
    zugBox.appendChild(reihe);
    zugBox.appendChild(el('p','zug-quelle',L('Fahrplan ohne Gewähr, Richtung Heidenau/Dresden.','Timetable without guarantee, towards Heidenau/Dresden.')));
  }
  /* Wintersaison Altenberg: Kasten oben; automatisch nach Datum oder per Chef-App an/aus */
  var WINTER=%%WINTER%%;
  function winterAktiv(){if(WINTER.modus==='an')return true;if(WINTER.modus==='aus')return false;var md=isoTag(0).slice(5);
    return WINTER.von<=WINTER.bis?(md>=WINTER.von&&md<=WINTER.bis):(md>=WINTER.von||md<=WINTER.bis);}
  setTimeout(function(){var w=document.getElementById('winter');if(!w)return;try{w.hidden=!winterAktiv();}catch(e){}
    var b=document.getElementById('winter-bestellen');if(b)b.addEventListener('click',function(){abh.laden='altenberg';abhSpeichern();ladenZeigen();oeffnen();});
    var g=document.getElementById('winter-gruppe');if(g)g.addEventListener('click',function(){abh.laden='altenberg';abhSpeichern();var s=document.querySelector('[data-sammel-start]');if(s)s.click();});},0);
  function zeitenFuellen(){
    selZeit.textContent='';selTag.textContent='';hinweisZ.hidden=true;ZINFO={};
    if(!abh.laden){[selTag,selZeit].forEach(function(s){var o=el('option',null,L('Bitte zuerst den Laden wählen','Please choose the shop first'));o.value='';s.appendChild(o);s.disabled=true;});return;}
    selTag.disabled=selZeit.disabled=false;
    var n=jetzt(),en=SP!=='de',tage=[];
    for(var i=0;i<=VORBESTELL_TAGE;i++){if(slots(i).length)tage.push(i);}
    tage.forEach(function(off){
      var t=off===0?L('Heute','Today'):off===1?L('Morgen, ','Tomorrow, ')+tagKurz(1,en):tagKurz(off,en);
      var o=el('option',null,t);o.value=tagDatum(off,{year:'numeric',month:'2-digit',day:'2-digit'},'en-CA');o.dataset.off=off;selTag.appendChild(o);
    });
    if(!tage.length)return;
    if(![].some.call(selTag.options,function(o){return o.value===abh.tag;}))abh.tag=selTag.options[0].value;
    selTag.value=abh.tag;
    var off=+selTag.selectedOptions[0].dataset.off,optionen=[];
    if(tage[0]>0){hinweisZ.textContent=L('Heute ist keine Abholung mehr möglich. Sie können vorbestellen.','Pickup is no longer possible today. You can pre-order.');hinweisZ.hidden=false;}
    /* Wert = Text für die Nachricht an den Laden (immer deutsch) */
    var vor=off===0?'heute':off===1?'morgen, '+tagLang(1):tagLang(off);
    var wz=warte(abh.laden),h0=tagZeit(abh.laden,0);
    var hz=tagZeit(abh.laden,0);
    var sl0=slots(0);
    if(off===0&&hz&&sl0.length&&n.min>=hz[1]-60){var lz=sl0[sl0.length-1];hinweisZ.textContent=L('Bald Feierabend: letzte Abholung heute um '+zeitText(lz)+'.','Closing soon: last pickup today at '+zeitText(lz,true)+'.');hinweisZ.hidden=false;}
    if(off===0&&wz){hinweisZ.textContent=L('Gerade viel los: Abholung frühestens in ca. '+(wz+20)+' Minuten.','Busy right now: earliest pickup in about '+(wz+20)+' minutes.');hinweisZ.hidden=false;}
    if(off===0&&h0&&n.min>=h0[0]){
      optionen.push({v:'heute, so schnell wie möglich',t:L('So schnell wie möglich','As soon as possible')});ZINFO['heute, so schnell wie möglich']={off:0,min:n.min+20+wz};}
    slots(off).forEach(function(m){var v=vor+', '+zeitText(m);optionen.push({v:v,t:zeitText(m,en)});ZINFO[v]={off:off,min:m};});
    optionen.forEach(function(x){var o=el('option',null,x.t);o.value=x.v;selZeit.appendChild(o);});
    if(optionen.some(function(x){return x.v===abh.zeit;}))selZeit.value=abh.zeit;else abh.zeit=selZeit.value;
    if(abh.zug&&!ZINFO[abh.zeit])abh.zug='';
    zugZeigen(off,slots(off));
    abhSpeichern();zeichnenSpaeter();
  }
  var zsp=false;function zeichnenSpaeter(){if(zsp)return;zsp=true;setTimeout(function(){zsp=false;zeichnen();waAktualisieren();},0);}
  var WA=%%WA%%,waKnopf=document.getElementById('zettel-whatsapp'),waHinweis=document.getElementById('wa-hinweis');
  var verfHinweis=document.getElementById('verf-hinweis');
  function konflikte(){return zettel.filter(function(x){return sperreZettel(x.k);}).length;}
  function waAktualisieren(){
    var nr=abh.laden&&WA[abh.laden],kf=konflikte();
    verfHinweis.hidden=!kf;document.getElementById('zettel-kopieren').disabled=!!kf;
    verfHinweis.textContent=kf===1?L('Ein Gericht ist zur gewählten Zeit nicht zu haben. Bitte oben ändern.','One dish is not available at the chosen time. Please change it above.')
      :L(kf+' Gerichte sind zur gewählten Zeit nicht zu haben. Bitte oben ändern.',kf+' dishes are not available at the chosen time. Please change them above.');
    if(kf||sammel)nr=null;
    waKnopf.hidden=!nr;waHinweis.hidden=!!nr||!!kf||!Object.keys(WA).length;
    if(nr)waKnopf.href='https://wa.me/'+nr+'?text='+encodeURIComponent(zettelText(true));
  }
  function ladenZeigen(){
    document.querySelectorAll('[data-laden]').forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.laden===abh.laden));});
    document.querySelectorAll('[data-anruf]').forEach(function(a){a.hidden=!!abh.laden&&a.dataset.anruf!==abh.laden;});
    zeitenFuellen();waAktualisieren();
  }
  document.querySelectorAll('[data-laden]').forEach(function(b){b.addEventListener('click',function(){abh.laden=b.dataset.laden;abhSpeichern();ladenZeigen();verfZeigen();});});
  selZeit.addEventListener('change',function(){abh.zeit=selZeit.value;abh.zug='';try{zeitenFuellen();}catch(e){}abhSpeichern();zeichnen();waAktualisieren();});
  selTag.addEventListener('change',function(){abh.tag=selTag.value;abh.zeit='';abhSpeichern();zeitenFuellen();waAktualisieren();});
  eName.value=abh.name||'';eName.addEventListener('input',function(){abh.name=eName.value;abhSpeichern();waAktualisieren();});
  ladenZeigen();
  zl.addEventListener('click',function(){zeitenFuellen();waAktualisieren();});
  var TEL=%%TEL%%,waGesendet=document.getElementById('wa-gesendet');
  waKnopf.addEventListener('click',function(){waAktualisieren();letzteMerken();
    try{var bw=JSON.parse(localStorage.getItem('saray-bewertung')||'null');if(!bw||!bw.fertig)localStorage.setItem('saray-bewertung',JSON.stringify({l:abh.laden,t:Date.now()}));}catch(e){}
    if(waKnopf.hidden)return;var tl=TEL[abh.laden];waGesendet.textContent='';bnrGesendet=true;
    var nrP=el('p','wa-nr');nrP.appendChild(document.createTextNode(L('Ihre Bestellnummer: ','Your order number: ')));nrP.appendChild(el('b',null,BNR));waGesendet.appendChild(nrP);
    waGesendet.appendChild(document.createTextNode(L('Gesendet? Der Laden bestätigt Ihre Bestellung per WhatsApp. Ohne Antwort bitte anrufen: ','Sent? The shop confirms your order via WhatsApp. No reply? Please call: ')));
    var a=el('a',null,tl[0]);a.href='tel:'+tl[1];waGesendet.appendChild(a);
    var zi=ZINFO[abh.zeit];
    if(zi){var kb=knopf(L('📅 Abholung in den Kalender','📅 Add pickup to calendar'),{'class':'knopf knopf-linie wa-kalender','id':'wa-kalender'});
      var ics=icsText(zi,BNR);kb.addEventListener('click',function(){icsLaden(ics,'saray-abholung-'+BNR+'.ics');});waGesendet.appendChild(kb);}
    waGesendet.hidden=false;});
  /* Kalendereintrag (.ics) für die Abholung, mit Erinnerung 15 Minuten vorher */
  var ADR=%%ADR%%;
  function icsText(zi,nr){
    var d=tagDatum(zi.off,{year:'numeric',month:'2-digit',day:'2-digit'},'en-CA').replace(/-/g,''),
        z=function(m){return ('0'+Math.floor(m/60)).slice(-2)+('0'+m%60).slice(-2)+'00';},
        esc=function(t){return String(t).replace(/[\\;,]/g,function(c){return '\\'+c;}).replace(/\n/g,'\\n');},
        jetztZ=new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d+/,'');
    return ['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Saray Doener//Bestellung//DE','BEGIN:VEVENT',
      'UID:'+nr+'-'+d+'-'+zi.min+'@saray-doener','DTSTAMP:'+jetztZ,
      'DTSTART;TZID=Europe/Berlin:'+d+'T'+z(zi.min),'DTEND;TZID=Europe/Berlin:'+d+'T'+z(zi.min+15),
      'SUMMARY:'+esc('Saray Döner abholen ('+nr+')'),'LOCATION:'+esc(ADR[abh.laden]||''),
      'DESCRIPTION:'+esc(zettel.map(function(x){return x.q+'× '+x.n;}).join('\n')+'\nSumme: '+euro(summe())+' (nur Barzahlung)'),
      'BEGIN:VALARM','ACTION:DISPLAY','DESCRIPTION:'+esc('Saray Döner abholen'),'TRIGGER:-PT15M','END:VALARM',
      'END:VEVENT','END:VCALENDAR'].join('\r\n');
  }
  function icsLaden(text,name){
    var url=URL.createObjectURL(new Blob([text],{type:'text/calendar;charset=utf-8'})),a=document.createElement('a');
    a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(function(){URL.revokeObjectURL(url);},4000);
  }
  /* „Wie letztes Mal“: Zettel merken, sobald er abgeschickt, kopiert oder vorgelesen wird */
  var LK='saray-letzte',letzte=null,boxL=document.getElementById('letzte');
  try{letzte=JSON.parse(localStorage.getItem(LK)||'null');}catch(e){letzte=null;}
  function letzteMerken(){
    if(!zettel.length)return;
    letzte={am:Date.now(),p:zettel.map(function(x){return {k:x.k,g:x.g,q:x.q,o:x.o,notiz:x.notiz||''};})};
    try{localStorage.setItem(LK,JSON.stringify(letzte));}catch(e){}
  }
  function letzteGueltig(){
    if(!letzte||!Array.isArray(letzte.p))return [];
    return letzte.p.filter(function(p){var li=gerichtLi(p.k);if(!li)return false;var gs=li.dataset.g?li.dataset.g.split('|'):[''];return gs.indexOf(p.g||'')>-1;});
  }
  function letzteZeigen(){
    if(!boxL)return;
    var g=letzteGueltig(),suche=document.getElementById('suche-feld');
    boxL.hidden=!g.length||zettel.length>0||!!(suche&&suche.value.trim());
    if(boxL.hidden)return;
    var zus={};g.forEach(function(p){var li=gerichtLi(p.k),nm=(SP!=='de'?nameFremd(li,li.dataset.n):li.dataset.n)+(p.g?' ('+p.g+')':'');zus[nm]=(zus[nm]||0)+p.q;});
    document.getElementById('letzte-liste').textContent=Object.keys(zus).map(function(k){return zus[k]+'× '+k;}).join(' · ');
  }
  /* Eintrag aus gespeicherten/geteilten Daten mit aktuellem Preis; null, wenn es das Gericht nicht mehr gibt */
  function ausDaten(p,fuer){
    var li=p&&typeof p.k==='string'&&gerichtLi(p.k);if(!li)return null;
    var gs=li.dataset.g?li.dataset.g.split('|'):[''],i=gs.indexOf(p.g||'');if(i<0)return null;
    var pr=li.dataset.p.split('|').map(Number),o=Object.assign(grund(li.dataset.t),JSON.parse(JSON.stringify(p.o||{})));
    ['s','ohne','ex','wahl'].forEach(function(a){if(!Array.isArray(o[a]))o[a]=[];o[a]=o[a].filter(function(v){return typeof v==='string';}).slice(0,12);});
    if(typeof o.va!=='string')o.va='';
    return {k:p.k,n:li.dataset.n,d:li.dataset.d,g:p.g||'',c:pr[i],q:Math.min(50,Math.max(1,+p.q||1)),t:li.dataset.t||'',v:li.dataset.v||'',o:o,
      notiz:String(p.notiz||'').slice(0,200),fuer:fuer?String(fuer).slice(0,40):(p.fuer?String(p.fuer).slice(0,40):''),u:uidZ++};
  }
  document.getElementById('letzte-knopf').addEventListener('click',function(){
    letzteGueltig().forEach(function(p){var x=ausDaten(p);if(x)zettel.push(x);});
    zusammenfassen();speichern();zeichnen();zeitenFuellen();waAktualisieren();oeffnen();
  });
  document.querySelectorAll('[data-anruf]').forEach(function(a){a.addEventListener('click',letzteMerken);});
  var codeBox=document.getElementById('code-box'),codeFeld=document.getElementById('code-feld'),codeInfo=document.getElementById('code-info');
  function codeZeigen(){if(!codeBox)return;var d=codeAktiv(),rb=rabatt();codeBox.hidden=!CODES.length;
    if(abh.code){var ganz=CODES.filter(function(x){return x.h===abh.code.h;})[0];
      var en=SP!=='de';
      codeInfo.textContent=d?(en?fuell(T('{x}: {p} % off'),{x:d.name,p:d.prozent}):d.name+': '+d.prozent+' % Rabatt')+(rb?' (−'+euro(rb)+')':'')+(d.za!=null?' · '+zeitText(d.za,true)+'–'+zeitText(d.zb,en):'')
        :ganz?(en?fuell(T('Code {x} does not apply to this pickup.'),{x:abh.code.c}):'Code '+abh.code.c+' gilt nicht für diese Abholung.')+(ganz.za!=null?' ('+zeitText(ganz.za,true)+'–'+zeitText(ganz.zb,en)+')':''):L('Code abgelaufen.','Code expired.');
      codeInfo.hidden=false;document.getElementById('code-weg').hidden=false;}else{codeInfo.hidden=true;document.getElementById('code-weg').hidden=true;}}
  function codeHash(c){return crypto.subtle.digest('SHA-256',new TextEncoder().encode('saray|'+c)).then(function(b){return [].map.call(new Uint8Array(b),function(x){return ('0'+x.toString(16)).slice(-2);}).join('');});}
  if(codeBox){
    document.getElementById('code-form').addEventListener('submit',function(ev){ev.preventDefault();var c=codeFeld.value.toUpperCase().replace(/[^A-Z0-9]/g,'');if(!c)return;
      if(!window.crypto||!crypto.subtle){codeInfo.textContent=L('Code hier nicht prüfbar.','Code cannot be checked here.');codeInfo.hidden=false;return;}
      codeHash(c).then(function(h){var d=CODES.filter(function(x){return x.h===h;})[0];
        if(!d){codeInfo.textContent=L('Diesen Code kennen wir nicht.','Unknown code.');codeInfo.hidden=false;return;}
        abh.code={h:h,c:c};codeFeld.value='';abhSpeichern();zeichnen();waAktualisieren();});});
    document.getElementById('code-weg').addEventListener('click',function(){delete abh.code;abhSpeichern();zeichnen();waAktualisieren();});}
  /* Küchenansicht: Bestellung als Link (Daten stehen im Link selbst, kein Server) */
  function b64url(t){return btoa(unescape(encodeURIComponent(t))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');}
  function kuecheLink(){
    if(!/^https?:/.test(location.protocol)||!zettel.length)return '';
    var zi=ZINFO[abh.zeit],t='';
    if(zi){var hh=Math.floor(zi.min/60),mm=zi.min%60;t=isoTag(zi.off)+'T'+(hh<10?'0':'')+hh+':'+(mm<10?'0':'')+mm;}
    var o={v:1,nr:BNR,l:abh.laden||'',z:abh.zeit||'',t:t,m:(abh.name||'').slice(0,40),s:summe(),r:rabatt(),rc:(codeAktiv()||{}).name||'',zug:abh.zug||'',sp:SP,
      test:document.body.classList.contains('vorschau')?1:0,a:Date.now(),
      p:zettel.map(function(x){var w=x.t||fehlend(x).length?wuensche(x):'';return [x.q,x.n+(x.g?' ('+x.g+')':''),w,x.fuer||'',x.notiz||'',stueck(x)*x.q];})};
    return new URL('kueche/#b='+b64url(JSON.stringify(o)),location.href).href;
  }
  function zettelText(mitKueche){
    var test=document.body.classList.contains('vorschau')?['*TEST – Entwurf, keine echte Bestellung*','']:[];
    var vb=ZINFO[abh.zeit]&&ZINFO[abh.zeit].off>0;
    var z=[(vb?'Vorbestellung':'Bestellung')+' Saray Döner'+(abh.laden?' '+(abh.laden==='freital'?'Freital':'Altenberg'):'')];
    z.push('Bestellnummer: '+BNR);
    if(abh.zeit)z.push('Abholung: '+abh.zeit+(abh.zug&&abh.laden===ZUG.laden?' (Zug '+abh.zug+')':''));
    if(abh.name)z.push('Name: '+abh.name);
    z.push('');
    zettel.forEach(function(x){z.push(zeileText(x));});
    var rb=rabatt(),cd=codeAktiv();if(rb&&cd)z.push('Firmen-Code: '+abh.code.c+' ('+cd.name+') – '+cd.prozent+' % Rabatt: −'+euro(rb));
    z.push('Summe: '+euro(summe()));
    var kl=mitKueche?kuecheLink():'';if(kl){z.push('');z.push('Für die Küche: '+kl);}
    return test.concat(z).join('\n');
  }
  function zeileText(x){var w=x.t||fehlend(x).length?wuensche(x):'';
    return x.q+'× '+x.n+(x.g?' ('+x.g+')':'')+(w?', '+w:'')+(x.fuer?' (für '+x.fuer+')':'')+': '+euro(stueck(x)*x.q)+(aktionZ(x)?' (Aktion)':'')+(x.notiz?'\n   Wunsch: '+x.notiz:'');}
  /* Teilen: Teilen-Menü des Handys (WhatsApp, SMS, Mail, Teams …); sonst in die Zwischenablage kopieren */
  function teilen(t,titel){
    var kopiert=L('Bestellung kopiert – jetzt in WhatsApp, SMS, E-Mail oder Teams einfügen.','Order copied – now paste it into WhatsApp, a text message, e-mail or Teams.');
    function notfall(){var ta=document.createElement('textarea');ta.value=t;ta.setAttribute('readonly','');ta.style.position='fixed';ta.style.opacity='0';
      document.body.appendChild(ta);ta.select();var ok=false;try{ok=document.execCommand('copy');}catch(e){}ta.remove();
      melden(ok?kopiert:L('Kopieren hat nicht geklappt. Bitte die Bestellung abschreiben.','Copying did not work. Please write the order down.'));}
    function kopieren(){if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(t).then(function(){melden(kopiert);},notfall);else notfall();}
    if(navigator.share&&(window.matchMedia&&matchMedia('(pointer:coarse)').matches)){
      navigator.share({title:titel||'Bestellung Saray Döner',text:t}).catch(function(e){if(!e||e.name!=='AbortError')kopieren();});
    }else kopieren();
  }
  document.getElementById('zettel-kopieren').addEventListener('click',function(){letzteMerken();teilen(zettelText());});

  /* ---------- Sammelbestellung (ohne Server) ----------
     Einladung:  …/#sammel=<daten>  -> Teilnehmer wählen und schicken „ihren Teil“ zurück
     Teil:       …/#teil=<daten>    -> Sammler fügt ihn mit Namen („für Anna“) zur eigenen Bestellung hinzu */
  function kodieren(o){return btoa(unescape(encodeURIComponent(JSON.stringify(o)))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');}
  function dekodieren(t){t=t.replace(/-/g,'+').replace(/_/g,'/');while(t.length%4)t+='=';return JSON.parse(decodeURIComponent(escape(atob(t))));}
  function basisUrl(){return location.origin+location.pathname;}
  var SK='saray-sammel',SIK='saray-sammel-import',sammel=null;
  try{sammel=JSON.parse(localStorage.getItem(SK)||'null');}catch(e){sammel=null;}
  function sammelSpeichern(){try{if(sammel)localStorage.setItem(SK,JSON.stringify(sammel));else localStorage.removeItem(SK);}catch(e){}}
  var sDlg=document.getElementById('sammel-dialog'),sBand=document.getElementById('sammel-band'),sTeil=document.getElementById('sammel-teil');
  function dialog(titel,inhalt,knoepfe){
    document.getElementById('sammel-titel').textContent=titel;
    var box=document.getElementById('sammel-inhalt');box.textContent='';inhalt.forEach(function(x){box.appendChild(x);});
    var r=document.getElementById('sammel-knoepfe');r.textContent='';
    knoepfe.forEach(function(k,i){var b=knopf(k[0],{'class':i?'knopf knopf-linie':'knopf knopf-dunkel'});b.addEventListener('click',k[1]);r.appendChild(b);});
    sDlg.hidden=false;dlgAnpassen();
    /* Handy: Tastatur nicht sofort öffnen – erst wenn man ins Feld tippt */
    var beruehrung=window.matchMedia&&matchMedia('(pointer:coarse)').matches;
    var f=beruehrung?sDlg.querySelector('.sammel-box'):sDlg.querySelector('input,button');if(f)f.focus({preventScroll:true});
  }
  function dialogZu(){sDlg.hidden=true;if(huelle.hidden)document.documentElement.style.overflow='';}
  /* Fenster steht auf dem Handy oben (CSS) – kein Nachschieben beim Tippen; Seite dahinter festhalten */
  function dlgAnpassen(){document.documentElement.style.overflow='hidden';}
  sDlg.addEventListener('click',function(ev){if(ev.target===sDlg)dialogZu();});
  document.addEventListener('keydown',function(ev){if(ev.key==='Escape'&&!sDlg.hidden)dialogZu();});
  function nameFeld(){var f=document.createElement('input');f.type='text';f.id='sammel-name';f.autocomplete='given-name';f.maxLength=40;f.value=abh.name||'';
    var lb=el('label',null,L('Ihr Name','Your name'));lb.htmlFor='sammel-name';return [lb,f];}
  function einladen(){
    var nf=nameFeld(),fehler=el('p','abhol-hinweis');fehler.hidden=true;
    dialog(L('Gemeinsam bestellen','Order as a group'),[el('p',null,L('Sie laden andere ein. Jeder sucht sich sein Essen aus und schickt Ihnen seinen Teil zurück. Sie bestellen dann alles zusammen.','You invite others. Everyone picks their food and sends their part back to you. You then order everything together.'))].concat(nf,[fehler]),
      [[L('Einladung teilen','Share invitation'),function(){var name=nf[1].value.trim();
          if(!name){fehler.textContent=L('Bitte Ihren Namen eintragen.','Please enter your name.');fehler.hidden=false;nf[1].focus();return;}
          abh.name=name;eName.value=name;abhSpeichern();dialogZu();
          var link=basisUrl()+'#sammel='+kodieren({an:name,l:abh.laden||''});
          teilen('Ich bestelle bei Saray Döner für mehrere. Such dir dein Essen aus und schick mir deinen Teil zurück:\n'+link,'Sammelbestellung Saray Döner');}],
       [L('Abbrechen','Cancel'),dialogZu]]);
  }
  document.querySelectorAll('[data-sammel-start]').forEach(function(b){b.addEventListener('click',einladen);});
  function teilSchicken(){
    var name=(eName.value||'').trim();
    if(!name){eName.focus();melden(L('Bitte zuerst Ihren Namen eintragen.','Please enter your name first.'));return;}
    if(!zettel.length)return;
    var link=basisUrl()+'#teil='+kodieren({von:name,p:zettel.map(function(x){return {k:x.k,g:x.g,q:x.q,o:x.o,notiz:x.notiz||''};})});
    var z=['Mein Teil für die Sammelbestellung bei Saray Döner ('+name+'):'];zettel.forEach(function(x){z.push(zeileText(x));});
    z.push('Summe: '+euro(summe()),'','Zum Hinzufügen öffnen:',link);
    teilen(z.join('\n'),'Mein Teil – Saray Döner');
  }
  sTeil.addEventListener('click',teilSchicken);
  function sammelZeigen(){
    sBand.hidden=!sammel;
    document.querySelectorAll('.sammel-start').forEach(function(x){x.hidden=!!sammel;});
    if(sammel)document.getElementById('sammel-band-text').textContent=L('👥 Sammelbestellung für ','👥 Group order for ')+sammel.an+
      L(': Essen mit „+“ wählen, dann in „Meine Bestellung“ Ihren Teil zurückschicken.',': pick your food with “+”, then send your part back from “My order”.');
    sTeil.hidden=!sammel||!zettel.length;
    if(sammel){var sp=sTeil.querySelector('span')||sTeil;sp.textContent=L('Meinen Teil an ','Send my part to ')+sammel.an+L(' schicken','');}
    document.getElementById('sammel-einladen').hidden=!!sammel;
    document.getElementById('zettel').classList.toggle('im-sammel',!!sammel);
  }
  document.getElementById('sammel-ende').addEventListener('click',function(){sammel=null;sammelSpeichern();sammelZeigen();waAktualisieren();});
  document.getElementById('sammel-einladen').addEventListener('click',einladen);
  function linkPruefen(){
    var m=/^#(sammel|teil)=([A-Za-z0-9_-]+)/.exec(location.hash);if(!m)return;
    history.replaceState(null,'',location.pathname+location.search);
    var d;try{d=dekodieren(m[2]);}catch(e){melden(L('Der Link ist unvollständig. Bitte noch einmal schicken lassen.','The link is incomplete. Please ask for it again.'));return;}
    if(m[1]==='sammel'){
      if(!d||!d.an)return;
      sammel={an:String(d.an).slice(0,40)};sammelSpeichern();
      if(d.l&&ZEITEN[d.l]&&!abh.laden){abh.laden=d.l;abhSpeichern();ladenZeigen();}
      sammelZeigen();waAktualisieren();
      dialog(L('Sammelbestellung von ','Group order from ')+sammel.an,[el('p',null,L(sammel.an+' sammelt die Bestellung. Wählen Sie Ihr Essen mit „+“, öffnen Sie „Meine Bestellung“ und tippen Sie auf „Meinen Teil an '+sammel.an+' schicken“.',
        sammel.an+' is collecting the order. Pick your food with “+”, open “My order” and tap “Send my part to '+sammel.an+'”.'))],[[L('Los geht’s','Let’s go'),dialogZu]]);
      return;
    }
    var von=String(d&&d.von||'?').slice(0,40),teile=(d&&Array.isArray(d.p)?d.p:[]).slice(0,60).map(function(p){return ausDaten(p,von);}).filter(Boolean);
    var schon=[];try{schon=JSON.parse(localStorage.getItem(SIK)||'[]');}catch(e){}
    var ist=schon.indexOf(m[2].slice(0,80))>-1,summeT=teile.reduce(function(a,x){return a+x.q*stueck(x);},0);
    var liste=el('ul','sammel-liste');teile.forEach(function(x){liste.appendChild(el('li',null,x.q+'× '+nameA(x)+(x.g?' ('+x.g+')':'')+': '+euro(stueck(x)*x.q)));});
    var inhalt=[liste,el('p','sammel-summe',L('Summe: ','Total: ')+euro(summeT))];
    if(ist)inhalt.push(el('p','abhol-hinweis',L('Diesen Teil haben Sie schon hinzugefügt.','You have already added this part.')));
    if(!teile.length){dialog(L('Teil von ','Part from ')+von,[el('p',null,L('Der Teil enthält keine Gerichte aus der aktuellen Karte.','This part contains no dishes from the current menu.'))],[[L('OK','OK'),dialogZu]]);return;}
    dialog(von+L(' schickt den eigenen Teil',' sent their part'),inhalt,[[L('Zur Bestellung hinzufügen','Add to my order'),function(){
        teile.forEach(function(x){zettel.push(x);});zusammenfassen();speichern();zeichnen();zeitenFuellen();waAktualisieren();
        schon.push(m[2].slice(0,80));try{localStorage.setItem(SIK,JSON.stringify(schon.slice(-50)));}catch(e){}
        dialogZu();oeffnen();melden(L('Teil von ','Part from ')+von+L(' hinzugefügt.',' added.'));}],
      [L('Verwerfen','Discard'),dialogZu]]);
  }
  var leeren=document.getElementById('zettel-leeren'),leerenTimer=null;
  leeren.addEventListener('click',function(){
    if(leeren.dataset.sicher){zettel=[];offen=null;speichern();zeichnen();schliessen();melden(L('Bestellung geleert.','Order cleared.'));delete leeren.dataset.sicher;leeren.textContent=L('Bestellung leeren','Clear order');return;}
    leeren.dataset.sicher='1';leeren.textContent=L('Wirklich alles löschen? Nochmal tippen.','Really delete everything? Tap again.');
    clearTimeout(leerenTimer);leerenTimer=setTimeout(function(){delete leeren.dataset.sicher;leeren.textContent=L('Bestellung leeren','Clear order');},4000);
  });
  zeichnen();verfZeigen();regelnLaden();sammelZeigen();linkPruefen();
  window.addEventListener('hashchange',linkPruefen);
  setInterval(function(){try{verfZeigen();zeitenFuellen();}catch(e){}},60000);
'''

JS = r"""
(function(){
  var ZEITEN=%%ZEITEN%%,SONDER=%%SONDER%%,WARTE=%%WARTE%%,AKTIONEN=%%AKTIONEN%%;
  var TAGE=['Sonntag','Montag','Dienstag','Mittwoch','Donnerstag','Freitag','Samstag'];
  var TAGE_E=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  /* Sprache: gespeicherte Wahl, sonst Browsersprache (Suchmaschinen bekommen immer Deutsch) */
  /* Weitere Sprachen: Wörterbuch Englisch -> Sprache (docs/lang/<code>.json); fehlt ein Text, bleibt Englisch.
     Zahlen im Text werden als {n} nachgeschlagen, damit „3 dishes found“ und „{n} dishes found“ zusammenpassen. */
  var SPRACHEN=%%SPRACHEN%%,DICT=%%DICTS%%,LOC={de:'de-DE',en:'en-GB',cs:'cs-CZ',ru:'ru-RU',tr:'tr-TR',ar:'ar-u-nu-latn'};
  var SPK='saray-sprache',SP='de';
  try{SP=localStorage.getItem(SPK)||'';}catch(e){SP='';}
  if(!SPRACHEN.some(function(x){return x[0]===SP;})){
    var langs=(navigator.languages&&navigator.languages.length?navigator.languages:[navigator.language||'de']);
    SP='en';
    if(/bot|crawl|spider|lighthouse/i.test(navigator.userAgent))SP='de';
    else for(var li0=0;li0<langs.length;li0++){var k0=String(langs[li0]).slice(0,2).toLowerCase();if(SPRACHEN.some(function(x){return x[0]===k0;})){SP=k0;break;}}
  }
  function T(en){
    if(SP==='en'||SP==='de'||en==null)return en;var d=DICT[SP]||{},r=en;
    if(d[en]!=null)r=d[en];
    else{var z=[],k=String(en).replace(/\d+(?:[.,:]\d+)*/g,function(m){z.push(m);return '{n}';});
      if(z.length&&d[k]!=null){var i=0;r=d[k].replace(/\{n\}/g,function(){return z[i++];});}}
    return LTR_ZAHLEN(r);
  }
  /* Rechts-nach-links (Arabisch): Telefonnummern, Uhrzeiten und Preise als Block links-nach-rechts halten */
  function LTR_ZAHLEN(r){
    if(document.documentElement.dir!=='rtl'||typeof r!=='string')return r;
    return r.split(/(<[^>]*>)/).map(function(t){return t.charAt(0)==='<'?t:t.replace(/\+?\d[\d.,:\u2013\- ]*\d(?: ?€)?|\d(?: ?€)?/g,function(m){return '\u2066'+m+'\u2069';});}).join('');
  }
  function L(de,en){return SP==='de'?de:T(en);}
  function fuell(tpl,w){return tpl.replace(/\{(\w+)\}/g,function(_,k){return w[k]!=null?w[k]:'';});}
  /* Linkshänder-Modus: auf diesem Gerät gemerkt */
  var HK='saray-hand',linkshand=false;
  try{linkshand=localStorage.getItem(HK)==='links';}catch(e){}
  function handZeigen(){document.documentElement.classList.toggle('links',linkshand);
    document.querySelectorAll('[data-hand]').forEach(function(b){b.textContent=linkshand?L('✋ Rechtshänder? Knöpfe nach rechts','✋ Right-handed? Buttons to the right'):L('✋ Linkshänder? Knöpfe nach links','✋ Left-handed? Buttons to the left');
      b.setAttribute('aria-pressed',String(linkshand));});}
  document.addEventListener('click',function(ev){if(!ev.target.closest('[data-hand]'))return;linkshand=!linkshand;
    try{localStorage.setItem(HK,linkshand?'links':'rechts');}catch(e){}handZeigen();});
  handZeigen();
  function handSetzen(v){linkshand=v;try{localStorage.setItem(HK,v?'links':'rechts');}catch(e){}handZeigen();}
  /* Kleiner Hinweis-Kasten unten (z. B. „Hat’s geschmeckt?“) */
  var handTimer=null;
  function handTippZeigen(text,knoepfe,dauer){
    var box=document.getElementById('hand-tipp');box.textContent='';
    var pa=document.createElement('p');pa.innerHTML=text;box.appendChild(pa);
    var reihe=document.createElement('div');
    knoepfe.forEach(function(k,i){var b=document.createElement('button');b.type='button';b.textContent=k[0];if(i)b.className='zweit';
      b.addEventListener('click',k[1]);reihe.appendChild(b);});
    box.appendChild(reihe);box.hidden=false;
    clearTimeout(handTimer);handTimer=setTimeout(handTippZu,dauer||12000);
  }
  function handTippZu(){clearTimeout(handTimer);document.getElementById('hand-tipp').hidden=true;}
  var KURZ={Sun:0,Mon:1,Tue:2,Wed:3,Thu:4,Fri:5,Sat:6};
  var weniger=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;

  function jetzt(){
    var o={};
    new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Berlin',weekday:'short',hour:'2-digit',minute:'2-digit',hourCycle:'h23'})
      .formatToParts(new Date()).forEach(function(p){o[p.type]=p.value;});
    return {tag:KURZ[o.weekday],min:(+o.hour)*60+(+o.minute)};
  }
  /* ISO-Datum (deutsche Zeit) in off Tagen; Öffnungszeit dieses Tages – besondere Tage gehen vor */
  function isoTag(off){return new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Berlin',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(Date.now()+(off||0)*864e5));}
  function tagZeit(ort,off){var s=SONDER[ort]||{},d=isoTag(off);if(d in s)return s[d];return ZEITEN[ort][(jetzt().tag+off)%7]||null;}
  /* Sonderaktion für Gericht k (Größe i) an Datum iso und Laden (null = noch nicht gewählt) */
  function aktion(k,i,iso,laden,min){
    var wt=new Date(iso+'T12:00:00Z').getUTCDay();
    for(var j=0;j<AKTIONEN.length;j++){var a=AKTIONEN[j],p=a.p[k];
      if(!p||iso<a.von||iso>a.bis||(a.tage&&a.tage.indexOf(wt)<0)||(a.laden&&a.laden!==laden))continue;
      if(a.za!=null&&(min==null||min<a.za||min>=a.zb))continue;
      return {c:p[Math.min(i||0,p.length-1)],a:a};}
    return null;
  }
  function euroK(c){return (c/100).toFixed(2).replace('.',',')+' €';}
  /* Speisekarte: heute laufende Aktionen markieren (alter Preis durchgestrichen, Aktionspreis als Marke) */
  function aktionenZeigen(){
    var iso=isoTag(0),wt=new Date(iso+'T12:00:00Z').getUTCDay(),jm=jetzt().min;
    document.querySelectorAll('[data-mittag]').forEach(function(sec){var a=AKTIONEN[+sec.dataset.mittag];
      sec.hidden=!a||iso<a.von||iso>a.bis||(a.tage&&a.tage.indexOf(wt)<0)||(a.zb!=null&&jm>=a.zb);});
    document.querySelectorAll('.marke-aktion').forEach(function(m){m.remove();});
    document.querySelectorAll('.preis-alt').forEach(function(m){m.classList.remove('preis-alt');});
    AKTIONEN.forEach(function(a){
      if(iso<a.von||iso>a.bis||(a.tage&&a.tage.indexOf(wt)<0))return;
      Object.keys(a.p).forEach(function(k){
        var st=document.querySelector('.sticker');
        if(k==='1'&&st&&!a.laden&&a.za==null){var c=a.p[k][0],sp=st.querySelector('.sticker-preis');st.querySelector('small').textContent=L('Aktion','Offer');
          if(sp)sp.innerHTML=Math.floor(c/100)+'<span class="ct">'+('0'+c%100).slice(-2)+'</span>';st.classList.add('sticker-aktion');}
        document.querySelectorAll('li[data-k="'+(window.CSS&&CSS.escape?CSS.escape(k):k)+'"]').forEach(function(li){
          var ziel=li.querySelector('.name, .tipp-name');if(!ziel)return;
          var m=document.createElement('span');m.className='marke-beliebt marke-aktion';
          var ort=a.laden?(a.laden==='freital'?' Freital':' Altenberg'):'';
          var uz=a.za!=null?' '+uhr(a.za).replace(' Uhr','')+'–'+uhr(a.zb):'';
          m.textContent=(a.m?L('Mittag ','Lunch '):L('Aktion ','Offer '))+a.p[k].map(euroK).join(' / ')+uz+(ort?(SP==='de'?' (nur'+ort+')':' '+fuell(T('({ort} only)'),{ort:ort.trim()})):'');
          ziel.appendChild(document.createTextNode(' '));ziel.appendChild(m);
          li.querySelectorAll('.preis, .tipp-preis').forEach(function(p){p.classList.add('preis-alt');});
        });
      });
    });
  }
  function warte(ort){var w=WARTE[ort];return w&&w.datum===isoTag(0)?w.min:0;}
  function uhr(m){var h=Math.floor(m/60),r=m%60;if(SP!=='de')return h+':'+(r<10?'0':'')+r;return r?h+':'+(r<10?'0':'')+r+' Uhr':h+' Uhr';}
  function lage(ort){
    var n=jetzt(),h=tagZeit(ort,0),w=warte(ort);
    if(h&&n.min>=h[0]&&n.min<h[1]-30)return{offen:true,text:(SP==='de'?'Jetzt geöffnet, bis '+uhr(h[1]):fuell(T('Open now, until {zeit}'),{zeit:uhr(h[1])}))+(w?L(' · Wartezeit ca. '+w+' Min.',' · waiting time approx. '+w+' min'):'')};
    if(h&&n.min>=h[0]&&n.min<h[1])return{offen:true,bald:true,text:SP==='de'?'Bald Feierabend – geöffnet bis '+uhr(h[1]):fuell(T('Closing soon – open until {zeit}'),{zeit:uhr(h[1])})};
    if(h&&n.min<h[0])return{offen:false,text:SP==='de'?'Geschlossen, öffnet heute um '+uhr(h[0]):fuell(T('Closed, opens today at {zeit}'),{zeit:uhr(h[0])})};
    for(var i=1;i<=14;i++){var t=(n.tag+i)%7,zi=tagZeit(ort,i);if(zi)return{offen:false,text:SP!=='de'?(SP==='en'?'Closed, opens '+(i===1?'tomorrow':i<7?'on '+TAGE_E[t]:'on '+TAGE_E[t]+' '+isoTag(i).slice(8)+'/'+isoTag(i).slice(5,7))+' at '+uhr(zi[0])
        :fuell(T(i===1?'Closed, opens tomorrow at {zeit}':'Closed, opens on {tag} at {zeit}'),{zeit:uhr(zi[0]),tag:new Intl.DateTimeFormat(LOC[SP],Object.assign({timeZone:'Europe/Berlin',weekday:'long'},i<7?{}:{day:'numeric',month:'numeric'})).format(new Date(Date.now()+i*864e5))})):'Geschlossen, öffnet '+(i===1?'morgen':i<7?'am '+TAGE[t]:'am '+TAGE[t]+', '+isoTag(i).slice(8)+'.'+isoTag(i).slice(5,7)+'.')+' um '+uhr(zi[0])};}
    return{offen:false,text:''};
  }
  function aktualisieren(){
    document.querySelectorAll('[data-status]').forEach(function(el){
      var s=lage(el.getAttribute('data-status'));el.setAttribute('data-offen',s.offen?(s.bald?'bald':'ja'):'nein');
      el.querySelector('.status-text').textContent=s.text;
    });
    var tag=jetzt().tag,hi=isoTag(0);
    document.querySelectorAll('.sonder li[data-datum]').forEach(function(li){li.hidden=li.dataset.datum<hi;li.classList.toggle('heute',li.dataset.datum===hi);});
    document.querySelectorAll('.sonder').forEach(function(b){b.hidden=!b.querySelector('li:not([hidden])');});
    document.querySelectorAll('tr[data-tage]').forEach(function(tr){
      tr.classList.toggle('heute',tr.getAttribute('data-tage').split(',').indexOf(String(tag))>-1);
    });
  }
  try{aktualisieren();setInterval(aktualisieren,60000);}catch(e){}
  try{aktionenZeigen();}catch(e){}
  /* Zählen ohne Cookies (GoatCounter-Pixel, nur wenn ZAEHLER gesetzt) */
  var GC=%%ZAEHLER%%;
  function zaehlen(pfad,ereignis){
    if(!GC||navigator.doNotTrack==='1'||/^(localhost|127\.)/.test(location.hostname))return;
    try{(new Image()).src='https://'+GC+'.goatcounter.com/count?p='+encodeURIComponent(pfad)+(ereignis?'&e=true&t='+encodeURIComponent(pfad):'&t='+encodeURIComponent(document.title))+'&rnd='+Math.random().toString(36).slice(2);}catch(e){}
  }
  zaehlen(location.pathname);
  document.addEventListener('click',function(ev){
    var a=ev.target.closest('a,button');if(!a)return;var laden=a.dataset.anruf||'',href=a.getAttribute('href')||'';
    if(!laden&&/^tel:/.test(href))try{Object.keys(TEL).forEach(function(l){if('tel:'+TEL[l][1]===href)laden=l;});}catch(e){}
    if(a.id==='zettel-whatsapp')zaehlen('whatsapp-'+((typeof abh==='object'&&abh&&abh.laden)||'bestellung'));
    else if(/^tel:/.test(href))zaehlen('anrufen'+(laden?'-'+laden:''));
    else if(a.id==='zettel-kopieren')zaehlen('bestellung-teilen');
    else if(a.id==='sammel-einladen')zaehlen('gemeinsam-bestellen');
  },true);
  /* Offline: Speisekarte bleibt verfügbar (Service Worker, nur auf der echten Seite) */
  if(%%SW%%&&'serviceWorker' in navigator&&location.protocol==='https:')window.addEventListener('load',function(){navigator.serviceWorker.register('sw.js').catch(function(){});});
  /* „Hat's geschmeckt?“ – einmal, beim nächsten Besuch nach einer WhatsApp-Bestellung (2 Std. bis 14 Tage später) */
  var GOOGLE=%%GOOGLE%%;
  setTimeout(function(){
    var bw=null;try{bw=JSON.parse(localStorage.getItem('saray-bewertung')||'null');}catch(e){return;}
    if(!bw||bw.fertig||!GOOGLE[bw.l])return;var alt=Date.now()-bw.t;if(alt<2*36e5||alt>14*864e5)return;
    if(!document.getElementById('hand-tipp').hidden)return;
    try{bw.fertig=1;localStorage.setItem('saray-bewertung',JSON.stringify(bw));}catch(e){return;}
    var ort=bw.l==='freital'?'Freital':'Altenberg';
    handTippZeigen('<b>'+L('Hat’s geschmeckt?','Did you enjoy it?')+'</b><br>'+(SP==='de'?'Über eine Google-Bewertung für Saray Döner '+ort+' freuen wir uns sehr.':fuell(T('We would love a Google review for Saray Döner {ort}.'),{ort:ort})),
      [[L('⭐ Bewerten','⭐ Review'),function(){zaehlen('bewertung-'+bw.l);window.open('https://search.google.com/local/writereview?placeid='+GOOGLE[bw.l],'_blank','noopener');handTippZu();}],
       [L('Nein danke','No thanks'),handTippZu]],25000);
  },1500);
  /* „Inhaltsstoffe … · Allergene …“ öffnet die Liste unten */
  document.addEventListener('click',function(ev){if(!ev.target.closest('[data-allergene]'))return;var d=document.getElementById('allergene');if(d)d.open=true;});
  if(location.hash==='#allergene'){var dA=document.getElementById('allergene');if(dA)dA.open=true;}

  /* Kategorien: Die angeklickte Kategorie wird sofort markiert und bleibt es.
     Erst wenn man selbst scrollt, wandert die Markierung mit dem Inhalt mit. */
  var nav=document.querySelector('.kategorien'),leiste=nav&&nav.querySelector('ul');
  var links={},gruppen=[].slice.call(document.querySelectorAll('.gruppe')),aktiv=null,fest=null,geplant=false;
  nav&&nav.querySelectorAll('a').forEach(function(a){links[a.getAttribute('href').slice(1)]=a;});
  function markiere(id){
    if(id===aktiv)return;aktiv=id;
    Object.keys(links).forEach(function(k){
      if(k===id)links[k].setAttribute('aria-current','true');else links[k].removeAttribute('aria-current');
    });
    var a=id&&links[id];
    if(a&&leiste&&leiste.scrollWidth>leiste.clientWidth){
      leiste.scrollTo({left:a.offsetLeft-leiste.clientWidth/2+a.offsetWidth/2,behavior:weniger?'auto':'smooth'});
    }
  }
  function imBlick(){
    var linie=Math.min(window.innerHeight*0.35,170),id=null;
    for(var i=0;i<gruppen.length;i++){
      if(gruppen[i].hidden)continue;
      if(gruppen[i].getBoundingClientRect().top<=linie)id=gruppen[i].id;else break;
    }
    return id;
  }
  /* Kategorie-Band klebt oben? Dann weiß darüber und weiße Browserleiste */
  /* Klebt das Band? Dann liegt es tiefer als die unsichtbare Marke direkt davor.
     Solange es klebt, liegt eine feste weiße Fläche dahinter (.deckel-oben): Safari 26 färbt danach den Bereich
     unter der gläsernen Adressleiste weiß. Wichtig: kein anderes festes Element darf ganz oben darüber liegen. */
  var marke=document.querySelector('.kat-marke'),deckel=null,glas=null;
  function klebtPruefen(){if(!nav||!marke)return;
    /* klebt = steht oben fest; am Ende der Speisekarte schiebt der Inhalt das Band nach oben weg – dann darf die weiße Fläche nicht stehen bleiben */
    var r=nav.getBoundingClientRect(),k=getComputedStyle(nav).position==='sticky'&&r.top-marke.getBoundingClientRect().bottom>1&&r.bottom>0;
    if(k!==nav.classList.contains('klebt'))nav.classList.toggle('klebt',k);
    if(k&&glas){glas.remove();glas=null;}
    if(!k&&!glas){glas=document.createElement('div');glas.className='glas-oben';glas.setAttribute('aria-hidden','true');document.body.appendChild(glas);}
    if(k&&!deckel){deckel=document.createElement('div');deckel.className='deckel-oben';deckel.setAttribute('aria-hidden','true');document.body.appendChild(deckel);}
    if(deckel)deckel.style.height=Math.max(0,Math.round(r.bottom))+'px';
    if(!k&&deckel){deckel.remove();deckel=null;}
    if(dbg){var vv=window.visualViewport;dbg.textContent='scrollY '+Math.round(scrollY)+'\ninnerH '+innerHeight+' vv.h '+(vv?Math.round(vv.height):'-')+' vv.top '+(vv?Math.round(vv.offsetTop):'-')+
      '\nnav.top '+Math.round(nav.getBoundingClientRect().top)+' marke.bottom '+Math.round(marke.getBoundingClientRect().bottom)+
      '\nposition '+getComputedStyle(nav).position+' top '+getComputedStyle(nav).top+'\nklebt '+nav.classList.contains('klebt')+
      '\ndeckel '+(deckel?deckel.style.height:'-')+' glas '+(glas?'ja':'-')+'\nsafe-top '+getComputedStyle(document.documentElement).getPropertyValue('--sat');}}
  var dbg=null;
  if(/[?&]debug/.test(location.search)){dbg=document.createElement('div');dbg.id='debug-info';document.body.appendChild(dbg);
    document.documentElement.style.setProperty('--sat','env(safe-area-inset-top)');
    var tst=document.createElement('div');tst.style.cssText='position:fixed;top:0;height:env(safe-area-inset-top)';document.body.appendChild(tst);
    document.documentElement.style.setProperty('--sat',tst.getBoundingClientRect().height+'px');}
  function verfolgen(){klebtPruefen();if(!fest)markiere(imBlick());}
  function loesen(){fest=null;}
  window.addEventListener('scroll',function(){
    if(geplant)return;geplant=true;
    requestAnimationFrame(function(){geplant=false;verfolgen();});
  },{passive:true});
  window.addEventListener('resize',verfolgen);window.addEventListener('pageshow',verfolgen);window.addEventListener('load',verfolgen);
  window.addEventListener('wheel',loesen,{passive:true});
  window.addEventListener('touchmove',loesen,{passive:true});
  window.addEventListener('mousedown',function(ev){if(!(nav&&nav.contains(ev.target)))loesen();});
  window.addEventListener('keydown',function(ev){
    var t=ev.target&&ev.target.tagName;
    if(t!=='INPUT'&&t!=='TEXTAREA'&&/^(ArrowUp|ArrowDown|PageUp|PageDown|Home|End| )$/.test(ev.key))loesen();
  });
  Object.keys(links).forEach(function(id){
    links[id].addEventListener('click',function(){fest=id;markiere(id);});
  });
  if(links[location.hash.slice(1)]){fest=location.hash.slice(1);markiere(fest);}else verfolgen();

  /* Suche */
  function norm(s){
    return s.toLowerCase().replace(/ä|ae/g,'a').replace(/ö|oe/g,'o').replace(/ü|ue/g,'u').replace(/ß/g,'ss')
      .normalize('NFD').replace(/[̀-ͯ]/g,'');
  }
  /* Ernährung: '' | 'veg' | 'pesc' – filtert die Karte und blendet im Zettel Fleisch (und bei veg Fisch) aus */
  var DIAET='',vegK=document.getElementById('veg-schalter');
  document.querySelectorAll('[data-diaet]').forEach(function(k){k.addEventListener('click',function(){
    DIAET=DIAET===k.dataset.diaet?'':k.dataset.diaet;
    document.querySelectorAll('[data-diaet]').forEach(function(x){x.setAttribute('aria-pressed',String(x.dataset.diaet===DIAET));});
    suchen();try{zeichnen();}catch(e){}});});
  var feld=document.getElementById('suche-feld'),gerichte=[].slice.call(document.querySelectorAll('.gericht'));
  var treffer=document.querySelector('.treffer'),nichts=document.querySelector('.nichts'),wort=nichts&&nichts.querySelector('q');
  gerichte.forEach(function(g){g._s=norm(g.getAttribute('data-s'));});
  function suchen(){
    var roh=feld.value.trim(),q=norm(roh),teile=q.split(/\s+/).filter(Boolean),n=0,veg=!!DIAET;
    gerichte.forEach(function(g){var ok=teile.every(function(w){return g._s.indexOf(w)>-1;})&&(!DIAET||g.hasAttribute('data-veg')||(DIAET==='pesc'&&g.hasAttribute('data-fisch')));g.hidden=!ok;if(ok)n++;});
    document.querySelectorAll('.liste').forEach(function(l){
      var v=l.querySelectorAll('.gericht:not([hidden])').length;l.style.setProperty('--zeilen',Math.max(1,Math.ceil(v/2)));
      l.closest('.abschnitt').hidden=v===0;
    });
    document.querySelectorAll('.gruppe').forEach(function(g){
      var leer=!g.querySelector('.gericht:not([hidden])');g.hidden=leer;if(links[g.id])links[g.id].classList.toggle('leer',leer);
    });
    treffer.hidden=!(teile.length||veg)||n===0;
    treffer.textContent=n===1?L('1 Gericht gefunden','1 dish found'):n+L(' Gerichte gefunden',' dishes found');
    nichts.hidden=!(teile.length&&n===0);if(wort)wort.textContent=roh;
    document.body.classList.toggle('sucht',teile.length>0);
    var bl=document.querySelector('.beliebt');if(bl){bl.hidden=teile.length>0;
      bl.querySelectorAll('.tipp').forEach(function(t){t.hidden=DIAET?!(t.hasAttribute('data-veg')||(DIAET==='pesc'&&t.hasAttribute('data-fisch'))):t.hasAttribute('data-nur-diaet');});
      bl.querySelectorAll('ul.tipps').forEach(function(u){var leer=!u.querySelector('.tipp:not([hidden])');u.hidden=leer;
        var h=u.previousElementSibling;if(h&&h.classList.contains('beliebt-titel'))h.hidden=leer;});
      if(!bl.querySelector('.tipp:not([hidden])'))bl.hidden=true;}
    if(typeof letzteZeigen==='function')letzteZeigen();
    fest=null;verfolgen();
  }
%%ZETTEL_JS%%
  if(feld){
    feld.addEventListener('input',suchen);
    nichts.querySelector('button').addEventListener('click',function(){feld.value='';suchen();feld.focus();});
  }

  /* „Nach oben“-Knopf: erscheint, wenn man etwa eine Bildschirmhöhe gescrollt hat */
  var obenK=document.getElementById('nach-oben'),obenGeplant=false;
  function obenPruefen(){obenK.hidden=window.scrollY<window.innerHeight*0.9;}
  window.addEventListener('scroll',function(){if(obenGeplant)return;obenGeplant=true;requestAnimationFrame(function(){obenGeplant=false;obenPruefen();});},{passive:true});
  obenK.addEventListener('click',function(){
    window.scrollTo({top:0,behavior:weniger?'auto':'smooth'});
    var ziel=document.querySelector('#oben a');if(ziel)ziel.focus({preventScroll:true});
  });
  obenPruefen();

  /* Hinweis-Band nach deutschem Datum */
  function hinweiseZeigen(){
    var d=new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Berlin',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
    document.querySelectorAll('.hinweis-band').forEach(function(b){b.hidden=!(d>=b.dataset.von&&d<=b.dataset.bis);});
  }
  try{hinweiseZeigen();}catch(e){}

  /* Sprachumschalter Deutsch/Englisch */
  var spKnopf=document.getElementById('sprache'),spMenue=document.getElementById('sprachen-menu');
  function textFuer(l,de,en){return l==='de'?de:(l==='en'?en:T(en));}
  function sprache(l,merken){
    if(l!=='de'&&l!=='en'&&!DICT[l]){ /* Wörterbuch erst laden, dann umschalten */
      fetch('lang/'+l+'.json').then(function(r){return r.ok?r.json():{};}).then(function(d){DICT[l]=d||{};sprache(l,merken);},function(){DICT[l]={};sprache(l,merken);});return;}
    SP=l;document.documentElement.lang=l;document.documentElement.dir=l==='ar'?'rtl':'ltr';
    document.querySelectorAll('[data-en]').forEach(function(x){if(x._de==null)x._de=x.textContent;x.textContent=textFuer(l,x._de,x.dataset.en);});
    document.querySelectorAll('[data-en-html]').forEach(function(x){if(x._de==null)x._de=x.innerHTML;x.innerHTML=textFuer(l,x._de,x.dataset.enHtml);});
    document.querySelectorAll('[data-en-ph]').forEach(function(x){if(x._de==null)x._de=x.placeholder;x.placeholder=textFuer(l,x._de,x.dataset.enPh);});
    document.querySelectorAll('[data-en-aria]').forEach(function(x){if(x._dea==null)x._dea=x.getAttribute('aria-label');
      var en=x.dataset.enAria,m=/^Add (.+) to my order$/.exec(en),v=m&&l!=='de'&&l!=='en'?fuell(T('Add {x} to my order'),{x:T(m[1])}):textFuer(l,x._dea,en);x.setAttribute('aria-label',v);});
    document.querySelectorAll('[data-en-title]').forEach(function(x){if(x._det==null)x._det=x.getAttribute('title');x.setAttribute('title',textFuer(l,x._det,x.dataset.enTitle));});
    spKnopf.textContent=l.toUpperCase();
    spKnopf.setAttribute('aria-label','Sprache / Language: '+(SPRACHEN.filter(function(x){return x[0]===l;})[0]||['',''])[1]);
    spMenue.querySelectorAll('[data-sp]').forEach(function(b){b.setAttribute('aria-current',b.dataset.sp===l?'true':'false');});
    if(merken){try{localStorage.setItem(SPK,l);}catch(e){}}
    try{aktualisieren();}catch(e){}
    if(feld&&feld.value.trim())suchen();
    zeichnen();zeitenFuellen();waAktualisieren();handZeigen();try{aktionenZeigen();}catch(e){}
    try{verfZeigen();}catch(e){}
  }
  /* Sprachwahl: Knopf mit Kürzel, darunter die Liste in der jeweiligen Sprache */
  SPRACHEN.forEach(function(x){var b=document.createElement('button');b.type='button';b.dataset.sp=x[0];b.lang=x[0];b.textContent=x[1];
    if(x[0]==='ar')b.dir='rtl';b.addEventListener('click',function(){menueZu();sprache(x[0],true);spKnopf.focus();});var li=document.createElement('li');li.appendChild(b);spMenue.appendChild(li);});
  function menueZu(){spMenue.hidden=true;spKnopf.setAttribute('aria-expanded','false');}
  spKnopf.addEventListener('click',function(ev){ev.stopPropagation();var auf=spMenue.hidden;spMenue.hidden=!auf;spKnopf.setAttribute('aria-expanded',String(auf));
    if(auf){var akt=spMenue.querySelector('[aria-current="true"]')||spMenue.querySelector('button');if(akt)akt.focus();}});
  document.addEventListener('click',function(ev){if(!spMenue.hidden&&!spMenue.contains(ev.target))menueZu();});
  document.addEventListener('keydown',function(ev){if(ev.key==='Escape'&&!spMenue.hidden){menueZu();spKnopf.focus();}});
  if(SP!=='de')sprache(SP,false);
  else spMenue.querySelectorAll('[data-sp]').forEach(function(b){b.setAttribute('aria-current',b.dataset.sp==='de'?'true':'false');});

  /* Impressum/Datenschutz per Link öffnen */
  function oeffne(){var d=document.getElementById(location.hash.slice(1));if(d&&d.tagName==='DETAILS')d.open=true;}
  window.addEventListener('hashchange',oeffne);oeffne();
})();
"""

SEITE = r"""<!doctype html>
<!--
  Saray Döner – neue Website (Stand: 16.10.2026)
  Vor dem Livegang: Impressum und Datenschutz unten ausfüllen (gelb markiert),
  Adresse/Öffnungszeiten Altenberg und Preise mit dem Inhaber gegenprüfen.
  Keine externen Dienste: Schriften und Fotos sind in dieser Datei eingebettet.
-->
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>%%TITEL_PRAEFIX%%Saray Döner Freital &amp; Altenberg – Döner, Pizza und Salate seit 1997</title>
<meta name="description" content="Saray Döner in Freital (Dresdner Str. 87) und Altenberg (Dresdner Str. 23): Döner, Dürüm, Pizza, Lahmacun und Salate. Speisekarte mit Preisen, Öffnungszeiten und Telefonnummern.">
<link rel="canonical" href="%%DOMAIN%%">
<meta name="theme-color" content="#FFD21F">
<meta name="format-detection" content="telephone=no">
<meta property="og:type" content="website">
<meta property="og:locale" content="de_DE">
<meta property="og:title" content="Saray Döner – Freital &amp; Altenberg">
<meta property="og:description" content="Döner, Dürüm, Pizza und Salate seit 1997. Speisekarte, Öffnungszeiten und Telefon.">
<meta property="og:url" content="%%DOMAIN%%">
<link rel="icon" href="%%FAVICON_PNG%%" type="image/png" sizes="96x96">
<link rel="icon" href="%%IMG_KOPF%%" type="image/svg+xml">%%APP_KOPF%%
%%ROBOTS%%%%CSS_EINBINDEN%%
<script type="application/ld+json">%%LD%%</script>
</head>
<body%%BODY_KLASSE%%>
%%VORSCHAU_BAND%%
<a class="skip" href="#speisekarte" data-en="Skip to menu">Zur Speisekarte springen</a>

<header class="kopf-band" id="oben">
  <div class="seitenkopf wrap">
    <a class="marke" href="#oben">
      <img class="logo" src="%%IMG_KOPF%%" width="58" height="58" alt="">
      <span class="marke-text"><b>Saray Döner</b><small data-en="Döner &amp; pizza since 1997">Döner &amp; Pizza seit 1997</small></span>
    </a>
    <nav class="kopf-nav" aria-label="Hauptmenü">
      <a href="#speisekarte" data-en="Menu">Speisekarte</a><a href="#standorte" data-en="Opening hours">Öffnungszeiten</a>
      <span class="sprache-wahl"><button type="button" class="sprache" id="sprache" aria-label="Sprache / Language" aria-haspopup="true" aria-expanded="false" aria-controls="sprachen-menu">DE</button>
      <ul class="sprachen-menu" id="sprachen-menu" hidden></ul></span>
    </nav>
  </div>
</header>

%%HINWEISE%%
<main id="inhalt">
<div class="buehne-band">
  <section class="buehne wrap" aria-labelledby="titel">
    <div class="buehne-text">
      <img class="koch-klein" src="%%IMG_KOCH%%" width="430" height="470" alt="">
      <h1 id="titel" data-en-html="Fresh off the skewer.&lt;br&gt; Since 1997.">Frisch vom Spieß.<br> Seit 1997.</h1>
      <p class="lead" data-en="Döner, dürüm, pizza and salads – in Freital on Dresdner Straße and in Altenberg right by the station.">Döner, Dürüm, Pizza und Salate – in Freital an der Dresdner Straße und in Altenberg direkt am Bahnhof.</p>
      <ul class="schilder" aria-label="Unsere Läden">
%%SCHILDER%%
      </ul>
      <aside class="winter" id="winter" hidden aria-label="Wintersaison Altenberg">
        <p class="winter-titel"><span aria-hidden="true">❄️ </span><span data-en="After the slopes in Altenberg">Nach der Piste in Altenberg</span></p>
        <p data-en="Pre-order and pick up hot – right by the station. Taking the train back? We time your pickup to the departure.">Vorbestellen und warm abholen – direkt am Bahnhof. Mit dem Zug zurück? Wir richten die Abholung nach der Abfahrt.</p>
        <div class="winter-knoepfe"><button type="button" class="knopf knopf-dunkel" id="winter-bestellen" data-en="Pre-order in Altenberg">In Altenberg vorbestellen</button>
        <button type="button" class="knopf knopf-linie" id="winter-gruppe" data-en="👥 Ski class or group">👥 Skikurs oder Gruppe</button></div>
      </aside>
    </div>
    <div class="bilder">
      <figure class="foto"><img src="%%IMG_LADEN%%" srcset="%%IMG_LADEN_480%% 480w, %%IMG_LADEN%% 894w" sizes="(min-width: 900px) 440px, 100vw" width="894" height="700" decoding="async"
        alt="Der Laden von außen: Eckhaus mit grünen Schildern, davor Tische und bunte Stühle."></figure>
      <img class="koch" src="%%IMG_KOCH%%" width="430" height="470" alt="">
      <p class="sticker" aria-hidden="true"><small>Döner Kebap</small><b>%%STICKER%%</b></p>
    </div>
  </section>
</div>

<section class="karte" id="speisekarte" aria-labelledby="karte-titel">
  <div class="wrap">
    <header class="karte-kopf abschnitt-kopf">
      <h2 id="karte-titel" data-en="Menu">Speisekarte</h2>
      <p data-en="All prices in euros incl. VAT. Pickup only, no delivery or shipping costs. Every dish comes with your choice of sauce: garlic, herb or chili.">Alle Preise in Euro inkl. MwSt. Nur Abholung, keine Liefer- oder Versandkosten. Zu jedem Gericht gibt es Soße nach Wahl: Knoblauch, Kräuter oder Chili.</p>
      <p data-en="The menu applies in Freital and Altenberg.">Die Karte gilt in Freital und Altenberg.</p>
      <p class="sammel-start"><button type="button" class="knopf knopf-linie knopf-sammel" data-sammel-start data-en="👥 Order as a group">👥 Gemeinsam bestellen</button></p>
      <div class="sammel-band" id="sammel-band" hidden><p id="sammel-band-text"></p><button type="button" class="knopf-klein" id="sammel-ende" data-en="End">Beenden</button></div>
    </header>
    <div class="karte-layout">
      <div class="karte-seite">
        <div class="suche" role="search">
          <label for="suche-feld" data-en="Search dishes">Gericht suchen</label>
          <div class="suche-feld">%%SUCH_ICON%%<input id="suche-feld" type="search" placeholder="Name oder Nummer" data-en-ph="Name or number" autocomplete="off" enterkeyhint="search"></div>
          <div class="diaet" role="group" aria-label="Ernährung" data-en-aria="Diet">
          <button type="button" class="veg-schalter" id="veg-schalter" data-diaet="veg" aria-pressed="false"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 19C5 10 11 5 20 4c0 9-5 15-14 15z" fill="#2E7D32"/></svg><span data-en="Vegetarian">Vegetarisch</span></button>
          <button type="button" class="veg-schalter pesc" id="pesc-schalter" data-diaet="pesc" aria-pressed="false"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12c3-5 9-6 14-3l5-3-1 6 1 6-5-3c-5 3-11 2-14-3z" fill="#1565C0"/></svg><span data-en="Pescetarian">Pescetarisch</span></button>
          </div>
        </div>
        <div class="kat-marke" aria-hidden="true"></div>
        <nav class="kategorien" aria-label="Kategorien der Speisekarte"><ul>%%NAV%%</ul></nav>
      </div>
      <div class="karte-inhalt">
        <section class="letzte" id="letzte" hidden aria-labelledby="letzte-titel">
          <h3 id="letzte-titel" data-en="Same as last time?">Wie letztes Mal?</h3>
          <p class="letzte-liste" id="letzte-liste"></p>
          <button type="button" class="knopf knopf-dunkel" id="letzte-knopf" data-en="Order the same again">Nochmal so bestellen</button>
        </section>
        <p class="treffer" aria-live="polite" hidden></p>
        <div class="nichts" hidden><p><span data-en="No dish matches">Kein Gericht passt zu</span> <q></q>.</p><button type="button" class="knopf knopf-linie" data-en="Clear search">Suche löschen</button></div>
%%BELIEBT%%
%%KARTE%%
%%ALLERGENE%%
      </div>
    </div>
  </div>
</section>

<section class="gruppen" id="gruppen" aria-labelledby="gruppen-titel">
  <div class="wrap gruppen-wrap">
    <div>
      <h2 id="gruppen-titel" data-en="For companies, clubs and parties">Für Firmen, Vereine und Feiern</h2>
      <p class="intro" data-en="Several people, one pickup: at lunchtime for the office or in the evening for the birthday party.">Mehrere Leute, eine Abholung: mittags fürs Büro oder abends für die Geburtstagsfeier.</p>
      <ol class="schritte">
        <li><b data-en="Start">Starten</b> <span data-en="Tap “Order as a group” and send the link to your group – WhatsApp, Teams or e-mail.">„Gemeinsam bestellen“ antippen und den Link in Ihre Gruppe schicken – per WhatsApp, Teams oder E-Mail.</span></li>
        <li><b data-en="Choose">Aussuchen</b> <span data-en="Everyone picks their food on their own phone and sends you their part.">Jeder sucht sich sein Essen am eigenen Handy aus und schickt Ihnen seinen Teil.</span></li>
        <li><b data-en="Send">Abschicken</b> <span data-en="You choose the shop and pickup time – even days ahead – and send everything in one message.">Sie wählen Laden und Abholzeit – auch Tage im Voraus – und schicken alles mit einer Nachricht.</span></li>
      </ol>
      <p class="sammel-start"><button type="button" class="knopf knopf-dunkel knopf-sammel" data-sammel-start data-en="👥 Order as a group">👥 Gemeinsam bestellen</button></p>
    </div>
    <aside class="gruppen-info">
      <p><b data-en="Larger orders">Größere Bestellungen</b> <span data-en="Please pre-order in good time or give us a quick call:">bitte rechtzeitig vorbestellen oder kurz anrufen:</span></p>
      %%GRUPPEN_TEL%%
      %%GRUPPEN_BAR%%
      <p class="gutschein-hinweis"><span aria-hidden="true">🎁 </span><b data-en="Gift vouchers">Geschenkgutscheine</b> <span data-en="for birthdays, Christmas or as a thank-you – available at the counter in both shops.">zum Geburtstag, zu Weihnachten oder als Dankeschön – an der Theke in beiden Läden.</span></p>
    </aside>
  </div>
</section>

<section class="standorte" id="standorte" aria-labelledby="standorte-titel">
  <div class="wrap">
    <h2 id="standorte-titel" data-en="Opening hours and directions">Öffnungszeiten und Anfahrt</h2>
    <p class="intro" data-en="Two Saray shops: in Freital and in Altenberg.">Zweimal Saray: in Freital und in Altenberg.</p>
    <div class="orte">
%%ORTE%%
    </div>
    <p class="feiertage" data-en="Opening hours may differ on public holidays.">An Feiertagen können die Öffnungszeiten abweichen.</p>
  </div>
</section>
</main>

<footer class="fuss">
  <div class="wrap">
    <div class="fuss-raster">
      <div>
        <img class="logo" src="%%IMG_KOPF%%" width="76" height="76" alt="">
        <p class="motto" data-en="Quality is no accident.">Qualität ist kein Zufall.</p>
        <p><span lang="tr">Afiyet olsun</span> – <span data-en="enjoy your meal!">guten Appetit!</span></p>
        <p class="klein fuss-hand"><button type="button" class="hand-knopf" data-hand>Linkshänder: Knöpfe links</button></p>
        <p class="klein app-tipp" data-en="Tip: Put Saray on your home screen – in Safari via “Share” → “Add to Home Screen”, in Chrome via the menu → “Add to home screen”.">Tipp: Saray auf den Home-Bildschirm legen – in Safari über „Teilen“ → „Zum Home-Bildschirm“, in Chrome über das Menü → „Zum Startbildschirm hinzufügen“.</p>
      </div>
%%FUSS_ORTE%%
    </div>
    <div class="recht">
      <details id="impressum"><summary data-en="Impressum (legal notice)">Impressum</summary>
        <p>Angaben gemäß § 5 DDG</p>
        <p><b>Saray Döner Freital</b><br><span class="platzhalter">[Inhaber Khan – vollständiger Name, Anschrift, E-Mail, ggf. Firmenform und USt-IdNr.]</span><br>Dresdner Str. 87<br>01705 Freital<br>
        Telefon: <a href="tel:+4935127676660">0351 27676660</a></p>
        <p><b>Saray Döner Altenberg</b><br>Ahmet Saglam<br>Bahnhof 3<br>01773 Altenberg</p>
        <p>Telefon: <a href="tel:+493505623674">035056 23674</a><br>
        Telefax: 035056 23676<br>
        E-Mail: <a href="mailto:solino1@hotmail.de">solino1@hotmail.de</a></p>
      </details>
      <details id="datenschutz"><summary data-en="Datenschutz (privacy policy)">Datenschutz</summary>
%%DATENSCHUTZ%%
      </details>
    </div>
  </div>
</footer>

<button type="button" class="nach-oben" id="nach-oben" hidden aria-label="Nach oben" data-en-aria="Back to top" title="Nach oben"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 19V5M5.5 11.5 12 5l6.5 6.5"/></svg></button>
<button type="button" class="zettel-leiste" id="zettel-leiste" hidden><span class="zl-anzahl">0</span><svg class="ico tuete" viewBox="0 0 24 24" aria-hidden="true"><path d="M5.5 8h13l-1.2 12.5H6.7z"/><path d="M9 10.5V7a3 3 0 0 1 6 0v3.5"/></svg><span data-en="My order">Meine Bestellung</span><span class="zl-summe"></span></button>
<p class="zettel-meldung" id="zettel-meldung" role="status" hidden></p>
<div class="hand-tipp" id="hand-tipp" role="status" hidden></div>
<div class="sammel-dialog" id="sammel-dialog" hidden><div class="sammel-box" role="dialog" aria-modal="true" aria-labelledby="sammel-titel" tabindex="-1">
  <h2 id="sammel-titel"></h2><div id="sammel-inhalt"></div><div class="sammel-knoepfe" id="sammel-knoepfe"></div></div></div>
<div class="zettel-huelle" id="zettel" hidden>
  <div class="zettel-hinter" data-zu></div>
  <section class="zettel" role="dialog" aria-modal="true" aria-labelledby="zettel-titel">
    <header class="zettel-kopf"><h2 id="zettel-titel" tabindex="-1"><svg class="ico tuete" viewBox="0 0 24 24" aria-hidden="true"><path d="M5.5 8h13l-1.2 12.5H6.7z"/><path d="M9 10.5V7a3 3 0 0 1 6 0v3.5"/></svg><span data-en="My order">Meine Bestellung</span></h2>
      <button type="button" class="zettel-zu" data-zu aria-label="Bestellung schließen" data-en-aria="Close my order">×</button></header>
    <p class="zettel-leer" data-en="Nothing selected yet. Tap “+” in the menu.">Noch nichts ausgewählt. Tippen Sie in der Speisekarte auf „+“.</p>
    <div class="zettel-voll">
      <ul class="zettel-liste" id="zettel-liste"></ul>
      <p class="zettel-summe-zeile"><span data-en="Total">Summe</span><b id="zettel-summe"></b></p>
      <details class="code-box" id="code-box" hidden><summary data-en="Company code?">Firmen-Code?</summary>
        <form id="code-form" class="code-form"><input id="code-feld" type="text" autocomplete="off" autocapitalize="characters" aria-label="Firmen-Code" data-en-aria="Company code" placeholder="z. B. ELBTAL10" data-en-ph="e.g. ELBTAL10">
        <button type="submit" class="knopf knopf-linie" data-en="Apply">Einlösen</button></form>
        <p class="code-info" id="code-info" role="status" hidden></p><button type="button" class="link-knopf" id="code-weg" hidden data-en="Remove code">Code entfernen</button></details>
      <fieldset class="abholung">
        <legend data-en="Pickup">Abholung</legend>
        <div class="z-chips" role="group" aria-label="Laden" data-en-aria="Shop">%%LADEN_CHIPS%%</div>
        <label for="abhol-tag" data-en="Day">Tag</label>
        <select id="abhol-tag"></select>
        <label for="abhol-zeit" data-en="Time">Uhrzeit</label>
        <select id="abhol-zeit"></select>
        <p class="abhol-hinweis" id="abhol-hinweis" hidden></p>
        <div class="zug-wahl" id="zug-wahl" hidden></div>
        <label for="abhol-name" data-en="Name for the order">Name für die Bestellung</label>
        <input id="abhol-name" type="text" autocomplete="given-name" placeholder="z. B. Michael" data-en-ph="e.g. Michael">
      </fieldset>
      <p class="zettel-hinweis" data-en="Order via WhatsApp or call and read it out. Your order is saved on this device.">Bestellen Sie per WhatsApp oder rufen Sie an und lesen Sie die Bestellung vor. Sie bleibt auf diesem Gerät gespeichert.</p>
      %%ZETTEL_BAR%%
      <div class="zettel-knoepfe">
        <button type="button" class="knopf knopf-dunkel" id="sammel-teil" hidden><span></span></button>
        <a class="knopf knopf-whatsapp" id="zettel-whatsapp" href="#" target="_blank" rel="noopener">%%WA_ICON%%<span data-en="Order via WhatsApp">Per WhatsApp bestellen</span></a>
        <p class="wa-gesendet" id="wa-gesendet" role="status" hidden></p>
        <p class="abhol-hinweis verf-hinweis" id="verf-hinweis" hidden></p>
        <p class="abhol-hinweis" id="wa-hinweis" hidden data-en="Choose the shop above to order via WhatsApp.">Bitte oben den Laden wählen, dann können Sie per WhatsApp bestellen.</p>
        %%ZETTEL_ANRUF%%
        <button type="button" class="knopf knopf-linie" id="zettel-kopieren"><svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 15V3"/><path d="M7.5 7.5 12 3l4.5 4.5"/><path d="M5 12v7.5h14V12"/></svg><span data-en="Share order">Bestellung teilen</span></button>
        <button type="button" class="knopf knopf-linie" id="sammel-einladen"><span data-en="👥 Order as a group">👥 Gemeinsam bestellen</span></button>
        <button type="button" class="knopf-klein" id="zettel-leeren" data-en="Clear order">Bestellung leeren</button>
      </div>
    </div>
  </section>
</div>
%%JS_EINBINDEN%%
</body>
</html>
"""


# Hinweis-Band oben auf der Seite (z. B. Betriebsurlaub, Feiertage, Tagesangebot).
# Erscheint nur zwischen "von" und "bis" (jeweils einschließlich, deutsches Datum).
# Beispiel:
# {"text": "Am 24.12. haben wir bis 14 Uhr geöffnet.", "en": "On 24 Dec we are open until 2 pm.",
#  "von": "2026-12-20", "bis": "2026-12-24"},
HINWEISE = []
HINWEISE = HINWEISE + ANP.hinweise(ANPASSUNGEN.get("hinweise"), WARNUNGEN.append)

# Sonderaktionen aus der Chef-App: Aktionspreis gilt am Abholtag; oben erscheint automatisch ein Hinweis
AKTIONEN = [a for a in ANP.aktionen(ANPASSUNGEN.get("aktionen"), GRUPPEN, WARNUNGEN.append) if a["bis"] >= HEUTE_ISO]
_WT = ["sonntags", "montags", "dienstags", "mittwochs", "donnerstags", "freitags", "samstags"]
_WT_EN = ["Sundays", "Mondays", "Tuesdays", "Wednesdays", "Thursdays", "Fridays", "Saturdays"]
for _a in AKTIONEN:
    _bis = f'{_a["bis"][8:]}.{_a["bis"][5:7]}.'
    _tage = (" " + ", ".join(_WT[t] for t in _a["tage"])) if _a.get("tage") else ""
    _tage_en = (" on " + ", ".join(_WT_EN[t] for t in _a["tage"])) if _a.get("tage") else ""
    if _a.get("zeit_ab"):
        _uz = f" {ANP.uhr(ANP._min(_a['zeit_ab']))}–{ANP.uhr(ANP._min(_a['zeit_bis']))} Uhr"
        _tage += _uz
        _tage_en += f" {_a['zeit_ab']}–{_a['zeit_bis']}"
    _laden = next((f" – nur in {s['name']}" for s in STANDORTE if s["id"] == _a.get("laden")), "")
    _laden_en = next((f" – {s['name']} only" for s in STANDORTE if s["id"] == _a.get("laden")), "")
    _m = _a.get("art") == "mittag"
    HINWEISE.append({"text": f"{'' if _m else 'Aktion: '}{_a['name']}{_tage} – bis {_bis}{_laden}",
                     "en": f"{'Lunch special' if _m else 'Special offer'}: {_a['name']}{_tage_en} – until {_bis}{_laden_en}",
                     "von": _a["von"], "bis": _a["bis"], "aktion": True})
JS_AKTIONEN = json.dumps([{"n": a["name"], "m": 1 if a.get("art") == "mittag" else 0, "von": a["von"], "bis": a["bis"], "tage": a.get("tage"), "laden": a.get("laden"),
                           "za": ANP._min(a["zeit_ab"]) if a.get("zeit_ab") else None, "zb": ANP._min(a["zeit_bis"]) if a.get("zeit_bis") else None,
                           "p": {k: [int(x.replace(",", "")) for x in v] for k, v in a["preise"].items()}} for a in AKTIONEN], ensure_ascii=False)


# Mittagstisch: Aktionen mit "art": "mittag" bekommen oben einen eigenen Kasten (sichtbar nur an ihren Tagen bis Ende der Uhrzeit)
def mittag_html():
    teile = []
    for i, a in enumerate(AKTIONEN):
        if a.get("art") != "mittag":
            continue
        nrs = [k for k in a["preise"] if k in GERICHT]
        if not nrs:
            continue
        zeit = f'{ANP.uhr(ANP._min(a["zeit_ab"]))}–{ANP.uhr(ANP._min(a["zeit_bis"]))} Uhr' if a.get("zeit_ab") else ""
        zeit_en = f'{a["zeit_ab"]}–{a["zeit_bis"]}' if a.get("zeit_ab") else ""
        tage = ", ".join(ANP.KURZ[t] for t in a["tage"]) if a.get("tage") else ""
        ort = next((s_["name"] for s_ in STANDORTE if s_["id"] == a.get("laden")), "")
        unter = " · ".join(x for x in (tage, zeit, ("nur " + ort) if ort else "") if x)
        unter_en = " · ".join(x for x in (", ".join(TAGE_EN[t][:3] for t in a["tage"]) if a.get("tage") else "", zeit_en, (ort + " only") if ort else "") if x)
        teile.append(f'<section class="mittag" data-mittag="{i}" hidden aria-label="Mittagstisch">'
                     f'<h3 class="beliebt-titel"><span aria-hidden="true">🍽 </span>{e(a["name"])}</h3>'
                     f'<p class="mittag-zeit" data-en="{e(unter_en)}">{e(unter)}</p>'
                     '<ul class="tipps">' + "".join(beliebt_karte(n) for n in nrs) + '</ul></section>')
    return "".join(teile)


MITTAG_HTML = mittag_html()


# Verfügbarkeit: feste Regeln, die immer gelten (tagesaktuelle Änderungen: docs/status.json).
# "was": Gruppe aus SPERRGRUPPEN (siehe unten) oder Gerichtsnummer, auch als Liste.
# Optional: "laden": "freital"/"altenberg", "datum": "2026-10-21" (oder Liste), "tage": [1..5] (0 = Sonntag),
# "ab": "17:00" (erst ab), "bis": "14:00" (nur bis). Ohne ab/bis: nicht verfügbar.
# Beispiel: {"was": "nuggets", "ab": "17:00"}
VERFUEGBARKEIT = []
VERFUEGBARKEIT = VERFUEGBARKEIT + ANP.regeln(ANPASSUNGEN.get("verfuegbarkeit"), WARNUNGEN.append)

# Vorbestellung: so viele Tage im Voraus kann man die Abholung wählen (0 = nur heute)
VORBESTELL_TAGE = 14


def sperrgruppen():
    """Gruppen, die der Inhaber auf einmal sperren kann: jede Kategorie der Karte plus Zutaten."""
    alle = []
    for gr in GRUPPEN:
        for ab in gr["abschnitte"]:
            for g in ab["gerichte"]:
                if g[0]:
                    alle.append((gr["id"], g[0], g[1], g[2]))
    gruppen = {gr["id"]: {"de": gr["titel"], "en": EN.titel(gr["titel"]), "nr": [n for gid, n, _, _ in alle if gid == gr["id"]]}
               for gr in GRUPPEN}
    def zutat(de, en, test):
        return {"de": de, "en": en, "nr": [n for gid, n, name, desc in alle if test(n, name, desc)]}
    gruppen["huhn"] = zutat("Hähnchen", "Chicken", lambda n, a, b: "Hähnchen" in a + " " + b and n != "17")
    gruppen["nuggets"] = zutat("Nuggets", "Nuggets", lambda n, a, b: "Nuggets" in a)
    gruppen["falafel"] = zutat("Falafel", "Falafel", lambda n, a, b: "Falafel" in a + " " + b)
    gruppen["halloumi"] = zutat("Halloumi", "Halloumi", lambda n, a, b: "Halloumi" in a + " " + b)
    gruppen["schnitzel-fleisch"] = zutat("Schnitzel", "Schnitzel", lambda n, a, b: "Schnitzel" in a)
    gruppen["fisch"] = zutat("Fisch", "Fish", lambda n, a, b: "Fisch" in a)
    # Pommes aus (Chef-App „Zutaten“): nur die reinen Pommes sind dann nicht zu haben;
    # alle anderen Gerichte gibt es ohne Pommes bzw. ohne Reis, je 0,50 € günstiger (BEILAGEN unten)
    gruppen["z:Pommes"] = zutat("Pommes", "Fries", lambda n, a, b: a.startswith("Pommes"))
    return gruppen


def beilagen():
    """Gerichte mit Pommes bzw. Reis als Beilage: {Nr: ["Pommes", "Reis"]}"""
    aus = {}
    for gr in GRUPPEN:
        for ab in gr["abschnitte"]:
            for g in ab["gerichte"]:
                if not g[0] or g[1].startswith("Pommes"):
                    continue
                text = g[1] + " " + g[2]
                b = [x for x in ("Pommes", "Reis") if x in text.replace("Reisen", "")]
                if b:
                    aus[g[0]] = b
    return aus


BEILAGEN = beilagen()
BEILAGE_RABATT = 50   # Cent weniger je fehlender Beilage


SPERRGRUPPEN = sperrgruppen()


def datenschutz_html():
    """Entwurf der Datenschutzerklärung – beschreibt, was die Seite tatsächlich tut. Vor dem Livegang prüfen lassen."""
    zaehlen = (
        '<h3>Reichweitenmessung mit GoatCounter</h3>'
        '<p>Um zu sehen, wie die Website genutzt wird, zählen wir Seitenaufrufe und Klicks auf „Per WhatsApp bestellen“, „Anrufen“, '
        '„Bestellung teilen“, „Gemeinsam bestellen“ und „Bewerten“ mit GoatCounter (Anbieter: Martin Tournoij, goatcounter.com). '
        'Dabei werden keine Cookies gesetzt und keine Informationen auf Ihrem Gerät gespeichert oder aus ihm ausgelesen. Übermittelt werden nur '
        'die aufgerufene Seite bzw. der Klick sowie technisch bedingt Ihre IP-Adresse und Browserkennung; GoatCounter speichert die '
        'IP-Adresse nicht, sondern bildet daraus nur kurzzeitig eine nicht rückverfolgbare Kennung, um Mehrfachzählungen zu vermeiden. '
        'Ist in Ihrem Browser „Do Not Track“ eingeschaltet, zählen wir nicht. Rechtsgrundlage ist unser berechtigtes Interesse an einer '
        'datensparsamen Auswertung (Art. 6 Abs. 1 lit. f DSGVO). '
        '<span class="platzhalter">[Vertrag zur Auftragsverarbeitung mit GoatCounter klären und hier nennen]</span></p>') if ZAEHLER else ""
    entwurf = '<p class="platzhalter">Entwurf – vor dem Freischalten rechtlich prüfen lassen.</p>' if VORSCHAU else ""
    return f"""{entwurf}
        <h3>Verantwortlich</h3>
        <p>Für Saray Döner Freital: <span class="platzhalter">[Khan – Name, Anschrift, E-Mail]</span>, Dresdner Str. 87, 01705 Freital, Telefon 0351 27676660.
        Für Saray Döner Altenberg: Ahmet Saglam, Bahnhof 3, 01773 Altenberg, Telefon 035056 23674, E-Mail solino1@hotmail.de.
        <span class="platzhalter">[Klären: Betreiben beide die Website gemeinsam (dann gemeinsam Verantwortliche nach Art. 26 DSGVO mit Vereinbarung) oder jeder für seinen Laden?]</span></p>
        <h3>Das Wichtigste vorab</h3>
        <p>Diese Website setzt keine Cookies. Schriften, Bilder und Stadtpläne liegen auf unserem eigenen Webspace; Inhalte fremder Anbieter
        binden wir nicht ein{" – mit Ausnahme der unten beschriebenen Besucherzählung mit GoatCounter" if ZAEHLER else ""}.
        Sie müssen keine Daten angeben, um die Speisekarte anzusehen.</p>
        <h3>Hosting und Server-Logfiles</h3>
        <p>Die Website wird bei GitHub Pages betrieben (GitHub, Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, USA).
        Beim Aufruf verarbeitet GitHub technisch notwendige Daten wie IP-Adresse, Datum und Uhrzeit, aufgerufene Datei, Browser und
        Betriebssystem, um die Seite auszuliefern und die Sicherheit zu gewährleisten. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO.
        Eine Übermittlung in die USA ist möglich; GitHub ist nach dem EU-US Data Privacy Framework zertifiziert.
        Mehr dazu: <a href="https://docs.github.com/de/site-policy/privacy-policies/github-general-privacy-statement" target="_blank" rel="noopener">Datenschutzerklärung von GitHub</a>.</p>
        <h3>Speicherung auf Ihrem Gerät</h3>
        <p>Ihre Bestellung, die gewählte Abholung und Ihr Name, Ihre letzte abgeschickte Bestellung (für „Wie letztes Mal?“), die Angaben
        einer laufenden Sammelbestellung („Gemeinsam bestellen“), ob wir Sie nach einer Bestellung schon einmal um eine Bewertung gebeten haben,
        die Sprache und die Einstellung für Linkshänder speichern wir nur in Ihrem
        Browser (Local Storage), damit sie beim nächsten Besuch noch da sind. Diese Daten werden nicht an uns übertragen. Für die Nutzung
        ohne Internet legt Ihr Browser außerdem Seite, Schriften und Bilder in einem Zwischenspeicher ab. Sie können all das jederzeit
        in den Einstellungen Ihres Browsers löschen („Websitedaten löschen“). Rechtsgrundlage: § 25 Abs. 2 Nr. 2 TDDDG, Art. 6 Abs. 1 lit. f DSGVO.</p>
        <h3>Bestellung per WhatsApp oder Telefon</h3>
        <p>Wenn Sie auf „Per WhatsApp bestellen“ tippen, öffnet sich WhatsApp mit Ihrer Bestellung als vorbereiteter Nachricht. Erst wenn
        Sie die Nachricht dort absenden, erhalten wir sie – zusammen mit Ihrer Telefonnummer und Ihrem WhatsApp-Namen. Für WhatsApp gilt die
        Datenschutzerklärung von WhatsApp Ireland Ltd. (Meta). Wir nutzen Ihre Angaben nur, um die Bestellung zu bearbeiten
        (Art. 6 Abs. 1 lit. b DSGVO) und löschen den Chat, wenn er dafür nicht mehr gebraucht wird. Gleiches gilt für telefonische Bestellungen.
        „Bestellung teilen“ und „Gemeinsam bestellen“ nutzen das Teilen-Menü Ihres Geräts; was Sie wohin senden, entscheiden Sie selbst.</p>
        {zaehlen}
        <h3>Links zu Google</h3>
        <p>„Route planen“ und „Bewerten“ öffnen Google Maps bzw. die Google-Bewertung erst, wenn Sie darauf tippen. Dann gilt die
        Datenschutzerklärung von Google.</p>
        <h3>Ihre Rechte</h3>
        <p>Sie haben das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit sowie Widerspruch
        gegen Verarbeitungen auf Grundlage berechtigter Interessen (Art. 15–21 DSGVO). Wenden Sie sich dazu an die oben genannte Adresse.
        Sie können sich außerdem bei einer Datenschutz-Aufsichtsbehörde beschweren, zum Beispiel bei der Sächsischen Datenschutz- und
        Transparenzbeauftragten, Maternistraße 17, 01067 Dresden.</p>
        <p class="klein">Stand: {_dt.date.today().strftime("%m/%Y")}</p>"""


def hinweise_html(liste):
    return "".join(
        f'<div class="hinweis-band{" hinweis-aktion" if h.get("aktion") else ""}" data-von="{h["von"]}" data-bis="{h["bis"]}" hidden><p class="wrap">'
        f'<span data-en="{e(h.get("en") or h["text"])}">{e(h["text"])}</span></p></div>' for h in liste)


import datetime as _dt, zoneinfo as _zi
STAND = _dt.datetime.now(_zi.ZoneInfo("Europe/Berlin")).strftime("%d.%m. %H:%M")


def whatsapp_nummern(einzeln):
    """Nummern aus STANDORTE. Nur für die Einzeldatei-Vorschau zusätzlich aus lokal.json
    (nicht im Repo), damit Testnummern nie auf der öffentlichen Seite landen."""
    nr = {st["id"]: st["whatsapp"] for st in STANDORTE if st.get("whatsapp")}
    lokal = HIER / "lokal.json"
    if einzeln and lokal.exists():
        nr.update(json.loads(lokal.read_text()).get("whatsapp", {}))
    return nr


SW = r"""/* Saray Döner – offline-Speicher. Seite und status.json: erst Netz, sonst Speicher. Rest: erst Speicher. */
var V='saray-%%V%%',VOR=%%LISTE%%;
self.addEventListener('install',function(e){e.waitUntil(caches.open(V).then(function(c){return c.addAll(VOR);}).then(function(){return self.skipWaiting();}));});
self.addEventListener('activate',function(e){e.waitUntil(caches.keys().then(function(ks){return Promise.all(ks.filter(function(k){return k!==V&&k.indexOf('saray-')===0;}).map(function(k){return caches.delete(k);}));}).then(function(){return self.clients.claim();}));});
self.addEventListener('fetch',function(e){
  var r=e.request,u=new URL(r.url);
  if(r.method!=='GET'||u.origin!==location.origin||u.pathname.indexOf('/chef/')>-1||u.pathname.indexOf('/druck/')>-1||u.pathname.indexOf('/kueche/')>-1||u.pathname.indexOf('/tv/')>-1)return;
  var seite=r.mode==='navigate',schluessel=seite?'./':r;
  if(seite||/status\.json$/.test(u.pathname)){
    e.respondWith(fetch(r).then(function(res){if(res.ok){var k=res.clone();caches.open(V).then(function(c){c.put(schluessel,k);});}return res;})
      .catch(function(){return caches.match(schluessel).then(function(m){return m||Response.error();});}));
    return;
  }
  e.respondWith(caches.match(r).then(function(m){return m||fetch(r).then(function(res){if(res.ok){var k=res.clone();caches.open(V).then(function(c){c.put(r,k);});}return res;});}));
});
"""


def bauen(hinweise=None, ziel=None, einzeln=False):
    """einzeln=True: eine Datei (ziel, Standard index.html). Sonst: Ordner (ziel, Standard docs/)."""
    css = (CSS.replace("%%SLAB_B%%", b64("Roboto-Slab-Bold.sub.woff", "font/woff"))
              .replace("%%SLAB_R%%", b64("Roboto-Slab-Regular.sub.woff", "font/woff"))
              .replace("%%LATO_R%%", b64("lato-normal.sub.woff", "font/woff"))
              .replace("%%LATO_B%%", b64("lato-bold.sub.woff", "font/woff")))
    js = (JS.replace("%%ZEITEN%%", JS_ZEITEN).replace("%%SONDER%%", JS_SONDER).replace("%%AKTIONEN%%", JS_AKTIONEN).replace("%%WARTE%%", JS_WARTE).replace("%%ZETTEL_JS%%", ZETTEL_JS)
            .replace("%%WA%%", json.dumps(whatsapp_nummern(einzeln)))
            .replace("%%GOOGLE%%", json.dumps({st["id"]: st["google"] for st in STANDORTE if st.get("google")}))
            .replace("%%TEL%%", json.dumps({st["id"]: [st["tel"], st["tel_href"]] for st in STANDORTE}))
            .replace("%%ADR%%", json.dumps({st["id"]: f'Saray Döner, {st["strasse"]}, {st["plz"]} {st["ort"]}' for st in STANDORTE}, ensure_ascii=False))
            .replace("%%SPERR%%", json.dumps(SPERRGRUPPEN, ensure_ascii=False))
            .replace("%%REGELN%%", json.dumps(VERFUEGBARKEIT, ensure_ascii=False))
            .replace("%%VORBESTELL_TAGE%%", str(VORBESTELL_TAGE)).replace("%%ZUG%%", json.dumps(ZUG)).replace("%%WINTER%%", json.dumps(WINTER)).replace("%%CODES%%", json.dumps(CODES, ensure_ascii=False))
            .replace("%%SPRACHEN%%", json.dumps(SP.LISTE, ensure_ascii=False))
            .replace("%%DICTS%%", json.dumps(SP.woerterbuecher(), ensure_ascii=False) if einzeln else "{}")
            .replace("%%BEILAGEN%%", json.dumps(BEILAGEN)).replace("%%BEILAGE_RABATT%%", str(BEILAGE_RABATT))
            .replace("%%ZAEHLER%%", json.dumps("" if einzeln else ZAEHLER))
            .replace("%%SW%%", "false" if einzeln else "true"))
    ersetzen = {
        "%%LD%%": json.dumps(LD, ensure_ascii=False),
        "%%DOMAIN%%": DOMAIN,
        "%%FAVICON_PNG%%": maskottchen("favicon-96.png", "image/png"),
        "%%IMG_KOPF%%": maskottchen("saray-koch-kopf.svg", "image/svg+xml"),
        "%%SCHILDER%%": STATUS_KARTEN,
        "%%IMG_KOCH%%": maskottchen("saray-koch.svg", "image/svg+xml"),
        "%%IMG_LADEN%%": b64("laden_web.webp", "image/webp"),
        "%%IMG_LADEN_480%%": b64("laden_480.webp", "image/webp"),
        "%%STICKER%%": preis(DOENER_PREIS, "sticker-preis") if DOENER_PREIS else "",
        "%%SUCH_ICON%%": SUCH_ICON,
        "%%NAV%%": NAV,
        "%%KARTE%%": KARTE,
        "%%BELIEBT%%": MITTAG_HTML + BELIEBT_HTML,
        "%%ORTE%%": ORTE,
        "%%GRUPPEN_TEL%%": "".join(f'<a class="knopf knopf-linie" href="tel:{st["tel_href"]}">{TEL_ICON}{e(st["name"])}: {e(st["tel"])}</a>' for st in STANDORTE),
        "%%GRUPPEN_BAR%%": ('<p class="bar">' + BAR_ICON + t("Bezahlt wird bei Abholung – nur bar.", "You pay on pickup – cash only.") + '</p>') if all(st.get("bar") for st in STANDORTE) else "",
        "%%ZETTEL_BAR%%": ('<p class="zettel-bar">' + BAR_ICON + t("Bezahlt wird bei Abholung – nur bar.", "You pay on pickup – cash only.") + '</p>') if all(st.get("bar") for st in STANDORTE) else "",
        "%%ALLERGENE%%": allergene_html(),
        "%%DATENSCHUTZ%%": datenschutz_html(),
        "%%FUSS_ORTE%%": FUSS_ORTE,
        "%%HINWEISE%%": hinweise_html(HINWEISE if hinweise is None else hinweise),
        "%%WA_ICON%%": '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 20.5l1.3-4.2A8.5 8.5 0 1 1 8 19.4z"/><path d="M9 8.5c0 3 2.5 6 6 6.5l1.2-1.4-2-1-.9.8c-1-.4-1.9-1.3-2.3-2.3l.8-.9-1-2L9.4 8.4"/></svg>',
        "%%LADEN_CHIPS%%": "".join(f'<button type="button" class="chip" data-laden="{st["id"]}" aria-pressed="false">{e(st["name"])}</button>' for st in STANDORTE),
        "%%ZETTEL_ANRUF%%": "".join(f'<a class="knopf knopf-dunkel" data-anruf="{st["id"]}" href="tel:{st["tel_href"]}">{TEL_ICON}{t(st["name"] + " anrufen: " + st["tel"], "Call " + st["name"] + ": " + st["tel"])}</a>' for st in STANDORTE),

        "%%TITEL_PRAEFIX%%": "[Entwurf] " if VORSCHAU else "",
        "%%BODY_KLASSE%%": ' class="vorschau"' if VORSCHAU else "",
        "%%VORSCHAU_BAND%%": ('<div class="vorschau-band" role="note"><strong data-en="DRAFT">ENTWURF</strong> '
                              '<span data-en="Not yet the official website of Saray Döner. Orders go to a test number.">'
                              'Noch nicht die offizielle Seite von Saray Döner. Bestellungen gehen an eine Testnummer.</span>'
                              f' <small class="stand">Stand {STAND}</small></div>')
                             if VORSCHAU else "",
        "%%APP_KOPF%%": "" if einzeln else (
            '\n<link rel="manifest" href="manifest.webmanifest">'
            f'\n<link rel="apple-touch-icon" href="{maskottchen("app-180.png", "image/png")}">'
            '\n<meta name="apple-mobile-web-app-title" content="Saray">'
            '\n<meta name="mobile-web-app-capable" content="yes">'
            '\n<meta name="apple-mobile-web-app-capable" content="yes">'),
        "%%ROBOTS%%": '<meta name="robots" content="noindex">\n' if VORSCHAU and not einzeln else "",
    }
    if einzeln:
        ersetzen["%%CSS_EINBINDEN%%"] = f"<style>{css}</style>"
        ersetzen["%%JS_EINBINDEN%%"] = f"<script>{js}</script>"
    else:
        # Versionskennung aus dem Inhalt: nach jeder Änderung lädt der Browser die neue Datei statt der zwischengespeicherten
        import hashlib
        v_css = hashlib.sha1(css.encode()).hexdigest()[:8]
        v_js = hashlib.sha1(js.encode()).hexdigest()[:8]
        ersetzen["%%CSS_EINBINDEN%%"] = f'<link rel="stylesheet" href="css/style.css?v={v_css}">'
        ersetzen["%%JS_EINBINDEN%%"] = f'<script src="js/main.js?v={v_js}"></script>'
    seite = SEITE
    for k, v in ersetzen.items():
        seite = seite.replace(k, v)
    if einzeln:
        seite = dateien_aufloesen(seite, True)
        assert "%%" not in seite, "Platzhalter übrig"
        ziel = pathlib.Path(ziel or HIER / "index.html")
        ziel.write_text(seite, encoding="utf-8")
        print(f"{ziel}  {ziel.stat().st_size // 1024} KB  ·  {ANZAHL} Positionen")
        return
    aus = pathlib.Path(ziel or HIER / "docs")
    status = (aus / "status.json").read_text() if (aus / "status.json").exists() else None
    if aus.exists():
        shutil.rmtree(aus)
    (aus / "css").mkdir(parents=True)
    (aus / "js").mkdir()
    seite = dateien_aufloesen(seite, False, aus, "")
    css = dateien_aufloesen(css, False, aus, "../")
    for name, inhalt in (("index.html", seite), ("css/style.css", css), ("js/main.js", js)):
        assert "%%" not in inhalt, f"Platzhalter übrig in {name}"
        (aus / name).write_text(inhalt.strip() + "\n", encoding="utf-8")
    (aus / ".nojekyll").write_text("")
    (aus / "lang").mkdir(exist_ok=True)
    for code, d in SP.woerterbuecher().items():   # weitere Sprachen, werden erst bei Bedarf geladen
        (aus / "lang" / f"{code}.json").write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    # Service Worker: Seite, CSS, JS, Schriften und Bilder für offline; Version aus dem Inhalt (ohne „Stand“-Zeit)
    import hashlib
    ohne_stand = re.sub(r'<small class="stand">.*?</small>', "", seite)
    vor = ["./"] + re.findall(r'(?:href|src)="((?:css|js)/[^"]+)"', seite) \
        + sorted({"img/" + f.name for f in (aus / "img").iterdir() if f.suffix == ".svg"} | {"fonts/" + f.name for f in (aus / "fonts").iterdir()})
    (aus / "sw.js").write_text(SW.replace("%%V%%", hashlib.sha1((ohne_stand + css + js).encode()).hexdigest()[:10])
                               .replace("%%LISTE%%", json.dumps(vor)))
    for g in (192, 512):
        shutil.copyfile(MASKOTT / f"app-{g}.png", aus / "img" / f"app-{g}.png")
    (aus / "manifest.webmanifest").write_text(json.dumps({
        "name": "Saray Döner" + (" (Vorschau)" if VORSCHAU else ""), "short_name": "Saray",
        "description": "Speisekarte, Öffnungszeiten und Bestellung bei Saray Döner in Freital und Altenberg.",
        "lang": "de", "start_url": "./", "scope": "./", "display": "standalone",
        "background_color": "#FFD21F", "theme_color": "#FFD21F",
        "icons": [{"src": f"img/app-{g}.png", "sizes": f"{g}x{g}", "type": "image/png", "purpose": "any maskable"} for g in (192, 512)],
    }, ensure_ascii=False, indent=2) + "\n")
    (aus / "status.json").write_text(status or '{\n  "regeln": []\n}\n')
    if CNAME:
        (aus / "CNAME").write_text(CNAME + "\n")
    (aus / "robots.txt").write_text("User-agent: *\n" + ("Disallow: /\n" if VORSCHAU else "Disallow: /chef/\nDisallow: /druck/\nDisallow: /kueche/\nDisallow: /tv/\n"))
    import chef_app
    chef_app.schreiben(aus, STANDARD_GRUPPEN, STANDORTE, SPERRGRUPPEN, REPO, ZAEHLER, CNAME, FOTOS)
    # Bildschirm im Laden (tv/) und Küchenansicht (kueche/)
    import laden_seiten
    tv_gruppen = [{"id": g["id"], "titel": g["titel"], "abschnitte": [{
        "titel": ab["titel"], "groessen": ab.get("groessen") or [],
        "gerichte": [{"k": x[0] or x[1], "nr": anz(x[0]) if x[0] else "", "name": x[1], "desc": x[2].rstrip(":").rstrip(),
                      "p": [int(p.replace(",", "")) for p in x[3]]} for x in ab["gerichte"]]} for ab in g["abschnitte"]]} for g in GRUPPEN]
    tv_index = {x["k"]: x for g in tv_gruppen for ab in g["abschnitte"] for x in ab["gerichte"]}
    (aus / "img" / "gerichte").mkdir(parents=True, exist_ok=True)
    for nr in FOTOS:
        if (FOTO_CACHE / f"nr-{nr}-800.webp").exists():
            shutil.copyfile(FOTO_CACHE / f"nr-{nr}-800.webp", aus / "img" / "gerichte" / f"nr-{nr}-800.webp")
    tv = {
        "gruppen": tv_gruppen, "index": tv_index,
        "empf": [n for n in EMPFEHLUNG if n in GERICHT and n not in NUR_DIAET],
        "fotos": {nr: f"../img/gerichte/nr-{nr}-800.webp" for nr in FOTOS},
        "aktionen": json.loads(JS_AKTIONEN), "sperr": SPERRGRUPPEN, "regeln": VERFUEGBARKEIT,
        "beilagen": sorted({b for v in BEILAGEN.values() for b in v}), "rabatt": BEILAGE_RABATT,
        "laeden": {st["id"]: {"name": st["name"], "zeiten": json.loads(JS_ZEITEN)[st["id"]], "sonder": json.loads(JS_SONDER)[st["id"]],
                              "warte": WARTE.get(st["id"])} for st in STANDORTE},
    }
    version = hashlib.sha1((ohne_stand + css + js + json.dumps(tv, sort_keys=True)).encode()).hexdigest()[:10]
    tv["version"] = version
    laden_seiten.schreiben(aus, tv, {st["id"]: st["name"] for st in STANDORTE}, DOMAIN if not VORSCHAU else f"https://{CNAME}/", version)
    gesamt = sum(f.stat().st_size for f in aus.rglob("*") if f.is_file())
    for w in WARNUNGEN:
        print("WARNUNG:", w)
    print(f"{aus}/  {gesamt // 1024} KB in {sum(1 for f in aus.rglob('*') if f.is_file())} Dateien  ·  {ANZAHL} Positionen")


if __name__ == "__main__":
    bauen(einzeln="--einzeln" in sys.argv)
