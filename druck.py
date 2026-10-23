#!/usr/bin/env python3
"""Druckvorlagen mit den aktuellen Preisen (inkl. Änderungen aus der Chef-App):

    python3 druck.py [ziel]   ->  <ziel>/flyer.pdf, <ziel>/aufsteller-<laden>.pdf   (Standard: docs/druck)

Aktions-Plakate: je laufender/kommender Sonderaktion ein A4-Plakat (aktion-<von>-<name>.pdf) und ein Bild 1080 × 1080 (….png).
Allergenmappe (allergenmappe.pdf) für die Theke, Aufkleber-Bogen (aufkleber.pdf, 24 × 70 × 37 mm) für Tüten,
Preisschilder (preisschilder.pdf, 8 × 105 × 74 mm je A4) für alle Getränke.
Flyer: A4 quer, beidseitig, Wickelfalz (3 Spalten je Seite). Außen: Innenklappe | Rückseite | Titel.
Der GitHub-Workflow erzeugt die PDFs nach jedem Bauen; die Chef-App verlinkt sie unter „Mehr → Drucken“.
Braucht Playwright mit Chromium.
"""
import asyncio
import datetime
import html
import pathlib
import sys
import zoneinfo

from playwright.async_api import async_playwright

import build
import aufsteller
from menu import ALLERGENE, ZUTATEN, KENNZEICHNUNG, SOSSEN, GERICHT_ALLERGENE
from qr import qr_svg

HIER = pathlib.Path(__file__).parent
e = html.escape
INNEN = [["doener", "duerum"], ["teller", "schnitzel", "kinder"], ["pizza", "lahmacun"]]
KLAPPE = ["salate", "baguette"]
RUECKSEITE = ["getraenke"]


def uri(*teile):
    return (HIER.joinpath(*teile)).resolve().as_uri()


def gruppe_html(gid):
    gr = next((g for g in build.GRUPPEN if g["id"] == gid), None)
    if not gr:
        return ""
    out = [f'<section><h2>{e(gr["titel"])}</h2>']
    for ab in gr["abschnitte"]:
        if not ab["gerichte"]:
            continue
        gross = ab.get("groessen") or []
        kopf = e(ab["titel"]) if ab["titel"] != gr["titel"] else ""
        info = e(ab.get("info", ""))
        kz = KENNZEICHNUNG.get(ab["titel"])
        kz = f'<span class="kz">{kz[0].replace(",", ", ")} · {kz[1].replace(",", ", ")}</span>' if kz else ""
        if kopf or info or gross or kz:
            out.append(f'<h3>{kopf}{" " if kopf and info else ""}{"<small>" + info + "</small>" if info else ""}{kz}'
                       + (f'<span class="gr">{"".join(f"<b>{e(g)}</b>" for g in gross)}</span>' if gross else "") + '</h3>')
        out.append('<ul>')
        for g in ab["gerichte"]:
            nr, name, desc, preise = g[:4]
            var = " · ".join(f"{k}: {v}" for k, v in (g[4] if len(g) > 4 else []))
            fisch = ", ".join(f"enthält {ALLERGENE[x]} ({x})" for x in GERICHT_ALLERGENE.get(nr, "").split(",") if x)
            klein = " – ".join(x for x in (desc, var, fisch) if x)
            out.append(f'<li><span class="nr">{e(build.anz(nr) if nr else "")}</span><span class="nm"><b>{e(name)}</b>'
                       f'{"<small> " + e(klein) + "</small>" if klein else ""}</span>'
                       f'<span class="pr">{"".join(f"<b>{p}</b>" for p in preise)}</span></li>')
        out.append('</ul>')
        if ab.get("notiz"):
            out.append(f'<p class="notiz">{e(ab["notiz"])}</p>')
    out.append('</section>')
    return "".join(out)


def flyer_html():
    heute = datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Berlin")).strftime("%d.%m.%Y")
    qr = qr_svg(f"https://{build.CNAME}/#speisekarte", "M", "#3A1531")
    muster = '<div class="muster">ENTWURF</div>' if build.VORSCHAU else ""
    laeden = "".join(
        f'<div class="laden"><h3>{e(s["name"])}</h3><p>{e(s["strasse"])}, {e(s["plz"])} {e(s["ort"])}<br>'
        f'Telefon <b>{e(s["tel"])}</b></p><table>'
        + "".join(f'<tr><td>{e(z["de"])}</td><td>{e(z["zeit"])}</td></tr>' for z in s["zeilen_neu"])
        + '</table></div>' for s in build.STANDORTE)
    bar = '<p class="bar">Bei uns zahlen Sie bar.</p>' if all(s.get("bar") for s in build.STANDORTE) else ""
    leg = " · ".join(f"<b>{k}</b> {e(v)}" for k, v in ALLERGENE.items())
    zut = " · ".join(f"<b>{k}</b> {e(v[0])}" for k, v in ZUTATEN.items())
    spalte = lambda ids, cls="": f'<div class="panel karte {cls}"><div class="fit">{"".join(gruppe_html(i) for i in ids)}</div></div>'
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><style>
@font-face{{font-family:Slab;src:url({uri("assets", "Roboto-Slab-Bold.sub.woff")});font-weight:700}}
@font-face{{font-family:Text;src:url({uri("assets", "lato-normal.sub.woff")});font-weight:400}}
@font-face{{font-family:Text;src:url({uri("assets", "lato-bold.sub.woff")});font-weight:700}}
@page{{size:297mm 210mm;margin:0}}
*{{box-sizing:border-box}}
html,body{{margin:0}}
body{{font-family:Text;color:#3A1531;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.seite{{width:297mm;height:210mm;display:flex;page-break-after:always;position:relative;overflow:hidden}}
.panel{{width:100mm;height:210mm;padding:7mm 6.5mm;overflow:hidden;position:relative}}
.panel.schmal{{width:97mm}}
.panel + .panel{{border-left:.2mm dashed #e3d6de}}
.fit{{font-size:8.6pt;line-height:1.22;height:100%;overflow:hidden}}
h2{{font:700 1.55em/1.1 Slab;margin:0 0 1.2mm;padding:1.2mm 2.5mm;background:#FFD21F;border-radius:1.5mm}}
section{{margin-bottom:2.4mm}}
h3{{font:700 1.05em/1.2 Slab;margin:1.6mm 0 .6mm;display:flex;align-items:baseline;gap:1.5mm;flex-wrap:wrap}}
h3 small{{font:400 .82em Text;opacity:.8}}
.kz{{font:400 .72em Text;opacity:.7;margin-left:auto}}
.gr{{display:flex;gap:0;margin-left:auto}}.gr b{{width:11mm;text-align:right;font:700 .78em Text}}
ul{{list-style:none;margin:0;padding:0}}
li{{display:flex;gap:1.5mm;padding:.45mm 0;border-bottom:.15mm dotted #d9cbd4;break-inside:avoid}}
.nr{{width:6mm;flex:none;font-weight:700;opacity:.65;font-size:.9em}}
.nm{{flex:1}}.nm small{{font-size:.84em;opacity:.8}}
.pr{{display:flex;flex:none}}.pr b{{width:11mm;text-align:right}}
.notiz{{margin:.8mm 0 0;font-size:.85em;font-style:italic}}
.titel{{background:#FFD21F;display:flex;flex-direction:column;align-items:center;text-align:center;justify-content:space-between;padding:10mm 8mm}}
.titel img{{width:46mm}}
.titel .seit{{font:700 11pt Slab;letter-spacing:.3mm}}
.titel h1{{font:700 30pt/1 Slab;margin:2mm 0 0;color:#C8371A}}
.titel .unter{{font:700 13pt Slab;margin:1mm 0 0}}
.titel .orte{{font:700 12pt Text;margin:3mm 0 0}}
.titel .qr{{display:flex;gap:4mm;align-items:center;background:#fff;border:.8mm solid #3A1531;border-radius:3mm;padding:3mm;text-align:left}}
.titel .qr svg{{width:26mm;height:26mm;flex:none}}
.titel .qr b{{font:700 11pt/1.2 Slab;display:block;margin-bottom:1mm}}
.titel .qr span{{font-size:8.5pt;line-height:1.3}}
.gueltig{{font-size:7.5pt;opacity:.8}}
.rueck .fit{{font-size:9pt;line-height:1.25}}
.laden table{{font-size:1em}}
.laden{{margin-bottom:3mm}}.laden h3{{font-size:1.25em;margin:0 0 .6mm}}.laden p{{margin:0 0 1mm}}
.laden table{{border-collapse:collapse;width:100%}}.laden td{{padding:.4mm 0}}.laden td+td{{text-align:right;font-weight:700}}
.bar{{font-weight:700;background:#3A1531;color:#fff;border-radius:2mm;padding:1.6mm 3mm;margin:0 0 3mm}}
.klein{{font-size:.82em;line-height:1.3;margin-top:2mm}}.klein p{{margin:0 0 1.4mm}}
.muster{{position:absolute;left:0;right:0;top:0;z-index:5;background:#3A1531;color:#fff;text-align:center;font:700 7pt Text;padding:1mm;letter-spacing:.3mm}}
</style></head><body>
<div class="seite">{muster}
  {spalte(KLAPPE, "schmal")}
  <div class="panel rueck"><div class="fit"><h2>Öffnungszeiten</h2>{laeden}{bar}
    {"".join(gruppe_html(i) for i in RUECKSEITE)}
    <div class="klein"><p><b>Allergene:</b> {leg}</p><p><b>Inhaltsstoffe:</b> {zut}</p>
    <p><b>Soßen</b> ({e(SOSSEN[0])}): {SOSSEN[1]} · {SOSSEN[2].replace(",", ", ")}</p>
    <p>Genaue Angaben zu Zutaten und Allergenen erhalten Sie an der Theke und auf unserer Website. Preise in Euro inkl. MwSt.</p></div></div></div>
  <div class="panel titel"><div><div class="seit">seit 1997</div><img src="{uri("maskottchen", "saray-koch.svg")}" alt="">
    <h1>Saray Döner</h1><div class="unter">Döner · Pizza · Lahmacun</div><div class="orte">{" · ".join(e(s["name"]) for s in build.STANDORTE)}</div></div>
    <div class="qr">{qr}<div><b>Speisekarte &amp; vorbestellen</b><span>Code scannen und per WhatsApp vorbestellen – ohne Warten an der Theke.<br>{e(build.CNAME)}</span></div></div>
    <div class="gueltig">Preise gültig ab {heute}</div></div>
</div>
<div class="seite">
  {spalte(INNEN[0])}{spalte(INNEN[1])}{spalte(INNEN[2], "schmal")}
</div>
<script>
/* Schrift je Spalte verkleinern, bis alles hineinpasst */
document.fonts.ready.then(function(){{
  document.querySelectorAll('.fit').forEach(function(f){{var s=8.6;
    while(f.scrollHeight>f.clientHeight+1&&s>6.2){{s-=.1;f.style.fontSize=s+'pt';}}
    f.dataset.passt=f.scrollHeight<=f.clientHeight+1?'ja':'nein';}});
  document.body.dataset.fertig='1';
}});
</script>
</body></html>"""


def slug(name, von):
    """Dateiname eines Aktions-Plakats – gleiche Regel wie in der Chef-App."""
    t = name.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        t = t.replace(a, b)
    t = "".join(c if c.isascii() and c.isalnum() else "-" for c in t)
    t = "-".join(x for x in t.split("-") if x)[:40].strip("-")
    return f"aktion-{von}-{t or 'x'}"


TAGE_LANG = ["sonntags", "montags", "dienstags", "mittwochs", "donnerstags", "freitags", "samstags"]


def plakat_html(a, quadrat=False, status=False):
    """A4 hoch: Aktions-Plakat fürs Schaufenster. quadrat=True: Bild zum Posten (Instagram). status=True: 1080 × 1920 für den WhatsApp-Status."""
    gerichte = {(g[0] or g[1]): (g, ab) for gr in build.GRUPPEN for ab in gr["abschnitte"] for g in ab["gerichte"]}
    zeilen = []
    for k, neu in a["preise"].items():
        if k not in gerichte:
            continue
        g, ab = gerichte[k]
        gr = ab.get("groessen") or []
        alt = " / ".join(g[3])
        neu_t = " / ".join(neu)
        zusatz = f'<small>{" / ".join(gr)}</small>' if gr else ""
        zeilen.append(f'<li><span class="nm">{e(g[1])}{zusatz}</span><span class="alt">{alt} €</span><span class="neu">{neu_t} €</span></li>')
    def d(iso):
        return f"{iso[8:]}.{iso[5:7]}."
    wann = f"{d(a['von'])} – {d(a['bis'])}{a['bis'][:4]}" if a["von"] != a["bis"] else f"am {d(a['bis'])}{a['bis'][:4]}"
    woche = [1, 2, 3, 4, 5, 6, 0]
    ts = sorted(a.get("tage", []), key=woche.index)
    folge = len(ts) >= 3 and [woche.index(t) for t in ts] == list(range(woche.index(ts[0]), woche.index(ts[0]) + len(ts)))
    tage = f"{TAGE_LANG[ts[0]]} bis {TAGE_LANG[ts[-1]]}" if folge else ", ".join(TAGE_LANG[t] for t in ts)
    uhr = f"{build.ANP.uhr(build.ANP._min(a['zeit_ab']))}–{build.ANP.uhr(build.ANP._min(a['zeit_bis']))} Uhr" if a.get("zeit_ab") else ""
    wo = next((f"nur in {s['name']}" for s in build.STANDORTE if s["id"] == a.get("laden")),
              " und ".join(s["name"] for s in build.STANDORTE))
    qr = qr_svg(f"https://{build.CNAME}/#speisekarte", "M", "#3A1531")
    muster = '<div class="muster">ENTWURF</div>' if build.VORSCHAU else ""
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><style>
@font-face{{font-family:Slab;src:url({uri("assets", "Roboto-Slab-Bold.sub.woff")});font-weight:700}}
@font-face{{font-family:Text;src:url({uri("assets", "lato-normal.sub.woff")});font-weight:400}}
@font-face{{font-family:Text;src:url({uri("assets", "lato-bold.sub.woff")});font-weight:700}}
@page{{size:A4;margin:0}}
*{{box-sizing:border-box}}html,body{{margin:0}}
body{{width:210mm;height:297mm;font-family:Text;color:#3A1531;background:#FFD21F;display:flex;flex-direction:column;align-items:center;
  -webkit-print-color-adjust:exact;print-color-adjust:exact;position:relative;overflow:hidden}}
main{{flex:1;min-height:0;width:100%;display:flex;flex-direction:column;align-items:center;overflow:hidden}}
.kopf{{display:flex;align-items:center;gap:5mm;margin-top:14mm}}
.kopf img{{width:24mm}}.kopf b{{font:700 12mm/1 Slab}}
.stoerer{{margin-top:9mm;background:#C8371A;color:#fff;font:700 26mm/1 Slab;padding:5mm 14mm 7mm;border-radius:6mm;transform:rotate(-3deg);letter-spacing:1mm}}
h1{{font:700 14mm/1.1 Slab;text-align:center;margin:11mm 14mm 0}}
ul{{list-style:none;margin:10mm 0 0;padding:0;width:170mm}}
li{{display:flex;align-items:baseline;gap:5mm;background:#fff;border:1mm solid #3A1531;border-radius:4mm;padding:4mm 6mm;margin-bottom:4mm}}
.nm{{flex:1;font:700 8.5mm/1.15 Slab}}.nm small{{display:block;font:400 4.5mm Text}}
.alt{{font-size:6mm;text-decoration:line-through;opacity:.55;white-space:nowrap}}
.neu{{font:700 13mm/1 Slab;color:#C8371A;white-space:nowrap}}
.wann{{margin-top:6mm;padding:0 16mm;font:700 8mm/1.25 Text;text-align:center}}
.wann span{{display:block;font-size:6.5mm;font-weight:400}}
.fuss{{flex:none;margin:6mm 0 12mm;display:flex;align-items:center;gap:6mm;background:#fff;border-radius:4mm;padding:5mm 7mm;width:170mm}}
.fuss svg{{width:34mm;height:34mm;flex:none}}.fuss b{{font:700 7mm/1.2 Slab;display:block}}.fuss p{{margin:1mm 0 0;font-size:4.6mm;line-height:1.35}}
.muster{{position:absolute;left:0;right:0;top:0;background:#3A1531;color:#fff;text-align:center;font:700 3.6mm Text;padding:1.6mm;letter-spacing:.3mm}}
{"body{height:210mm}.kopf{margin-top:8mm}.stoerer{margin-top:5mm;font-size:18mm}h1{margin-top:6mm}ul{margin-top:6mm}.fuss{margin:4mm 0 8mm}.fuss svg{width:26mm;height:26mm}" if quadrat else ""}
{"body{height:373.3mm}.kopf{margin-top:34mm}.kopf img{width:30mm}.kopf b{font-size:15mm}.stoerer{margin-top:16mm;font-size:22mm}h1{margin-top:16mm;font-size:16mm}ul{margin-top:14mm}main{justify-content:flex-start}.fuss{margin:8mm 0 30mm}" if status else ""}
</style></head><body>{"" if quadrat or status else muster}
<main><div class="kopf"><img src="{uri("maskottchen", "saray-koch-kopf.svg")}" alt=""><b>Saray Döner</b></div>
<div class="stoerer">{"MITTAGSTISCH" if a.get("art") == "mittag" else "AKTION"}</div>
<h1>{e(a["name"]).replace(" €", "&nbsp;€")}</h1>
<ul>{"".join(zeilen)}</ul>
<div class="wann">{wann}<span>{" · ".join(x for x in (tage, uhr, wo) if x)}</span></div></main>
<div class="fuss">{qr}<div><b>Jetzt vorbestellen</b><p>Code scannen, Gerichte wählen und per WhatsApp schicken – ohne Warten an der Theke.<br>{e(build.CNAME)}</p></div></div>
<script>/* bei vielen Gerichten verkleinern, bis alles auf die Seite passt */
var m=document.querySelector('main'),z=1;while(m.scrollHeight>m.clientHeight+1&&z>.5){{z-=.03;m.style.zoom=z;}}</script>
</body></html>"""


def status_empfehlung_html():
    """1080 × 1920 für den WhatsApp-Status: „Heute bei Saray“ mit den Empfehlungen und QR-Code zum Vorbestellen."""
    gerichte = {(g[0] or g[1]): g for gr in build.GRUPPEN for ab in gr["abschnitte"] for g in ab["gerichte"]}
    zeilen = "".join(f'<li><span class="nm">{e(gerichte[n][1])}<small>{e(gerichte[n][2])}</small></span><span class="neu">{gerichte[n][3][0]} €</span></li>'
                     for n in [x for x in build.EMPFEHLUNG if x in gerichte and x not in build.NUR_DIAET][:4])
    qr = qr_svg(f"https://{build.CNAME}/#speisekarte", "M", "#3A1531")
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><style>
@font-face{{font-family:Slab;src:url({uri("assets", "Roboto-Slab-Bold.sub.woff")});font-weight:700}}
@font-face{{font-family:Text;src:url({uri("assets", "lato-normal.sub.woff")});font-weight:400}}
@font-face{{font-family:Text;src:url({uri("assets", "lato-bold.sub.woff")});font-weight:700}}
*{{box-sizing:border-box}}html,body{{margin:0}}
body{{width:210mm;height:373.3mm;font-family:Text;color:#3A1531;background:#FFD21F;display:flex;flex-direction:column;align-items:center;overflow:hidden}}
.kopf{{display:flex;align-items:center;gap:5mm;margin-top:34mm}}.kopf img{{width:30mm}}.kopf b{{font:700 15mm/1 Slab}}
h1{{font:700 19mm/1.05 Slab;text-align:center;margin:16mm 12mm 0}}
.koch{{width:70mm;margin-top:8mm}}
ul{{list-style:none;margin:10mm 0 0;padding:0;width:176mm}}
li{{display:flex;align-items:center;gap:5mm;background:#fff;border:1mm solid #3A1531;border-radius:4mm;padding:4mm 6mm;margin-bottom:4mm}}
.nm{{flex:1;font:700 8.5mm/1.15 Slab}}.nm small{{display:block;font:400 4.5mm Text;margin-top:1mm}}
.neu{{font:700 11mm/1 Slab;color:#C8371A;white-space:nowrap}}
.fuss{{margin:auto 0 30mm;display:flex;align-items:center;gap:6mm;background:#fff;border-radius:4mm;padding:5mm 7mm;width:176mm}}
.fuss svg{{width:34mm;height:34mm;flex:none}}.fuss b{{font:700 7mm/1.2 Slab;display:block}}.fuss p{{margin:1mm 0 0;font-size:4.6mm;line-height:1.35}}
</style></head><body>
<div class="kopf"><img src="{uri("maskottchen", "saray-koch-kopf.svg")}" alt=""><b>Saray Döner</b></div>
<h1>Frisch vom Spieß.<br>Heute bei uns:</h1>
<ul>{zeilen}</ul>
<img class="koch" src="{uri("maskottchen", "saray-koch.svg")}" alt="">
<div class="fuss">{qr}<div><b>Jetzt vorbestellen</b><p>Code scannen, wählen, per WhatsApp schicken – ohne Warten abholen. Nur Barzahlung.<br>{e(build.CNAME)}</p></div></div>
</body></html>"""


def aushang_html():
    """A3 hoch: die ganze Karte als Aushang fürs Schaufenster oder den Rahmen an der Theke – immer mit aktuellen Preisen."""
    heute = datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Berlin")).strftime("%d.%m.%Y")
    spalten = "".join(gruppe_html(g["id"]) for g in build.GRUPPEN)
    qr = qr_svg(f"https://{build.CNAME}/#speisekarte", "M", "#3A1531")
    orte = " · ".join(f'<b>{e(st["name"])}</b> {e(st["strasse"])}, Tel. {e(st["tel"])}, {e(st["kurz"])}' for st in build.STANDORTE)
    muster = '<div class="muster">ENTWURF</div>' if build.VORSCHAU else ""
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><style>
@font-face{{font-family:Slab;src:url({uri("assets", "Roboto-Slab-Bold.sub.woff")});font-weight:700}}
@font-face{{font-family:Text;src:url({uri("assets", "lato-normal.sub.woff")});font-weight:400}}
@font-face{{font-family:Text;src:url({uri("assets", "lato-bold.sub.woff")});font-weight:700}}
@page{{size:A3;margin:0}}*{{box-sizing:border-box}}html,body{{margin:0}}
body{{width:297mm;height:420mm;font-family:Text;color:#3A1531;background:#FFD21F;display:flex;flex-direction:column;padding:12mm 12mm 10mm;
  -webkit-print-color-adjust:exact;print-color-adjust:exact;overflow:hidden;position:relative}}
.kopf{{display:flex;align-items:center;gap:5mm}}.kopf img{{width:18mm}}.kopf h1{{font:700 11mm/1 Slab;margin:0;flex:1;white-space:nowrap}}.kopf span{{font:700 4mm/1.3 Text;text-align:right}}
.spalten{{flex:1;min-height:0;columns:4;column-gap:5mm;column-fill:auto;margin-top:5mm;font-size:3.1mm;overflow:hidden}}
section{{break-inside:auto;margin-bottom:3mm}}
h2{{font:700 5.2mm/1 Slab;background:#3A1531;color:#FFD21F;padding:1.6mm 2.5mm;border-radius:1.6mm;margin:0 0 1.5mm;break-after:avoid}}
h3{{font:700 3.6mm Slab;margin:2mm 0 1mm;border-bottom:.35mm solid #3A1531;display:flex;flex-wrap:wrap;gap:1mm 2mm;align-items:baseline;break-after:avoid}}
h3 small{{font:400 2.7mm Text}}h3 .kz{{font:400 2.5mm Text;color:#6b5566}}h3 .gr{{margin-left:auto;display:flex;gap:3mm;font:700 2.7mm Text}}
ul{{list-style:none;margin:0;padding:0}}li{{display:flex;gap:1.6mm;padding:.7mm 0;break-inside:avoid;border-bottom:.15mm dotted #b39a2a}}
.nr{{width:6mm;flex:none;text-align:right;font-weight:700;color:#6b5566}}.nm{{flex:1}}.nm small{{display:block;font-size:2.5mm;color:#4d3347}}
.pr{{display:flex;gap:2.4mm;white-space:nowrap;color:#C8371A}}.pr b{{font:700 3.4mm Slab}}
.notiz{{margin:1mm 0 0;font-size:2.6mm}}
.fuss{{display:flex;align-items:center;gap:5mm;background:#fff;border-radius:3mm;padding:3mm 5mm;margin-top:4mm;font-size:3.2mm;line-height:1.4}}
.fuss svg{{width:26mm;height:26mm;flex:none}}.fuss b{{font-family:Slab}}
.muster{{position:absolute;left:0;right:0;top:0;background:#3A1531;color:#fff;text-align:center;font:700 3.6mm Text;padding:1.4mm}}
</style></head><body>{muster}
<div class="kopf"><img src="{uri("maskottchen", "saray-koch-kopf.svg")}" alt=""><h1>Saray Döner · Speisekarte</h1><span>Nur Barzahlung · Preise in Euro inkl. MwSt.<br>Stand {heute}</span></div>
<div class="spalten">{spalten}</div>
<div class="fuss">{qr}<div><b>Vorbestellen per WhatsApp: {e(build.CNAME)}</b><br>{orte}<br>Alle Gerichte mit Soße nach Wahl: Knoblauch, Kräuter, Chili. Allergene und Inhaltsstoffe: Mappe an der Theke.</div></div>
<script>/* passt alles auf das Blatt? sonst Schrift verkleinern */
var sp=document.querySelector('.spalten'),f=3.1;
function zuViel(){{var r=sp.getBoundingClientRect();return [].some.call(sp.querySelectorAll('li,h3'),function(x){{var q=x.getBoundingClientRect();return q.right>r.right+1||q.bottom>r.bottom+1;}});}}
document.fonts.ready.then(function(){{while(zuViel()&&f>1.9){{f-=.05;sp.style.fontSize=f+'mm';}}document.body.dataset.fertig=f.toFixed(2);}});</script>
</body></html>"""


VORBESTELLEN = [  # (Sprache, Überschrift, Schritte, Zusatz) – für den Aushang „Hier vorbestellen“
    ("de", "Hier vorbestellen –<br>ohne Warten abholen", ["Code scannen", "Essen wählen", "per WhatsApp schicken", "abholen und bar bezahlen"], "Döner, Dürüm, Pizza und Salate"),
    ("en", "Order ahead here –<br>pick up without waiting", ["Scan the code", "Choose your food", "Send via WhatsApp", "Pick up and pay cash"], "Döner, dürüm, pizza and salads"),
    ("cs", "Objednejte předem –<br>vyzvedněte bez čekání", ["Naskenujte kód", "Vyberte jídlo", "Pošlete přes WhatsApp", "Vyzvedněte a zaplaťte hotově"], "Döner, dürüm, pizza a saláty"),
    ("tr", "Önceden sipariş verin –<br>beklemeden alın", ["Kodu tarayın", "Yemeğinizi seçin", "WhatsApp ile gönderin", "Teslim alın, nakit ödeyin"], "Döner, dürüm, pizza ve salatalar"),
    ("ru", "Закажите заранее –<br>заберите без ожидания", ["Сканируйте код", "Выберите еду", "Отправьте через WhatsApp", "Заберите и оплатите наличными"], "Дёнер, дюрюм, пицца и салаты"),
    ("ar", "اطلب مسبقًا هنا –<br>واستلم دون انتظار", ["امسح الرمز", "اختر طعامك", "أرسل عبر واتساب", "استلم وادفع نقدًا"], "دونر، دوروم، بيتزا وسلطات"),
]


def vorbestellen_html():
    """A5-Aushang „Hier vorbestellen“ für Fenster, Bushaltestelle und Bahnhof: Seite 1 alle Sprachen, danach je Sprache eine Seite
    mit eigenem QR-Code (öffnet die Seite gleich in dieser Sprache)."""
    kopf = uri("maskottchen", "saray-koch-kopf.svg")
    orte = " · ".join(f'{e(st["name"])}: {e(st["strasse"])}' for st in build.STANDORTE)
    seiten = []
    qr_alle = qr_svg(f"https://{build.CNAME}/#speisekarte", "M", "#3A1531")
    zeilen = "".join(f'<li lang="{c}" dir="{"rtl" if c == "ar" else "ltr"}"><b>{u.replace("<br>", " ")}</b></li>' for c, u, _, _ in VORBESTELLEN[1:])
    seiten.append(f'<section class="s alle"><div class="k"><img src="{kopf}" alt=""><b>Saray Döner</b></div><h1>{VORBESTELLEN[0][1]}</h1>'
                  f'<div class="qr">{qr_alle}</div><ul>{zeilen}</ul><p class="f">{e(build.CNAME)} · {orte}</p></section>')
    for c, ueber, schritte, zusatz in VORBESTELLEN:
        qr = qr_svg(f"https://{build.CNAME}/?sp={c}#speisekarte", "M", "#3A1531")
        liste = "".join(f"<li><span>{i + 1}</span>{e(x)}</li>" for i, x in enumerate(schritte))
        seiten.append(f'<section class="s" lang="{c}" dir="{"rtl" if c == "ar" else "ltr"}"><div class="k" dir="ltr"><img src="{kopf}" alt=""><b>Saray Döner</b></div>'
                      f'<h1>{ueber}</h1><p class="z">{e(zusatz)}</p><div class="qr">{qr}</div><ol>{liste}</ol>'
                      f'<p class="f" dir="ltr">{e(build.CNAME)} · {orte}</p></section>')
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><style>
@font-face{{font-family:Slab;src:url({uri("assets", "Roboto-Slab-Bold.sub.woff")});font-weight:700}}
@font-face{{font-family:Text;src:url({uri("assets", "lato-normal.sub.woff")});font-weight:400}}
@font-face{{font-family:Text;src:url({uri("assets", "lato-bold.sub.woff")});font-weight:700}}
@page{{size:A5;margin:0}}*{{box-sizing:border-box}}html,body{{margin:0}}
body{{font-family:Text,"Noto Sans","DejaVu Sans",sans-serif;color:#3A1531;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.s{{width:148mm;height:210mm;background:#FFD21F;padding:10mm 11mm;display:flex;flex-direction:column;align-items:center;text-align:center;break-after:page;overflow:hidden}}
.k{{display:flex;align-items:center;gap:3mm}}.k img{{width:14mm}}.k b{{font:700 9mm/1 Slab}}
h1{{font:700 10mm/1.12 Slab,"Noto Sans","DejaVu Sans",sans-serif;margin:7mm 0 0}}
[lang=ar] h1,[lang=ru] h1{{font-family:"Noto Sans","DejaVu Sans",sans-serif}}
.z{{margin:2mm 0 0;font-size:4.4mm}}
.qr{{background:#fff;border-radius:4mm;padding:3mm;margin-top:6mm;width:62mm;height:62mm}}.qr svg{{width:100%;height:100%;display:block}}
ol{{list-style:none;padding:0;margin:6mm 0 0;width:100%;text-align:start}}
ol li{{display:flex;align-items:center;gap:3mm;background:#fff;border-radius:3mm;padding:2.2mm 3.5mm;margin-bottom:2mm;font:700 5mm/1.2 Text,"Noto Sans","DejaVu Sans",sans-serif}}
ol li span{{flex:none;width:8mm;height:8mm;border-radius:50%;background:#3A1531;color:#FFD21F;display:grid;place-items:center;font:700 4.5mm Slab}}
.alle ul{{list-style:none;padding:0;margin:5mm 0 0;width:100%}}.alle li{{background:#fff;border-radius:3mm;padding:1.8mm 3mm;margin-bottom:1.6mm;font-size:4mm}}
.f{{margin-top:auto;font-size:3.2mm}}
</style></head><body>{"".join(seiten)}</body></html>"""


def allergenmappe_html():
    """Allergenmappe für die Theke: jedes Gericht mit Inhaltsstoffen und Allergenen (A4 hoch, mehrere Seiten)."""
    heute = datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Berlin")).strftime("%d.%m.%Y")
    leg = "".join(f"<tr><td><b>{k}</b></td><td>{e(v)}</td></tr>" for k, v in ALLERGENE.items())
    zut = "".join(f"<tr><td><b>{k}</b></td><td><b>{e(n)}</b> – {e(t)}</td></tr>" for k, (n, t) in ZUTATEN.items())
    teile = []
    for gr in build.GRUPPEN:
        zeilen = []
        for ab in gr["abschnitte"]:
            kz = KENNZEICHNUNG.get(ab["titel"])
            for g in ab["gerichte"]:
                nr, name = g[0], g[1]
                al = (kz[1] if kz else "")
                extra = GERICHT_ALLERGENE.get(nr, "")
                al = ", ".join(x for x in (al + "," + extra).split(",") if x)
                zeilen.append(f'<tr><td class="nr">{e(build.anz(nr) if nr else "")}</td><td>{e(name)}<small>{e(g[2])}</small></td>'
                              f'<td>{e(kz[0].replace(",", ", ")) if kz else "–"}</td><td>{e(al) if al else "<i>bitte erfragen</i>"}</td></tr>')
        teile.append(f'<section><h2>{e(gr["titel"])}</h2><table><thead><tr><th>Nr.</th><th>Gericht</th><th>Inhaltsstoffe</th><th>Allergene</th></tr></thead>'
                     f'<tbody>{"".join(zeilen)}</tbody></table></section>')
    muster = '<div class="muster">ENTWURF</div>' if build.VORSCHAU else ""
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><style>
@font-face{{font-family:Slab;src:url({uri("assets", "Roboto-Slab-Bold.sub.woff")});font-weight:700}}
@font-face{{font-family:Text;src:url({uri("assets", "lato-normal.sub.woff")});font-weight:400}}
@font-face{{font-family:Text;src:url({uri("assets", "lato-bold.sub.woff")});font-weight:700}}
@page{{size:A4;margin:14mm 14mm 16mm}}
body{{font:9.5pt/1.35 Text;color:#3A1531;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
h1{{font:700 20pt/1.1 Slab;margin:0 0 2mm}}h2{{font:700 13pt Slab;margin:6mm 0 2mm;padding:1.5mm 3mm;background:#FFD21F;border-radius:1.5mm;break-after:avoid}}
.stand{{color:#6b5566;margin:0 0 4mm}}
table{{width:100%;border-collapse:collapse}}th,td{{text-align:left;vertical-align:top;padding:1.2mm 2mm;border-bottom:.2mm solid #e3d6de}}
th{{font-size:8pt;text-transform:uppercase;letter-spacing:.04em;color:#6b5566}}tr{{break-inside:avoid}}
td small{{display:block;color:#6b5566;font-size:8pt}}td.nr{{width:10mm;font-weight:700}}
.leg td:first-child{{width:8mm}}.kasten{{display:grid;grid-template-columns:1fr 1.6fr;gap:6mm;margin-bottom:4mm}}
.hinweis{{margin-top:6mm;font-size:8.5pt;color:#6b5566}}
.muster{{background:#3A1531;color:#fff;text-align:center;font:700 8pt Text;padding:1mm;margin:-2mm 0 4mm}}
</style></head><body>{muster}
<h1>Allergene und Inhaltsstoffe</h1><p class="stand">Saray Döner Freital und Altenberg · Stand {heute}</p>
<div class="kasten"><div><h2>Allergene</h2><table class="leg">{leg}</table>
<p>Soßen ({e(SOSSEN[0])}): Inhaltsstoff {SOSSEN[1]} · Allergene {SOSSEN[2].replace(",", ", ")}</p></div>
<div><h2>Inhaltsstoffe</h2><table class="leg">{zut}</table></div></div>
{"".join(teile)}
<p class="hinweis">Angaben nach Herstellerangaben. Spuren anderer Allergene durch die Zubereitung in unserer Küche sind möglich.
Bei Fragen sprechen Sie uns bitte an.</p>
</body></html>"""


def preisschilder_html():
    """Preisschilder für Theke und Kühlschrank: alle Getränke, 8 Schilder je A4 (105 × 74 mm), mit Schnittlinien.
    Preise und Kennzeichnung immer aktuell (inkl. Änderungen aus der Chef-App)."""
    kopf = uri("maskottchen", "saray-koch-kopf.svg")
    schilder = []
    for gr in build.GRUPPEN:
        if gr["id"] != "getraenke":
            continue
        for ab in gr["abschnitte"]:
            kz = KENNZEICHNUNG.get(ab["titel"])
            pfand = ab.get("info", "") if "Pfand" in ab.get("info", "") else ""
            for g in ab["gerichte"]:
                preis = g[3][0]
                euro, cent = preis.split(",")
                kenn = ""
                if kz:
                    teile = []
                    if kz[0]:
                        teile.append("Inhaltsstoffe " + kz[0].replace(",", ", "))
                    if kz[1]:
                        teile.append("Allergene " + kz[1].replace(",", ", "))
                    kenn = " · ".join(teile)
                schilder.append(f'<div class="s"><div class="k"><img src="{kopf}" alt=""><span>{e(ab["titel"])}</span></div>'
                                f'<b class="n">{e(g[1])}</b><span class="d">{e(g[2])}</span>'
                                f'<span class="p">{euro}<sup>{cent}</sup> €</span>'
                                f'<span class="f">{e(pfand)}{" · " if pfand and kenn else ""}{e(kenn)}</span></div>')
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><style>
@font-face{{font-family:Slab;src:url({uri("assets", "Roboto-Slab-Bold.sub.woff")});font-weight:700}}
@font-face{{font-family:Text;src:url({uri("assets", "lato-normal.sub.woff")});font-weight:400}}
@font-face{{font-family:Text;src:url({uri("assets", "lato-bold.sub.woff")});font-weight:700}}
@page{{size:A4;margin:0}}*{{box-sizing:border-box}}html,body{{margin:0}}
body{{width:210mm;display:grid;grid-template-columns:repeat(2,105mm);grid-auto-rows:74.25mm;font-family:Text;color:#3A1531;
  -webkit-print-color-adjust:exact;print-color-adjust:exact}}
.s{{position:relative;display:flex;flex-direction:column;padding:6mm 7mm 5mm;border:.2mm dashed #b9a9b4;background:#FFD21F;break-inside:avoid;overflow:hidden}}
.s:nth-child(8n+1){{break-before:page}}
.k{{display:flex;align-items:center;gap:2mm;font:700 3.2mm Text;text-transform:uppercase;letter-spacing:.06em}}.k img{{width:8mm;height:8mm}}
.n{{font:700 8mm/1.08 Slab;margin-top:3mm}}.d{{font-size:4mm;margin-top:1mm}}
.p{{margin-top:auto;font:700 17mm/1 Slab;color:#C8381E}}.p sup{{font-size:.5em;vertical-align:.75em;margin-left:.5mm}}
.f{{font-size:2.8mm;margin-top:1.5mm;min-height:3mm}}
</style></head><body>{"".join(schilder)}</body></html>"""


def aufkleber_html():
    """A4-Bogen mit 24 Etiketten 70 × 37 mm (z. B. Zweckform 3474) für Tüten: QR-Code zur Speisekarte."""
    qr = qr_svg(f"https://{build.CNAME}/#speisekarte", "M", "#3A1531")
    kopf = uri("maskottchen", "saray-koch-kopf.svg")
    eins = (f'<div class="et"><div>{qr}</div><div class="t"><div class="k"><img src="{kopf}" alt=""><b>Saray Döner</b></div>'
            f'<p>Nächstes Mal online vorbestellen – ohne Warten.</p><small>{e(build.CNAME)}</small></div></div>')
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><style>
@font-face{{font-family:Slab;src:url({uri("assets", "Roboto-Slab-Bold.sub.woff")});font-weight:700}}
@font-face{{font-family:Text;src:url({uri("assets", "lato-normal.sub.woff")});font-weight:400}}
@font-face{{font-family:Text;src:url({uri("assets", "lato-bold.sub.woff")});font-weight:700}}
@page{{size:A4;margin:0}}*{{box-sizing:border-box}}html,body{{margin:0}}
body{{width:210mm;height:297mm;display:grid;grid-template-columns:repeat(3,70mm);grid-template-rows:repeat(8,37mm);align-content:start;
  font-family:Text;color:#3A1531;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.et{{display:flex;align-items:center;gap:2.5mm;padding:2.5mm 3mm;overflow:hidden}}
.et svg{{width:27mm;height:27mm;display:block}}
.t{{min-width:0}}.k{{display:flex;align-items:center;gap:1.5mm}}.k img{{width:7mm;height:7mm}}.k b{{font:700 4.2mm/1 Slab}}
.t p{{margin:1.5mm 0 1mm;font:700 3.1mm/1.25 Text}}.t small{{font-size:2.6mm}}
</style></head><body>{eins * 24}</body></html>"""


def gruppen_flyer_html():
    """A5-Flyer für Betriebe, Vereine und Feiern: gemeinsam bestellen, gesammelt abholen."""
    qr = qr_svg(f"https://{build.CNAME}/#gruppen", "M", "#3A1531")
    muster = '<div class="muster">ENTWURF</div>' if build.VORSCHAU else ""
    laeden = "".join(f'<div class="laden"><b>{e(st["name"])}</b><span>{e(st["strasse"])}</span><span>Tel. {e(st["tel"])}</span>'
                     f'<span>{e(st["kurz"])}</span></div>' for st in build.STANDORTE)
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><style>
@font-face{{font-family:Slab;src:url({uri("assets", "Roboto-Slab-Bold.sub.woff")});font-weight:700}}
@font-face{{font-family:Text;src:url({uri("assets", "lato-normal.sub.woff")});font-weight:400}}
@font-face{{font-family:Text;src:url({uri("assets", "lato-bold.sub.woff")});font-weight:700}}
@page{{size:A5;margin:0}}*{{box-sizing:border-box}}html,body{{margin:0}}
body{{width:148mm;height:210mm;font-family:Text;color:#3A1531;background:#fff;display:flex;flex-direction:column;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.kopf{{background:#FFD21F;padding:7mm 9mm 5mm;border-bottom:1.5mm solid #3A1531}}
.kopf .marke{{display:flex;align-items:center;gap:3mm;font:700 6mm Slab}}.kopf img{{width:13mm}}
h1{{font:700 9mm/1.05 Slab;margin:4mm 0 2mm}}.kopf p{{margin:0;font-size:4.2mm;line-height:1.35}}
.inhalt{{flex:1;min-height:0;padding:5mm 9mm;display:flex;flex-direction:column;gap:3.5mm}}
ol{{margin:0;padding:0;list-style:none;counter-reset:s;display:grid;gap:3mm}}
li{{counter-increment:s;display:grid;grid-template-columns:9mm 1fr;align-items:start;font-size:3.9mm;line-height:1.35}}
li::before{{content:counter(s);display:grid;place-items:center;width:7mm;height:7mm;border-radius:50%;background:#FFD21F;font:700 4mm Slab}}
li b{{font-family:Slab}}
.qr{{display:flex;gap:5mm;align-items:center;border:.7mm solid #3A1531;border-radius:3mm;padding:3.5mm}}
.qr svg{{width:26mm;height:26mm;flex:none}}.qr b{{font:700 5mm/1.2 Slab;display:block}}.qr span{{font-size:3.5mm}}
.hinweis{{font-size:3.5mm;background:#FFF3C2;border-radius:2mm;padding:2.5mm 3mm}}
.laeden{{display:grid;grid-template-columns:1fr 1fr;gap:4mm;font-size:3.2mm;padding:3.5mm 9mm 6mm;border-top:.3mm solid #e6dbe2}}
.laden{{display:flex;flex-direction:column;gap:.6mm}}.laden b{{font:700 4mm Slab}}
.muster{{background:#3A1531;color:#fff;text-align:center;font:700 3mm Text;padding:1mm}}
</style></head><body>{muster}
<div class="kopf"><div class="marke"><img src="{uri("maskottchen", "saray-koch-kopf.svg")}" alt="">Saray Döner</div>
<h1>Mittagspause fürs Team? Feier am Abend?</h1><p>Für Firmen, Vereine und Feiern: alle bestellen gemeinsam, einer holt ab.</p></div>
<div class="inhalt"><ol>
<li><span><b>Starten:</b> Code scannen, „Gemeinsam bestellen“ antippen und den Link an die Gruppe schicken.</span></li>
<li><span><b>Aussuchen:</b> Jeder wählt sein Essen am eigenen Handy und schickt seinen Teil zurück.</span></li>
<li><span><b>Abholen:</b> Laden und Uhrzeit wählen – auch Tage im Voraus – und alles mit einer Nachricht schicken.</span></li>
</ol>
<div class="qr">{qr}<div><b>Gemeinsam bestellen</b><span>{e(build.CNAME)}</span></div></div>
<p class="hinweis"><b>Größere Bestellungen</b> bitte rechtzeitig vorbestellen oder kurz anrufen. Bezahlt wird bei Abholung, nur bar.</p></div>
<div class="laeden">{laeden}</div>
</body></html>"""


async def main(ziel):
    ziel.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        tmp = HIER / "_flyer.html"
        tmp.write_text(flyer_html(), encoding="utf-8")
        pg = await b.new_page(viewport={"width": 1123, "height": 794})
        await pg.goto(tmp.as_uri())
        await pg.wait_for_selector("body[data-fertig]")
        zu_voll = await pg.evaluate("[...document.querySelectorAll('.fit')].filter(f=>f.dataset.passt!=='ja').length")
        if zu_voll:
            print(f"WARNUNG: {zu_voll} Flyer-Spalte(n) zu voll – Inhalt abgeschnitten")
        await pg.pdf(path=str(ziel / "flyer.pdf"), width="297mm", height="210mm", print_background=True)
        await pg.screenshot(path=str(HIER / "druck" / "flyer-vorschau.png"), full_page=True)
        await pg.close()
        tmp.unlink()
        for st in build.STANDORTE:
            tmp = HIER / f"_aufsteller-{st['id']}.html"
            tmp.write_text(aufsteller.vorlage(st), encoding="utf-8")
            pg = await b.new_page(viewport={"width": 559, "height": 794})
            await pg.goto(tmp.as_uri())
            await pg.wait_for_timeout(400)
            await pg.pdf(path=str(ziel / f"aufsteller-{st['id']}.pdf"), format="A5", print_background=True)
            await pg.close()
            tmp.unlink()
        tmp = HIER / "_gruppen.html"
        tmp.write_text(gruppen_flyer_html(), encoding="utf-8")
        pg = await b.new_page(viewport={"width": 559, "height": 794})
        await pg.goto(tmp.as_uri())
        await pg.wait_for_timeout(400)
        await pg.pdf(path=str(ziel / "flyer-gruppen.pdf"), format="A5", print_background=True)
        if "--vorschau" in sys.argv:
            await pg.screenshot(path=str(HIER / "druck" / "gruppen-vorschau.png"))
        await pg.close()
        tmp.unlink()
        for name, inhalt in (("allergenmappe", allergenmappe_html()), ("aufkleber", aufkleber_html()), ("preisschilder", preisschilder_html())):
            tmp = HIER / f"_{name}.html"
            tmp.write_text(inhalt, encoding="utf-8")
            pg = await b.new_page(viewport={"width": 794, "height": 1123})
            await pg.goto(tmp.as_uri())
            await pg.wait_for_timeout(400)
            await pg.pdf(path=str(ziel / f"{name}.pdf"), format="A4", print_background=True,
                         prefer_css_page_size=True)
            if "--vorschau" in sys.argv:
                await pg.screenshot(path=str(HIER / "druck" / f"{name}-vorschau.png"))
            await pg.close()
            tmp.unlink()
        # A5 „Hier vorbestellen“ in allen Sprachen
        tmp = HIER / "_vorbestellen.html"
        tmp.write_text(vorbestellen_html(), encoding="utf-8")
        pg = await b.new_page(viewport={"width": 559, "height": 794})
        await pg.goto(tmp.as_uri())
        await pg.wait_for_timeout(500)
        await pg.pdf(path=str(ziel / "aushang-vorbestellen.pdf"), format="A5", print_background=True, prefer_css_page_size=True)
        if "--vorschau" in sys.argv:
            await pg.screenshot(path=str(HIER / "druck" / "vorbestellen-vorschau.png"), full_page=True)
        await pg.close()
        tmp.unlink()
        # Aushang A3 mit der ganzen Karte
        tmp = HIER / "_aushang.html"
        tmp.write_text(aushang_html(), encoding="utf-8")
        pg = await b.new_page(viewport={"width": 1123, "height": 1587})
        await pg.goto(tmp.as_uri())
        await pg.wait_for_selector("body[data-fertig]")
        await pg.wait_for_timeout(300)
        await pg.pdf(path=str(ziel / "aushang-a3.pdf"), format="A3", print_background=True, prefer_css_page_size=True)
        if "--vorschau" in sys.argv:
            await pg.screenshot(path=str(HIER / "druck" / "aushang-vorschau.png"))
        await pg.close()
        tmp.unlink()
        # Bilder für den WhatsApp-Status (1080 × 1920): Empfehlungen + je Aktion/Mittagstisch
        status = [("status-empfehlung.png", status_empfehlung_html())] + [(f"status-{slug(a['name'], a['von'])}.png", plakat_html(a, status=True)) for a in build.AKTIONEN]
        for name, inhalt in status:
            tmp = HIER / "_status.html"
            tmp.write_text(inhalt, encoding="utf-8")
            pg = await b.new_page(viewport={"width": 794, "height": 1411}, device_scale_factor=1080 / 794)
            await pg.goto(tmp.as_uri())
            await pg.wait_for_timeout(400)
            await pg.screenshot(path=str(ziel / name))
            await pg.close()
            tmp.unlink()
        for a in build.AKTIONEN:
            # quadratisches Bild zum Posten (1080 × 1080)
            tmp = HIER / "_bild.html"
            tmp.write_text(plakat_html(a, quadrat=True), encoding="utf-8")
            pg = await b.new_page(viewport={"width": 794, "height": 794}, device_scale_factor=1080 / 794)
            await pg.goto(tmp.as_uri())
            await pg.wait_for_timeout(400)
            await pg.screenshot(path=str(ziel / f"{slug(a['name'], a['von'])}.png"))
            await pg.close()
            tmp.unlink()
            tmp = HIER / "_plakat.html"
            tmp.write_text(plakat_html(a), encoding="utf-8")
            pg = await b.new_page(viewport={"width": 794, "height": 1123})
            await pg.goto(tmp.as_uri())
            await pg.wait_for_timeout(400)
            await pg.pdf(path=str(ziel / f"{slug(a['name'], a['von'])}.pdf"), format="A4", print_background=True)
            if "--vorschau" in sys.argv:
                await pg.screenshot(path=str(HIER / "druck" / "plakat-vorschau.png"))
            await pg.close()
            tmp.unlink()
        await b.close()
    print("Druck:", ", ".join(f.name for f in sorted(list(ziel.glob("*.pdf")) + list(ziel.glob("*.png")))))


if __name__ == "__main__":
    pfade = [x for x in sys.argv[1:] if not x.startswith("--")]
    asyncio.run(main(pathlib.Path(pfade[0]) if pfade else HIER / "docs" / "druck"))
