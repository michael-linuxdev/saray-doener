#!/usr/bin/env python3
"""Erzeugt die PNG-Fassungen des Maskottchens (inkl. Favicon) aus den SVGs.

Braucht Playwright mit Chromium:  pip install playwright && playwright install chromium
Aufruf nach  python3 maskottchen.py:  python3 png_export.py
"""
import asyncio, pathlib
from playwright.async_api import async_playwright

D = pathlib.Path(__file__).parent / "maskottchen"
JOBS = [("saray-koch.svg", 430, 470, 3, "saray-koch.png"),
        ("saray-koch-kopf.svg", 200, 200, 3.6, "saray-koch-kopf.png"),
        ("saray-koch-kopf.svg", 96, 96, 1, "favicon-96.png")]


# App-Symbole (Home-Bildschirm): Kopf auf gelbem Grund mit Rand, damit auch runde/abgerundete Masken passen
APP = [("app-180.png", 180), ("app-192.png", 192), ("app-512.png", 512)]


async def app_symbole(b):
    for name, groesse in APP:
        vorlage = D / "_app_vorlage.html"
        vorlage.write_text('<html><body style="margin:0;background:#FFD21F;display:grid;place-items:center;height:100vh">'
                           '<img src="saray-koch-kopf.svg" style="width:78%;height:78%"></body></html>')
        pg = await b.new_page(viewport={"width": groesse, "height": groesse})
        await pg.goto(vorlage.resolve().as_uri())
        await pg.wait_for_timeout(300)
        await pg.screenshot(path=str(D / name))
        await pg.close()
        vorlage.unlink()


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for svg, w, h, dpr, png in JOBS:
            pg = await b.new_page(viewport={"width": w, "height": h}, device_scale_factor=dpr)
            await pg.goto((D / svg).resolve().as_uri())
            await pg.wait_for_timeout(300)
            await pg.screenshot(path=str(D / png), omit_background=True)
            await pg.close()
        await app_symbole(b)
        await b.close()

asyncio.run(main())
