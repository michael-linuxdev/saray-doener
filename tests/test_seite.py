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
def linkshaender_hinweis(b, url):
    s = Seite(b, url, hand_tipp=True)
    s.p.click("#nr-1 .plus")
    assert not s.js("document.getElementById('hand-tipp').hidden"), "Hinweis fehlt beim ersten Plus"
    assert "Döner Kebap ist in Ihrer Bestellung" in s.p.text_content("#hand-tipp")
    s.p.click("#hand-tipp >> text=Knöpfe nach links")
    assert s.js("document.documentElement.classList.contains('links')")
    s.p.click("#hand-tipp >> text=Rückgängig")
    assert not s.js("document.documentElement.classList.contains('links')")
    assert "Fußzeile" in s.p.text_content("#hand-tipp")
    s.p.click("#hand-tipp >> text=OK")
    s.p.reload()
    s.p.wait_for_timeout(200)
    s.p.click("#nr-2 .plus")
    assert s.js("document.getElementById('hand-tipp').hidden"), "Hinweis kam ein zweites Mal"
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


def chef_oeffnen(b, url, anp=None, gespeichert=None):
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
        if r.method == "PUT":
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
    p.click("text=Freital")
    p.locator(".karte", has=p.locator("h3", has_text="Hähnchen")).locator("text=Heute aus").click()
    p.locator(".karte", has=p.locator("h3", has_text="Nuggets")).locator("text=Ab Uhrzeit …").click()
    p.select_option("#ab-zeit", "17:00")
    p.check("#ab-immer")
    p.click("text=Übernehmen")
    # Hinweis
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
