#!/usr/bin/env python3
"""Druckvorlagen für die Theke: je Laden ein A5-Aufsteller mit zwei QR-Codes.

    python3 aufsteller.py   ->  druck/aufsteller-freital.pdf, druck/aufsteller-altenberg.pdf (+ PNG-Vorschau)

Oben: Speisekarte & Vorbestellen (wählt den Laden im Bestellzettel vor).
Unten: Google-Bewertung für genau diesen Laden.
Braucht Playwright mit Chromium (wie png_export.py). Vor dem Druck die Codes mit dem Handy testen!
"""
import asyncio
import html
import pathlib

from playwright.async_api import async_playwright

import build
from qr import qr_svg

HIER = pathlib.Path(__file__).parent
AUS = HIER / "druck"
# Adresse, auf die der Speisekarten-Code zeigt. Nach dem Umzug auf saraydöner.de hier ändern und neu erzeugen.
SEITE = f"https://{build.CNAME}/"
GOOGLE = {st["id"]: st["google"] for st in build.STANDORTE}  # Google-Place-IDs (in STANDORTE)
e = html.escape


def vorlage(st):
    karte = qr_svg(f"{SEITE}?laden={st['id']}#speisekarte", "M", "#3A1531")
    bewertung = qr_svg(f"https://search.google.com/local/writereview?placeid={GOOGLE[st['id']]}", "M", "#3A1531")
    muster = '<div class="muster">ENTWURF</div>' if build.VORSCHAU else ""
    font = lambda n: (HIER / "assets" / n).resolve().as_uri()
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><style>
@font-face{{font-family:Slab;src:url({font("Roboto-Slab-Bold.sub.woff")});font-weight:700}}
@font-face{{font-family:Text;src:url({font("lato-normal.sub.woff")});font-weight:400}}
@font-face{{font-family:Text;src:url({font("lato-bold.sub.woff")});font-weight:700}}
@page{{size:A5;margin:0}}
*{{box-sizing:border-box}}
html,body{{margin:0;width:148mm;height:210mm}}
body{{font-family:Text;color:#3A1531;background:#fff;display:flex;flex-direction:column;position:relative}}
.kopf{{display:flex;align-items:center;gap:4mm;padding:7mm 9mm 5mm}}
.kopf img{{width:19mm;height:19mm}}
.kopf h1{{font:700 9mm/1 Slab;margin:0}}
.kopf p{{margin:1.2mm 0 0;font-size:4mm}}
.teil{{flex:1;display:flex;align-items:center;gap:6mm;padding:6mm 9mm}}
.teil svg{{width:52mm;height:52mm;flex:none;border-radius:3mm}}
.gelb{{background:#FFD21F;border-top:1.5mm solid #3A1531;border-bottom:1.5mm solid #3A1531}}
.gelb svg{{border:2mm solid #fff}}
h2{{font:700 7.4mm/1.1 Slab;margin:0 0 3mm}}
.teil p{{margin:0;font-size:4.3mm;line-height:1.35}}
.sterne{{font-size:8mm;letter-spacing:1mm;color:#C8371A;margin-bottom:2mm}}
.fuss{{padding:4.5mm 9mm 6mm;font-size:3.6mm;display:flex;justify-content:space-between;gap:4mm}}
.fuss b{{font-family:Slab}}
.muster{{background:repeating-linear-gradient(-45deg,#3A1531 0 4mm,#5a2350 4mm 8mm);color:#fff;text-align:center;
  font:700 3.6mm/1 Text;letter-spacing:.3mm;padding:2.2mm 4mm}}
</style></head><body>
{muster}
<div class="kopf"><img src="{(HIER / 'maskottchen' / 'saray-koch-kopf.svg').resolve().as_uri()}" alt="">
  <div><h1>Saray Döner</h1><p>{e(st['name'])} · {e(st['strasse'])}</p></div></div>
<div class="teil gelb">{karte}
  <div><h2>Speisekarte &amp; vorbestellen</h2>
  <p>Code scannen, Gerichte auf den Bestellzettel legen und per WhatsApp vorbestellen – ohne Warten an der Theke.</p></div></div>
<div class="teil">{bewertung}
  <div><div class="sterne">★★★★★</div><h2>Hat’s geschmeckt?</h2>
  <p>Wir freuen uns über Ihre Bewertung bei Google. Danke!</p></div></div>
<div class="fuss"><span><b>Telefon</b> {e(st['tel'])}</span><span>{e(st['kurz'])}</span></div>
</body></html>"""


async def main():
    AUS.mkdir(exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for st in build.STANDORTE:
            datei = AUS / f"_aufsteller-{st['id']}.html"
            datei.write_text(vorlage(st), encoding="utf-8")
            pg = await b.new_page(viewport={"width": 559, "height": 794}, device_scale_factor=2)
            await pg.goto(datei.resolve().as_uri())
            await pg.wait_for_timeout(400)
            await pg.pdf(path=str(AUS / f"aufsteller-{st['id']}.pdf"), format="A5", print_background=True)
            await pg.screenshot(path=str(AUS / f"aufsteller-{st['id']}.png"))
            await pg.close()
            datei.unlink()
            print(AUS / f"aufsteller-{st['id']}.pdf")
        await b.close()

if __name__ == "__main__":
    asyncio.run(main())
