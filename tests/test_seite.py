#!/usr/bin/env python3
"""Automatische Tests für die fertige Seite.

Aufruf:  python3 tests/test_seite.py            -> baut eine Standard-Seite (ohne Chef-App-Änderungen) in einen
                                                   Testordner und prüft dort alle Abläufe
         python3 tests/test_seite.py --echt     -> prüft nur, dass die echte Seite in docs/ fehlerfrei lädt
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
import os
import subprocess
import tempfile
import traceback
import urllib.parse

from playwright.sync_api import sync_playwright

REPO = pathlib.Path(__file__).resolve().parent.parent
DOCS = REPO / "docs"   # wird in main() auf die Standard-Seite im Testordner umgestellt
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

    def __init__(self, browser, url, vp=HANDY, locale="de-DE", zeit=ZEIT, regeln=None, mobil=True, hand_tipp=False):
        self.ctx = browser.new_context(viewport=vp, locale=locale, timezone_id="Europe/Berlin",
                                       reduced_motion="reduce", is_mobile=mobil, has_touch=mobil)
        self.p = self.ctx.new_page()
        self.fehler = []
        self.p.on("pageerror", lambda e: self.fehler.append(str(e)))
        self.p.clock.set_fixed_time(zeit)
        if not hand_tipp:   # Linkshänder-Hinweis beim ersten „+“ in den übrigen Tests unterdrücken
            self.p.add_init_script("try{localStorage.setItem('saray-hand-gefragt','1')}catch(e){}")
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
    s.p.click("#sprachen-menu [data-sp=de]")
    assert s.js("document.documentElement.lang") == "de"
    s.schliessen()


@test
def weitere_sprachen(b, url):
    s = Seite(b, url)
    erwartet = {"cs": "Nyní otevřeno", "tr": "Şu an açık", "ru": "Открыто", "ar": "مفتوح الآن"}
    for code, anfang in erwartet.items():
        s.p.click("#sprache")
        s.p.click(f"#sprachen-menu [data-sp={code}]")
        s.p.wait_for_function(f"document.documentElement.lang==='{code}'")
        s.p.wait_for_timeout(200)
        status = s.js("document.querySelector('.status-text').textContent")
        assert status.startswith(anfang), (code, status)
        rtl = s.js("document.documentElement.dir")
        assert (rtl == "rtl") == (code == "ar"), (code, rtl)
    s.p.click("#nr-1 .plus")
    s.p.click("#zettel-leiste")
    s.p.click("[data-laden=altenberg]")
    text = s.wa_text()
    assert "Nr. 1 Döner Kebap" in text and "Abholung: heute" in text, text
    s.p.click(".zettel-zu")
    s.p.click("#sprache")
    s.p.click("#sprachen-menu [data-sp=de]")
    assert s.js("document.documentElement.dir") in ("", "ltr")
    s.schliessen()



@test
def sprachknopf_mit_globus(b, url):
    s = Seite(b, url)
    assert s.p.text_content(".kopf-nav a[href='#speisekarte']") == "Menü"
    assert s.p.text_content("#sprache .sp-code") == "DE" and s.p.locator("#sprache .globus").count() == 1
    assert s.p.locator("#sprachen-zeile").count() == 0
    s.p.click("#sprache")
    s.p.click("#sprachen-menu [data-sp=tr]")
    s.p.wait_for_function("document.documentElement.lang==='tr'")
    assert s.p.text_content("#sprache .sp-code") == "TR"
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
def sperre_fuer_gewaehlten_laden(b, url):
    s = Seite(b, url + "?laden=freital", regeln=[{"was": "nuggets", "laden": "freital"}])
    s.p.wait_for_timeout(300)
    assert s.js("document.getElementById('nr-60').classList.contains('nicht-da')"), "Nuggets in Freital nicht ausgegraut"
    assert s.js("document.querySelector('#nr-60 .plus').disabled")
    assert s.js("document.querySelector('#nr-60 .marke-verf').textContent") == "nicht verfügbar in Freital"
    s.p.click("#nr-1 .plus")
    s.p.click("#zettel-leiste")
    s.p.click("[data-laden=altenberg]")
    s.p.click(".zettel-zu")
    assert not s.js("document.getElementById('nr-60').classList.contains('nicht-da')"), "in Altenberg gesperrt"
    s.p.click("#nr-60 .plus")
    s.p.click("#zettel-leiste")
    s.p.click("[data-laden=freital]")
    assert s.js("document.getElementById('zettel-whatsapp').hidden")
    assert s.js("document.getElementById('zettel-kopieren').disabled")
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


@test
def home_bildschirm(b, url):
    s = Seite(b, url)
    m = s.js("fetch(document.querySelector('link[rel=manifest]').href).then(r=>r.json())")
    assert m["short_name"] == "Saray" and m["display"] == "standalone", m
    for icon in m["icons"] + [{"src": s.js("document.querySelector('link[rel=apple-touch-icon]').getAttribute('href')")}]:
        status = s.js(f"fetch('{icon['src']}').then(r=>r.status)")
        assert status == 200, f"{icon['src']}: {status}"
    s.schliessen()


@test
def qr_waehlt_laden_vor(b, url):
    s = Seite(b, url + "?laden=altenberg")
    s.p.click("#nr-1 .plus")
    s.p.click("#zettel-leiste")
    assert s.js("document.querySelector('[data-laden=altenberg]').getAttribute('aria-pressed')") == "true"
    s.schliessen()


@test
def laden_karte_springt_zu_zeiten(b, url):
    for vp, mobil in ((HANDY, True), (DESKTOP, False)):
        s = Seite(b, url, vp, mobil=mobil)
        for laden in ("freital", "altenberg"):
            s.js("window.scrollTo(0,0)")
            s.p.click(f'.schild:has(a[href="#ort-{laden}"]) .schild-adresse', force=True)
            s.p.wait_for_timeout(300)
            top = s.js(f"document.getElementById('ort-{laden}').getBoundingClientRect().top")
            assert 0 <= top < 120, f"{vp['width']}px {laden}: Abschnitt nicht oben (top {top})"
        # Telefon-Knopf bleibt ein Anruf-Link und liegt über der Karte
        s.js("window.scrollTo(0,0)")
        s.p.wait_for_timeout(100)
        ziel = s.js("(()=>{const t=document.querySelector('.schild-tel');t.scrollIntoView({block:'center'});const r=t.getBoundingClientRect();"
                    "return document.elementFromPoint(r.x+r.width/2,r.y+r.height/2).closest('a').getAttribute('href')})()")
        assert ziel.startswith("tel:"), ziel
        s.schliessen()


@test
def tastatur_bleibt_im_zettel(b, url):
    s = Seite(b, url, vp=DESKTOP, mobil=False)
    s.p.click("#nr-1 .plus")
    s.p.click("#zettel-leiste")
    for _ in range(40):
        s.p.keyboard.press("Tab")
        assert s.js("!!document.activeElement.closest('#zettel')"), "Fokus hat den Bestellzettel verlassen"
    s.p.keyboard.press("Escape")
    assert s.js("document.getElementById('zettel').hidden")
    s.schliessen()


@test
def sammelbestellung(b, url):
    geteilt = "window.__geteilt=[];navigator.share=function(d){window.__geteilt.push(d.text);return Promise.resolve();};0"
    # Michael startet die Sammelbestellung
    m = Seite(b, url)
    m.js(geteilt)
    m.p.click("#nr-1 .plus")
    m.p.click("[data-sammel-start]")
    m.p.fill("#sammel-name", "Michael")
    m.p.click("#sammel-knoepfe >> text=Einladung teilen")
    einladung = m.js("window.__geteilt[0]")
    link = einladung.split("\n")[-1]
    assert "#sammel=" in link, einladung
    # Anna öffnet die Einladung auf ihrem Handy
    a = Seite(b, link.replace(url.rstrip("/"), url.rstrip("/")))
    a.js(geteilt)
    assert not a.js("document.getElementById('sammel-band').hidden"), "Sammel-Hinweis fehlt"
    assert "Michael" in a.p.text_content("#sammel-titel")
    a.p.click("#sammel-knoepfe >> text=Los geht")
    a.p.click("#nr-7 .plus")
    a.p.click("#zettel-leiste")
    a.p.click("[data-anpassen]")
    a.p.click('[data-o="ohne"][data-w="Zwiebeln"]')
    a.p.click("[data-fertig]")
    assert a.js("document.getElementById('zettel-whatsapp').hidden"), "Teilnehmerin soll nicht selbst beim Laden bestellen"
    assert not a.js("document.querySelector('[data-laden=freital]').offsetParent"), "Ladenwahl sollte für Teilnehmer ausgeblendet sein"
    a.p.click("#sammel-teil")
    assert "Namen" in a.p.text_content("#zettel-meldung")
    a.p.fill("#abhol-name", "Anna")
    a.p.click("#sammel-teil")
    teil = a.js("window.__geteilt[0]")
    assert "Nr. 7 Super Döner mit Käse" in teil and "ohne Zwiebeln" in teil, teil
    teil_link = teil.split("\n")[-1]
    assert "#teil=" in teil_link, teil
    a.schliessen()
    # Michael öffnet Annas Teil
    m.p.goto(teil_link)
    m.p.wait_for_timeout(300)
    assert "Anna" in m.p.text_content("#sammel-titel")
    assert "Super Döner mit Käse" in m.p.text_content("#sammel-inhalt")
    m.p.click("#sammel-knoepfe >> text=Zur Bestellung hinzufügen")
    assert not m.js("location.hash"), "Link-Daten nicht aus der Adresse entfernt"
    m.p.click("[data-laden=freital]")
    text = m.wa_text()
    assert "1× Nr. 1 Döner Kebap, Kräuter-Soße: 7,00 €" in text, text
    assert "1× Nr. 7 Super Döner mit Käse, Kräuter-Soße, ohne Zwiebeln (für Anna): 9,50 €" in text, text
    assert "Summe: 16,50 €" in text, text
    # derselbe Link noch einmal: Warnung
    m.p.goto(teil_link)
    m.p.wait_for_timeout(300)
    assert "schon hinzugefügt" in m.p.text_content("#sammel-inhalt")
    m.schliessen()


@test
def linkshaender_kein_hinweis_beim_plus(b, url):
    """Linkshänder-Modus gibt es nur unten in der Fußzeile – kein Hinweis beim ersten „+“."""
    s = Seite(b, url, hand_tipp=True)
    s.p.click("#nr-1 .plus")
    assert s.js("document.getElementById('hand-tipp').hidden"), "Hinweis beim ersten Plus"
    s.p.click("footer [data-hand]")
    assert s.js("document.documentElement.classList.contains('links')")
    s.schliessen()


@test
def linkshaender(b, url):
    s = Seite(b, url)
    s.p.click(".fuss [data-hand]")
    assert s.js("document.documentElement.classList.contains('links')")
    plus = s.js("document.querySelector('#nr-1 .plus').getBoundingClientRect().left")
    assert plus < 60, f"Plus nicht links ({plus})"
    # Empfehlungs-/Beliebt-Karten bleiben unverändert (sonst verdeckt das Plus den Preis)
    tipp = s.js("(()=>{const c=document.querySelector('.tipps:not(.tipps-empfehlung) .tipp'),p=c.querySelector('.plus').getBoundingClientRect(),r=c.getBoundingClientRect();return p.right>r.right-30})()")
    assert tipp, "Plus der Beliebt-Karte nicht mehr rechts"
    assert s.js("getComputedStyle(document.getElementById('nach-oben')).left") == "14px", "Nach-oben-Pfeil nicht links"
    s.p.reload()
    s.p.wait_for_timeout(200)
    assert s.js("document.documentElement.classList.contains('links')"), "Linkshänder-Modus nicht gemerkt"
    s.schliessen()


# WCAG-Grundprüfung: Kontrast (4,5:1 bzw. 3:1 für große Schrift), Namen für Links/Knöpfe, Alt-Texte,
# Beschriftungen für Felder, Tippziele ≥ 24 px, Überschriften-Reihenfolge, Sprache
WCAG_PRUEF = r"""
(()=>{
 function rgb(s){const m=s.match(/rgba?\(([^)]+)\)/);if(!m)return null;const p=m[1].split(/[ ,\/]+/).filter(Boolean).map(Number);return {r:p[0],g:p[1],b:p[2],a:p.length>3?p[3]:1};}
 function lum(c){return [c.r,c.g,c.b].map(v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)}).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);}
 function ratio(a,b){const x=lum(a),y=lum(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);}
 function bg(el){while(el){const cs=getComputedStyle(el);if(cs.backgroundImage!=='none'&&!el.matches('body'))return null;const c=rgb(cs.backgroundColor);if(c&&c.a>0.95)return c;el=el.parentElement;}return {r:255,g:255,b:255,a:1};}
 const res={kontrast:[],ohneName:[],ohneAlt:[],ohneLabel:[],klein:[],ueberschriften:[]};
 const seen=new Set();
 const tw=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;
 while(n=tw.nextNode()){const t=n.textContent.trim();if(!t)continue;const el=n.parentElement;
   if(!el||el.closest('[hidden],script,style,.sr-only,[aria-hidden=true]')||!el.offsetParent&&getComputedStyle(el).position!=='fixed')continue;
   const cs=getComputedStyle(el);if(cs.visibility==='hidden'||+cs.opacity<.5)continue;
   const fg=rgb(cs.color),b=bg(el);if(!fg||!b)continue;
   const r=ratio(fg,b),gr=parseFloat(cs.fontSize),fett=+cs.fontWeight>=700,gross=gr>=24||(fett&&gr>=18.66);
   if(r<(gross?3:4.5)){const k=el.className+'|'+cs.color+'|'+cs.backgroundColor;if(!seen.has(k)){seen.add(k);res.kontrast.push({text:t.slice(0,30),ratio:r.toFixed(2),soll:gross?3:4.5,el:el.tagName+'.'+el.className,fg:cs.color,bg:`rgb(${b.r},${b.g},${b.b})`});}}
 }
 document.querySelectorAll('a,button,[role=button]').forEach(e=>{if(e.closest('[hidden]'))return;const name=(e.getAttribute('aria-label')||e.textContent||e.title||'').trim();if(!name)res.ohneName.push(e.outerHTML.slice(0,90));
   const r=e.getBoundingClientRect();if(e.offsetParent&&(r.width<24||r.height<24)&&!e.closest('p,li.varianten,address,figcaption,.fuss'))res.klein.push((e.textContent||e.getAttribute('aria-label')||'').trim().slice(0,25)+' '+Math.round(r.width)+'x'+Math.round(r.height));});
 document.querySelectorAll('img').forEach(i=>{if(!i.hasAttribute('alt'))res.ohneAlt.push(i.src.slice(-40));});
 document.querySelectorAll('input,select,textarea').forEach(i=>{if(i.type==='hidden')return;const ok=i.getAttribute('aria-label')||(i.id&&document.querySelector('label[for="'+i.id+'"]'))||i.closest('label');if(!ok)res.ohneLabel.push(i.outerHTML.slice(0,80));});
 let last=1;document.querySelectorAll('h1,h2,h3,h4,h5,h6').forEach(h=>{const l=+h.tagName[1];if(l>last+1)res.ueberschriften.push(h.tagName+': '+h.textContent.trim().slice(0,30)+' (nach h'+last+')');last=l;});
 res.lang=document.documentElement.lang;res.h1=document.querySelectorAll('h1').length;
 return res;})()
"""


@test
def barrierefreiheit(b, url):
    for vp, mobil in ((HANDY, True), (DESKTOP, False)):
        s = Seite(b, url, vp, mobil=mobil, regeln=[{"was": "huhn"}])
        s.p.click("#nr-1 .plus")
        s.p.click("#zettel-leiste")
        s.p.click("[data-anpassen]")
        r = s.js(WCAG_PRUEF)
        for k in ("kontrast", "ohneName", "ohneAlt", "ohneLabel", "klein", "ueberschriften"):
            assert not r[k], f"{vp['width']}px {k}: {r[k]}"
        assert r["lang"] == "de" and r["h1"] == 1, r
        s.schliessen()
    ctx, p, fehler = chef_oeffnen(b, url, gespeichert=[])
    r = p.evaluate(WCAG_PRUEF)
    for k in ("kontrast", "ohneName", "ohneAlt", "ohneLabel", "klein"):
        assert not r[k], f"Chef-App {k}: {r[k]}"
    ctx.close()


FOTO_HOCHGELADEN = []


def chef_oeffnen(b, url, anp=None, gespeichert=None, vorher=None, tour=False):
    """Öffnet die Chef-App mit nachgebildeter GitHub-API (es wird nichts wirklich gespeichert)."""
    import base64
    ctx = b.new_context(viewport=HANDY, locale="de-DE", timezone_id="Europe/Berlin", is_mobile=True, has_touch=True)
    p = ctx.new_page()
    fehler = []
    p.on("pageerror", lambda e: fehler.append(str(e)))
    p.clock.set_fixed_time(ZEIT)
    inhalt = base64.b64encode(json.dumps(anp or {}).encode()).decode()

    def github(route):
        r = route.request
        if "daten/fotos/" in r.url:
            if r.method == "PUT":
                body = json.loads(r.post_data)
                FOTO_HOCHGELADEN.append((r.url.split("/contents/")[1], body["message"], len(body["content"])))
                route.fulfill(status=200, json={"content": {"sha": "f1"}, "commit": {"sha": "c1"}})
            else:
                route.fulfill(status=404, json={"message": "Not Found"})
        elif "/commits?" in r.url:
            route.fulfill(status=200, json=[{"sha": "c2", "commit": {"message": "Chef-App: 1 Änderung(en)", "author": {"date": "2026-10-21T15:00:00Z"}}},
                                            {"sha": "c1", "commit": {"message": "vorher", "author": {"date": "2026-10-20T15:00:00Z"}}}])
        elif "ref=c1" in r.url:
            route.fulfill(status=200, json={"sha": "x", "content": base64.b64encode(json.dumps(vorher or {}).encode()).decode()})
        elif r.method == "PUT":
            body = json.loads(r.post_data)
            assert r.headers.get("authorization") == "Bearer TESTTOKEN", r.headers
            gespeichert.append(json.loads(base64.b64decode(body["content"]).decode("utf-8")))
            route.fulfill(status=200, json={"content": {"sha": "neu"}, "commit": {"sha": "c1"}})
        elif "/actions/runs" in r.url:
            route.fulfill(status=200, json={"workflow_runs": [{"head_sha": "c1", "status": "completed", "conclusion": "success"}]})
        else:
            route.fulfill(status=200, json={"sha": "alt", "content": inhalt})
    p.route("https://api.github.com/**", github)
    if not tour:
        p.add_init_script("try{localStorage.setItem('saray-chef-tour','1')}catch(e){}")
    p.goto(url + "chef/#token=%20TESTTOKEN")   # Leerzeichen beim Kopieren wird entfernt
    p.wait_for_selector("nav.tabs:not([hidden])")
    return ctx, p, fehler


@test
def chef_app_aenderungen(b, url):
    gespeichert = []
    ctx, p, fehler = chef_oeffnen(b, url, gespeichert=gespeichert)
    assert "token" not in p.url, "Token steht noch in der Adresse"
    # Heute: Hähnchen aus (nur Freital), Nuggets ab 17 Uhr jeden Tag
    p.click(".wahl button:text-is('Freital')")
    p.locator(".karte", has=p.locator("h3", has_text="Hähnchen")).locator("text=Heute aus").click()
    p.locator(".karte", has=p.locator("h3", has_text="Nuggets")).locator("text=Ab Uhrzeit …").click()
    p.select_option("#ab-zeit", "17:00")
    p.check("#ab-immer")
    p.click("text=Übernehmen")
    # Hinweis (unter „Mehr“)
    p.click('nav.tabs [data-tab="heute"]')
    p.fill("#h-text", "Heute Lieferung ab 18 Uhr")
    p.click("text=Hinweis hinzufügen")
    # Karte: Preis Nr. 1 ändern, Nr. 8 löschen, neues Gericht
    p.click('nav.tabs [data-tab="karte"]')
    p.click('.liste-gericht[data-k="1"]')
    p.fill("#b-preis-0", "7.5")
    p.click("text=Übernehmen")
    p.click('.liste-gericht[data-k="8"]')
    p.click(".blatt >> text=Löschen")
    p.click("text=+ Neues Gericht")
    p.select_option("#b-ab", index=0)
    p.fill("#b-nr", "13a")
    p.fill("#b-name", "Döner Spezial")
    p.fill("#b-desc", "Fladenbrot, Fleisch, Salat, Feta")
    p.fill("#b-preis-0", "9")
    p.click("text=Übernehmen")
    p.click("text=+ Neues Gericht")
    p.fill("#b-nr", "2")
    p.fill("#b-name", "Doppelte Nummer")
    p.fill("#b-preis-0", "5")
    p.click("text=Übernehmen")
    assert "schon vergeben" in p.text_content(".blatt .fehler")
    p.click(".blatt >> text=Abbrechen")
    # Zeiten: Altenberg samstags ab 11 Uhr
    p.click('nav.tabs [data-tab="zeiten"]')
    p.select_option(".karte:has(h3:text('Altenberg')) select[aria-label='Sa von']", "11:00")
    assert "nicht gespeichert" in p.text_content("#speichern-text")
    p.click("#speichern-knopf")
    p.wait_for_selector(".status.ok >> text=Online")
    assert len(gespeichert) == 1, gespeichert
    d = gespeichert[0]
    assert d["gerichte"] == {"1": {"preise": ["7,50"]}}, d
    assert d["geloescht"] == ["8"], d
    assert d["neu"] == [{"gruppe": "doener", "abschnitt": "Döner", "nr": "13a", "name": "Döner Spezial",
                         "desc": "Fladenbrot, Fleisch, Salat, Feta", "preise": ["9,00"], "seit": "2026-10-21"}], d
    assert d["zeiten"] == {"altenberg": {"6": ["11:00", "21:00"]}}, d
    assert {"was": "huhn", "datum": "2026-10-21", "laden": "freital"} in d["verfuegbarkeit"], d
    assert {"was": "nuggets", "ab": "17:00", "laden": "freital"} in d["verfuegbarkeit"], d
    assert d["hinweise"] == [{"text": "Heute Lieferung ab 18 Uhr", "von": "2026-10-21", "bis": "2026-10-21"}], d
    assert not fehler, fehler
    ctx.close()
    # Das Gespeicherte muss sich fehlerfrei bauen lassen und auf der Seite ankommen
    import subprocess, tempfile, os
    with tempfile.TemporaryDirectory() as tmp:
        datei = pathlib.Path(tmp) / "anp.json"
        datei.write_text(json.dumps(d))
        root = REPO
        out = subprocess.run([sys.executable, "-c", f"import build; build.bauen(ziel={str(pathlib.Path(tmp) / 'docs')!r})"],
                             cwd=root, env=dict(os.environ, SARAY_ANPASSUNGEN=str(datei)), capture_output=True, text=True)
        assert out.returncode == 0 and "WARNUNG" not in out.stdout, out.stdout + out.stderr
        seite = (pathlib.Path(tmp) / "docs" / "index.html").read_text()
        assert 'id="nr-8"' not in seite and "Döner Spezial" in seite and 'data-p="750"' in seite
        assert "Sa–So 11–21 Uhr" in seite and "Heute Lieferung ab 18 Uhr" in seite


@test
def chef_app_standard_wiederherstellen(b, url):
    gespeichert = []
    ctx, p, fehler = chef_oeffnen(b, url, anp={"gerichte": {"1": {"preise": ["9,99"]}}, "geloescht": ["8"]}, gespeichert=gespeichert)
    p.click('nav.tabs [data-tab="karte"]')
    assert "9,99" in p.text_content('.liste-gericht[data-k="1"]')
    assert "gelöscht" in p.text_content('.liste-gericht[data-k="8"]')
    p.click('nav.tabs [data-tab="mehr"]')
    p.click('[data-seite="gefahr"]')
    p.click("text=Alles auf Standard zurücksetzen")
    p.click(".blatt >> text=Ja, zurücksetzen")
    p.wait_for_selector(".status.ok")
    assert list(gespeichert[0]) == ["preisverlauf"] and gespeichert[0]["preisverlauf"][0]["neu"] == ["7,00"], gespeichert  # Zurücksetzen landet im Preis-Verlauf
    assert not fehler, fehler
    ctx.close()


@test
def allergene_und_barzahlung(b, url):
    s = Seite(b, url)
    assert s.js("document.querySelectorAll('.kennz').length") >= 14
    assert s.js("document.querySelector('#doener .kennz').textContent").replace("\xa0", " ").startswith("Inhaltsstoffe 1, 7, 8, 9 · Allergene a, b, c, f, g")
    assert not s.js("document.getElementById('allergene').open")
    s.p.click("#doener .kennz a")
    s.p.wait_for_timeout(200)
    assert s.js("document.getElementById('allergene').open")
    assert "Süßmolkepulver" in s.p.text_content("#allergene")
    assert "h = Fisch" in s.p.text_content("#allergene").replace("\xa0", " ")
    assert "enthält Fisch (h)" in s.p.text_content("#nr-87")
    assert "inkl. MwSt." in s.p.text_content("#speisekarte")
    assert s.js("document.querySelectorAll('.ort .bar').length") == 2
    # Bestellen: „nur bar“ im Zettel, nach WhatsApp der Hinweis mit Telefonnummer
    s.p.click("#nr-1 .plus")
    s.p.click("#zettel-leiste")
    assert "nur bar" in s.p.text_content(".zettel-bar")
    s.p.click('[data-laden="freital"]')
    assert s.js("document.getElementById('wa-gesendet').hidden")
    s.wa_text()
    assert not s.js("document.getElementById('wa-gesendet').hidden")
    assert s.p.get_attribute("#wa-gesendet a", "href") == "tel:+4935127676660"
    s.schliessen()


def bauen_mit(anp, ordner, env=None):
    datei = pathlib.Path(ordner) / "anp.json"
    datei.write_text(json.dumps(anp))
    out = subprocess.run([sys.executable, "-c", f"import build; build.bauen(ziel={str(pathlib.Path(ordner) / 'docs')!r})"],
                         cwd=REPO, env=dict(os.environ, SARAY_ANPASSUNGEN=str(datei), SARAY_HEUTE="2026-10-21", **(env or {})), capture_output=True, text=True)
    assert out.returncode == 0 and "WARNUNG" not in out.stdout, out.stdout + out.stderr
    handler = functools.partial(Leise, directory=str(pathlib.Path(ordner) / "docs"))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/"


@test
def besondere_tage_und_wartezeit(b, url):
    with tempfile.TemporaryDirectory() as tmp:
        srv, u = bauen_mit({"sonderzeiten": {"2026-10-20": {"freital": None}, "2026-10-21": {"freital": None},
                                             "2026-10-22": {"freital": ["12:00", "15:00"]}},
                            "wartezeit": {"altenberg": {"datum": "2026-10-21", "min": 30}}}, tmp)
        seite = (pathlib.Path(tmp) / "docs" / "index.html").read_text()
        assert 'data-datum="2026-10-20"' not in seite, "vergangener Tag steht noch drin"
        assert '"specialOpeningHoursSpecification"' in seite
        s = Seite(b, u)
        st = s.js("Object.fromEntries([...document.querySelectorAll('.schild [data-status]')].map(x=>[x.dataset.status,x.textContent]))")
        assert st["freital"].startswith("Geschlossen, öffnet morgen um 12 Uhr"), st
        assert "Wartezeit ca. 30 Min." in st["altenberg"], st
        s.p.click("#nr-1 .plus")
        s.p.click("#zettel-leiste")
        s.p.click('[data-laden="altenberg"]')
        zeiten = s.js("[...document.querySelectorAll('#abhol-zeit option')].map(o=>o.value)")
        assert zeiten[0] == "heute, so schnell wie möglich" and zeiten[1] == "heute, 18:45 Uhr", zeiten
        assert "frühestens in ca. 50 Minuten" in s.p.text_content("#abhol-hinweis")
        s.p.click('[data-laden="freital"]')
        tage = s.js("[...document.querySelectorAll('#abhol-tag option')].map(o=>o.value)")
        assert tage[0] == "2026-10-22", tage
        zeiten = s.js("[...document.querySelectorAll('#abhol-zeit option')].map(o=>o.value)")
        assert zeiten[0].endswith("12:15 Uhr") and zeiten[-1].endswith("14:45 Uhr"), zeiten
        s.schliessen()
        srv.shutdown()


@test
def chef_app_wartezeit_tage_rueckgaengig(b, url):
    gespeichert = []
    ctx, p, fehler = chef_oeffnen(b, url, anp={"geloescht": ["8"]}, gespeichert=gespeichert, vorher={"hinweise": []})
    p.locator(".karte", has=p.locator("h3", has_text="Wartezeit")).locator("button", has_text="+30 Min.").first.click()
    p.click('nav.tabs [data-tab="zeiten"]')
    p.fill("#s-datum", "2026-12-24")
    p.click(".wahl >> text=Freital")
    p.click("text=Andere Zeiten")
    p.select_option("#s-von", "10:00")
    p.select_option("#s-bis", "14:00")
    p.click("text=Tag hinzufügen")
    p.fill("#s-datum", "2026-12-25")
    p.click(".wahl >> text=Beide")
    p.click(".wahl button:text-is('Geschlossen')")
    p.click("text=Tag hinzufügen")
    assert "24.12. Freital: 10:00–14:00 Uhr" in p.text_content("#app")
    p.click("#speichern-knopf")
    p.wait_for_selector(".status.ok >> text=Online")
    d = gespeichert[-1]
    assert d["wartezeit"] == {"freital": {"datum": "2026-10-21", "min": 30}}, d
    assert d["sonderzeiten"] == {"2026-12-24": {"freital": ["10:00", "14:00"]},
                                 "2026-12-25": {"freital": None, "altenberg": None}}, d
    # Rückgängig: holt den Stand vor der letzten Speicherung
    p.click('nav.tabs [data-tab="mehr"]')
    p.click('[data-seite="rueckgaengig"]')
    p.click("text=Rückgängig machen …")
    p.click(".blatt >> text=Ja, rückgängig")
    p.wait_for_selector(".status.ok >> text=Online")
    assert gespeichert[-1] == {}, gespeichert[-1]
    assert not fehler, fehler
    ctx.close()


@test
def sonderaktion_auf_der_seite(b, url):
    with tempfile.TemporaryDirectory() as tmp:
        srv, u = bauen_mit({"aktionen": [
            {"name": "Döner 5 €", "von": "2026-10-20", "bis": "2026-10-25", "preise": {"1": ["5,00"], "80": ["5,00", "6,00"]}},
            {"name": "Dürüm-Donnerstag", "von": "2026-10-20", "bis": "2026-10-30", "tage": [4], "laden": "altenberg", "preise": {"50": ["6,00"]}},
            {"name": "Vorbei", "von": "2026-10-01", "bis": "2026-10-05", "preise": {"1": ["1,00"]}}]}, tmp)
        s = Seite(b, u)
        assert "Aktion 5,00 €" in s.p.text_content("#nr-1 .marke-aktion")
        assert s.js("document.querySelector('#nr-1 .preis').classList.contains('preis-alt')")
        assert "5,00 € / 6,00 €" in s.p.text_content("#nr-80 .marke-aktion")
        assert not s.js("!!document.querySelector('#nr-50 .marke-aktion')"), "Donnerstags-Aktion schon am Mittwoch"
        baender = s.js("[...document.querySelectorAll('.hinweis-band:not([hidden])')].map(x=>x.textContent)")
        assert any("Aktion: Döner 5 € – bis 25.10." in x for x in baender), baender
        assert not any("Vorbei" in x for x in baender)
        s.p.click("#nr-1 .plus")
        s.p.click("#nr-50 .plus")
        s.p.click("#zettel-leiste")
        s.p.click('[data-laden="altenberg"]')
        s.p.select_option("#abhol-tag", "2026-10-22")
        text = s.wa_text()
        assert "Nr. 1 Döner Kebap, Kräuter-Soße: 5,00 € (Aktion)" in text, text
        assert "Nr. 50 Dürüm, Kräuter-Soße: 6,00 € (Aktion)" in text, text
        assert "Summe: 11,00 €" in text, text
        s.p.select_option("#abhol-tag", "2026-10-23")
        text = s.wa_text()
        assert "Nr. 50 Dürüm, Kräuter-Soße: 8,00 €" in text and "Summe: 13,00 €" in text, text
        s.schliessen()
        srv.shutdown()


@test
def chef_app_aktion_und_preisstaende(b, url):
    gespeichert = []
    ctx, p, fehler = chef_oeffnen(b, url, anp={"gerichte": {"1": {"preise": ["7,50"]}}}, gespeichert=gespeichert)
    p.click('nav.tabs [data-tab="preise"]')
    p.click("text=Heutige Preise als Stand festlegen")
    assert "Stand 21.10.2026" in p.text_content("#app")
    p.click('nav.tabs [data-tab="karte"]')
    p.click('.liste-gericht[data-k="1"]')
    p.locator(".frueher .reihe", has_text="Stand 01.02.2024").locator("button").click()
    assert p.input_value("#b-preis-0") == "7,00"
    p.click(".blatt >> text=Übernehmen >> nth=-1")
    p.click("text=+ Neue Aktion")
    p.fill("#a-name", "Dürüm 6 €")
    p.fill("#a-such", "Dürüm")
    p.locator(".blatt .liste-gericht", has_text="Dürüm").first.click()
    p.fill("[data-ak='50']", "6")
    p.click(".blatt >> text=Übernehmen")
    assert "Dürüm 6 €" in p.text_content("#app")
    p.click("#speichern-knopf")
    p.wait_for_selector(".status.ok >> text=Online")
    d = gespeichert[-1]
    assert "gerichte" not in d, d
    assert d["staende"][0]["name"] == "Stand 21.10.2026" and d["staende"][0]["preise"]["1"] == ["7,50"], d["staende"]
    assert d["aktionen"] == [{"name": "Dürüm 6 €", "von": "2026-10-21", "bis": "2026-10-27", "preise": {"50": ["6,00"]}}], d["aktionen"]
    assert not fehler, fehler
    ctx.close()
    with tempfile.TemporaryDirectory() as tmp:
        srv, u = bauen_mit(d, tmp)
        srv.shutdown()


@test
def vegetarisch_filtern(b, url):
    s = Seite(b, url)
    assert s.js("!!document.querySelector('#nr-3 svg.veg')") and not s.js("!!document.querySelector('#nr-1 svg.veg')")
    s.p.click("#veg-schalter")
    assert s.js("document.getElementById('nr-1').hidden") and not s.js("document.getElementById('nr-3').hidden")
    assert s.js("document.getElementById('kinder').hidden") and s.js("document.getElementById('lahmacun').hidden")
    assert not s.js("document.getElementById('nr-80').hidden")
    karten = s.js("[...document.querySelectorAll('.beliebt .tipp:not([hidden])')].map(t=>t.dataset.k)")
    assert karten == ["3", "91", "125", "52", "5", "58", "24", "84", "130"], karten
    assert not s.js("document.querySelector('.beliebt').hidden")
    s.p.fill("#suche-feld", "pizza")
    sichtbar = s.js("[...document.querySelectorAll('.gericht:not([hidden])')].map(g=>g.dataset.k)")
    assert "80" in sichtbar and "82" not in sichtbar, sichtbar
    s.p.fill("#suche-feld", "")
    s.p.click("#veg-schalter")
    assert not s.js("document.getElementById('nr-1').hidden")
    karten = s.js("[...document.querySelectorAll('.beliebt .tipp:not([hidden])')].map(t=>t.dataset.k)")
    assert karten == ["1", "26", "91", "125", "50", "23", "130", "100", "105", "124"], karten
    s.schliessen()


@test
def bewertung_nach_bestellung(b, url):
    s = Seite(b, url)
    s.p.click("#nr-1 .plus")
    s.p.click("#zettel-leiste")
    s.p.click('[data-laden="altenberg"]')
    s.wa_text()
    assert s.js("JSON.parse(localStorage.getItem('saray-bewertung')).l") == "altenberg"
    s.schliessen()
    # nächster Besuch drei Stunden später: erst ab der 3. Bestellung einmal fragen; danach nicht mehr
    ms = int(ZEIT.timestamp() * 1000) - 3 * 3600 * 1000
    for n, fertig in ((2, False), (3, False), (3, True)):
        ctx = b.new_context(viewport=HANDY, locale="de-DE", timezone_id="Europe/Berlin", reduced_motion="reduce", is_mobile=True, has_touch=True)
        p = ctx.new_page()
        p.clock.set_fixed_time(ZEIT)
        wert = json.dumps({"l": "freital", "t": ms, **({"fertig": 1} if fertig else {})})
        gast = json.dumps({"id": "ABCDEFGH", "n": n, "letzte": "X11"})
        p.add_init_script(f"try{{localStorage.setItem('saray-hand-gefragt','1');localStorage.setItem('saray-bewertung',{json.dumps(wert)});localStorage.setItem('saray-gast',{json.dumps(gast)})}}catch(e){{}}")
        p.goto(url)
        p.wait_for_timeout(1900)
        if n < 3:
            assert p.evaluate("document.getElementById('hand-tipp').hidden"), "Bewertung erst ab der 3. Bestellung"
            assert '"fertig"' not in p.evaluate("localStorage.getItem('saray-bewertung')")
        elif not fertig:
            assert "schon 3-mal" in p.text_content("#hand-tipp"), p.text_content("#hand-tipp")
            assert not p.evaluate("document.getElementById('hand-tipp').hidden"), "Bewertungs-Hinweis fehlt"
            assert "Hat alles gepasst?" in p.text_content("#hand-tipp") and "Freital" in p.text_content("#hand-tipp")
            assert '"fertig":1' in p.evaluate("localStorage.getItem('saray-bewertung')")
            p.click("#hand-tipp >> text=👍 Ja, lecker")
            assert "Google-Bewertung" in p.text_content("#hand-tipp")
            p.click("#hand-tipp >> text=Nein danke")
        else:
            assert p.evaluate("document.getElementById('hand-tipp').hidden"), "Hinweis kam ein zweites Mal"
        ctx.close()


@test
def sonderaktion_mit_uhrzeit_und_datenschutz(b, url):
    with tempfile.TemporaryDirectory() as tmp:
        srv, u = bauen_mit({"aktionen": [{"name": "Mittag", "von": "2026-10-20", "bis": "2026-10-30", "zeit_ab": "11:00", "zeit_bis": "14:00",
                                          "preise": {"130": ["4,00"]}}]}, tmp)
        s = Seite(b, u)
        assert "11–14 Uhr" in s.p.text_content("#nr-130 .marke-aktion")
        assert "GoatCounter" in s.p.text_content("#datenschutz") and "GitHub" in s.p.text_content("#datenschutz")
        s.p.click("#nr-130 .plus")
        s.p.click("#zettel-leiste")
        s.p.click('[data-laden="freital"]')
        s.p.select_option("#abhol-tag", "2026-10-22")
        for uhr, preis in (("12:00 Uhr", "4,00 € (Aktion)"), ("15:00 Uhr", "5,00 €\n")):
            s.js(f"(()=>{{const z=document.getElementById('abhol-zeit');z.value=[...z.options].find(o=>o.value.endsWith(', {uhr}')).value;z.dispatchEvent(new Event('change'))}})()")
            text = s.wa_text() + "\n"
            assert "Nr. 130 Salat" in text and preis in text.split("Nr. 130 Salat")[1].split("\n")[0] + "\n", text
        s.schliessen()
        srv.shutdown()


@test
def chef_app_zahlen(b, url):
    ctx, p, fehler = chef_oeffnen(b, url, gespeichert=[])
    gefragt = []

    def gc(route):
        gefragt.append(route.request.url)
        if len(gefragt) == 2:   # einmal gebremst, ohne CORS-Kopf -> im Browser nur „Load failed“
            route.fulfill(status=429, body="rate limited")
            return
        assert route.request.headers.get("authorization") == "Bearer GCKEY"
        start = urllib.parse.parse_qs(urllib.parse.urlparse(route.request.url).query)["start"][0]
        f = {"2026-10-20T22:00:00Z": 1, "2026-10-14T22:00:00Z": 5, "2026-09-21T22:00:00Z": 20, "2026-10-01T00:00:00Z": 30}[start]
        route.fulfill(status=200, headers={"Access-Control-Allow-Origin": "*"}, json={"hits": [
            {"path": "/", "count": 30 * f, "event": False},
            {"path": "whatsapp-freital", "count": 4 * f, "event": True},
            {"path": "anrufen-altenberg", "count": 2 * f, "event": True}]})
    p.route("https://saraymicana.goatcounter.com/**", gc)
    p.click('nav.tabs [data-tab="mehr"]')
    p.click('[data-seite="zahlen"]')
    p.fill("#gc-schl", " GCKEY ")
    p.click(".karte:has(#gc-schl) >> text=Speichern")
    p.wait_for_selector("table.zahlen", timeout=30000)
    zeilen = p.evaluate("[...document.querySelectorAll('table.zahlen tr')].map(r=>r.innerText.replace(/\\s+/g,' ').trim())")
    assert "Besucher 30 150 600 900" in zeilen and "WhatsApp Freital 4 20 80 120" in zeilen, zeilen
    assert zeilen[0].split() == ["Heute", "7", "Tage", "30", "Tage", "Gesamt"], zeilen[0]
    assert all("stats/hits" in x for x in gefragt), gefragt
    assert not fehler, fehler
    ctx.close()


@test
def pizzabroetchen_belag(b, url):
    s = Seite(b, url)
    s.p.click("#nr-125 .plus")
    s.p.click("#zettel-leiste")
    s.p.click('[data-laden="freital"]')
    assert "Belag wählen" in s.wa_text()
    s.p.click("[data-anpassen]")
    s.p.click('.z-optionen [data-o="va"][data-w="Dönerfleisch"]')
    s.p.click('.z-optionen [data-o="va"][data-w="Schinken"]')
    text = s.wa_text()
    assert "Nr. 125 Pizzabrötchen, mit Schinken: 7,50 €" in text, text
    s.schliessen()


@test
def teller_umwandeln(b, url):
    s = Seite(b, url)
    s.p.click("#nr-26 .plus")
    s.p.click("#zettel-leiste")
    s.p.click('[data-laden="freital"]')
    s.p.click("[data-anpassen]")
    s.p.click('[data-fuell="kalb"]')
    assert "Nr. 23 Döner-Teller" in s.wa_text()
    s.p.click('[data-bei="P"]')
    text = s.wa_text()
    assert "Nr. 22 Döner-Teller" in text and "10,00 €" in text, text
    s.p.click('[data-fuell="huhn"]')
    assert "Nr. 35 Hähnchen-Döner-Teller" in s.wa_text()
    s.p.click('[data-fuell="beide"]')
    assert "Nr. 26 Saray-Teller" in s.wa_text()
    s.schliessen()


@test
def salat_anpassen(b, url):
    s = Seite(b, url)
    assert s.js("!!document.querySelector('.tipps:not(.tipps-empfehlung) li[data-k=\"130\"]')"), "Salat fehlt bei Beliebt"
    s.p.click("#nr-130 .plus")
    s.p.click("#zettel-leiste")
    s.p.click('[data-laden="freital"]')
    s.p.click("[data-anpassen]")
    s.p.click('[data-fuell="huhn"]')
    assert "Nr. 134 Salat mit Hähnchenfleisch" in s.wa_text()
    s.p.click("[data-kaese]")
    text = s.wa_text()
    assert "Nr. 135 Salat mit Hähnchenfleisch und Käse" in text and "8,00 €" in text, text
    s.p.click('[data-fuell="tonno"]')
    assert "Nr. 136 Salat Tonno" in s.wa_text()
    s.schliessen()


@test
def pescetarisch_und_auswahl_ohne_fleisch(b, url):
    s = Seite(b, url)
    s.p.click("#pesc-schalter")
    sichtbar = set(s.js("[...document.querySelectorAll('.gericht:not([hidden])')].map(g=>g.dataset.k)"))
    assert {"87", "136", "71", "130", "3"} <= sichtbar and not {"1", "82", "131"} & sichtbar, sichtbar
    karten = s.js("[...document.querySelectorAll('.tipps-empfehlung .tipp:not([hidden])')].map(t=>t.dataset.k)")
    assert karten == ["87", "3", "91", "125"], karten
    s.p.click("#nr-130 .plus")
    s.p.click("#zettel-leiste")
    s.p.click("[data-anpassen]")
    fuell = s.js("[...document.querySelectorAll('[data-fuell]')].map(b=>b.dataset.fuell)")
    assert "tonno" in fuell and "huhn" not in fuell and "kalb" not in fuell, fuell
    s.p.click(".zettel-zu")
    s.p.click("#veg-schalter")
    assert s.js("document.getElementById('pesc-schalter').getAttribute('aria-pressed')") == "false"
    assert s.js("document.getElementById('nr-87').hidden")
    s.p.click("#zettel-leiste")
    s.p.click("[data-anpassen]")
    fuell = s.js("[...document.querySelectorAll('[data-fuell]')].map(b=>b.dataset.fuell)")
    assert "tonno" not in fuell and "huhn" not in fuell and "halloumi" in fuell, fuell
    s.schliessen()


@test
def pizza_ohne_zutaten(b, url):
    s = Seite(b, url)
    s.p.click("#nr-87 .plus")
    s.p.click("#nr-87 .wahl button >> nth=0")
    s.p.click("#zettel-leiste")
    s.p.click('[data-laden="freital"]')
    s.p.click("[data-anpassen]")
    zut = s.js("[...document.querySelectorAll('[data-o=\"ohne\"]')].map(b=>b.dataset.w)")
    assert zut == ["Thunfisch", "Zwiebel", "Käse"], zut
    s.p.click('[data-o="ex"][data-w="Zwiebel"]')
    s.p.click('[data-o="ohne"][data-w="Zwiebel"]')
    assert not s.js("!!document.querySelector('[data-o=\"ex\"][data-w=\"Zwiebel\"]')"), "abgewählte Zutat noch als Extra"
    text = s.wa_text()
    assert "Pizza Tonno (24 cm), ohne Zwiebel: 8,50 €" in text, text
    s.schliessen()



@test
def pizza_saray_ohne_kaese_nicht_zur_wahl(b, url):
    s = Seite(b, url)
    s.p.click("#nr-91 .plus")
    s.p.click("#nr-91 .wahl button >> nth=0")
    s.p.click("#zettel-leiste")
    s.p.click('[data-laden="freital"]')
    s.p.click("[data-anpassen]")
    for z in ("Käse", "Halloumikäse", "Fetakäse"):
        s.p.click(f'[data-o="wahl"][data-w="{z}"]')
    s.p.click('[data-o="ohne"][data-w="Käse"]')
    wahl = s.js("[...document.querySelectorAll('[data-o=\"wahl\"][aria-pressed=\"true\"]')].map(b=>b.dataset.w)")
    assert wahl == ["Halloumikäse", "Fetakäse"], wahl
    assert s.js("document.querySelector('[data-o=\"wahl\"][data-w=\"Käse\"]').disabled")
    assert "(2 von 3)" in s.p.text_content(".z-optionen")
    assert "noch 1 Zutat wählen" in s.wa_text()
    s.p.click('[data-o="wahl"][data-w="Paprika"]')
    text = s.wa_text()
    zeile = [z for z in text.split("\n") if "Pizza Saray" in z][0]
    assert "ohne Käse" in zeile and "mit Käse" not in zeile and "Halloumikäse, Fetakäse und Paprika" in zeile, zeile
    s.schliessen()


@test
def entwurf_band_verdeckt_zettel_nicht(b, url):
    s = Seite(b, url, {"width": 390, "height": 664})
    for nr in ("1", "130", "136", "3", "5"):
        s.p.click(f"#nr-{nr} .plus")
    s.js("window.scrollTo(0,0)")
    s.p.click("#zettel-leiste")
    for nr in range(3):
        s.p.click(".z-eintrag [data-anpassen] >> nth=0") if nr == 0 else None
    s.js("document.querySelector('.zettel').scrollTop=400")
    s.p.wait_for_timeout(200)
    oben = s.js("(()=>{const r=document.querySelector('.zettel-zu').getBoundingClientRect();const e=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return e&&e.closest('.zettel-zu')?'ok':(e&&e.className)})()")
    assert oben == "ok", f"Schließen-Knopf verdeckt von {oben}"
    s.p.click(".zettel-zu")
    assert s.js("document.getElementById('zettel').hidden")
    s.schliessen()


@test
def zutaten_aus(b, url):
    s = Seite(b, url, regeln=[{"was": "z:Kräuter"}, {"was": "z:Zwiebel"}, {"was": "z:Ananas", "laden": "freital"}])
    s.p.click("#nr-1 .plus")
    s.p.click("#nr-89 .plus")
    s.p.click("#nr-89 .wahl button >> nth=0")
    s.p.click("#zettel-leiste")
    s.p.click('[data-laden="freital"]')
    text = s.wa_text()
    assert "Kräuter" not in text and "ohne Soße" in text, text
    s.p.click("[data-anpassen] >> nth=0")
    assert s.js("document.querySelector('[data-o=\"s\"][data-w=\"Kräuter\"]').disabled")
    assert s.js("document.querySelector('[data-o=\"ohne\"][data-w=\"Zwiebeln\"]').disabled")
    s.p.click("[data-fertig]")
    s.p.click(".z-eintrag:has-text('Hawaii') [data-anpassen]")
    assert s.js("document.querySelector('[data-o=\"ohne\"][data-w=\"Ananas\"]').disabled")
    assert s.js("document.querySelector('[data-o=\"ex\"][data-w=\"Ananas\"]').disabled")
    assert not s.js("document.querySelector('[data-o=\"ex\"][data-w=\"Mais\"]').disabled")
    s.p.click('[data-laden="altenberg"]')
    assert not s.js("document.querySelector('[data-o=\"ex\"][data-w=\"Ananas\"]').disabled"), "Ananas nur in Freital aus"
    s.schliessen()


@test
def pommes_und_reis_aus(b, url):
    s = Seite(b, url, regeln=[{"was": "z:Pommes"}, {"was": "z:Reis"}])
    assert s.js("document.getElementById('nr-72').classList.contains('nicht-da')"), "reine Pommes müssen aus sein"
    assert not s.js("document.getElementById('nr-23').classList.contains('nicht-da')")
    for nr in ("23", "26", "70"):
        s.p.click(f"#nr-{nr} .plus")
    s.p.click("#zettel-leiste")
    s.p.click('[data-laden="freital"]')
    text = s.wa_text()
    assert "Nr. 23 Döner-Teller, Kräuter-Soße, ohne Pommes (heute aus, −0,50 €): 10,50 €" in text, text
    assert "Nr. 26 Saray-Teller, Kräuter-Soße, ohne Pommes und Reis (heute aus, −1,00 €): 14,00 €" in text, text
    assert "Nr. 70 Schnitzel, ohne Pommes (heute aus, −0,50 €): 9,50 €" in text, text
    s.p.click("[data-anpassen] >> nth=0")
    assert s.js("document.querySelector('[data-bei=\"P\"]').disabled")
    s.schliessen()


@test
def chef_app_zutaten(b, url):
    gespeichert = []
    ctx, p, fehler = chef_oeffnen(b, url, gespeichert=gespeichert)
    p.click('[data-zutat="Ananas"]')
    p.click('[data-zutat="Chili"]')
    p.click('[data-zutat="Chili"]')
    assert p.get_attribute('[data-zutat="Ananas"]', "aria-pressed") == "true"
    p.click("#speichern-knopf")
    p.wait_for_selector(".status.ok >> text=Online")
    assert gespeichert[-1]["verfuegbarkeit"] == [{"was": "z:Ananas"}], gespeichert[-1]
    assert not fehler, fehler
    ctx.close()


@test
def chef_app_checkliste_und_gefahrenbereich(b, url):
    gespeichert = []
    ctx, p, fehler = chef_oeffnen(b, url, anp={"geloescht": ["8"]}, gespeichert=gespeichert)
    p.click('nav.tabs [data-tab="mehr"]')
    p.click('[data-seite="checkliste"]')
    assert "von 40 offen" in p.text_content(".checkliste summary")
    p.check("#cl-domain")
    p.fill("#cl-wa-altenberg-n", "0151 1234567")
    p.press("#cl-wa-altenberg-n", "Tab")
    assert "GitHub Pro" in p.text_content(".checkliste")
    p.click("#speichern-knopf")
    p.wait_for_selector(".status.ok >> text=Online")
    assert gespeichert[-1]["checkliste"] == {"domain": {"ok": True}, "wa-altenberg": {"notiz": "0151 1234567"}}, gespeichert[-1]
    p.click("#zurueck")
    assert "Gefahrenbereich" in p.text_content("#app")
    p.click('[data-seite="gefahr"]')
    p.click("text=Alles auf Standard zurücksetzen")
    p.click(".blatt >> text=Ja, zurücksetzen")
    p.wait_for_timeout(500)
    assert gespeichert[-1] == {"checkliste": {"domain": {"ok": True}, "wa-altenberg": {"notiz": "0151 1234567"}}}, gespeichert[-1]
    assert not fehler, fehler
    ctx.close()


@test
def chef_app_nummer_aendern(b, url):
    gespeichert = []
    ctx, p, fehler = chef_oeffnen(b, url, gespeichert=gespeichert)
    p.click('nav.tabs [data-tab="karte"]')
    p.click('.liste-gericht[data-k="12"]')
    p.fill("#b-nr", "11")
    p.click(".blatt >> text=Übernehmen")
    assert "schon vergeben" in p.text_content(".blatt .fehler")
    p.fill("#b-nr", "12a")
    p.click(".blatt >> text=Übernehmen")
    p.click("#speichern-knopf")
    p.wait_for_selector(".status.ok >> text=Online")
    d = gespeichert[-1]
    assert d["gerichte"] == {"12": {"nr": "12a"}}, d
    assert not fehler, fehler
    ctx.close()
    with tempfile.TemporaryDirectory() as tmp:
        srv, u = bauen_mit(d, tmp)
        s = Seite(b, u)
        assert s.p.text_content("#nr-12 .nr").endswith("12a")
        s.p.click("#nr-12 .plus")
        s.p.click("#zettel-leiste")
        s.p.click('[data-laden="freital"]')
        assert "Nr. 12a Falafel-Döner" in s.wa_text()
        s.schliessen()
        srv.shutdown()


@test
def weisse_flaeche_folgt_dem_band(b, url):
    """Am Ende der Speisekarte rutscht das Band weg – die weiße Fläche darüber muss mitgehen."""
    s = Seite(b, url)
    for y in (300, 200, 120, 60, 0):
        s.js(f"window.scrollTo(0, document.getElementById('standorte').getBoundingClientRect().top + scrollY - {y})")
        s.p.wait_for_timeout(150)
        frei = s.js("""(()=>{const h=document.getElementById('standorte-titel').getBoundingClientRect();
            if(h.top<0||h.top>innerHeight)return 'ok';const e=document.elementFromPoint(h.left+20,h.top+h.height/2);
            return e&&e.closest('#standorte-titel')?'ok':(e&&e.className)})()""")
        assert frei == "ok", f"Überschrift verdeckt von {frei} (Abstand {y})"
        hoehe = s.js("(()=>{const d=document.querySelector('.deckel-oben');return d?d.getBoundingClientRect().height:0})()")
        unten = s.js("Math.max(0,document.querySelector('.kategorien').getBoundingClientRect().bottom)")
        assert hoehe <= unten + 1, (y, hoehe, unten)
    s.schliessen()


@test
def gemeinsam_dialog_oben_und_ruhig(b, url):
    s = Seite(b, url)
    assert s.js("getComputedStyle(document.querySelector('.sammel-start')).textAlign") == "center"
    breiten = s.js("[...document.querySelectorAll('.diaet .veg-schalter')].map(b=>Math.round(b.getBoundingClientRect().width))")
    suche = s.js("Math.round(document.getElementById('suche-feld').getBoundingClientRect().width)")
    assert sum(breiten) + 10 >= suche - 4, (breiten, suche)
    s.p.click("[data-sammel-start]")
    oben = s.js("document.querySelector('.sammel-box').getBoundingClientRect().top")
    assert oben < 40, oben
    assert s.js("document.documentElement.style.overflow") == "hidden"
    s.p.click("#sammel-name")
    s.p.keyboard.type("Mi")
    assert s.js("document.querySelector('.sammel-box').getBoundingClientRect().top") == oben
    s.p.keyboard.press("Escape")
    assert s.js("document.documentElement.style.overflow") == ""
    s.schliessen()


@test
def bestellnummer_und_kalender(b, url):
    s = Seite(b, url)
    s.p.click("#nr-1 .plus")
    s.p.click("#zettel-leiste")
    s.p.click('[data-laden="freital"]')
    text = s.wa_text()
    import re as _re
    nr = _re.search(r"Bestellnummer: ([A-Z][0-9]{2})", text).group(1)
    assert s.p.text_content(".wa-nr b") == nr
    s.js("window.__ics=null;URL.createObjectURL=function(b){b.text().then(t=>window.__ics=t);return 'blob:x'};0")
    s.p.click("#wa-kalender")
    s.p.wait_for_timeout(200)
    ics = s.js("window.__ics")
    assert "BEGIN:VEVENT" in ics and "DTSTART;TZID=Europe/Berlin:20261021T" in ics and nr in ics and "Dresdner Str. 87" in ics, ics
    assert "TRIGGER:-PT15M" in ics
    # gleiche Nummer bei erneutem Senden ohne Änderung, neue Nummer nach Änderung
    assert ("Bestellnummer: " + nr) in s.wa_text()
    s.p.click(".z-eintrag [data-a=plus]")
    assert ("Bestellnummer: " + nr) not in s.wa_text()
    s.schliessen()


@test
def chef_app_foto_hochladen(b, url):
    from PIL import Image
    FOTO_HOCHGELADEN.clear()
    ctx, p, fehler = chef_oeffnen(b, url, gespeichert=[])
    with tempfile.TemporaryDirectory() as tmp:
        bild = pathlib.Path(tmp) / "doener.jpg"
        Image.new("RGB", (3000, 2000), (200, 120, 40)).save(bild)
        p.click('nav.tabs [data-tab="karte"]')
        p.click('.liste-gericht[data-k="1"]')
        p.set_input_files("#foto-datei", str(bild))
        p.wait_for_selector(".foto-bereich >> text=Foto gespeichert")
    assert FOTO_HOCHGELADEN and FOTO_HOCHGELADEN[0][0] == "daten/fotos/nr-1.jpg" and FOTO_HOCHGELADEN[0][1] == "Chef-App: Foto Nr. 1", FOTO_HOCHGELADEN
    assert FOTO_HOCHGELADEN[0][2] < 1_500_000, "Foto nicht verkleinert"
    assert not fehler, fehler
    ctx.close()


@test
def chef_app_feiertage_und_google(b, url):
    gespeichert = []
    ctx, p, fehler = chef_oeffnen(b, url, gespeichert=gespeichert)
    assert "Reformationstag" in p.text_content("#app"), "Hinweis auf Feiertag fehlt unter Heute"
    p.click("text=Jetzt festlegen")
    p.locator('[data-feiertag="2026-10-31"]').locator("text=Wie sonntags").click()
    p.locator('[data-feiertag="2026-11-18"]').locator("text=Normal geöffnet").click()
    p.click("#speichern-knopf")
    p.wait_for_selector(".status.ok >> text=Online")
    d = gespeichert[-1]
    assert d["sonderzeiten"] == {"2026-10-31": {"freital": ["11:00", "22:00"], "altenberg": ["11:00", "21:00"]}}, d
    assert d["feiertage_ok"] == ["2026-11-18"], d
    p.click('nav.tabs [data-tab="mehr"]')
    p.click('[data-seite="google"]')
    p.click("text=Google-Unternehmensprofil")
    txt = p.evaluate("[...document.querySelectorAll('.gp-zeile textarea, .gp-zeile input')].map(x=>x.value).join('|')")
    assert "Dresdner Str. 87, 01705 Freital" in txt and "Mo: 10:00–22:00" in txt and "Nur Barzahlung" in txt, txt
    assert not fehler, fehler
    ctx.close()


@test
def gruppen_abschnitt(b, url):
    s = Seite(b, url)
    assert "Für Firmen, Vereine und Feiern" in s.p.text_content("#gruppen")
    s.p.click("#gruppen [data-sammel-start]")
    assert not s.js("document.getElementById('sammel-dialog').hidden")
    s.schliessen()



@test
def mittagstisch(b, url):
    mittag = {"name": "Mittagstisch", "art": "mittag", "von": "2026-10-19", "bis": "2026-10-30", "tage": [1, 2, 3, 4, 5],
              "zeit_ab": "11:00", "zeit_bis": "14:00", "preise": {"23": ["8,50"]}}
    with tempfile.TemporaryDirectory() as tmp:
        srv, u = bauen_mit({"aktionen": [mittag]}, tmp)
        s = Seite(b, u, zeit=datetime.datetime.fromisoformat("2026-10-21T12:00:00+02:00"))
        assert s.js("!document.querySelector('[data-mittag]').hidden"), "Mittagstisch-Kasten fehlt mittags"
        assert "Mo, Di, Mi, Do, Fr · 11–14 Uhr" in s.p.text_content(".mittag-zeit")
        assert "Mittag 8,50 €" in s.p.text_content("#nr-23 .marke-aktion")
        baender = s.js("[...document.querySelectorAll('.hinweis-band:not([hidden])')].map(x=>x.textContent)")
        assert any(x.startswith("Mittagstisch") for x in baender) and not any("Aktion: Mittagstisch" in x for x in baender), baender
        s.p.click(".mittag .plus")
        s.p.click("#zettel-leiste")
        s.p.click("[data-laden=freital]")
        text = s.wa_text()
        assert "Döner-Teller" in text and "8,50 € (Aktion)" in text, text
        s.schliessen()
        s = Seite(b, u)   # 17:45 Uhr: vorbei
        assert s.js("document.querySelector('[data-mittag]').hidden"), "Mittagstisch nach 14 Uhr noch sichtbar"
        s.schliessen()
        srv.shutdown()


@test
def zug_ab_altenberg(b, url):
    s = Seite(b, url)
    s.p.click("#nr-1 .plus")
    s.p.click("#zettel-leiste")
    s.p.click("[data-laden=freital]")
    assert s.js("document.getElementById('zug-wahl').hidden"), "Zugvorschlag in Freital"
    s.p.click("[data-laden=altenberg]")
    chips = s.js("[...document.querySelectorAll('#zug-wahl .chip')].map(c=>c.textContent)")
    assert chips and chips[0] == "Zug 19:18 → abholen 19:00", chips   # 18:18 ist zu knapp (frühestens 18:15)
    s.p.click("#zug-wahl .chip >> nth=0")
    assert s.p.input_value("#abhol-zeit") == "heute, 19:00 Uhr"
    assert "Abholung: heute, 19:00 Uhr (Zug 19:18)" in s.wa_text()
    s.p.select_option("#abhol-zeit", "heute, 19:15 Uhr")
    assert "(Zug" not in s.wa_text()
    s.p.select_option("#abhol-tag", "2026-10-24")   # Samstag: RE 19 um 17:18, keine Werktagszüge
    chips = s.js("[...document.querySelectorAll('#zug-wahl .chip')].map(c=>c.textContent.split(' ')[1])")
    assert "17:18" in chips and "18:18" in chips and "19:18" not in chips and "13:18" not in chips, chips
    s.schliessen()
    s = Seite(b, url, zeit=datetime.datetime.fromisoformat("2026-11-17T12:00:00+01:00"))
    s.p.click("#nr-1 .plus")
    s.p.click("#zettel-leiste")
    s.p.click("[data-laden=altenberg]")
    s.p.select_option("#abhol-tag", "2026-11-18")   # Buß- und Bettag: wie Feiertag, RE 19 um 15:18
    chips = s.js("[...document.querySelectorAll('#zug-wahl .chip')].map(c=>c.textContent.split(' ')[1])")
    assert "15:18" in chips and "11:18" not in chips, chips
    s.schliessen()


@test
def kuechenansicht(b, url):
    s = Seite(b, url)
    s.p.click("#nr-1 .plus")
    s.p.click("#nr-50 .plus")
    s.p.click("#zettel-leiste")
    s.p.click("[data-laden=freital]")
    s.p.fill("#abhol-name", "Jana")
    s.p.press("#abhol-name", "Tab")
    text = s.wa_text()
    nr = [z for z in text.split("\n") if z.startswith("Bestellnummer: ")][0].split(": ")[1]
    link = [z for z in text.split("\n") if z.startswith("Für die Küche: ")][0].split(": ", 1)[1]
    assert "/kueche/#b=" in link, link
    k = s.ctx.new_page()
    k.goto(link)
    k.wait_for_selector("#offen .bon")
    assert "#b=" not in k.url
    assert k.text_content("#offen .bon .bnr").startswith(nr)
    inhalt = k.text_content("#offen .bon")
    assert "Döner Kebap" in inhalt and "Dürüm" in inhalt and "Jana" in inhalt and "Freital" in inhalt and "15,00 €" in inhalt, inhalt
    k.click("#offen .bon .pos li >> nth=0")
    assert k.get_attribute("#offen .bon .pos li >> nth=0", "aria-checked") == "true"
    k.goto(link)   # derselbe Link noch einmal: nicht doppelt
    k.wait_for_selector("#offen .bon")
    assert k.locator("#offen .bon").count() == 1
    k.evaluate("window.open=function(u){window._offen=decodeURIComponent(u)}")
    k.click("#offen .bon [data-bestaetigen]")
    gesendet = k.evaluate("window._offen")
    assert gesendet.startswith("https://wa.me/?text=Hallo Jana, danke für Ihre Bestellung " + nr + "!"), gesendet
    assert "in Freital abholbereit" in gesendet and "15,00 €" in gesendet, gesendet
    assert k.text_content("#offen .bon [data-bestaetigen]") == "✓ Bestätigt"
    k.click("#offen .bon >> text=Fertig ✓")
    assert k.locator("#offen .bon").count() == 0 and not k.is_hidden("#leer")
    assert k.text_content("#erledigt-titel") == "Erledigt (1)"
    k.evaluate("document.getElementById('erledigt-box').open=true")
    k.click("#erledigt .bon [data-melden]")
    assert "ist fertig und liegt in Freital für Sie bereit" in k.evaluate("window._offen")
    k.evaluate("document.getElementById('abschluss').open=true")
    zahlen = k.evaluate("[...document.querySelectorAll('#abschluss .zahlen b')].map(x=>x.textContent)")
    assert zahlen[:3] == ["0", "0,00 €", "0"], zahlen   # Vorschau-Bestellungen sind Test und zählen nicht
    assert "1 Test-Bestellung" in k.text_content("#abschluss")
    k.close()
    s.schliessen()


@test
def bildschirm_im_laden(b, url):
    ctx = b.new_context(viewport={"width": 1920, "height": 1080}, locale="de-DE", timezone_id="Europe/Berlin")
    p = ctx.new_page()
    fehler = []
    p.on("pageerror", lambda e: fehler.append(str(e)))
    p.clock.set_fixed_time(ZEIT)
    p.route("**/status.json", lambda r: r.fulfill(status=200, content_type="application/json",
                                                 body=json.dumps({"regeln": [{"was": "huhn", "datum": "2026-10-21"}, {"was": "z:Pommes", "datum": "2026-10-21"}]})))
    p.goto(url + "tv/")
    assert p.locator(".wahl a").count() == 2   # ohne Laden: Auswahl
    p.goto(url + "tv/?laden=altenberg&modus=fenster")
    p.wait_for_function("window.TV && TV.seiten() === 1")
    assert p.locator(".qr-gross svg").count() == 1 and p.is_hidden(".fuss")
    p.goto(url + "tv/?laden=freital&sek=999")
    p.wait_for_function("window.TV && TV.seiten() >= 5")
    p.wait_for_timeout(500)
    assert p.text_content("#status") == "Geöffnet bis 22 Uhr"
    assert "Heute leider ohne: Pommes – Gerichte mit Pommes 0,50 € günstiger" in p.text_content("#baender")
    aus = p.evaluate("[...document.querySelectorAll('.g.aus .nm')].map(x=>x.firstChild.textContent)")
    assert "Hähnchen-Döner" in aus and "Döner Kebap" not in aus, aus
    # nichts abgeschnitten: jedes Gericht liegt innerhalb seiner Seite
    raus = p.evaluate("""[...document.querySelectorAll('.seite')].flatMap(s=>{s.classList.add('an');const sp=s.querySelector('.spalten');if(!sp){s.classList.remove('an');return [];}
      const r=sp.getBoundingClientRect(),x=[...sp.querySelectorAll('.g')].filter(g=>{const q=g.getBoundingClientRect();return q.right>r.right+2||q.bottom>r.bottom+2}).map(g=>g.textContent);
      s.classList.remove('an');return x;})""")
    assert not raus, raus
    alle = p.evaluate("document.querySelectorAll('.spalten .g').length")
    assert alle == 140, alle
    assert not fehler, fehler
    ctx.close()


@test
def wintersaison(b, url):
    s = Seite(b, url)
    assert s.js("document.getElementById('winter').hidden"), "Wintersaison im Oktober sichtbar"
    s.schliessen()
    s = Seite(b, url, zeit=datetime.datetime.fromisoformat("2027-01-09T12:00:00+01:00"))
    assert not s.js("document.getElementById('winter').hidden"), "Wintersaison im Januar unsichtbar"
    s.p.click("#winter-bestellen")
    assert s.js("!document.getElementById('zettel').hidden || !document.querySelector('.zettel-huelle, #zettel-huelle')?.hidden")
    assert s.p.get_attribute("[data-laden=altenberg]", "aria-pressed") == "true"
    s.schliessen()
    with tempfile.TemporaryDirectory() as tmp:
        srv, u = bauen_mit({"winter": "aus"}, tmp)
        s = Seite(b, u, zeit=datetime.datetime.fromisoformat("2027-01-09T12:00:00+01:00"))
        assert s.js("document.getElementById('winter').hidden"), "Wintersaison trotz „aus“ sichtbar"
        s.schliessen()
        srv.shutdown()


@test
def chef_app_gutscheine_mittag_winter(b, url):
    gespeichert = []
    ctx, p, fehler = chef_oeffnen(b, url, gespeichert=gespeichert)
    p.evaluate("window.print=()=>{window._gedruckt=(window._gedruckt||0)+1}")
    p.click('nav.tabs [data-tab="preise"]')
    p.click("[data-gs-wert='2500']")
    p.click("[data-gs-anzahl='2']")
    p.click("#gs-erstellen")
    p.wait_for_function("window._gedruckt===1")
    karten = p.evaluate("[...document.querySelectorAll('#gs-druck .gs-nr')].map(x=>x.textContent)")
    assert len(karten) == 2 and karten[0].startswith("Nr. G26-001 · Code "), karten
    code = karten[0].split("Code ")[1]
    assert "25 €" in p.text_content("#gs-druck .gs-wert")
    p.fill("#gs-nr", "g26-001")
    p.fill("#gs-code", "XXXXXX")
    p.click("#gs-pruefen")
    p.wait_for_selector("#gs-ergebnis .fehler")
    assert "Code passt nicht" in p.text_content("#gs-ergebnis")
    p.fill("#gs-code", code.lower())
    p.click("#gs-pruefen")
    p.wait_for_selector("#gs-einloesen")
    assert "Gültig: 25 €" in p.text_content("#gs-ergebnis")
    p.click("#gs-einloesen")
    p.click('nav.tabs [data-tab="zeiten"]')
    p.click("[data-winter='an']")
    p.click('nav.tabs [data-tab="karte"]')
    p.click("text=+ Mittagstisch")
    assert p.input_value("#a-name") == "Mittagstisch"
    p.fill("#a-such", "23")
    p.locator(".blatt .liste-gericht", has_text="Döner-Teller").first.click()
    p.fill("[data-ak='23']", "8,5")
    p.click(".blatt >> text=Übernehmen")
    p.click("#speichern-knopf")
    p.wait_for_selector(".status.ok >> text=Online")
    d = gespeichert[-1]
    gs = d["gutscheine"]
    assert len(gs) == 2 and gs[0]["nr"] == "G26-001" and gs[0]["wert"] == 2500 and gs[0]["bis"] == "2029-12-31", gs
    assert gs[0]["eingeloest"] == "2026-10-21" and "eingeloest" not in gs[1], gs
    assert all("code" not in g and len(g["h"]) == 64 for g in gs), gs
    assert d["winter"] == "an", d
    assert d["aktionen"] == [{"name": "Mittagstisch", "art": "mittag", "von": "2026-10-21", "bis": "2026-11-17", "tage": [1, 2, 3, 4, 5],
                              "zeit_ab": "11:00", "zeit_bis": "14:00", "preise": {"23": ["8,50"]}}], d["aktionen"]
    assert not fehler, fehler
    ctx.close()
    with tempfile.TemporaryDirectory() as tmp:
        srv, u = bauen_mit(d, tmp)
        srv.shutdown()



@test
def chef_app_tuerkisch(b, url):
    ctx, p, fehler = chef_oeffnen(b, url, gespeichert=[])
    assert p.get_attribute("[data-ue-sp=de]", "aria-pressed") == "true" and p.get_attribute("[data-ue-sp=tr]", "aria-pressed") == "false"
    assert p.locator("#sprache svg").count() == 2, "Flaggen fehlen"
    p.click("[data-ue-sp=tr]")
    p.wait_for_selector("nav.tabs:not([hidden])")
    assert p.get_attribute("[data-ue-sp=tr]", "aria-pressed") == "true"
    assert p.text_content("#sprache") == "DETR", "Sprachwahl darf nicht übersetzt werden"
    assert "Bugün" in p.text_content("nav.tabs") and "Diğer" in p.text_content("nav.tabs")
    assert "Bugün ne yok?" in p.text_content("#app")
    p.click('nav.tabs [data-tab="karte"]')
    assert "Pizza Margherita" in p.text_content("#app"), "Gerichtsnamen bleiben deutsch"
    p.click('nav.tabs [data-tab="preise"]')
    assert "Hediye çekleri" in p.text_content("#app")
    p.click('nav.tabs [data-tab="mehr"]')
    p.click('[data-seite="checkliste"]')
    assert "40 / 40 açık" in p.text_content(".checkliste summary"), p.text_content(".checkliste summary")
    p.click("[data-ue-sp=de]")
    p.wait_for_selector("nav.tabs:not([hidden])")
    assert "Heute" in p.text_content("nav.tabs")
    assert not fehler, fehler
    ctx.close()



@test
def firmen_code(b, url):
    import hashlib
    h = hashlib.sha256(b"saray|ELBTAL10").hexdigest()
    with tempfile.TemporaryDirectory() as tmp:
        srv, u = bauen_mit({"codes": [{"h": h, "name": "Elbtal GmbH", "prozent": 10, "zeit_ab": "11:00", "zeit_bis": "14:00", "bis": "2027-10-21"}],
                            "aktionen": [{"name": "Dürüm 6 €", "von": "2026-10-20", "bis": "2026-10-25", "preise": {"50": ["6,00"]}}]}, tmp,
                           env={"SARAY_FIRMEN_CODES": "1"})
        s = Seite(b, u, zeit=datetime.datetime.fromisoformat("2026-10-21T12:00:00+02:00"))
        s.p.click("#nr-1 .plus")
        s.p.click("#nr-50 .plus")
        s.p.click("#zettel-leiste")
        s.p.click("[data-laden=freital]")
        s.p.click("#code-box summary")
        s.p.fill("#code-feld", "falsch1")
        s.p.press("#code-feld", "Enter")
        s.p.wait_for_selector("#code-info:not([hidden])")
        assert "kennen wir nicht" in s.p.text_content("#code-info")
        s.p.fill("#code-feld", "elbtal 10")
        s.p.press("#code-feld", "Enter")
        s.p.wait_for_function("document.getElementById('code-info').textContent.indexOf('Elbtal')>-1")
        assert s.p.text_content("#code-info").startswith("Elbtal GmbH: 10 % Rabatt (−0,70 €)"), s.p.text_content("#code-info")
        assert s.p.text_content("#zettel-summe") == "12,30 €"
        text = s.wa_text()
        assert "Firmen-Code: ELBTAL10 (Elbtal GmbH) – 10 % Rabatt: −0,70 €" in text and "Summe: 12,30 €" in text, text
        s.p.select_option("#abhol-zeit", "heute, 15:00 Uhr")
        assert "gilt nicht" in s.p.text_content("#code-info")
        text = s.wa_text()
        assert "Firmen-Code" not in text and "Summe: 13,00 €" in text, text
        s.schliessen()
        srv.shutdown()


@test
def bald_feierabend(b, url):
    s = Seite(b, url, zeit=datetime.datetime.fromisoformat("2026-10-21T21:35:00+02:00"))
    assert s.js("document.querySelector('[data-status=freital]').getAttribute('data-offen')") == "bald"
    assert s.js("document.querySelector('[data-status=freital] .status-text').textContent") == "Bald Feierabend – geöffnet bis 22 Uhr"
    s.schliessen()
    s = Seite(b, url, zeit=datetime.datetime.fromisoformat("2026-10-21T21:00:00+02:00"))
    s.p.click("#nr-1 .plus")
    s.p.click("#zettel-leiste")
    s.p.click("[data-laden=freital]")
    assert "Bald Feierabend: letzte Abholung heute um 21:45 Uhr." in s.p.text_content("#abhol-hinweis")
    s.schliessen()


@test
def chef_app_codes_und_viel_los(b, url):
    import hashlib
    gespeichert = []
    tmp0 = tempfile.TemporaryDirectory()
    srv0, url = bauen_mit({}, tmp0.name, env={"SARAY_FIRMEN_CODES": "1"})
    ctx, p, fehler = chef_oeffnen(b, url, gespeichert=gespeichert)
    p.click("#viel-los")
    assert "wieder aus" in p.text_content("#viel-los")
    p.click('nav.tabs [data-tab="preise"]')
    p.fill("#c-firma", "Elbtal GmbH")
    assert p.input_value("#c-code") == "ELBTALGM10"
    p.click("#c-anlegen")
    p.click(".blatt >> text=Notiert")
    assert "Elbtal GmbH · 10 % · EL…10 · 11:00–14:00 Uhr" in p.text_content("#app")
    p.click("#speichern-knopf")
    p.wait_for_selector(".status.ok >> text=Online")
    d = gespeichert[-1]
    assert d["codes"] == [{"h": hashlib.sha256(b"saray|ELBTALGM10").hexdigest(), "name": "Elbtal GmbH", "prozent": 10, "hinweis": "EL…10",
                           "bis": "2027-10-21", "zeit_ab": "11:00", "zeit_bis": "14:00"}], d["codes"]
    assert d["wartezeit"] == {"freital": {"datum": "2026-10-21", "min": 15}, "altenberg": {"datum": "2026-10-21", "min": 15}}, d["wartezeit"]
    assert d["hinweise"][0]["von"] == "2026-10-21" and "viel los" in d["hinweise"][0]["text"], d["hinweise"]
    assert not fehler, fehler
    ctx.close()
    srv0.shutdown()
    tmp0.cleanup()
    with tempfile.TemporaryDirectory() as tmp:
        srv, u = bauen_mit(d, tmp)
        srv.shutdown()


@test
def kueche_bedarf_und_jahr(b, url):
    import base64
    def link(o):
        return url + "kueche/#b=" + base64.urlsafe_b64encode(json.dumps(o).encode()).decode().rstrip("=")
    ctx = b.new_context(viewport={"width": 1180, "height": 900}, locale="de-DE", timezone_id="Europe/Berlin")
    k = ctx.new_page()
    k.clock.set_fixed_time(ZEIT)
    a = {"v": 1, "nr": "A11", "l": "freital", "z": "heute, 18:00 Uhr", "t": "2026-10-21T18:00", "m": "Ali", "s": 2100, "sp": "tr", "a": 1792600000000,
         "p": [[2, "Nr. 1 Döner Kebap", "", "", "", 1400], [1, "Nr. 50 Dürüm", "", "", "", 700]]}
    c = dict(a, nr="C22", t="2026-10-21T20:00", s=700, sp="de", a=1792600000001, p=[[1, "Nr. 1 Döner Kebap", "", "", "", 700]])
    k.goto(link(a))
    k.goto(link(c))
    k.wait_for_selector("#bedarf:not([hidden])")
    k.evaluate("document.getElementById('bedarf').open=true")
    zeilen = k.evaluate("[...document.querySelectorAll('#bedarf-liste tr')].map(r=>r.textContent)")
    assert zeilen == ["2×Nr. 1 Döner Kebap", "1×Nr. 50 Dürüm"], zeilen   # nächste Stunde: nur A11
    k.click("#bedarf-wahl >> text=Alle offenen")
    zeilen = k.evaluate("[...document.querySelectorAll('#bedarf-liste tr')].map(r=>r.textContent)")
    assert zeilen[0] == "3×Nr. 1 Döner Kebap", zeilen
    k.evaluate("document.getElementById('jahr').open=true")
    zahlen = k.evaluate("[...document.querySelectorAll('#jahr .zahlen b')].map(x=>x.textContent)")
    assert zahlen == ["2", "28,00 €", "4", "14,00 €"], zahlen
    inhalt = k.text_content("#jahr-inhalt")
    assert "Türkisch" in inhalt and "Döner Kebap" in inhalt and "18 Uhr" in inhalt, inhalt
    ctx.close()



@test
def firmen_codes_standardmaessig_aus(b, url):
    s = Seite(b, url)
    assert s.js("!document.getElementById('code-box')"), "Firmen-Code-Feld sichtbar, obwohl abgeschaltet"
    s.schliessen()
    ctx, p, fehler = chef_oeffnen(b, url, gespeichert=[])
    p.click('nav.tabs [data-tab="preise"]')
    assert p.locator("h3", has_text="Firmen-Codes").count() == 0 and p.locator("#c-anlegen").count() == 0
    ctx.close()


@test
def bestell_pause(b, url):
    with tempfile.TemporaryDirectory() as tmp:
        srv, u = bauen_mit({"pause": {"freital": {"bis": "2026-10-21T18:15"}}}, tmp)
        s = Seite(b, u)
        assert s.js("document.querySelector('[data-status=freital] .status-text').textContent") == "Online-Bestellungen pausiert bis 18:15 Uhr – anrufen geht"
        s.p.click("#nr-1 .plus")
        s.p.click("#zettel-leiste")
        s.p.click("[data-laden=freital]")
        assert s.p.is_hidden("#zettel-whatsapp") and "pausiert" in s.p.text_content("#pause-hinweis")
        s.p.select_option("#abhol-tag", "2026-10-22")
        assert s.p.is_visible("#zettel-whatsapp") and s.p.is_hidden("#pause-hinweis")
        s.p.click("[data-laden=altenberg]")
        s.p.select_option("#abhol-tag", "2026-10-21")
        assert s.p.is_visible("#zettel-whatsapp")
        s.schliessen()
        srv.shutdown()
    gespeichert = []
    ctx, p, fehler = chef_oeffnen(b, url, gespeichert=gespeichert)
    p.click("[data-pause='freital-30']")
    assert "pausiert bis 18:15 Uhr" in p.text_content("#app")
    p.click("#speichern-knopf")
    p.wait_for_selector(".status.ok >> text=Online")
    assert gespeichert[-1]["pause"] == {"freital": {"bis": "2026-10-21T18:15"}}, gespeichert[-1]
    assert not fehler, fehler
    ctx.close()



@test
def rueckmeldung_zuerst_an_den_laden(b, url):
    ctx = b.new_context(viewport=HANDY, locale="de-DE", timezone_id="Europe/Berlin", reduced_motion="reduce", is_mobile=True, has_touch=True)
    p = ctx.new_page()
    p.clock.set_fixed_time(ZEIT)
    wert = json.dumps({"l": "freital", "t": int(ZEIT.timestamp() * 1000) - 3 * 3600 * 1000, "nr": "K47"})
    gast = json.dumps({"id": "ABCDEFGH", "n": 4, "letzte": "X11"})
    p.add_init_script(f"try{{localStorage.setItem('saray-hand-gefragt','1');localStorage.setItem('saray-bewertung',{json.dumps(wert)});localStorage.setItem('saray-gast',{json.dumps(gast)})}}catch(e){{}}window.open=function(u){{window._offen=decodeURIComponent(u)}}")
    p.goto(url)
    p.wait_for_timeout(1900)
    p.click("#hand-tipp >> text=👎 Nicht ganz")
    assert "Sagen Sie es uns direkt" in p.text_content("#hand-tipp")
    p.click("#hand-tipp >> text=💬 Nachricht an den Laden")
    assert p.evaluate("window._offen").startswith("https://wa.me/4915733729521?text=Rückmeldung zu meiner Bestellung K47 bei Saray Döner Freital: ")
    ctx.close()


@test
def nochmal_bestellen_und_doener_tag(b, url):
    s = Seite(b, url)
    s.p.click("#nr-1 .plus")
    s.p.click("#nr-91 .plus")
    s.p.click("#nr-91 .wahl button >> nth=1")
    s.p.click("#zettel-leiste")
    s.p.click("[data-laden=altenberg]")
    text = s.wa_text()
    link = [z for z in text.split("\n") if z.startswith("Für die Küche: ")][0].split(": ", 1)[1]
    k = s.ctx.new_page()
    k.add_init_script("window.open=function(u){window._offen=decodeURIComponent(u)}")
    k.goto(link)
    k.click("#offen .bon [data-bestaetigen]")
    antwort = k.evaluate("window._offen")
    nochmal = antwort.split("genau so bestellen: ")[1]
    assert "#nochmal=" in nochmal, antwort
    k.close()
    s.schliessen()
    s = Seite(b, url)
    s.p.goto(nochmal)
    s.p.wait_for_selector("#sammel-dialog:not([hidden])")
    assert "Nochmal bestellen" in s.p.text_content("#sammel-titel")
    inhalt = s.p.text_content("#sammel-inhalt")
    assert "Döner Kebap" in inhalt and "Pizza Saray (30 cm)" in inhalt, inhalt
    s.p.click("#sammel-knoepfe >> text=In meine Bestellung")
    assert len(s.zettel_zeilen()) == 2, s.zettel_zeilen()
    assert s.p.get_attribute("[data-laden=altenberg]", "aria-pressed") == "true"
    s.p.click(".zettel-zu")
    # Fester Döner-Tag: wöchentliche Erinnerung mit Link „#gemeinsam“
    s.p.click("[data-doenertag]")
    s.p.click("#sammel-inhalt [data-tag='3']")
    with s.p.expect_download() as dl:
        s.p.click("#sammel-knoepfe >> text=📅 In den Kalender")
    ics = pathlib.Path(dl.value.path()).read_text()
    assert "RRULE:FREQ=WEEKLY;BYDAY=WE" in ics and "DTSTART:20261021T110000" in ics and "#gemeinsam" in ics, ics
    s.schliessen()
    s = Seite(b, url + "#gemeinsam")
    s.p.wait_for_selector("#sammel-dialog:not([hidden])")
    assert "Gemeinsam bestellen" in s.p.text_content("#sammel-titel")
    s.schliessen()



@test
def getraenk_dazu(b, url):
    s = Seite(b, url)
    s.p.click("#nr-1 .plus")
    s.p.wait_for_selector("#hand-tipp:not([hidden])")
    assert "Getränk dazu?" in s.p.text_content("#hand-tipp") and "2,50 €" in s.p.text_content("#hand-tipp")
    s.p.click("#hand-tipp >> text=Fanta")
    s.p.click("#nr-2 .plus")
    s.p.wait_for_timeout(1600)
    assert s.js("document.getElementById('hand-tipp').hidden"), "Frage kam ein zweites Mal"
    s.p.click("#zettel-leiste")
    s.p.click("[data-laden=freital]")
    text = s.wa_text()
    assert "1× Cola, Fanta, Sprite oder Wasser" in text and "Wunsch: Fanta" in text, text
    s.schliessen()


@test
def letzte_fuenf_bestellungen(b, url):
    s = Seite(b, url)
    for nr in ("1", "50", "130"):
        s.p.click(f"#nr-{nr} .plus")
        s.p.click("#zettel-leiste")
        s.p.click("[data-laden=freital]")
        s.wa_text()
        s.p.click("#zettel-leeren")
        s.p.click("#zettel-leeren")
        s.js("document.getElementById('hand-tipp').hidden=true")
    s.p.reload()
    s.p.wait_for_timeout(400)
    assert "Salat" in s.p.text_content("#letzte-liste")
    s.p.click("#letzte-mehr summary")
    weitere = s.js("[...document.querySelectorAll('#letzte-weitere li')].map(l=>l.textContent)")
    assert len(weitere) == 2 and "Dürüm" in weitere[0] and "Döner Kebap" in weitere[1], weitere
    s.p.click("#letzte-weitere li >> nth=1 >> button")
    assert "Döner Kebap" in s.zettel_zeilen()[0], s.zettel_zeilen()
    s.schliessen()


@test
def boxen_neu_marke_und_chef(b, url):
    paket = {"name": "Familienbox", "preis": "29,00", "inhalt": [{"k": "1", "q": 2}, {"k": "20", "q": 2}, {"k": "73", "q": 1}]}
    neu = {"gruppe": "doener", "abschnitt": "Döner", "nr": "13a", "name": "Döner Spezial", "desc": "mit Feta", "preise": ["8,50"], "seit": "2026-10-15"}
    with tempfile.TemporaryDirectory() as tmp:
        srv, u = bauen_mit({"pakete": [paket], "neu": [neu]}, tmp)
        s = Seite(b, u)
        karte = s.p.text_content(".pakete")
        assert "Familienbox" in karte and "2× Nr. 1 Döner Kebap" in karte and "2× Nr. 20 Kindermenü Nuggets" in karte and "statt" in karte, karte
        assert s.js("!document.querySelector('[data-neu-bis]').hidden")
        s.p.click(".pakete .plus")
        s.p.click("#zettel-leiste")
        s.p.click("[data-laden=freital]")
        text = s.wa_text()
        assert "1× Familienbox (2× Nr. 1 Döner Kebap" in text and "29,00 €" in text, text
        s.schliessen()
        s = Seite(b, u, zeit=datetime.datetime.fromisoformat("2026-11-20T12:00:00+01:00"))
        assert s.js("document.querySelector('[data-neu-bis]').hidden"), "Neu-Marke nach 30 Tagen noch da"
        s.schliessen()
        srv.shutdown()
    gespeichert = []
    ctx, p, fehler = chef_oeffnen(b, url, gespeichert=gespeichert)
    p.click('nav.tabs [data-tab="karte"]')
    p.click("#paket-neu")
    p.fill("#p-name", "Partybox")
    p.fill("#p-preis", "45")
    p.fill("#p-such", "Döner Kebap")
    p.locator(".blatt .liste-gericht", has_text="Döner Kebap").first.click()
    p.click(".blatt [aria-label=mehr]")
    p.click(".blatt >> text=Übernehmen")
    p.click('nav.tabs [data-tab="zeiten"]')
    p.fill("#u-von", "2026-12-24")
    p.fill("#u-bis", "2026-12-26")
    p.click("#u-eintragen")
    p.click("#speichern-knopf")
    p.wait_for_selector(".status.ok >> text=Online")
    d = gespeichert[-1]
    assert d["pakete"] == [{"name": "Partybox", "preis": "45,00", "inhalt": [{"k": "1", "q": 2}]}], d["pakete"]
    assert d["sonderzeiten"]["2026-12-25"] == {"freital": None, "altenberg": None}, d["sonderzeiten"]
    assert d["hinweise"][0]["text"] == "Betriebsferien: Saray Döner ist vom 24.12.2026 bis 26.12.2026 geschlossen." and d["hinweise"][0]["von"] == "2026-12-10", d["hinweise"]
    assert not fehler, fehler
    ctx.close()
    with tempfile.TemporaryDirectory() as tmp:
        srv, u = bauen_mit(d, tmp)
        srv.shutdown()


@test
def kueche_wartezeit_vorschlag(b, url):
    import base64
    gespeichert = []
    ctx = b.new_context(viewport={"width": 1180, "height": 900}, locale="de-DE", timezone_id="Europe/Berlin")
    k = ctx.new_page()
    k.clock.set_fixed_time(ZEIT)
    def github(route):
        r = route.request
        if r.method == "PUT":
            body = json.loads(r.post_data)
            gespeichert.append((body["message"], json.loads(base64.b64decode(body["content"]).decode())))
            route.fulfill(status=200, json={"content": {"sha": "neu"}})
        else:
            route.fulfill(status=200, json={"sha": "alt", "content": base64.b64encode(json.dumps({"hinweise": []}).encode()).decode()})
    k.route("https://api.github.com/**", github)
    k.add_init_script("localStorage.setItem('saray-chef-token','TESTTOKEN')")
    for i in range(8):
        o = {"v": 1, "nr": f"A{i}", "l": "altenberg", "z": "heute", "t": "2026-10-21T18:15", "m": "X", "s": 700, "a": 1792600000000 + i, "p": [[1, "Nr. 1 Döner Kebap", "", "", "", 700]]}
        k.goto(url + "kueche/#b=" + base64.urlsafe_b64encode(json.dumps(o).encode()).decode().rstrip("="))
        k.wait_for_function(f"document.querySelectorAll('#offen .bon').length==={i + 1}")
    k.wait_for_selector("#warte-vorschlag:not([hidden])")
    assert "Viel los in Altenberg: 8 Bestellungen" in k.text_content("#warte-vorschlag")
    k.click("#warte-ja")
    k.wait_for_selector("#warte-vorschlag", state="hidden")
    msg, anp = gespeichert[-1]
    assert msg == "Küche: Wartezeit Altenberg +15 Min." and anp["wartezeit"] == {"altenberg": {"datum": "2026-10-21", "min": 15}}, gespeichert
    ctx.close()



@test
def lieblingswunsch(b, url):
    s = Seite(b, url)
    s.p.click("#nr-1 .plus")
    s.p.click("#zettel-leiste")
    s.p.click("[data-laden=freital]")
    s.p.click("[data-anpassen]")
    s.p.click('[data-o="ohne"][data-w="Zwiebeln"]')
    s.p.fill(".z-notiz", "extra scharf")
    s.p.press(".z-notiz", "Tab")
    s.wa_text()
    s.p.click("#zettel-leeren")
    s.p.click("#zettel-leeren")
    s.js("document.getElementById('hand-tipp').hidden=true")
    s.p.click("#nr-1 .plus")
    s.p.wait_for_selector("#hand-tipp:not([hidden])")
    tipp = s.p.text_content("#hand-tipp")
    assert "Wie immer?" in tipp and "ohne Zwiebeln" in tipp and "extra scharf" in tipp, tipp
    s.p.click("#hand-tipp >> text=Ja, so")
    s.p.click("#zettel-leiste")
    text = s.wa_text()
    assert "Döner Kebap" in text and "ohne Zwiebeln" in text and "Wunsch: extra scharf" in text, text
    s.schliessen()


@test
def chef_app_zu_preise_google(b, url):
    gespeichert = []
    ctx, p, fehler = chef_oeffnen(b, url, gespeichert=gespeichert)
    p.click("[data-zu='freital']")
    assert "Freital doch geöffnet" in p.text_content("[data-zu='freital']")
    p.click('nav.tabs [data-tab="preise"]')
    p.click("[data-preis-gruppe='getraenke']")
    p.click("#preise-erhoehen")
    p.click(".blatt >> text=Ja, übernehmen")
    p.click('nav.tabs [data-tab="mehr"]')
    p.click('[data-seite="google"]')
    p.evaluate("document.querySelectorAll('details').forEach(d=>d.open=true)")
    google = p.evaluate("[...document.querySelectorAll('textarea')].map(t=>t.value).filter(v=>v.indexOf('Döner Kebap')>-1)[0]")
    assert "1 Döner Kebap (Fladenbrot, Fleisch, Salat): 7,00 €" in google and "80 Pizza Margherita (Tomate, Käse): 24 cm 6,50 € / 30 cm 7,50 €" in google, google[:400]
    assert "Tasse Kaffee: 3,00 €" in google, "Google-Text nicht mit neuen Preisen"
    p.click("#speichern-knopf")
    p.wait_for_selector(".status.ok >> text=Online")
    d = gespeichert[-1]
    assert d["sonderzeiten"]["2026-10-21"] == {"freital": None}, d
    assert d["hinweise"][0]["spontan"] == "freital" and "heute leider geschlossen" in d["hinweise"][0]["text"], d["hinweise"]
    assert d["gerichte"]["getraenke|Heiße Getränke|Tasse Kaffee"] == {"preise": ["3,00"]}, d["gerichte"]
    assert "1" not in d["gerichte"], "Döner wurde mit erhöht"
    assert d["staende"][0]["name"] == "Vor Änderung 21.10.2026" and d["staende"][0]["preise"]["getraenke|Heiße Getränke|Tasse Kaffee"] == ["2,50"], d["staende"][0]["name"]
    assert not fehler, fehler
    ctx.close()
    with tempfile.TemporaryDirectory() as tmp:
        srv, u = bauen_mit(d, tmp)
        s = Seite(b, u)
        assert s.js("document.querySelector('[data-status=freital]').getAttribute('data-offen')") == "nein"
        s.schliessen()
        srv.shutdown()



@test
def grosse_schrift(b, url):
    s = Seite(b, url)
    s.p.click("[data-gross]")
    assert s.js("document.documentElement.classList.contains('gross')")
    assert s.js("getComputedStyle(document.documentElement).fontSize") == "19.2px"
    s.p.reload()
    s.p.wait_for_timeout(300)
    assert s.js("document.documentElement.classList.contains('gross')") and "Normale Schrift" in s.p.text_content("[data-gross]")
    s.schliessen()


@test
def kueche_telefon_und_monat(b, url):
    ctx = b.new_context(viewport={"width": 1180, "height": 900}, locale="de-DE", timezone_id="Europe/Berlin")
    k = ctx.new_page()
    k.clock.set_fixed_time(ZEIT)
    k.add_init_script("window.open=function(u){window._offen=decodeURIComponent(u)}")
    k.goto(url + "kueche/")
    k.click("#tel-neu")
    k.click("#tel-laden >> text=Altenberg")
    k.fill("#tel-name", "Frau Müller")
    k.fill("#tel-such", "Döner Kebap")
    k.click("#tel-treffer button >> nth=0")
    k.click("#tel-pos .menge button >> nth=1")
    k.fill("#tel-pos input", "ohne Zwiebeln")
    k.fill("#tel-zeit", "18:30")
    k.click("#tel-ok")
    k.wait_for_selector("#offen .bon")
    bon = k.text_content("#offen .bon")
    assert "📞 Telefon" in bon and "Frau Müller" in bon and "Altenberg" in bon and "2×" in bon and "ohne Zwiebeln" in bon and "14,00 €" in bon, bon
    assert k.locator("#offen .bon [data-bestaetigen]").count() == 0
    k.evaluate("document.getElementById('jahr').open=true")
    text = k.text_content("#monat-inhalt")
    assert "Monatsbericht Oktober 2026" in text and "Bestellungen: 1 (davon 1 per Telefon, 0 online)" in text and "Summe (bar): 14,00 €" in text, text
    k.click("#monat-teilen")
    assert k.evaluate("window._offen").startswith("https://wa.me/?text=Saray Döner – Monatsbericht Oktober 2026")
    ctx.close()



@test
def allergie_und_testbestellung(b, url):
    s = Seite(b, url + "#testbestellung")
    s.p.wait_for_selector("#sammel-dialog:not([hidden])")
    assert "Testbestellung" in s.p.text_content("#sammel-titel")
    s.p.click("#sammel-knoepfe >> text=Los geht’s")
    assert "Döner Kebap" in s.zettel_zeilen()[0]
    s.p.fill(".z-notiz", "Nussallergie, bitte aufpassen")
    s.p.press(".z-notiz", "Tab")
    s.p.click("[data-laden=freital]")
    text = s.wa_text()
    assert text.startswith("*TEST – bitte nicht zubereiten*"), text
    assert "⚠ ALLERGIE / UNVERTRÄGLICHKEIT: Nussallergie, bitte aufpassen" in text, text
    link = [z for z in text.split("\n") if z.startswith("Für die Küche: ")][0].split(": ", 1)[1]
    k = s.ctx.new_page()
    k.goto(link)
    k.wait_for_selector("#offen .bon.allergie")
    assert "Allergie / Unverträglichkeit beachten: Nussallergie" in k.text_content("#offen .bon") and "TEST" in k.text_content("#offen .bon .bnr")
    sys.path.insert(0, str(REPO))
    import laden_seiten
    treffer = k.evaluate("['fıstık alerjisi var','glutenfrei bitte','без арахиса, аллергия','ohne Zwiebeln','extra scharf','no eggs please'].map(t=>new RegExp(" + json.dumps(laden_seiten.ALLERGIE_RE) + ",'i').test(t))")
    assert treffer == [True, True, True, False, False, True], treffer
    k.close()
    s.schliessen()


@test
def kueche_sync_und_tagesplan(b, url):
    a = b.new_context(viewport={"width": 1180, "height": 900}, locale="de-DE", timezone_id="Europe/Berlin")
    k = a.new_page()
    k.clock.set_fixed_time(ZEIT)
    k.add_init_script("window.open=function(u){window._offen=u};window.print=function(){window._druck=(window._druck||0)+1}")
    k.goto(url + "kueche/")
    for name, zeit in (("Ali", "19:00"), ("Bea", "18:15")):
        k.click("#tel-neu")
        k.fill("#tel-name", name)
        k.fill("#tel-such", "Dürüm")
        k.click("#tel-treffer button >> nth=0")
        k.fill("#tel-zeit", zeit)
        k.click("#tel-ok")
    k.click("#plan-knopf")
    zeilen = k.evaluate("[...document.querySelectorAll('#plan tr')].slice(1).map(r=>r.children[0].textContent+' '+r.children[2].textContent)")
    assert zeilen == ["18:15 Bea", "19:00 Ali"] and k.evaluate("window._druck") == 1, zeilen
    k.evaluate("window.dispatchEvent(new Event('afterprint'))")
    k.click("#sync-knopf")
    text = k.evaluate("window._syncText")
    link = text.split("\n")[1]
    assert "#sync=" in link
    a.close()
    c = b.new_context(viewport={"width": 1180, "height": 900}, locale="de-DE", timezone_id="Europe/Berlin")
    k2 = c.new_page()
    k2.clock.set_fixed_time(ZEIT)
    k2.goto(link)
    k2.wait_for_selector("#offen .bon")
    assert k2.locator("#offen .bon").count() == 2 and "#sync" not in k2.url
    k2.goto(link)
    k2.wait_for_timeout(400)
    assert k2.locator("#offen .bon").count() == 2, "doppelt übernommen"
    k2.evaluate("document.getElementById('jahr').open=true")
    assert k2.evaluate("document.querySelector('#jahr .zahlen b').textContent") == "2"
    c.close()



@test
def stammgast_und_sprache_per_link(b, url):
    s = Seite(b, url)
    s.p.click("#nr-1 .plus")
    s.p.click("#zettel-leiste")
    s.p.click("[data-laden=freital]")
    assert "von diesem Handy" not in s.wa_text()
    s.p.click(".zettel-zu")
    s.js("document.getElementById('hand-tipp').hidden=true")
    s.p.click("#nr-50 .plus")
    s.p.click("#zettel-leiste")
    text = s.wa_text()
    assert "· 2. Bestellung von diesem Handy" in text, text
    s.js("var g=JSON.parse(localStorage.getItem('saray-gast'));g.n=4;g.letzte='';localStorage.setItem('saray-gast',JSON.stringify(g))")
    s.p.reload()
    s.p.wait_for_timeout(400)
    s.p.click("#zettel-leiste")
    text = s.wa_text()
    assert "· 5. Bestellung von diesem Handy" in text, text
    link = [z for z in text.split("\n") if z.startswith("Für die Küche: ")][0].split(": ", 1)[1]
    k = s.ctx.new_page()
    k.goto(link)
    k.wait_for_selector("#offen .bon")
    assert "⭐ Stammgast · 5. Bestellung" in k.text_content("#offen .bon .bnr")
    k.close()
    s.schliessen()
    s = Seite(b, url + "?sp=cs")
    assert s.js("document.documentElement.lang") == "cs"
    s.schliessen()


@test
def chef_app_was_kommt(b, url):
    anp = {"aktionen": [{"name": "Döner 5 €", "von": "2026-10-26", "bis": "2026-10-30", "preise": {"1": ["5,00"]}}],
           "sonderzeiten": {"2026-10-31": {"altenberg": None}}}
    ctx, p, fehler = chef_oeffnen(b, url, anp=anp, gespeichert=[])
    p.click('nav.tabs [data-tab="zeiten"]')
    tage = p.evaluate("[...document.querySelectorAll('[data-was-kommt]')].map(d=>d.dataset.wasKommt+' '+d.textContent)")
    alles = " | ".join(tage)
    assert any(t.startswith("2026-10-26") and "Döner 5 € beginnt (bis 30.10.)" in t for t in tage), tage
    assert any(t.startswith("2026-10-31") and "Reformationstag" in t and "Altenberg geschlossen" in t for t in tage), tage
    assert "Buß- und Bettag" not in alles and "Wintersaison Altenberg beginnt" not in alles, alles   # 18.11. und 1.12. liegen außerhalb von 4 Wochen
    assert not fehler, fehler
    ctx.close()


@test
def echte_seite_laedt(b, url):
    """Für --echt: die Seite mit den aktuellen Chef-App-Änderungen lädt ohne Fehler."""
    for vp, mobil in ((HANDY, True), (DESKTOP, False)):
        s = Seite(b, url, vp, mobil=mobil)
        assert "Saray Döner" in s.p.title()
        assert s.js("document.querySelectorAll('.gericht').length") > 20
        s.schliessen()
        ctx = b.new_context()
        p = ctx.new_page()
        fehler = []
        p.on("pageerror", lambda e: fehler.append(str(e)))
        p.goto(url + "chef/")
        p.wait_for_timeout(300)
        assert not fehler, fehler
        ctx.close()


def standard_bauen(ziel):
    """Baut die Seite ohne Änderungen aus der Chef-App – die Tests erwarten den Standard."""
    leer = pathlib.Path(ziel) / "leer.json"
    leer.write_text("{}")
    out = subprocess.run([sys.executable, "-c", f"import build; build.bauen(ziel={str(pathlib.Path(ziel) / 'docs')!r})"],
                         cwd=REPO, env=dict(os.environ, SARAY_ANPASSUNGEN=str(leer)), capture_output=True, text=True)
    if out.returncode:
        print(out.stdout + out.stderr)
        raise SystemExit("Standard-Seite ließ sich nicht bauen")
    return pathlib.Path(ziel) / "docs"


@test
def chef_app_navigation_verlauf_slots(b, url):
    gespeichert = []
    anp = {"gerichte": {"1": {"preise": ["7,50"]}}, "voll": {"freital": {"2026-10-21": ["18:00"], "2026-10-01": ["12:00"]}},
           "preisverlauf": [{"d": "2026-10-20", "s": 1, "k": "1", "n": "1 Döner Kebap", "alt": ["7,00"], "neu": ["7,50"]}]}
    ctx, p, fehler = chef_oeffnen(b, url, anp, gespeichert)
    assert p.evaluate("[...document.querySelectorAll('nav.tabs button')].map(b=>b.dataset.tab).join()") == "heute,karte,preise,zeiten,mehr"
    assert "punkt" in p.get_attribute('nav.tabs [data-tab="mehr"]', "class"), "Punkt für offene Pflicht-Fragen fehlt"
    assert p.locator("#a-hinweis").count() == 1, "Hinweis gehört jetzt unter Heute"
    # Mehr: Menü, Unterseite, zurück; zweiter Tipp auf „Mehr“ zeigt wieder das Menü
    p.click('nav.tabs [data-tab="mehr"]')
    assert p.locator(".menue-punkt[data-seite]").count() == 10
    p.click('[data-seite="drucken"]')
    assert "aushang-fenster.pdf" in p.inner_html("#app")
    p.click('nav.tabs [data-tab="heute"]')
    p.click('nav.tabs [data-tab="mehr"]')
    assert p.locator("#zurueck").count() == 1, "Unterseite nicht gemerkt"
    p.click('nav.tabs [data-tab="mehr"]')
    assert p.locator("#mehr-suche").count() == 1
    # Suche führt in andere Reiter
    p.fill("#mehr-suche", "urlaub")
    p.click(".such-treffer .menue-punkt")
    assert p.get_attribute('nav.tabs [data-tab="zeiten"]', "aria-current") == "page"
    assert p.evaluate("Math.abs(document.getElementById('a-urlaub').getBoundingClientRect().top)<200")
    p.click('nav.tabs [data-tab="mehr"]')
    p.fill("#mehr-suche", "gutschein")
    assert "Geschenkgutscheine" in p.text_content(".such-treffer")
    p.fill("#mehr-suche", "xyzxyz")
    assert "Nichts gefunden" in p.text_content(".such-treffer")
    # Zeiten: Sprungleiste, Viertelstunden-Grenze, ausgebuchte Zeit freigeben
    p.click('nav.tabs [data-tab="zeiten"]')
    assert p.locator('.sprung [data-sprung="a-slots"]').count() == 1
    assert "Heute 18:00 Uhr ausgebucht" in p.text_content("#slot-karte") and "12:00" not in p.text_content("#slot-karte")
    p.click('[data-slot="freital-3"]')
    p.click("#slot-karte >> text=Freigeben")
    # Preise: Verlauf, einzeln zurück
    p.click('nav.tabs [data-tab="preise"]')
    assert "1 Döner Kebap: 7,00 → 7,50 €" in p.text_content("#verlauf-karte")
    p.click('[data-zurueck="1"]')
    p.click("#speichern-knopf")
    p.wait_for_selector(".status.ok >> text=Online")
    d = gespeichert[-1]
    assert "gerichte" not in d, d.get("gerichte")
    assert d["slot_max"] == {"freital": 3} and "voll" not in d, d
    v = d["preisverlauf"]
    assert len(v) == 2 and v[-1]["k"] == "1" and v[-1]["alt"] == ["7,50"] and v[-1]["neu"] == ["7,00"] and v[-1]["d"] == "2026-10-21", v
    assert p.is_disabled('[data-zurueck="1"] >> nth=0') or p.locator('[data-zurueck="1"]').count() == 2
    assert not fehler, fehler
    ctx.close()


@test
def slots_ausgebucht_seite_und_kueche(b, url):
    import base64
    with tempfile.TemporaryDirectory() as tmp:
        srv, u = bauen_mit({"voll": {"freital": {"2026-10-21": ["18:30"]}}}, tmp)
        s = Seite(b, u)
        s.p.add_init_script("try{localStorage.setItem('saray-abholung',JSON.stringify({laden:'freital',tag:'2026-10-21',zeit:'heute, 18:30 Uhr',name:''}))}catch(e){}")
        s.p.reload()
        s.p.wait_for_timeout(300)
        s.p.click("#nr-1 .plus")
        s.p.click("#zettel-leiste")
        opt = s.p.locator("#abhol-zeit option[value='heute, 18:30 Uhr']")
        assert opt.is_disabled() and "ausgebucht" in opt.text_content()
        assert s.p.input_value("#abhol-zeit") == "heute, 18:45 Uhr", s.p.input_value("#abhol-zeit")
        assert "18:30 Uhr ist schon ausgebucht" in s.p.text_content("#abhol-hinweis")
        assert "18:45" in s.wa_text()
        s.schliessen()
        srv.shutdown()
    # Küche: 5 Vorbestellungen für 19:00 in Freital -> Zeit wird online gesperrt
    gespeichert = []
    ctx = b.new_context(viewport={"width": 1180, "height": 900}, locale="de-DE", timezone_id="Europe/Berlin")
    k = ctx.new_page()
    k.clock.set_fixed_time(ZEIT)
    def github(route):
        r = route.request
        if r.method == "PUT":
            body = json.loads(r.post_data)
            gespeichert.append((body["message"], json.loads(base64.b64decode(body["content"]).decode())))
            route.fulfill(status=200, json={"content": {"sha": "neu"}})
        else:
            route.fulfill(status=200, json={"sha": "alt", "content": base64.b64encode(json.dumps({"voll": {"freital": {"2026-10-01": ["12:00"]}}}).encode()).decode()})
    k.route("https://api.github.com/**", github)
    k.add_init_script("localStorage.setItem('saray-chef-token','TESTTOKEN')")
    for i in range(5):
        o = {"v": 1, "nr": f"F{i}", "l": "freital", "z": "heute, 19:00 Uhr", "t": "2026-10-21T19:0" + str(i), "m": "X", "s": 700, "a": 1792600000000 + i, "p": [[1, "Nr. 1 Döner Kebap", "", "", "", 700]]}
        k.goto(url + "kueche/#b=" + base64.urlsafe_b64encode(json.dumps(o).encode()).decode().rstrip("="))
        k.wait_for_function(f"document.querySelectorAll('#offen .bon').length==={i + 1}")
        if i == 3:
            k.wait_for_timeout(300)
            assert not gespeichert, "zu früh gesperrt"
    k.wait_for_selector("#slot-info:not([hidden])")
    msg, anp = gespeichert[-1]
    assert msg == "Küche: ausgebucht freital 2026-10-21 19:00" and anp["voll"] == {"freital": {"2026-10-21": ["19:00"]}}, gespeichert
    assert "Online ausgebucht: Freital 19:00" in k.text_content("#slot-info")
    k.reload()
    k.wait_for_timeout(500)
    assert len(gespeichert) == 1, "doppelt gesperrt"
    ctx.close()


@test
def abholbereit_per_ton(b, url):
    import base64
    s = Seite(b, url)
    gesendet = []
    def ntfy(route):
        r = route.request
        if r.method == "POST":
            gesendet.append((r.url, r.post_data))
            route.fulfill(status=200, json={"id": "x"})
        else:
            gesendet.append((r.url, "GET"))
            route.fulfill(status=200, headers={"Content-Type": "text/event-stream", "Access-Control-Allow-Origin": "*"},
                          body='event: open\ndata: {"event":"open"}\n\ndata: {"id":"1","event":"message","message":"ok"}\n\ndata: {"id":"2","event":"message","message":"fertig"}\n\nretry: 600000\n\n')
    s.ctx.route("https://ntfy.sh/**", ntfy)
    s.p.click("#nr-1 .plus")
    s.p.click("#zettel-leiste")
    s.p.click("[data-laden=freital]")
    text = s.wa_text()
    link = [z for z in text.split("\n") if z.startswith("Für die Küche: ")][0].split(": ", 1)[1]
    roh = link.split("#b=")[1]
    o = json.loads(base64.urlsafe_b64decode(roh + "=" * (-len(roh) % 4)).decode())
    assert len(o["f"]) == 16, o
    assert s.p.locator(".ton-box").count() == 0, "ohne Antippen keine Verbindung"
    assert not gesendet
    s.p.click("#wa-ton")
    s.p.wait_for_selector(".ton-box.fertig")
    assert "ist fertig" in s.p.text_content(".ton-box")
    assert gesendet[0][0].startswith("https://ntfy.sh/saray-" + o["f"] + "/sse?since="), gesendet
    assert s.js("JSON.parse(localStorage.getItem('saray-ton')).z") == "fertig"
    s.p.click("#ton-aus")
    assert s.js("localStorage.getItem('saray-ton')") is None
    # Küche: „Fertig ✓“ meldet an den Dienst (nur das Stichwort und „fertig“)
    k = s.ctx.new_page()
    k.clock.set_fixed_time(ZEIT)
    k.goto(link)
    k.wait_for_selector("#offen .bon")
    k.click("#offen .bon >> text=Fertig ✓")
    k.wait_for_timeout(300)
    assert ("https://ntfy.sh/saray-" + o["f"], "fertig") in gesendet, gesendet
    s.schliessen()


@test
def chef_app_einfuehrung_und_antworten(b, url):
    ctx, p, fehler = chef_oeffnen(b, url, gespeichert=[], tour=True)
    p.wait_for_selector("#tour")
    assert "1 / 11" in p.text_content(".tour-karte") and "Willkommen" in p.text_content(".tour-karte")
    p.click("#tour-weiter")
    assert "Laden heute spontan zu" in p.text_content(".tour-karte")
    p.wait_for_function("parseFloat(getComputedStyle(document.querySelector('.tour-loch')).width)>100")  # hervorgehoben
    for _ in range(6):
        p.click("#tour-weiter")
    assert "Speichern" in p.text_content(".tour-karte") and p.is_visible("#speichern")
    p.click("#tour-zurueck")
    assert "Zeiten" in p.text_content(".tour-karte h3")
    p.click("#tour-ende")
    assert p.locator("#tour").count() == 0 and p.is_hidden("#speichern")
    assert p.evaluate("localStorage.getItem('saray-chef-tour')") == "1"
    p.reload()
    p.wait_for_selector("nav.tabs:not([hidden])")
    p.wait_for_timeout(500)
    assert p.locator("#tour").count() == 0, "Einführung darf nur beim ersten Mal von selbst kommen"
    p.click("#hilfe")
    p.wait_for_selector("#tour")
    p.click("#tour-ende")
    p.click('nav.tabs [data-tab="mehr"]')
    p.click('[data-seite="einfuehrung"]')
    p.wait_for_selector("#tour")
    p.click("#tour-ende")
    # WhatsApp-Antworten
    p.click('nav.tabs [data-tab="mehr"]')
    p.click('[data-seite="antworten"]')
    t = p.text_content("#antw-karte")
    assert "Mo–" in t and "/fertig" in t and "Dresdner Str. 87, 01705 Freital" in t, t
    assert "#speisekarte" in t
    p.click('[data-antw-laden="altenberg"]')
    p.click('[data-antw-sp="tr"]')
    t = p.text_content("#antw-karte")
    assert "Altenberg şubemize hoş geldiniz" in t and "Pzt" in t, t
    ctx.grant_permissions(["clipboard-read", "clipboard-write"])
    p.click("#antw-karte .antw >> nth=0 >> text=Kopieren")
    assert "hoş geldiniz" in p.evaluate("navigator.clipboard.readText()")
    assert not fehler, fehler
    ctx.close()


def main():
    global DOCS
    echt = "--echt" in sys.argv
    tmp = None
    if echt:
        auswahl = [echte_seite_laedt]
    else:
        tmp = tempfile.TemporaryDirectory()
        DOCS = standard_bauen(tmp.name)
        auswahl = [t for t in TESTS if t is not echte_seite_laedt]
    srv, url = server()
    ok = 0
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for t in auswahl:
            try:
                t(b, url)
                ok += 1
                print(f"  ok      {t.__name__}")
            except Exception:
                print(f"  FEHLER  {t.__name__}")
                traceback.print_exc()
        b.close()
    srv.shutdown()
    if tmp:
        tmp.cleanup()
    print(f"{ok} von {len(auswahl)} Tests bestanden")
    return 0 if ok == len(auswahl) else 1


if __name__ == "__main__":
    sys.exit(main())
