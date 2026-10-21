#!/usr/bin/env python3
"""Automatische Tests für die fertige Seite in docs/.

Aufruf:  python3 tests/test_seite.py
Braucht: pip install playwright && python -m playwright install chromium

Startet einen kleinen Webserver für docs/, öffnet die Seite in Chromium (Handy- und
Desktopgröße) und prüft die wichtigsten Abläufe. Rückgabewert 1, wenn etwas fehlschlägt.
"""
import datetime
import functools
import http.server
import json
import pathlib
import sys
import threading
import traceback
import urllib.parse

from playwright.sync_api import sync_playwright

DOCS = pathlib.Path(__file__).resolve().parent.parent / "docs"
HANDY = {"width": 390, "height": 844}
DESKTOP = {"width": 1440, "height": 900}
# Mittwoch 21.10.2026, 17:45 Uhr: beide Läden offen
ZEIT = datetime.datetime.fromisoformat("2026-10-21T17:45:00+02:00")


class Leise(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def server():
    handler = functools.partial(Leise, directory=str(DOCS))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/"


class Seite:
    """Öffnet die Seite mit fester Uhrzeit und sammelt JavaScript-Fehler."""

    def __init__(self, browser, url, vp=HANDY, locale="de-DE", zeit=ZEIT, regeln=None, mobil=True):
        self.ctx = browser.new_context(viewport=vp, locale=locale, timezone_id="Europe/Berlin",
                                       reduced_motion="reduce", is_mobile=mobil, has_touch=mobil)
        self.p = self.ctx.new_page()
        self.fehler = []
        self.p.on("pageerror", lambda e: self.fehler.append(str(e)))
        self.p.clock.set_fixed_time(zeit)
        status = {"regeln": regeln or []}
        self.p.route("**/status.json", lambda r: r.fulfill(status=200, content_type="application/json",
                                                          body=json.dumps(status)))
        self.p.goto(url)
        self.p.wait_for_timeout(300)

    def js(self, ausdruck):
        return self.p.evaluate(ausdruck)

    def wa_text(self):
        self.p.evaluate("document.getElementById('zettel-whatsapp').addEventListener('click',e=>e.preventDefault())")
        self.p.click("#zettel-whatsapp")
        href = self.p.get_attribute("#zettel-whatsapp", "href")
        return urllib.parse.parse_qs(urllib.parse.urlparse(href).query)["text"][0]

    def zettel_zeilen(self):
        return self.js("[...document.querySelectorAll('.z-eintrag')].map(l=>l.querySelector('.z-name').textContent"
                       "+' | '+l.querySelector('.z-preis').textContent)")

    def schliessen(self):
        assert not self.fehler, f"JavaScript-Fehler: {self.fehler}"
        self.ctx.close()


TESTS = []


def test(f):
    TESTS.append(f)
    return f


@test
def laedt_ohne_fehler(b, url):
    for vp, mobil in ((HANDY, True), (DESKTOP, False)):
        s = Seite(b, url, vp, mobil=mobil)
        assert "Saray Döner" in s.p.title()
        status = s.js("[...document.querySelectorAll('.status-text')].map(x=>x.textContent)")
        assert status and all(t.startswith("Jetzt geöffnet") for t in status), status
        assert s.js("document.querySelectorAll('.gericht').length") >= 130
        breite = s.js("document.documentElement.scrollWidth")
        assert breite <= vp["width"], f"waagrechter Überlauf: {breite}px"
        s.schliessen()


@test
def kategorie_bleibt_markiert(b, url):
    for vp, mobil in ((HANDY, True), (DESKTOP, False)):
        s = Seite(b, url, vp, mobil=mobil)
        ids = s.js("[...document.querySelectorAll('.kategorien a')].map(a=>a.getAttribute('href').slice(1))")
        for gid in ids:
            s.p.click(f'.kategorien a[href="#{gid}"]')
            s.p.wait_for_timeout(150)
            aktiv = s.js("document.querySelector('.kategorien a[aria-current=\"true\"]')?.getAttribute('href')")
            assert aktiv == "#" + gid, f"{vp['width']}px: {gid} geklickt, markiert {aktiv}"
        s.schliessen()


@test
def zettel_mit_wuenschen(b, url):
    s = Seite(b, url)
    s.p.click("#nr-1 .plus")
    s.p.click("#zettel-leiste")
    s.p.click("[data-anpassen]")
    s.p.click('[data-fuell="huhn"]')
    s.p.click("[data-super]")
    s.p.click("[data-kaese]")
    s.p.click('[data-o="s"][data-w="Chili"]')
    s.p.click('[data-o="ohne"][data-w="Zwiebeln"]')
    s.p.click("[data-fertig]")
    assert s.zettel_zeilen() == ["Nr. 33 Hähnchen Super Döner mit Käse | 9,50 €"], s.zettel_zeilen()
    s.p.click("[data-laden=freital]")
    s.p.fill("#abhol-name", "Test")
    text = s.wa_text()
    assert "1× Nr. 33 Hähnchen Super Döner mit Käse, Kräuter- und Chili-Soße, ohne Zwiebeln: 9,50 €" in text, text
    assert "Abholung: heute, so schnell wie möglich" in text and "Name: Test" in text, text
    s.schliessen()


@test
def pizza_groesse_und_extras(b, url):
    s = Seite(b, url)
    s.p.click("#nr-80 .plus")
    s.p.click("#nr-80 .wahl button >> nth=1")       # 30 cm
    s.p.click("#zettel-leiste")
    s.p.click("[data-anpassen]")
    s.p.click('[data-o="ex"][data-w="Salami"]')
    s.p.click('[data-o="ex"][data-w="Paprika"]')
    s.p.click("[data-fertig]")
    assert s.zettel_zeilen() == ["Nr. 80 Pizza Margherita (30 cm) | 11,00 €"], s.zettel_zeilen()
    s.schliessen()


@test
def ohne_fleisch_wird_vegetarisch(b, url):
    s = Seite(b, url)
    s.p.click("#nr-51 .plus")
    s.p.click("#zettel-leiste")
    s.p.click("[data-anpassen]")
    s.p.click('[data-fuell="veg"]')
    assert s.zettel_zeilen() == ["Nr. 53 Dürüm vegetarisch mit Käse | 8,00 €"], s.zettel_zeilen()
    fuellungen = s.js("[...document.querySelectorAll('[data-fuell]')].map(b=>b.dataset.fuell)")
    assert "schnitzel" not in fuellungen and "nuggets" not in fuellungen, fuellungen
    s.schliessen()


@test
def englisch_aber_bestellung_deutsch(b, url):
    s = Seite(b, url, locale="en-GB")
    assert s.js("document.documentElement.lang") == "en"
    assert s.js("document.querySelector('.status-text').textContent").startswith("Open now")
    s.p.click("#nr-1 .plus")
    s.p.click("#zettel-leiste")
    assert s.zettel_zeilen()[0].startswith("No. 1 Döner Kebap"), s.zettel_zeilen()
    s.p.click("[data-laden=altenberg]")
    text = s.wa_text()
    assert "Nr. 1 Döner Kebap, Kräuter-Soße" in text and "Abholung: heute" in text, text
    s.p.click(".zettel-zu")
    s.p.click("#sprache")
    assert s.js("document.documentElement.lang") == "de"
    s.schliessen()


@test
def vorbestellung_nach_ladenschluss(b, url):
    s = Seite(b, url, zeit=datetime.datetime.fromisoformat("2026-10-21T22:30:00+02:00"))
    s.p.click("#nr-1 .plus")
    s.p.click("#zettel-leiste")
    s.p.click("[data-laden=freital]")
    tage = s.js("[...document.getElementById('abhol-tag').options].map(o=>o.text)")
    assert tage[0].startswith("Morgen") and len(tage) >= 10, tage
    assert not s.js("document.getElementById('abhol-hinweis').hidden")
    s.p.select_option("#abhol-tag", index=3)
    text = s.wa_text()
    assert text.startswith("*TEST") or text.startswith("Vorbestellung"), text
    assert "Vorbestellung Saray Döner Freital" in text and "Abholung: Sonntag, 25.10., " in text, text
    s.schliessen()


@test
def verfuegbarkeit(b, url):
    regeln = [{"was": "huhn", "datum": "2026-10-21"}, {"was": "nuggets", "ab": "19:00"},
              {"was": "baguette", "laden": "altenberg"}]
    s = Seite(b, url, regeln=regeln)
    s.p.wait_for_timeout(300)
    assert s.js("document.getElementById('nr-30').classList.contains('nicht-da')")
    assert s.js("document.querySelector('#nr-30 .plus').disabled")
    assert "19 Uhr" in s.js("document.querySelector('#nr-60 .marke-verf').textContent")
    assert s.js("document.querySelector('#nr-150 .marke-verf').textContent").startswith("Altenberg")
    s.p.click("#nr-60 .plus")
    s.p.click("#zettel-leiste")
    s.p.click("[data-laden=freital]")
    s.p.select_option("#abhol-zeit", "heute, so schnell wie möglich")
    assert s.js("document.getElementById('zettel-whatsapp').hidden"), "WhatsApp trotz Sperre sichtbar"
    s.p.select_option("#abhol-zeit", "heute, 19:30 Uhr")
    assert not s.js("document.getElementById('zettel-whatsapp').hidden")
    s.schliessen()


@test
def wie_letztes_mal(b, url):
    s = Seite(b, url)
    s.p.click("#nr-7 .plus")
    s.p.click("#zettel-leiste")
    s.p.click("[data-laden=freital]")
    s.wa_text()
    s.p.click("#zettel-leeren")
    s.p.click("#zettel-leeren")
    assert not s.js("document.getElementById('letzte').hidden")
    s.p.click("#letzte-knopf")
    assert s.zettel_zeilen() == ["Nr. 7 Super Döner mit Käse | 9,50 €"], s.zettel_zeilen()
    s.schliessen()


@test
def zettel_auf_kleinem_handy_schliessbar(b, url):
    s = Seite(b, url, vp={"width": 390, "height": 450})
    for nr in ("1", "26", "51", "7", "37"):
        s.p.click(f"#nr-{nr} .plus")
    s.p.click("#zettel-leiste")
    s.js("document.querySelector('.zettel').scrollTop=99999")
    oben = s.js("document.querySelector('.zettel-zu').getBoundingClientRect().top")
    assert 0 <= oben < 120, f"X nicht sichtbar (top {oben})"
    s.p.click(".zettel-zu")
    assert s.js("document.getElementById('zettel').hidden")
    s.schliessen()


@test
def band_klebt_mit_weisser_flaeche(b, url):
    s = Seite(b, url)
    s.js("window.scrollTo(0,3000)")
    s.p.mouse.wheel(0, 1)
    s.p.wait_for_timeout(300)
    assert s.js("document.querySelector('.kategorien').classList.contains('klebt')")
    assert s.js("document.querySelectorAll('.deckel-oben').length") == 1
    s.js("window.scrollTo(0,0)")
    s.p.mouse.wheel(0, -1)
    s.p.wait_for_timeout(300)
    assert s.js("document.querySelectorAll('.deckel-oben').length") == 0
    s.schliessen()


def main():
    srv, url = server()
    ok = 0
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for t in TESTS:
            try:
                t(b, url)
                ok += 1
                print(f"  ok      {t.__name__}")
            except Exception:
                print(f"  FEHLER  {t.__name__}")
                traceback.print_exc()
        b.close()
    srv.shutdown()
    print(f"{ok} von {len(TESTS)} Tests bestanden")
    return 0 if ok == len(TESTS) else 1


if __name__ == "__main__":
    sys.exit(main())
