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


def chef_oeffnen(b, url, anp=None, gespeichert=None, vorher=None):
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
        if "/commits?" in r.url:
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
    p.click('nav.tabs [data-tab="mehr"]')
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
                         "desc": "Fladenbrot, Fleisch, Salat, Feta", "preise": ["9,00"]}], d
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
    p.click("text=Alles auf Standard zurücksetzen")
    p.click(".blatt >> text=Ja, zurücksetzen")
    p.wait_for_selector(".status.ok")
    assert gespeichert == [{}], gespeichert
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


def bauen_mit(anp, ordner):
    datei = pathlib.Path(ordner) / "anp.json"
    datei.write_text(json.dumps(anp))
    out = subprocess.run([sys.executable, "-c", f"import build; build.bauen(ziel={str(pathlib.Path(ordner) / 'docs')!r})"],
                         cwd=REPO, env=dict(os.environ, SARAY_ANPASSUNGEN=str(datei), SARAY_HEUTE="2026-10-21"), capture_output=True, text=True)
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
    p.click("text=Geschlossen")
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
    p.click('nav.tabs [data-tab="mehr"]')
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
    assert karten == ["91", "125", "130"], karten
    assert not s.js("document.querySelector('.beliebt').hidden")
    s.p.fill("#suche-feld", "pizza")
    sichtbar = s.js("[...document.querySelectorAll('.gericht:not([hidden])')].map(g=>g.dataset.k)")
    assert "80" in sichtbar and "82" not in sichtbar, sichtbar
    s.p.fill("#suche-feld", "")
    s.p.click("#veg-schalter")
    assert not s.js("document.getElementById('nr-1').hidden")
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
    # nächster Besuch drei Stunden später: einmal fragen; danach nicht mehr
    ms = int(ZEIT.timestamp() * 1000) - 3 * 3600 * 1000
    for fertig in (False, True):
        ctx = b.new_context(viewport=HANDY, locale="de-DE", timezone_id="Europe/Berlin", reduced_motion="reduce", is_mobile=True, has_touch=True)
        p = ctx.new_page()
        p.clock.set_fixed_time(ZEIT)
        wert = json.dumps({"l": "freital", "t": ms, **({"fertig": 1} if fertig else {})})
        p.add_init_script(f"try{{localStorage.setItem('saray-hand-gefragt','1');localStorage.setItem('saray-bewertung',{json.dumps(wert)})}}catch(e){{}}")
        p.goto(url)
        p.wait_for_timeout(1900)
        if not fertig:
            assert not p.evaluate("document.getElementById('hand-tipp').hidden"), "Bewertungs-Hinweis fehlt"
            assert "Hat’s geschmeckt?" in p.text_content("#hand-tipp") and "Freital" in p.text_content("#hand-tipp")
            assert '"fertig":1' in p.evaluate("localStorage.getItem('saray-bewertung')")
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
        assert route.request.headers.get("authorization") == "Bearer GCKEY"
        heute = "start=" in route.request.url and len(gefragt) % 2 == 1
        route.fulfill(status=200, headers={"Access-Control-Allow-Origin": "*"}, json={"hits": [
            {"path": "/", "count": 30 if heute else 200, "event": False},
            {"path": "whatsapp-freital", "count": 4 if heute else 21, "event": True},
            {"path": "anrufen-altenberg", "count": 2 if heute else 9, "event": True}]})
    p.route("https://saraymicana.goatcounter.com/**", gc)
    p.click('nav.tabs [data-tab="mehr"]')
    p.fill("#gc-schl", " GCKEY ")
    p.click(".karte:has(#gc-schl) >> text=Speichern")
    p.wait_for_selector("table.zahlen")
    zeilen = p.evaluate("[...document.querySelectorAll('table.zahlen tr')].map(r=>r.innerText.replace(/\\s+/g,' ').trim())")
    assert any(z.startswith("WhatsApp Freital") and z.split()[-2:] in (["4", "21"], ["21", "4"]) for z in zeilen), zeilen
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
