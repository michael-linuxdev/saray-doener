#!/usr/bin/env python3
"""Baut die Website von Saray Döner.

    python3 build.py            -> docs/ (index.html, css/, js/, fonts/, img/) für GitHub Pages
    python3 build.py --einzeln  -> index.html als eine einzige Datei mit allem eingebettet (Vorschau)

Keine externen Anfragen, keine Cookies. Speisekarte: menu.py · Englisch: englisch.py ·
Standorte/Zeiten: STANDORTE unten · Hinweis-Band: HINWEISE unten.
WhatsApp-Nummern stehen nicht im Repo: optional in lokal.json (siehe README).
"""
import base64, html, json, math, pathlib, re, shutil, sys, urllib.parse
from menu import GRUPPEN
import englisch as EN
import anpassungen as ANP

HIER = pathlib.Path(__file__).parent
A = HIER / "assets"
DOMAIN = "https://xn--saraydner-57a.de/"  # saraydöner.de (Canonical)
CNAME = "saray.micana.de"
REPO = "michael-linuxdev/saray-doener"     # Chef-App speichert Änderungen in diesem Repo (daten/anpassungen.json)                  # Adresse der GitHub Page
VORSCHAU = True                            # True: Suchmaschinen sollen die Vorschau-Adresse nicht aufnehmen

STANDORTE = [
    {
        "id": "freital", "name": "Freital", "strasse": "Dresdner Str. 87", "plz": "01705", "ort": "Freital",
        "tel": "0351 27676660", "tel_href": "+4935127676660", "tel_ld": "+49 351 27676660",
        "whatsapp": "491601836249",  # Testnummer (Michael) – vor dem Livegang durch die Ladennummer ersetzen; leer: Knopf ausgeblendet
        "zeilen": [("Montag bis Freitag", "10–22 Uhr", [1, 2, 3, 4, 5]), ("Samstag und Sonntag", "11–22 Uhr", [6, 0])],
        "zeilen_en": ["Monday to Friday", "Saturday and Sunday"], "extra_en": "Outdoor seating in good weather.",
        "kurz": "Mo–Fr 10–22 Uhr, Sa–So 11–22 Uhr",
        "extra": "Bei schönem Wetter sitzen Sie draußen.",
        "lage": "an der Dresdner Straße",
    },
    {
        "id": "altenberg", "name": "Altenberg", "strasse": "Dresdner Str. 23", "plz": "01773", "ort": "Altenberg",
        "tel": "035056 23674", "tel_href": "+493505623674", "tel_ld": "+49 35056 23674",
        "whatsapp": "491601836249",  # Testnummer (Michael)
        "zeilen": [("Montag bis Samstag", "10–21 Uhr", [1, 2, 3, 4, 5, 6]), ("Sonntag", "11–21 Uhr", [0])],
        "zeilen_en": ["Monday to Saturday", "Sunday"], "extra_en": "Right by the station.",
        "kurz": "Mo–Sa 10–21 Uhr, So 11–21 Uhr",
        "extra": "Direkt am Bahnhof.",
        "lage": "direkt am Bahnhof",
    },
]


def minuten(spanne):
    a, b = spanne.replace(" Uhr", "").split("–")
    return int(a) * 60, int(b) * 60


# Änderungen aus der Chef-App (daten/anpassungen.json) auf Speisekarte und Öffnungszeiten anwenden
import os
ANPASSUNGEN = ANP.laden(pathlib.Path(os.environ.get("SARAY_ANPASSUNGEN") or HIER / "daten" / "anpassungen.json"))
WARNUNGEN = []
STANDARD_GRUPPEN = GRUPPEN
GRUPPEN = ANP.karte(GRUPPEN, ANPASSUNGEN, WARNUNGEN.append)

for s in STANDORTE:
    std = {}
    for _, spanne, tage in s["zeilen"]:
        for t in tage:
            std[t] = minuten(spanne)
    s["zeiten_standard"] = std
    s["zeiten"] = ANP.zeiten(std, (ANPASSUNGEN.get("zeiten") or {}).get(s["id"]), WARNUNGEN.append, s["name"])
    s["zeilen_neu"] = ANP.zeilen(s["zeiten"])
    s["kurz"] = ", ".join(f'{z["kurz"]} {z["zeit"]}' for z in s["zeilen_neu"])
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
EMPFEHLUNG = "26"
BELIEBT = ["7", "51", "37", "100", "96", "99", "124", "17", "20"]
GERICHT = {g[0]: (g, gr, ab) for gr in GRUPPEN for ab in gr["abschnitte"] for g in ab["gerichte"] if g[0]}


D_NR = {"18", "19", "60", "61", "121", "123", "124"}


def gericht_typ(nr, gruppe, abschnitt):
    if abschnitt == "Pizza":
        return {"91": "S", "105": "R"}.get(nr, "P")
    if nr and (gruppe in ("Döner", "Dürüm") or abschnitt in ("Dönerbox", "Dönerteller") or nr in D_NR):
        return "D"
    if gruppe == "Salate":
        return "SA"
    return ""


def zettel_daten(nr, name, desc, preise, groessen, typ="", varianten=()):
    ne = (("No. " + nr + " ") if nr else "") + EN.name(name)
    cent = "|".join(str(int(x.replace(",", ""))) for x in preise)
    v = "|".join(f"{k}: {t}" for k, t in varianten)
    return (f' data-k="{e(nr or name)}" data-n="{e(("Nr. " + nr + " ") if nr else "")}{e(name)}" data-d="{e(desc)}"'
            f' data-p="{cent}" data-g="{e("|".join(groessen or []))}" data-t="{typ}" data-v="{e(v)}" data-ne="{e(ne)}" data-dn="{e(EN.text(desc))}"')


def plus_knopf(name):
    return f'<button type="button" class="plus" aria-label="{e(name)} zur Bestellung hinzufügen" data-en-aria="Add {e(EN.name(name))} to my order">+</button>'


def gericht_html(g, gruppe, abschnitt, groessen):
    nr, name, desc, preise = g[:4]
    varianten = g[4] if len(g) > 4 else []
    suchtext = " ".join([nr, name, desc, abschnitt, gruppe] + [v for _, v in varianten]
                        + [EN.name(name), EN.text(desc), EN.titel(abschnitt), EN.titel(gruppe)] + [EN.text(v) for _, v in varianten])
    beliebt = nr in BELIEBT
    empfohlen = nr == EMPFEHLUNG
    teile = [f'<li class="gericht{" ist-beliebt" if beliebt or empfohlen else ""}"{f' id="nr-{nr}"' if nr else ""} data-s="{e(suchtext)}{" beliebt" if beliebt else ""}{" empfehlung" if empfohlen else ""}"{zettel_daten(nr, name, desc, preise, groessen, gericht_typ(nr, gruppe, abschnitt), varianten)}>']
    teile.append(f'<span class="nr">{chr(60) + "span class=" + chr(34) + "sr-only" + chr(34) + ">Nr. </span>" + e(nr) if nr else ""}</span>')
    teile.append(f'<span class="zeile"><span class="name">{t(name, EN.name(name))}{' <span class="marke-beliebt" data-en="Popular">Beliebt</span>' if beliebt else ""}{' <span class="marke-beliebt marke-empfehlung" data-en="Recommended">Empfehlung</span>' if empfohlen else ""}</span><span class="punkte" aria-hidden="true"></span></span>')
    if groessen:
        for i, p in enumerate(preise):
            teile.append(preis(p, f"preis p{i + 1}", groessen[i]))
    else:
        teile.append(preis(preise[0]))
    teile.append(plus_knopf(name))
    if desc or varianten:
        inner = t(desc, EN.text(desc)) if desc else ""
        if varianten:
            inner += '<ul class="varianten">' + "".join(
                f"<li><b>{e(k)}</b> {t(v, EN.text(v))}</li>" for k, v in varianten) + "</ul>"
        teile.append(f'<div class="info">{inner}</div>')
    teile.append("</li>")
    return "".join(teile)


HAND_GESETZT = []


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
        if groessen:
            kopf = "".join(f"<span>{e(x)}</span>" for x in groessen) + "<span></span>"
            out.append(f'<div class="groessen-kopf" aria-hidden="true"><div class="groessen"><span></span><span></span>{kopf}</div>'
                       f'<div class="groessen nur-breit"><span></span><span></span>{kopf}</div></div>')
        klasse = "liste zwei" if groessen else "liste"
        if not any(g[0] for g in ab["gerichte"]):
            klasse += " ohne-nr"
        out.append(f'<ul class="{klasse}" style="--zeilen:{math.ceil(n / 2)}">')
        zeilen = [gericht_html(g, gr["titel"], ab["titel"], groessen) for g in ab["gerichte"]]
        if not HAND_GESETZT and zeilen:
            # Umschalter für Linkshänder direkt unter der ersten Bestellmöglichkeit (nur Handy)
            zeilen.insert(1, '<li class="hand-zeile"><button type="button" class="hand-knopf" data-hand>Linkshänder: Knöpfe links</button></li>')
            HAND_GESETZT.append(True)
        out += zeilen
        out.append("</ul>")
        if ab.get("notiz"):
            out.append(f'<p class="notiz" data-en="{e(EN.titel(ab["notiz"]))}">{e(ab["notiz"])}</p>')
        out.append("</div>")
    out.append("</section>")
    return "\n".join(out)


KARTE = "\n".join(gruppe_html(g) for g in GRUPPEN)


def beliebt_karte(nr, gross=False):
    g, gr, ab = GERICHT[nr]
    name, desc, preise = g[1], g[2], g[3]
    zusatz = f" ({ab['groessen'][0]})" if ab.get("groessen") else ""
    return (f'<li class="tipp{" tipp-gross" if gross else ""}"{zettel_daten(nr, name, desc, preise, ab.get("groessen"), gericht_typ(nr, gr["titel"], ab["titel"]), g[4] if len(g) > 4 else ())}><a href="#nr-{nr}">'
            f'<span class="tipp-nr"><span data-en="No.">Nr.</span> {nr}</span><b class="tipp-name" data-en="{e(EN.name(name))}">{e(name)}</b>'
            f'<span class="tipp-info" data-en="{e(EN.text(desc))}">{e(desc)}</span>'
            f'<span class="tipp-preis">{t("ab ", "from ") if zusatz else ""}{preis(preise[0])}</span>'
            + (f'<img class="tipp-koch" src="{maskottchen("saray-koch.svg", "image/svg+xml")}" width="430" height="470" alt="">' if gross else "")
            + '</a>' + plus_knopf(name) + '</li>')


# gelöschte Gerichte fallen aus Empfehlung und „Beliebt“ heraus
BELIEBT = [n for n in BELIEBT if n in GERICHT]
BELIEBT_HTML = ('<section class="beliebt" aria-label="Empfehlungen">'
                + ('<h3 class="beliebt-titel" data-en="Our recommendation">Wir empfehlen</h3><ul class="tipps tipps-empfehlung">' + beliebt_karte(EMPFEHLUNG, True) + '</ul>'
                   if EMPFEHLUNG in GERICHT else "") +
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
SUCH_ICON = ('<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/>'
             '<path d="M20 20l-4-4"/></svg>')


def status_html(s, klasse="status"):
    return (f'<p class="{klasse}" data-status="{s["id"]}"><span class="punkt" aria-hidden="true"></span>'
            f'<span class="status-text">{e(s["kurz"])}</span></p>')


STATUS_KARTEN = "\n".join(
    f'''<li class="schild">
  <p class="schild-ort"><a class="schild-link" href="#ort-{s["id"]}" data-en-aria="{e(s["name"])}: opening hours and directions" aria-label="{e(s["name"])}: Öffnungszeiten und Anfahrt">{e(s["name"])}</a></p>
  <p class="schild-adresse">{e(s["strasse"])}</p>
  {status_html(s)}
  <a class="schild-tel" href="tel:{s["tel_href"]}" aria-label="{e(s["name"])} anrufen: {e(s["tel"])}" title="{e(s["tel"])}">{TEL_ICON}</a>
</li>''' for s in STANDORTE)

def karte_html(s):
    alt = {"freital": "Stadtplan Freital-Potschappel: Saray Döner an der Dresdner Straße, Ecke Turnerstraße",
           "altenberg": "Stadtplan Altenberg: Saray Döner an der Dresdner Straße am Bahnhof"}[s["id"]]
    return (f'<figure class="karte-bild"><a href="{e(s["maps"])}" target="_blank" rel="noopener" aria-label="Route zu Saray Döner {e(s["name"])} planen">'
            f'<img src="{b64("karte_" + s["id"] + ".webp", "image/webp")}" width="940" height="680" loading="lazy" alt="{alt}">'
            f'<svg class="pin" viewBox="0 0 40 52" aria-hidden="true"><path d="M20 50 C20 50 4 31 4 19 a16 16 0 0 1 32 0 C36 31 20 50 20 50 Z" fill="#C8371A" stroke="#3A1531" stroke-width="3"/><circle cx="20" cy="19" r="6.5" fill="#fff"/></svg></a>'
            f'<figcaption>{t("Karte", "Map")}: © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>{t("-Mitwirkende", " contributors")}</figcaption></figure>')


ORTE = "\n".join(
    f'''<article class="ort" id="ort-{s["id"]}" aria-labelledby="h-{s["id"]}">
  <h3 id="h-{s["id"]}">{e(s["name"])}</h3>
  {status_html(s)}
  <address>Saray Döner<br>{e(s["strasse"])}<br>{e(s["plz"])} {e(s["ort"])}<br>
  {t("Telefon", "Phone")} <a href="tel:{s["tel_href"]}">{e(s["tel"])}</a></address>
  {karte_html(s)}
  <table class="zeiten"><caption class="sr-only">Öffnungszeiten {e(s["name"])}</caption><tbody>
  {"".join(f'<tr data-tage="{",".join(map(str, z["tage"]))}"><th scope="row" data-en="{e(z["en"])}">{e(z["de"])}</th><td data-en="{e(z["zeit_en"])}">{e(z["zeit"])}</td></tr>' for z in s["zeilen_neu"])}
  </tbody></table>
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
        "hasMenu": DOMAIN + "#speisekarte",
        "address": {"@type": "PostalAddress", "streetAddress": s["strasse"], "postalCode": s["plz"],
                    "addressLocality": s["ort"], "addressCountry": "DE"},
        "openingHoursSpecification": [{
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": [TAGE_EN[t] for t in z["tage"]],
            "opens": f"{z['wert'][0] // 60:02d}:{z['wert'][0] % 60:02d}", "closes": f"{z['wert'][1] // 60:02d}:{z['wert'][1] % 60:02d}"}
            for z in s["zeilen_neu"] if z["wert"]],
    } for s in STANDORTE],
}
JS_ZEITEN = json.dumps({s["id"]: {str(k): list(v) for k, v in s["zeiten"].items()} for s in STANDORTE})

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
.marke-beliebt{display:inline-block;vertical-align:2px;margin-left:6px;padding:1px 8px;border-radius:999px;background:var(--paprika);color:#fff;
  font:700 .7rem/1.5 var(--text);letter-spacing:.01em;white-space:nowrap}
.beliebt{margin-bottom:40px;min-width:0;max-width:100vw}
.karte-inhalt{min-width:0}
.tipps{width:calc(100% + 2 * var(--rand));position:relative}
.beliebt-titel{font-size:1.35rem;margin-bottom:12px}
.tipps{list-style:none;margin:0 calc(-1 * var(--rand));padding:4px var(--rand) 12px;display:flex;gap:12px;overflow-x:auto;scroll-snap-type:x mandatory;scroll-padding-inline:var(--rand);scrollbar-width:thin}
.tipp{flex:0 0 200px;scroll-snap-align:start;display:flex;flex-direction:column;border:2px solid var(--tinte);border-radius:16px;background:#fff}
.tipp a{display:flex;flex-direction:column;gap:4px;flex:1;padding:14px 16px;border-radius:14px;text-decoration:none}
@media (hover:hover){.tipp:hover{background:var(--gelb-blass)}.tipp-gross:hover{background:#FFDB4D}}
.tipp-gross{flex-basis:100%}
.tipps-empfehlung{overflow:visible;margin-bottom:22px}
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
  .tipps-empfehlung{grid-template-columns:minmax(0,1fr)}
  .tipp-gross{grid-column:auto}.gericht.ist-beliebt{scroll-margin-top:24px}}
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
.hand-zeile{list-style:none;margin:-2px 0 6px;font-size:.88rem;color:var(--tinte-weich)}
@media (min-width:720px){.hand-zeile{display:none}}
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

.allergene{margin-top:8px;background:var(--gelb-blass);border-radius:14px;padding:16px 18px;max-width:62ch;font-size:.97rem}

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
.vorschau-band{position:relative;z-index:80;padding:10px 16px;text-align:center;font:400 .9rem/1.4 var(--text);color:#fff;
  background:repeating-linear-gradient(-45deg,#3A1531 0 18px,#5a2350 18px 36px);border-bottom:4px solid var(--paprika)}
.vorschau-band strong{display:inline-block;margin-right:6px;padding:1px 10px;border-radius:999px;background:var(--paprika);letter-spacing:.08em}
/* nicht position:fixed: Safari 26 richtet die Farbe der Adressleiste nach festen Elementen am Rand aus */
body.vorschau{position:relative}
body.vorschau::after{content:"";position:absolute;inset:0;z-index:90;pointer-events:none;opacity:.09;
  background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='420' height='300'%3E%3Ctext x='210' y='160' text-anchor='middle' transform='rotate(-30 210 150)' font-family='Arial,sans-serif' font-weight='700' font-size='30' fill='%23C8371A'%3ENICHT FREIGESCHALTET%3C/text%3E%3C/svg%3E") repeat}
@media print{body.vorschau::after{opacity:.15;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
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
.chip:disabled{opacity:.35;cursor:not-allowed}
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
.zettel-hinweis{color:var(--tinte-weich);font-size:.92rem;margin-bottom:14px}
.zettel-knoepfe{display:grid;gap:10px}
.zettel-knoepfe .knopf{width:100%}
.knopf-klein{min-height:40px;font-size:.92rem;border:0;background:none;color:var(--tinte-weich);text-decoration:underline;cursor:pointer}
.zettel-meldung{position:fixed;z-index:70;left:50%;bottom:calc(80px + env(safe-area-inset-bottom));transform:translateX(-50%);max-width:calc(100% - 32px);
  padding:10px 16px;border-radius:12px;background:var(--tinte);color:#fff;font-weight:700;font-size:.95rem;text-align:center;box-shadow:0 8px 20px -8px rgba(0,0,0,.4)}
@media (min-width:720px){.zettel-meldung{bottom:92px;left:auto;right:24px;transform:none}}
@media print{.plus,.zettel-leiste{display:none!important}}

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
.zeiten th{text-align:left;font-weight:400}
.zeiten td{text-align:right;font-weight:700;white-space:nowrap;font-variant-numeric:tabular-nums}
html[lang=en] .zeiten tr.heute th::after{content:"today"}
.zeiten tr.heute th::after{content:"heute";display:inline-block;margin-left:8px;padding:1px 8px;border-radius:999px;background:var(--gelb);
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
.recht summary{cursor:pointer;font-weight:700;color:var(--gelb);padding:6px 0;width:max-content}
.recht details[open]{background:rgba(255,255,255,.06);border-radius:12px;padding:4px 16px 16px}
.recht details p{margin-bottom:8px;max-width:70ch}
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
  var PAARE=[['1','2'],['3','4'],['6','7'],['9','10'],['11','12'],['13','14'],['15','16'],['23','25'],['30','31'],['32','33'],['36','37'],
    ['40','41'],['42','43'],['50','51'],['52','53'],['54','55'],['60','61'],['123','124']],OHNE_K={},MIT_K={};
  PAARE.forEach(function(pq){OHNE_K[pq[0]]=pq[1];MIT_K[pq[1]]=pq[0];});
  /* Varianten: Form, Füllung, extra Fleisch (Super), Käse, Beilage.
     Die Schalter im Zettel suchen damit das passende Gericht der Karte. */
  var VAR={},FUELL=['kalb','huhn','veg','falafel','halloumi','hack'];
  var F_NAME={kalb:['Dönerfleisch','Döner meat'],huhn:['Hähnchen','Chicken'],veg:['ohne Fleisch','No meat'],falafel:['Falafel','Falafel'],
    halloumi:['Halloumi','Halloumi'],hack:['Hackfleisch','Minced meat']};
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
    ['24','teller','veg',0,0,'SP'],['28','ueber','kalb',0,0],['38','ueber','huhn',0,0],['18','kinder','kalb',0,0],['19','kinder','huhn',0,0],
    ['121','lahmacun','hack',0,0],['123','lahmacun','kalb',0,0],['124','lahmacun','kalb',0,1]
  ].forEach(function(v){VAR[v[0]]={k:v[0],form:v[1],f:v[2],sup:v[3],kae:v[4],bei:v[5]||''};});
  /* bestes Gericht mit den gewünschten Merkmalen; Vorrang: Beilage, Käse, Super */
  function variante(k,wunsch,streng){
    var a=VAR[k];if(!a)return null;var w=Object.assign({},a,wunsch),best=null,bp=-1;
    Object.keys(VAR).forEach(function(kk){var v=VAR[kk];if(v.form!==a.form||v.f!==w.f||!gerichtLi(kk))return;
      if(streng&&(v.sup!==w.sup||v.kae!==w.kae||v.bei!==w.bei))return;
      var pkt=(v.bei===w.bei?4:0)+(v.kae===w.kae?2:0)+(v.sup===w.sup?1:0);if(pkt>bp){bp=pkt;best=kk;}});
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
  function uhrK(t){var m=minAus(t),h=Math.floor(m/60),r=m%60;return SP==='en'?h+':'+(r<10?'0':'')+r:(r?h+':'+(r<10?'0':'')+r:h)+' Uhr';}
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
  var W={'Knoblauch':'garlic','Kräuter':'herb','Chili':'chili','Zwiebeln':'onions','Tomaten':'tomatoes','Gurken':'cucumber','Rotkohl':'red cabbage',
    'Weißkohl':'white cabbage','Eisbergsalat':'iceberg lettuce','Paprika':'bell pepper','Zwiebel':'onion','Champignon':'mushrooms','Tomate':'tomato',
    'Peperoni':'hot peppers','Ananas':'pineapple','Oliven':'olives','Brokkoli':'broccoli','Mais':'corn','Schinken':'ham','Salami':'salami',
    'Dönerfleisch':'döner meat','Hähnchen-Dönerfleisch':'chicken döner meat','Käse':'cheese','Halloumikäse':'halloumi','Fetakäse':'feta'};
  function w(v){if(SP!=='en'||!W[v])return v;return W[v].charAt(0).toUpperCase()+W[v].slice(1);}
  function gerichtLi(nr){return document.querySelector('li.gericht[data-k="'+nr+'"]');}
  try{zettel=JSON.parse(localStorage.getItem(ZK)||'[]');if(!Array.isArray(zettel))zettel=[];}catch(e){zettel=[];}
  zettel.forEach(function(x){x.u=uidZ++;if(x.o&&!Array.isArray(x.o.s))x.o.s=x.o.s?[x.o.s]:[];});
  function speichern(){try{localStorage.setItem(ZK,JSON.stringify(zettel.map(function(x){var y=Object.assign({},x);delete y.u;return y;})));}catch(e){}}
  function euro(c){return (c/100).toFixed(2).replace('.',',')+' €';}
  function grund(t){return {s:(t==='D'||t==='SA')?['Kräuter']:[],ohne:[],ex:[],wahl:[],va:''};}
  function exPreis(o){return (o.ex||[]).reduce(function(a,e){return a+(GEMUESE.indexOf(e)>-1?150:200);},0);}
  function stueck(x){return x.c+exPreis(x.o);}
  function sig(x){var o=x.o;return [x.k,x.g,o.s.slice().sort().join(','),o.ohne.slice().sort().join(','),o.ex.slice().sort().join(','),o.wahl.slice().sort().join(','),o.va,x.notiz||''].join('|');}
  function liste(a,en){var u=en?' and ':' und ';return a.length<2?a.join(''):a.slice(0,-1).join(', ')+u+a[a.length-1];}
  /* Wünsche als Text; en=true nur für die Anzeige, die Nachricht an den Laden ist immer deutsch */
  function wuensche(x,en){
    var o=x.o,t=[],tr=function(a){return en?a.map(function(v){return (W[v]||v);}):a;};
    if(x.t==='D'||x.t==='SA'){var so=SOSSEN.filter(function(n){return o.s.indexOf(n)>-1;});
      if(en)t.push(!so.length?'no sauce':liste(tr(so),true)+' sauce');
      else t.push(!so.length?'ohne Soße':so.length===1?so[0]+'-Soße':so.slice(0,-1).join('-, ')+'- und '+so[so.length-1]+'-Soße');}
    if(o.ohne.length)t.push((en?'no ':'ohne ')+liste(tr(o.ohne),en));
    if(x.t==='S')t.push(o.wahl.length<3?(en?'choose '+(3-o.wahl.length)+' more toppings':'noch '+(3-o.wahl.length)+' Zutaten wählen'):(en?'with ':'mit ')+liste(tr(o.wahl),en));
    if(x.t==='R')t.push(o.va?(en?'option ':'Variante ')+o.va.charAt(0):(en?'choose option':'Variante wählen'));
    tr(o.ex).forEach(function(e){t.push('extra '+e);});
    return t.join(', ');
  }
  /* Anzeigename/Beschreibung in der gewählten Sprache */
  function nameA(x){if(SP!=='en')return x.n;var li=gerichtLi(x.k);return li&&li.dataset.ne||x.n;}
  function beschrA(x){if(SP!=='en')return x.d;var li=gerichtLi(x.k);return li&&li.dataset.dn||x.d;}
  function zusammenfassen(){
    var neu=[],idx={};
    zettel.forEach(function(x){var k=sig(x);if(idx[k]!=null&&x.u!==offen&&neu[idx[k]].u!==offen){neu[idx[k]].q+=x.q;}else{idx[k]=neu.length;neu.push(x);}});
    zettel=neu;
  }
  var zl=document.getElementById('zettel-leiste'),huelle=document.getElementById('zettel'),zliste=document.getElementById('zettel-liste'),
      zsumme=document.getElementById('zettel-summe'),zmeld=document.getElementById('zettel-meldung'),meldTimer=null,zuletzt=null;
  function anzahl(){return zettel.reduce(function(a,x){return a+x.q;},0);}
  function summe(){return zettel.reduce(function(a,x){return a+x.q*stueck(x);},0);}
  function melden(t){zmeld.textContent=t;zmeld.hidden=false;clearTimeout(meldTimer);meldTimer=setTimeout(function(){zmeld.hidden=true;},2400);}
  function el(tag,cls,text){var x=document.createElement(tag);if(cls)x.className=cls;if(text!=null)x.textContent=text;return x;}
  function knopf(text,attrs){var b=el('button',null,text);b.type='button';for(var a in attrs)b.setAttribute(a,attrs[a]);return b;}
  function chips(titel,werte,gewaehlt,art,uid,extra){
    var g=el('div','z-gruppe');g.appendChild(el('span','z-gruppe-titel',titel));var wb=el('div','z-chips');
    werte.forEach(function(v){var an=gewaehlt.indexOf(v)>-1;var b=knopf(w(v)+(extra||''),{'class':'chip','aria-pressed':String(an),'data-o':art,'data-w':v,'data-u':uid});
      if(art==='wahl'&&!an&&gewaehlt.length>=3)b.disabled=true;wb.appendChild(b);});
    g.appendChild(wb);return g;
  }
  function editor(x){
    var box=el('div','z-optionen'),o=x.o;
    if(x.t==='D'||x.t==='SA')box.appendChild(chips(L('Soße (mehrere möglich)','Sauce (choose any)'),SOSSEN,o.s,'s',x.u));
    var va=VAR[x.k];
    if(x.t==='D'&&va){
      var fg=el('div','z-gruppe');fg.appendChild(el('span','z-gruppe-titel',L('Füllung','Filling')));var fw=el('div','z-chips');
      FUELL.forEach(function(f){
        var ziel=f===va.f?x.k:variante(x.k,{f:f});if(!ziel)return;
        var spF=f===va.f?null:(sperreZettel(ziel)||(function(){var nn=jetzt();var a=sperre(ziel,'freital',0,nn.min),b=sperre(ziel,'altenberg',0,nn.min);return a&&b&&a.art==='aus'&&b.art==='aus'?a:null;})());
        var fk=knopf(L(F_NAME[f][0],F_NAME[f][1])+(f===va.f?'':spF?' – '+sperrText(spF):preisDiff(x,ziel)),{'class':'chip','aria-pressed':String(f===va.f),'data-fuell':f,'data-u':x.u});
        if(spF)fk.disabled=true;fw.appendChild(fk);
      });
      if(fw.children.length>1){fg.appendChild(fw);box.appendChild(fg);}
      var su=variante(x.k,{sup:va.sup?0:1},true);
      if(su){var sg=el('div','z-gruppe');sg.appendChild(el('span','z-gruppe-titel',L('Fleisch','Meat')));var sw=el('div','z-chips');
        sw.appendChild(knopf(L('extra Fleisch (Super)','extra meat (Super)')+(va.sup?'':preisDiff(x,su)),{'class':'chip','aria-pressed':String(!!va.sup),'data-super':x.u}));
        sg.appendChild(sw);box.appendChild(sg);}
    }
    var kp=x.t==='D'&&kaesePartner(x.k);
    if(kp){
      var mit=VAR[x.k]?!!VAR[x.k].kae:!!MIT_K[x.k];
      var kg=el('div','z-gruppe');kg.appendChild(el('span','z-gruppe-titel',L('Käse','Cheese')));var kw=el('div','z-chips');
      kw.appendChild(knopf(L('mit Käse','with cheese')+(mit?'':preisDiff(x,kp)),{'class':'chip','aria-pressed':String(mit),'data-kaese':x.u}));
      kg.appendChild(kw);box.appendChild(kg);
    }
    if(x.t==='D'){
      /* Gemüse: alles drin, Abgewähltes geht als „ohne …“ an den Laden */
      var gg=chips(L('Gemüse – abwählen, was nicht rein soll','Vegetables – tap to leave out'),OHNE,[],'ohne',x.u);
      gg.querySelectorAll('.chip').forEach(function(c){c.setAttribute('aria-pressed',String(o.ohne.indexOf(c.dataset.w)<0));});
      box.appendChild(gg);
    }
    if(x.t==='S')box.appendChild(chips(L('3 Zutaten Ihrer Wahl (','3 toppings of your choice (')+o.wahl.length+L(' von 3)',' of 3)'),GEMUESE.concat(FLEISCH,KAESE),o.wahl,'wahl',x.u));
    if(x.t==='R')box.appendChild(chips(L('Variante','Option'),(x.v||'').split('|').filter(Boolean),[o.va],'va',x.u));
    if(x.t==='P'||x.t==='S'||x.t==='R'){
      box.appendChild(chips(L('Extra je Zutat +1,50 €','Extra per topping +1,50 €'),GEMUESE,o.ex,'ex',x.u));
      box.appendChild(chips(L('Extra je Zutat +2,00 €','Extra per topping +2,00 €'),FLEISCH.concat(KAESE),o.ex,'ex',x.u));
    }
    return box;
  }
  function zeichnen(){
    var n=anzahl();
    zl.hidden=n===0;document.body.classList.toggle('mit-zettel',n>0);
    zl.querySelector('.zl-anzahl').textContent=n;zl.querySelector('.zl-summe').textContent=euro(summe());
    zl.setAttribute('aria-label',L('Meine Bestellung ansehen: ','View my order: ')+n+(n===1?L(' Gericht, ',' dish, '):L(' Gerichte, ',' dishes, '))+euro(summe()));
    zliste.textContent='';
    zettel.forEach(function(x){
      var li=el('li','z-eintrag'),kopf=el('div');
      var na=nameA(x);
      kopf.appendChild(el('span','z-name',na+(x.g?' ('+x.g+')':'')));
      var wt=x.t?wuensche(x,SP==='en'):beschrA(x);if(wt&&SP==='en')wt=wt.charAt(0).toUpperCase()+wt.slice(1);if(wt){var wi=el('span','z-info',wt);if(/wählen|choose/.test(wt))wi.classList.add('z-fehlt');kopf.appendChild(wi);}
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
    zsumme.textContent=euro(summe());
    huelle.querySelector('.zettel-leer').hidden=n>0;huelle.querySelector('.zettel-voll').hidden=n===0;
    abgleichen();letzteZeigen();
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
        var nm=(SP==='en'&&li.dataset.ne||li.dataset.n)+(g?' '+g:'');
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
    var hinweis=neu.t==='S'?L(' Zutaten in der Bestellung wählen.',' Choose the toppings in your order.'):neu.t==='R'?L(' Variante in der Bestellung wählen.',' Choose the option in your order.'):'';
    melden(nameA(neu)+(g?' ('+g+')':'')+L(' ist in Ihrer Bestellung.',' added to your order.')+hinweis);
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
      else{var arr=o[art],i2=arr.indexOf(wert);if(i2>-1)arr.splice(i2,1);else if(!(art==='wahl'&&arr.length>=3))arr.push(wert);}
      speichern();zeichnen();var wieder=zliste.querySelector('[data-o="'+art+'"][data-w="'+wert+'"]');if(wieder)wieder.focus();return;}
    var fu=ev.target.closest('[data-fuell]');
    if(fu){var zf=finde(fu.dataset.u);if(!zf)return;var zielF=variante(zf.k,{f:fu.dataset.fuell});if(!zielF)return;
      wechseln(zf,zielF);speichern();zeichnen();var fw2=zliste.querySelector('[data-fuell="'+fu.dataset.fuell+'"]');if(fw2)fw2.focus();return;}
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
  function tagKurz(off,en){return tagDatum(off,{weekday:'short',day:'numeric',month:en?'short':'2-digit'},en?'en-GB':'de-DE');}
  function tagLang(off){var t=tagDatum(off,{weekday:'long',day:'2-digit',month:'2-digit'});return /\.$/.test(t)?t:t+'.';}   /* „Freitag, 24.10.“ */
  /* mögliche Abholzeiten eines Tages (Minuten), 15-Minuten-Raster, heute frühestens in 20 Minuten */
  function slots(off){
    var n=jetzt(),z=ZEITEN[abh.laden],tag=(n.tag+off)%7,h=z[tag],res=[];if(!h)return res;
    var start=h[0]+15;if(off===0)start=Math.max(start,Math.ceil((n.min+20)/15)*15);
    for(var m=start;m<=h[1]-15;m+=15)res.push(m);
    return res;
  }
  function zeitenFuellen(){
    selZeit.textContent='';selTag.textContent='';hinweisZ.hidden=true;ZINFO={};
    if(!abh.laden){[selTag,selZeit].forEach(function(s){var o=el('option',null,L('Bitte zuerst den Laden wählen','Please choose the shop first'));o.value='';s.appendChild(o);s.disabled=true;});return;}
    selTag.disabled=selZeit.disabled=false;
    var n=jetzt(),en=SP==='en',tage=[];
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
    if(off===0&&n.min>=ZEITEN[abh.laden][n.tag][0]){
      optionen.push({v:'heute, so schnell wie möglich',t:L('So schnell wie möglich','As soon as possible')});ZINFO['heute, so schnell wie möglich']={off:0,min:n.min+20};}
    slots(off).forEach(function(m){var v=vor+', '+zeitText(m);optionen.push({v:v,t:zeitText(m,en)});ZINFO[v]={off:off,min:m};});
    optionen.forEach(function(x){var o=el('option',null,x.t);o.value=x.v;selZeit.appendChild(o);});
    if(optionen.some(function(x){return x.v===abh.zeit;}))selZeit.value=abh.zeit;else abh.zeit=selZeit.value;
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
    if(kf)nr=null;
    waKnopf.hidden=!nr;waHinweis.hidden=!!nr||!!kf||!Object.keys(WA).length;
    if(nr)waKnopf.href='https://wa.me/'+nr+'?text='+encodeURIComponent(zettelText());
  }
  function ladenZeigen(){
    document.querySelectorAll('[data-laden]').forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.laden===abh.laden));});
    document.querySelectorAll('[data-anruf]').forEach(function(a){a.hidden=!!abh.laden&&a.dataset.anruf!==abh.laden;});
    zeitenFuellen();waAktualisieren();
  }
  document.querySelectorAll('[data-laden]').forEach(function(b){b.addEventListener('click',function(){abh.laden=b.dataset.laden;abhSpeichern();ladenZeigen();verfZeigen();});});
  selZeit.addEventListener('change',function(){abh.zeit=selZeit.value;abhSpeichern();zeichnen();waAktualisieren();});
  selTag.addEventListener('change',function(){abh.tag=selTag.value;abh.zeit='';abhSpeichern();zeitenFuellen();waAktualisieren();});
  eName.value=abh.name||'';eName.addEventListener('input',function(){abh.name=eName.value;abhSpeichern();waAktualisieren();});
  ladenZeigen();
  zl.addEventListener('click',function(){zeitenFuellen();waAktualisieren();});
  waKnopf.addEventListener('click',function(){waAktualisieren();letzteMerken();});
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
    var zus={};g.forEach(function(p){var li=gerichtLi(p.k),nm=(SP==='en'&&li.dataset.ne||li.dataset.n)+(p.g?' ('+p.g+')':'');zus[nm]=(zus[nm]||0)+p.q;});
    document.getElementById('letzte-liste').textContent=Object.keys(zus).map(function(k){return zus[k]+'× '+k;}).join(' · ');
  }
  document.getElementById('letzte-knopf').addEventListener('click',function(){
    letzteGueltig().forEach(function(p){
      var li=gerichtLi(p.k),gs=li.dataset.g?li.dataset.g.split('|'):[''],pr=li.dataset.p.split('|').map(Number);
      var o=Object.assign(grund(li.dataset.t),JSON.parse(JSON.stringify(p.o||{})));
      ['s','ohne','ex','wahl'].forEach(function(a){if(!Array.isArray(o[a]))o[a]=[];});
      zettel.push({k:p.k,n:li.dataset.n,d:li.dataset.d,g:p.g||'',c:pr[Math.max(0,gs.indexOf(p.g||''))],q:Math.max(1,+p.q||1),
        t:li.dataset.t||'',v:li.dataset.v||'',o:o,notiz:p.notiz||'',u:uidZ++});
    });
    zusammenfassen();speichern();zeichnen();zeitenFuellen();waAktualisieren();oeffnen();
  });
  document.querySelectorAll('[data-anruf]').forEach(function(a){a.addEventListener('click',letzteMerken);});
  function zettelText(){
    var test=document.body.classList.contains('vorschau')?['*TEST – Seite nicht freigeschaltet, keine echte Bestellung*','']:[];
    var vb=ZINFO[abh.zeit]&&ZINFO[abh.zeit].off>0;
    var z=[(vb?'Vorbestellung':'Bestellung')+' Saray Döner'+(abh.laden?' '+(abh.laden==='freital'?'Freital':'Altenberg'):'')];
    if(abh.zeit)z.push('Abholung: '+abh.zeit);
    if(abh.name)z.push('Name: '+abh.name);
    z.push('');
    zettel.forEach(function(x){var w=x.t?wuensche(x):'';
      z.push(x.q+'× '+x.n+(x.g?' ('+x.g+')':'')+(w?', '+w:'')+': '+euro(stueck(x)*x.q)+(x.notiz?'\n   Wunsch: '+x.notiz:''));});
    z.push('Summe: '+euro(summe()));return test.concat(z).join('\n');
  }
  /* Teilen: Teilen-Menü des Handys (WhatsApp, SMS, Mail, Teams …); sonst in die Zwischenablage kopieren */
  document.getElementById('zettel-kopieren').addEventListener('click',function(){
    var t=zettelText();
    letzteMerken();
    var kopiert=L('Bestellung kopiert – jetzt in WhatsApp, SMS, E-Mail oder Teams einfügen.','Order copied – now paste it into WhatsApp, a text message, e-mail or Teams.');
    function notfall(){var ta=document.createElement('textarea');ta.value=t;ta.setAttribute('readonly','');ta.style.position='fixed';ta.style.opacity='0';
      document.body.appendChild(ta);ta.select();var ok=false;try{ok=document.execCommand('copy');}catch(e){}ta.remove();
      melden(ok?kopiert:L('Kopieren hat nicht geklappt. Bitte die Bestellung abschreiben.','Copying did not work. Please write the order down.'));}
    function kopieren(){if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(t).then(function(){melden(kopiert);},notfall);else notfall();}
    if(navigator.share&&(window.matchMedia&&matchMedia('(pointer:coarse)').matches)){
      navigator.share({title:'Bestellung Saray Döner',text:t}).catch(function(e){if(!e||e.name!=='AbortError')kopieren();});
    }else kopieren();
  });
  var leeren=document.getElementById('zettel-leeren'),leerenTimer=null;
  leeren.addEventListener('click',function(){
    if(leeren.dataset.sicher){zettel=[];offen=null;speichern();zeichnen();schliessen();melden(L('Bestellung geleert.','Order cleared.'));delete leeren.dataset.sicher;leeren.textContent=L('Bestellung leeren','Clear order');return;}
    leeren.dataset.sicher='1';leeren.textContent=L('Wirklich alles löschen? Nochmal tippen.','Really delete everything? Tap again.');
    clearTimeout(leerenTimer);leerenTimer=setTimeout(function(){delete leeren.dataset.sicher;leeren.textContent=L('Bestellung leeren','Clear order');},4000);
  });
  zeichnen();verfZeigen();regelnLaden();
  setInterval(function(){try{verfZeigen();zeitenFuellen();}catch(e){}},60000);
'''

JS = r"""
(function(){
  var ZEITEN=%%ZEITEN%%;
  var TAGE=['Sonntag','Montag','Dienstag','Mittwoch','Donnerstag','Freitag','Samstag'];
  var TAGE_E=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  /* Sprache: gespeicherte Wahl, sonst Browsersprache (Suchmaschinen bekommen immer Deutsch) */
  var SPK='saray-sprache',SP='de';
  try{SP=localStorage.getItem(SPK)||'';}catch(e){SP='';}
  if(SP!=='de'&&SP!=='en'){
    var langs=(navigator.languages&&navigator.languages.length?navigator.languages:[navigator.language||'de']);
    SP=(/bot|crawl|spider|lighthouse/i.test(navigator.userAgent)||langs.some(function(l){return /^de/i.test(l);}))?'de':'en';
  }
  function L(de,en){return SP==='en'?en:de;}
  /* Linkshänder-Modus: auf diesem Gerät gemerkt */
  var HK='saray-hand',linkshand=false;
  try{linkshand=localStorage.getItem(HK)==='links';}catch(e){}
  function handZeigen(){document.documentElement.classList.toggle('links',linkshand);
    document.querySelectorAll('[data-hand]').forEach(function(b){b.textContent=linkshand?L('✋ Rechtshänder? Knöpfe nach rechts','✋ Right-handed? Buttons to the right'):L('✋ Linkshänder? Knöpfe nach links','✋ Left-handed? Buttons to the left');
      b.setAttribute('aria-pressed',String(linkshand));});}
  document.addEventListener('click',function(ev){if(!ev.target.closest('[data-hand]'))return;linkshand=!linkshand;
    try{localStorage.setItem(HK,linkshand?'links':'rechts');}catch(e){}handZeigen();});
  handZeigen();
  var KURZ={Sun:0,Mon:1,Tue:2,Wed:3,Thu:4,Fri:5,Sat:6};
  var weniger=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;

  function jetzt(){
    var o={};
    new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Berlin',weekday:'short',hour:'2-digit',minute:'2-digit',hourCycle:'h23'})
      .formatToParts(new Date()).forEach(function(p){o[p.type]=p.value;});
    return {tag:KURZ[o.weekday],min:(+o.hour)*60+(+o.minute)};
  }
  function uhr(m){var h=Math.floor(m/60),r=m%60;if(SP==='en')return h+':'+(r<10?'0':'')+r;return r?h+':'+(r<10?'0':'')+r+' Uhr':h+' Uhr';}
  function lage(ort){
    var z=ZEITEN[ort],n=jetzt(),h=z[n.tag];
    if(h&&n.min>=h[0]&&n.min<h[1])return{offen:true,text:L('Jetzt geöffnet, bis ','Open now, until ')+uhr(h[1])};
    if(h&&n.min<h[0])return{offen:false,text:L('Geschlossen, öffnet heute um ','Closed, opens today at ')+uhr(h[0])};
    for(var i=1;i<=7;i++){var t=(n.tag+i)%7;if(z[t])return{offen:false,text:SP==='en'?'Closed, opens '+(i===1?'tomorrow':'on '+TAGE_E[t])+' at '+uhr(z[t][0]):'Geschlossen, öffnet '+(i===1?'morgen':'am '+TAGE[t])+' um '+uhr(z[t][0])};}
    return{offen:false,text:''};
  }
  function aktualisieren(){
    document.querySelectorAll('[data-status]').forEach(function(el){
      var s=lage(el.getAttribute('data-status'));el.setAttribute('data-offen',s.offen?'ja':'nein');
      el.querySelector('.status-text').textContent=s.text;
    });
    var tag=jetzt().tag;
    document.querySelectorAll('tr[data-tage]').forEach(function(tr){
      tr.classList.toggle('heute',tr.getAttribute('data-tage').split(',').indexOf(String(tag))>-1);
    });
  }
  try{aktualisieren();setInterval(aktualisieren,60000);}catch(e){}

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
    var k=getComputedStyle(nav).position==='sticky'&&nav.getBoundingClientRect().top-marke.getBoundingClientRect().bottom>1;
    if(k!==nav.classList.contains('klebt'))nav.classList.toggle('klebt',k);
    if(k&&glas){glas.remove();glas=null;}
    if(!k&&!glas){glas=document.createElement('div');glas.className='glas-oben';glas.setAttribute('aria-hidden','true');document.body.appendChild(glas);}
    if(k&&!deckel){deckel=document.createElement('div');deckel.className='deckel-oben';deckel.setAttribute('aria-hidden','true');document.body.appendChild(deckel);}
    if(deckel)deckel.style.height=nav.offsetHeight+'px';
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
  var feld=document.getElementById('suche-feld'),gerichte=[].slice.call(document.querySelectorAll('.gericht'));
  var treffer=document.querySelector('.treffer'),nichts=document.querySelector('.nichts'),wort=nichts&&nichts.querySelector('q');
  gerichte.forEach(function(g){g._s=norm(g.getAttribute('data-s'));});
  function suchen(){
    var roh=feld.value.trim(),q=norm(roh),teile=q.split(/\s+/).filter(Boolean),n=0;
    gerichte.forEach(function(g){var ok=teile.every(function(w){return g._s.indexOf(w)>-1;});g.hidden=!ok;if(ok)n++;});
    document.querySelectorAll('.liste').forEach(function(l){
      var v=l.querySelectorAll('.gericht:not([hidden])').length;l.style.setProperty('--zeilen',Math.max(1,Math.ceil(v/2)));
      l.closest('.abschnitt').hidden=v===0;
    });
    document.querySelectorAll('.gruppe').forEach(function(g){
      var leer=!g.querySelector('.gericht:not([hidden])');g.hidden=leer;if(links[g.id])links[g.id].classList.toggle('leer',leer);
    });
    treffer.hidden=!teile.length||n===0;
    treffer.textContent=n===1?L('1 Gericht gefunden','1 dish found'):n+L(' Gerichte gefunden',' dishes found');
    nichts.hidden=!(teile.length&&n===0);if(wort)wort.textContent=roh;
    var bl=document.querySelector('.beliebt');if(bl)bl.hidden=teile.length>0;
    document.querySelectorAll('.hand-zeile').forEach(function(h){h.hidden=teile.length>0;});
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
  var spKnopf=document.getElementById('sprache');
  function sprache(l,merken){
    SP=l;document.documentElement.lang=l;
    document.querySelectorAll('[data-en]').forEach(function(x){if(x._de==null)x._de=x.textContent;x.textContent=l==='en'?x.dataset.en:x._de;});
    document.querySelectorAll('[data-en-html]').forEach(function(x){if(x._de==null)x._de=x.innerHTML;x.innerHTML=l==='en'?x.dataset.enHtml:x._de;});
    document.querySelectorAll('[data-en-ph]').forEach(function(x){if(x._de==null)x._de=x.placeholder;x.placeholder=l==='en'?x.dataset.enPh:x._de;});
    document.querySelectorAll('[data-en-aria]').forEach(function(x){if(x._dea==null)x._dea=x.getAttribute('aria-label');x.setAttribute('aria-label',l==='en'?x.dataset.enAria:x._dea);});
    spKnopf.textContent=l==='en'?'DE':'EN';spKnopf.lang=l==='en'?'de':'en';
    spKnopf.setAttribute('aria-label',l==='en'?'Auf Deutsch umschalten':'Switch to English');
    if(merken){try{localStorage.setItem(SPK,l);}catch(e){}}
    try{aktualisieren();}catch(e){}
    if(feld&&feld.value.trim())suchen();
    zeichnen();zeitenFuellen();waAktualisieren();handZeigen();
  }
  spKnopf.addEventListener('click',function(){sprache(SP==='en'?'de':'en',true);});
  if(SP==='en')sprache('en',false);

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
      <button type="button" class="sprache" id="sprache" aria-label="Switch to English" lang="en">EN</button>
    </nav>
  </div>
</header>

%%HINWEISE%%
<main id="inhalt">
<div class="buehne-band">
  <section class="buehne wrap" aria-labelledby="titel">
    <div class="buehne-text">
      <img class="koch-klein" src="%%IMG_KOCH%%" width="430" height="470" alt="">
      <h1 id="titel" data-en-html="Fresh off the spit.&lt;br&gt; Since 1997.">Frisch vom Spieß.<br> Seit 1997.</h1>
      <p class="lead" data-en="Döner, dürüm, pizza and salads – in Freital on Dresdner Straße and in Altenberg right by the station.">Döner, Dürüm, Pizza und Salate – in Freital an der Dresdner Straße und in Altenberg direkt am Bahnhof.</p>
      <ul class="schilder" aria-label="Unsere Läden">
%%SCHILDER%%
      </ul>
    </div>
    <div class="bilder">
      <figure class="foto"><img src="%%IMG_LADEN%%" width="894" height="700"
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
      <p data-en="All prices in euros. Every dish comes with your choice of sauce: garlic, herb or chili.">Alle Preise in Euro. Zu jedem Gericht gibt es Soße nach Wahl: Knoblauch, Kräuter oder Chili.</p>
      <p data-en="The menu applies in Freital and Altenberg.">Die Karte gilt in Freital und Altenberg.</p>
    </header>
    <div class="karte-layout">
      <div class="karte-seite">
        <div class="suche" role="search">
          <label for="suche-feld" data-en="Search dishes">Gericht suchen</label>
          <div class="suche-feld">%%SUCH_ICON%%<input id="suche-feld" type="search" placeholder="Name oder Nummer" data-en-ph="Name or number" autocomplete="off" enterkeyhint="search"></div>
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
        <p class="allergene" data-en="Ask at the counter about ingredients, allergens and additives – you can see our allergen menu at any time.">Fragen Sie an der Theke nach Zutaten, Allergenen und Zusatzstoffen – unsere Allergiker-Speisekarte können Sie jederzeit einsehen.</p>
      </div>
    </div>
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
        <p class="klein app-tipp" data-en="Tip: Put Saray on your home screen – in Safari via “Share” → “Add to Home Screen”, in Chrome via the menu → “Add to home screen”.">Tipp: Saray auf den Home-Bildschirm legen – in Safari über „Teilen“ → „Zum Home-Bildschirm“, in Chrome über das Menü → „Zum Startbildschirm hinzufügen“.</p>
      </div>
%%FUSS_ORTE%%
    </div>
    <div class="recht">
      <details id="impressum"><summary data-en="Impressum (legal notice)">Impressum</summary>
        <p>Angaben gemäß § 5 DDG</p>
        <p>Ahmet Saglam<br>Saray Döner<br>Bahnhof 3<br>01773 Altenberg</p>
        <p>Telefon: <a href="tel:+493505623674">035056 23674</a><br>
        Telefax: 035056 23676<br>
        E-Mail: <a href="mailto:solino1@hotmail.de">solino1@hotmail.de</a></p>
      </details>
      <details id="datenschutz"><summary data-en="Datenschutz (privacy policy)">Datenschutz</summary>
        <p><span class="platzhalter">[Datenschutzerklärung hier einfügen]</span></p>
        <p>Hinweis für die Erstellung: Diese Website setzt keine Cookies, nutzt kein Tracking und lädt nichts von fremden Servern.
        Schriften und Bilder sind in die Seite eingebettet. Zu beschreiben sind vor allem der Webhoster und dessen Server-Logfiles.</p>
      </details>
    </div>
  </div>
</footer>

<button type="button" class="nach-oben" id="nach-oben" hidden aria-label="Nach oben" data-en-aria="Back to top" title="Nach oben"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 19V5M5.5 11.5 12 5l6.5 6.5"/></svg></button>
<button type="button" class="zettel-leiste" id="zettel-leiste" hidden><span class="zl-anzahl">0</span><svg class="ico tuete" viewBox="0 0 24 24" aria-hidden="true"><path d="M5.5 8h13l-1.2 12.5H6.7z"/><path d="M9 10.5V7a3 3 0 0 1 6 0v3.5"/></svg><span data-en="My order">Meine Bestellung</span><span class="zl-summe"></span></button>
<p class="zettel-meldung" id="zettel-meldung" role="status" hidden></p>
<div class="zettel-huelle" id="zettel" hidden>
  <div class="zettel-hinter" data-zu></div>
  <section class="zettel" role="dialog" aria-modal="true" aria-labelledby="zettel-titel">
    <header class="zettel-kopf"><h2 id="zettel-titel" tabindex="-1"><svg class="ico tuete" viewBox="0 0 24 24" aria-hidden="true"><path d="M5.5 8h13l-1.2 12.5H6.7z"/><path d="M9 10.5V7a3 3 0 0 1 6 0v3.5"/></svg><span data-en="My order">Meine Bestellung</span></h2>
      <button type="button" class="zettel-zu" data-zu aria-label="Bestellung schließen" data-en-aria="Close my order">×</button></header>
    <p class="zettel-leer" data-en="Nothing selected yet. Tap “+” in the menu.">Noch nichts ausgewählt. Tippen Sie in der Speisekarte auf „+“.</p>
    <div class="zettel-voll">
      <ul class="zettel-liste" id="zettel-liste"></ul>
      <p class="zettel-summe-zeile"><span data-en="Total">Summe</span><b id="zettel-summe"></b></p>
      <fieldset class="abholung">
        <legend data-en="Pickup">Abholung</legend>
        <div class="z-chips" role="group" aria-label="Laden" data-en-aria="Shop">%%LADEN_CHIPS%%</div>
        <label for="abhol-tag" data-en="Day">Tag</label>
        <select id="abhol-tag"></select>
        <label for="abhol-zeit" data-en="Time">Uhrzeit</label>
        <select id="abhol-zeit"></select>
        <p class="abhol-hinweis" id="abhol-hinweis" hidden></p>
        <label for="abhol-name" data-en="Name for the order">Name für die Bestellung</label>
        <input id="abhol-name" type="text" autocomplete="given-name" placeholder="z. B. Michael" data-en-ph="e.g. Michael">
      </fieldset>
      <p class="zettel-hinweis" data-en="Order via WhatsApp or call and read it out. Your order is saved on this device.">Bestellen Sie per WhatsApp oder rufen Sie an und lesen Sie die Bestellung vor. Sie bleibt auf diesem Gerät gespeichert.</p>
      <div class="zettel-knoepfe">
        <a class="knopf knopf-whatsapp" id="zettel-whatsapp" href="#" target="_blank" rel="noopener">%%WA_ICON%%<span data-en="Order via WhatsApp">Per WhatsApp bestellen</span></a>
        <p class="abhol-hinweis verf-hinweis" id="verf-hinweis" hidden></p>
        <p class="abhol-hinweis" id="wa-hinweis" hidden data-en="Choose the shop above to order via WhatsApp.">Bitte oben den Laden wählen, dann können Sie per WhatsApp bestellen.</p>
        %%ZETTEL_ANRUF%%
        <button type="button" class="knopf knopf-linie" id="zettel-kopieren"><svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 15V3"/><path d="M7.5 7.5 12 3l4.5 4.5"/><path d="M5 12v7.5h14V12"/></svg><span data-en="Share order">Bestellung teilen</span></button>
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
    return gruppen


SPERRGRUPPEN = sperrgruppen()


def hinweise_html(liste):
    return "".join(
        f'<div class="hinweis-band" data-von="{h["von"]}" data-bis="{h["bis"]}" hidden><p class="wrap">'
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


def bauen(hinweise=None, ziel=None, einzeln=False):
    """einzeln=True: eine Datei (ziel, Standard index.html). Sonst: Ordner (ziel, Standard docs/)."""
    css = (CSS.replace("%%SLAB_B%%", b64("Roboto-Slab-Bold.sub.woff", "font/woff"))
              .replace("%%SLAB_R%%", b64("Roboto-Slab-Regular.sub.woff", "font/woff"))
              .replace("%%LATO_R%%", b64("lato-normal.sub.woff", "font/woff"))
              .replace("%%LATO_B%%", b64("lato-bold.sub.woff", "font/woff")))
    js = (JS.replace("%%ZEITEN%%", JS_ZEITEN).replace("%%ZETTEL_JS%%", ZETTEL_JS)
            .replace("%%WA%%", json.dumps(whatsapp_nummern(einzeln)))
            .replace("%%SPERR%%", json.dumps(SPERRGRUPPEN, ensure_ascii=False))
            .replace("%%REGELN%%", json.dumps(VERFUEGBARKEIT, ensure_ascii=False))
            .replace("%%VORBESTELL_TAGE%%", str(VORBESTELL_TAGE)))
    ersetzen = {
        "%%LD%%": json.dumps(LD, ensure_ascii=False),
        "%%DOMAIN%%": DOMAIN,
        "%%FAVICON_PNG%%": maskottchen("favicon-96.png", "image/png"),
        "%%IMG_KOPF%%": maskottchen("saray-koch-kopf.svg", "image/svg+xml"),
        "%%SCHILDER%%": STATUS_KARTEN,
        "%%IMG_KOCH%%": maskottchen("saray-koch.svg", "image/svg+xml"),
        "%%IMG_LADEN%%": b64("laden_web.jpg", "image/jpeg"),
        "%%STICKER%%": preis(DOENER_PREIS, "sticker-preis") if DOENER_PREIS else "",
        "%%SUCH_ICON%%": SUCH_ICON,
        "%%NAV%%": NAV,
        "%%KARTE%%": KARTE,
        "%%BELIEBT%%": BELIEBT_HTML,
        "%%ORTE%%": ORTE,
        "%%FUSS_ORTE%%": FUSS_ORTE,
        "%%HINWEISE%%": hinweise_html(HINWEISE if hinweise is None else hinweise),
        "%%WA_ICON%%": '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 20.5l1.3-4.2A8.5 8.5 0 1 1 8 19.4z"/><path d="M9 8.5c0 3 2.5 6 6 6.5l1.2-1.4-2-1-.9.8c-1-.4-1.9-1.3-2.3-2.3l.8-.9-1-2L9.4 8.4"/></svg>',
        "%%LADEN_CHIPS%%": "".join(f'<button type="button" class="chip" data-laden="{st["id"]}" aria-pressed="false">{e(st["name"])}</button>' for st in STANDORTE),
        "%%ZETTEL_ANRUF%%": "".join(f'<a class="knopf knopf-dunkel" data-anruf="{st["id"]}" href="tel:{st["tel_href"]}">{TEL_ICON}{t(st["name"] + " anrufen: " + st["tel"], "Call " + st["name"] + ": " + st["tel"])}</a>' for st in STANDORTE),

        "%%TITEL_PRAEFIX%%": "[Nicht freigeschaltet] " if VORSCHAU else "",
        "%%BODY_KLASSE%%": ' class="vorschau"' if VORSCHAU else "",
        "%%VORSCHAU_BAND%%": ('<div class="vorschau-band" role="note"><strong data-en="NOT RELEASED">NICHT FREIGESCHALTET</strong> '
                              '<span data-en="Draft – not yet the official website of Saray Döner. Orders go to a test number.">'
                              'Entwurf – noch nicht die offizielle Seite von Saray Döner. Bestellungen gehen an eine Testnummer.</span>'
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
    (aus / "robots.txt").write_text("User-agent: *\n" + ("Disallow: /\n" if VORSCHAU else "Disallow: /chef/\n"))
    import chef_app
    chef_app.schreiben(aus, STANDARD_GRUPPEN, STANDORTE, SPERRGRUPPEN, REPO)
    gesamt = sum(f.stat().st_size for f in aus.rglob("*") if f.is_file())
    for w in WARNUNGEN:
        print("WARNUNG:", w)
    print(f"{aus}/  {gesamt // 1024} KB in {sum(1 for f in aus.rglob('*') if f.is_file())} Dateien  ·  {ANZAHL} Positionen")


if __name__ == "__main__":
    bauen(einzeln="--einzeln" in sys.argv)
