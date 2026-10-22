#!/usr/bin/env python3
"""Druckvorlagen mit den aktuellen Preisen (inkl. Änderungen aus der Chef-App):

    python3 druck.py [ziel]   ->  <ziel>/flyer.pdf, <ziel>/aufsteller-<laden>.pdf   (Standard: docs/druck)

Aktions-Plakate: je laufender/kommender Sonderaktion ein A4-Plakat (aktion-<von>-<name>.pdf).
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
from menu import ALLERGENE, ZUTATEN, KENNZEICHNUNG, SOSSEN
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
            klein = " – ".join(x for x in (desc, var) if x)
            out.append(f'<li><span class="nr">{e(nr)}</span><span class="nm"><b>{e(name)}</b>'
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
    muster = '<div class="muster">MUSTER – Seite noch nicht freigeschaltet</div>' if build.VORSCHAU else ""
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
.titel .qr svg{{width:30mm;height:30mm;flex:none}}
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


def plakat_html(a):
    """A4 hoch: Aktions-Plakat fürs Schaufenster."""
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
    muster = '<div class="muster">MUSTER – Seite noch nicht freigeschaltet</div>' if build.VORSCHAU else ""
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
</style></head><body>{muster}
<main><div class="kopf"><img src="{uri("maskottchen", "saray-koch-kopf.svg")}" alt=""><b>Saray Döner</b></div>
<div class="stoerer">AKTION</div>
<h1>{e(a["name"]).replace(" €", "&nbsp;€")}</h1>
<ul>{"".join(zeilen)}</ul>
<div class="wann">{wann}<span>{" · ".join(x for x in (tage, uhr, wo) if x)}</span></div></main>
<div class="fuss">{qr}<div><b>Jetzt vorbestellen</b><p>Code scannen, Gerichte wählen und per WhatsApp schicken – ohne Warten an der Theke.<br>{e(build.CNAME)}</p></div></div>
<script>/* bei vielen Gerichten verkleinern, bis alles auf die Seite passt */
var m=document.querySelector('main'),z=1;while(m.scrollHeight>m.clientHeight+1&&z>.5){{z-=.03;m.style.zoom=z;}}</script>
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
        for a in build.AKTIONEN:
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
    print("Druck:", ", ".join(f.name for f in sorted(ziel.glob("*.pdf"))))


if __name__ == "__main__":
    pfade = [x for x in sys.argv[1:] if not x.startswith("--")]
    asyncio.run(main(pathlib.Path(pfade[0]) if pfade else HIER / "docs" / "druck"))
