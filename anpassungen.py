"""Änderungen des Inhabers (Chef-App) auf die Standard-Speisekarte und -Öffnungszeiten anwenden.

Die Datei daten/anpassungen.json enthält nur die Abweichungen vom Standard (menu.py, STANDORTE in build.py).
„Standard wiederherstellen“ heißt: Datei leeren. Fehlerhafte Einträge werden übersprungen und gemeldet,
damit eine Eingabe in der Chef-App nie die ganze Seite kaputt machen kann.

Aufbau (alle Teile optional):
{
  "gerichte":  {"<schlüssel>": {"name": "...", "desc": "...", "preise": ["7,50"]}},
  "geloescht": ["<schlüssel>", ...],
  "neu":       [{"gruppe": "doener", "abschnitt": "Döner", "nr": "13a", "name": "...", "desc": "...", "preise": ["8,00"]}],
  "zeiten":    {"freital": {"1": ["10:00", "22:00"], "0": null}},      # Wochentag 0 = Sonntag; null = geschlossen
  "verfuegbarkeit": [{"was": "huhn", "datum": "2026-10-21"}],          # wie VERFUEGBARKEIT in build.py
  "hinweise":  [{"text": "...", "en": "...", "von": "2026-12-20", "bis": "2026-12-24"}],
  "sonderzeiten": {"2026-12-24": {"freital": ["10:00", "16:00"], "altenberg": null}},   # einzelne Tage; null = geschlossen
  "wartezeit": {"freital": {"datum": "2026-10-22", "min": 30}},                     # gilt nur an diesem Tag
  "aktionen":  [{"name": "Mittagstisch", "art": "mittag", ...}],                     # art "mittag": eigener Kasten oben
  "winter":    "auto",                                                               # Wintersaison Altenberg: auto/an/aus
  "gutscheine": [{"nr": "G26-001", "h": "<sha256>", "wert": 2000, ...}],           # nur Chef-App; Seite liest sie nicht
  "slot_max":  {"freital": 5, "altenberg": 0},                                       # Vorbestellungen je Viertelstunde, 0 = keine Grenze
  "voll":      {"freital": {"2026-10-23": ["17:30", "17:45"]}},                      # ausgebuchte Viertelstunden (schreibt die Küche)
  "preisverlauf": [{"d": "2026-10-23", "s": 1761200000000, "k": "12", "n": "12 Döner", "alt": ["7,00"], "neu": ["7,50"]}]  # nur Chef-App
}
Schlüssel eines Gerichts: seine Nummer, bei Gerichten ohne Nummer "<gruppe>|<abschnitt>|<name>".
"""
import copy
import json
import re

PREIS_RE = re.compile(r"^\d{1,3},\d{2}$")
ZEIT_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")
DATUM_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TAGE = ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"]
TAGE_EN = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
KURZ = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"]
WOCHE = [1, 2, 3, 4, 5, 6, 0]


def laden(pfad):
    try:
        daten = json.loads(pfad.read_text(encoding="utf-8")) if pfad.exists() else {}
    except (OSError, ValueError) as fehler:
        print(f"WARNUNG: {pfad.name} nicht lesbar ({fehler}) – es gilt der Standard")
        return {}
    return daten if isinstance(daten, dict) else {}


def schluessel(gruppe_id, abschnitt_titel, gericht):
    return gericht[0] if gericht[0] else f"{gruppe_id}|{abschnitt_titel}|{gericht[1]}"


def _preise_ok(preise, anzahl):
    return isinstance(preise, list) and len(preise) == anzahl and all(isinstance(p, str) and PREIS_RE.match(p) for p in preise)


def _text_ok(t, laenge=200, leer=True):
    return isinstance(t, str) and len(t) <= laenge and (leer or t.strip())


def karte(gruppen, anp, warnen):
    """Gibt eine geänderte Kopie der Speisekarte zurück."""
    gruppen = copy.deepcopy(gruppen)
    aendern = anp.get("gerichte") if isinstance(anp.get("gerichte"), dict) else {}
    loeschen = set(x for x in anp.get("geloescht", []) if isinstance(x, str))
    vorhanden = set()
    for gr in gruppen:
        for ab in gr["abschnitte"]:
            anzahl = len(ab.get("groessen") or []) or 1
            neu = []
            for g in ab["gerichte"]:
                k = schluessel(gr["id"], ab["titel"], g)
                vorhanden.add(k)
                if k in loeschen:
                    continue
                g = list(g)
                a = aendern.get(k)
                if isinstance(a, dict):
                    if "name" in a:
                        if _text_ok(a["name"], 80, leer=False):
                            g[1] = a["name"].strip()
                        else:
                            warnen(f"Gericht {k}: Name ungültig – Standard bleibt")
                    if "desc" in a:
                        if _text_ok(a["desc"]):
                            g[2] = a["desc"].strip()
                        else:
                            warnen(f"Gericht {k}: Beschreibung ungültig – Standard bleibt")
                    if "preise" in a:
                        if _preise_ok(a["preise"], len(g[3])):
                            g[3] = list(a["preise"])
                        else:
                            warnen(f"Gericht {k}: Preise {a['preise']!r} ungültig – Standard bleibt")
                neu.append(tuple(g))
            ab["gerichte"] = neu
    nummern = {g[0] for gr in gruppen for ab in gr["abschnitte"] for g in ab["gerichte"] if g[0]}
    for n in anp.get("neu", []) if isinstance(anp.get("neu"), list) else []:
        if not isinstance(n, dict):
            continue
        gr = next((g for g in gruppen if g["id"] == n.get("gruppe")), None)
        ab = gr and next((a for a in gr["abschnitte"] if a["titel"] == n.get("abschnitt")), None)
        nr = str(n.get("nr", "")).strip()
        anzahl = (len(ab.get("groessen") or []) or 1) if ab else 1
        if not ab:
            warnen(f"Neues Gericht {n.get('name')!r}: Kategorie {n.get('gruppe')}/{n.get('abschnitt')} gibt es nicht")
        elif not _text_ok(n.get("name"), 80, leer=False):
            warnen(f"Neues Gericht: Name fehlt")
        elif nr and (nr in nummern or not re.match(r"^[0-9A-Za-z]{1,5}$", nr)):
            warnen(f"Neues Gericht {n['name']!r}: Nummer {nr} schon vergeben oder ungültig")
        elif not _preise_ok(n.get("preise"), anzahl):
            warnen(f"Neues Gericht {n['name']!r}: Preise {n.get('preise')!r} ungültig")
        elif not _text_ok(n.get("desc", "")):
            warnen(f"Neues Gericht {n['name']!r}: Beschreibung ungültig")
        else:
            ab["gerichte"].append((nr, n["name"].strip(), n.get("desc", "").strip(), list(n["preise"])))
            if nr:
                nummern.add(nr)
    for k in loeschen - vorhanden:
        pass  # gelöschte neue/alte Schlüssel, die es nicht (mehr) gibt: still ignorieren
    return gruppen


def _min(t):
    m = ZEIT_RE.match(t)
    return int(m.group(1)) * 60 + int(m.group(2))


def zeiten(standard, anp_laden, warnen, name):
    """standard: {tag: (von, bis)} in Minuten. anp_laden: {"0": ["11:00","22:00"] | None}."""
    z = dict(standard)
    if isinstance(anp_laden, dict):
        for tag, wert in anp_laden.items():
            if tag not in [str(i) for i in range(7)]:
                continue
            t = int(tag)
            if wert is None:
                z.pop(t, None)
            elif (isinstance(wert, list) and len(wert) == 2 and all(isinstance(w, str) and ZEIT_RE.match(w) for w in wert)
                  and _min(wert[0]) < _min(wert[1])):
                z[t] = (_min(wert[0]), _min(wert[1]))
            else:
                warnen(f"Öffnungszeit {name} {TAGE[t]}: {wert!r} ungültig – Standard bleibt")
    return z


def uhr(m, en=False):
    h, r = divmod(m, 60)
    if en:
        return f"{h}:{r:02d}"
    return f"{h}:{r:02d}" if r else f"{h}"


def zeilen(z):
    """Fasst gleiche Zeiten aufeinanderfolgender Tage zusammen: [(text_de, zeit_de, tage, text_en, zeit_en)]."""
    gruppen = []
    for t in WOCHE:
        wert = z.get(t)
        if gruppen and gruppen[-1][1] == wert:
            gruppen[-1][0].append(t)
        else:
            gruppen.append(([t], wert))
    aus = []
    for tage, wert in gruppen:
        if len(tage) == 1:
            de, en, kurz = TAGE[tage[0]], TAGE_EN[tage[0]], KURZ[tage[0]]
        elif len(tage) == 2:
            de = f"{TAGE[tage[0]]} und {TAGE[tage[1]]}"
            en = f"{TAGE_EN[tage[0]]} and {TAGE_EN[tage[1]]}"
            kurz = f"{KURZ[tage[0]]}–{KURZ[tage[1]]}"
        else:
            de = f"{TAGE[tage[0]]} bis {TAGE[tage[-1]]}"
            en = f"{TAGE_EN[tage[0]]} to {TAGE_EN[tage[-1]]}"
            kurz = f"{KURZ[tage[0]]}–{KURZ[tage[-1]]}"
        if wert:
            zeit_de = f"{uhr(wert[0])}–{uhr(wert[1])} Uhr"
            zeit_en = f"{uhr(wert[0], True)}–{uhr(wert[1], True)}"
        else:
            zeit_de, zeit_en = "geschlossen", "closed"
        aus.append({"de": de, "en": en, "kurz": kurz, "zeit": zeit_de, "zeit_en": zeit_en, "tage": tage, "wert": wert})
    return aus


def regeln(liste, warnen):
    ok = []
    for r in liste if isinstance(liste, list) else []:
        was = r.get("was") if isinstance(r, dict) else None
        if not (isinstance(was, str) or (isinstance(was, list) and all(isinstance(w, str) for w in was))):
            warnen(f"Verfügbarkeit: Regel {r!r} ohne gültiges „was“")
            continue
        sauber = {"was": was}
        for feld in ("ab", "bis"):
            if feld in r:
                if isinstance(r[feld], str) and ZEIT_RE.match(r[feld]):
                    sauber[feld] = r[feld]
                else:
                    warnen(f"Verfügbarkeit: {feld} {r[feld]!r} ungültig")
        if r.get("laden") in ("freital", "altenberg"):
            sauber["laden"] = r["laden"]
        if "datum" in r:
            d = r["datum"]
            if (isinstance(d, str) and DATUM_RE.match(d)) or (isinstance(d, list) and all(isinstance(x, str) and DATUM_RE.match(x) for x in d)):
                sauber["datum"] = d
            else:
                warnen(f"Verfügbarkeit: Datum {d!r} ungültig")
                continue
        if isinstance(r.get("tage"), list) and all(isinstance(x, int) and 0 <= x <= 6 for x in r["tage"]):
            sauber["tage"] = r["tage"]
        ok.append(sauber)
    return ok


def hinweise(liste, warnen):
    ok = []
    for h in liste if isinstance(liste, list) else []:
        if (isinstance(h, dict) and _text_ok(h.get("text"), 200, leer=False)
                and all(isinstance(h.get(f), str) and DATUM_RE.match(h[f]) for f in ("von", "bis"))):
            ok.append({"text": h["text"].strip(), "en": h.get("en", "") if _text_ok(h.get("en", "")) else "",
                       "von": h["von"], "bis": h["bis"]})
        else:
            warnen(f"Hinweis {h!r} ungültig")
    return ok


LAEDEN = ("freital", "altenberg")


def sonderzeiten(d, warnen, ab_datum):
    """{"2026-12-24": {"freital": (600, 960) | None}} – nur Tage ab ab_datum (ISO), sortiert."""
    ok = {}
    for tag, laeden in sorted(d.items()) if isinstance(d, dict) else []:
        if not (isinstance(tag, str) and DATUM_RE.match(tag)) or not isinstance(laeden, dict):
            warnen(f"Besonderer Tag {tag!r} ungültig")
            continue
        if tag < ab_datum:
            continue
        for laden, wert in laeden.items():
            if laden not in LAEDEN:
                continue
            if wert is None:
                ok.setdefault(tag, {})[laden] = None
            elif (isinstance(wert, list) and len(wert) == 2 and all(isinstance(w, str) and ZEIT_RE.match(w) for w in wert)
                  and _min(wert[0]) < _min(wert[1])):
                ok.setdefault(tag, {})[laden] = (_min(wert[0]), _min(wert[1]))
            else:
                warnen(f"Besonderer Tag {tag} {laden}: {wert!r} ungültig")
    return ok


SLOT_STANDARD = 5   # Vorbestellungen je Viertelstunde, wenn in der Chef-App nichts eingestellt ist


def slot_max(d, warnen):
    """Höchstzahl Vorbestellungen je Viertelstunde und Laden (0 = keine Grenze)."""
    ok = {l: SLOT_STANDARD for l in LAEDEN}
    for laden, n in d.items() if isinstance(d, dict) else []:
        if laden in LAEDEN and isinstance(n, int) and not isinstance(n, bool) and 0 <= n <= 30:
            ok[laden] = n
        else:
            warnen(f"Höchstzahl je Viertelstunde {laden}: {n!r} ungültig")
    return ok


def voll(d, warnen, ab_datum):
    """Ausgebuchte Viertelstunden: {laden: {datum: [HH:MM, …]}} – vergangene Tage fallen weg."""
    ok = {}
    for laden, tage in d.items() if isinstance(d, dict) else []:
        if laden not in LAEDEN or not isinstance(tage, dict):
            warnen(f"Ausgebucht {laden}: {tage!r} ungültig")
            continue
        for tag, zeiten in tage.items():
            if not (isinstance(tag, str) and DATUM_RE.match(tag) and isinstance(zeiten, list)):
                warnen(f"Ausgebucht {laden} {tag}: ungültig")
                continue
            if tag < ab_datum:
                continue
            z = sorted({x for x in zeiten if isinstance(x, str) and ZEIT_RE.match(x)}, key=_min)[:96]
            if z:
                ok.setdefault(laden, {})[tag] = [f"{_min(x) // 60:02d}:{_min(x) % 60:02d}" for x in z]
    return ok


def wartezeit(d, warnen):
    ok = {}
    for laden, w in d.items() if isinstance(d, dict) else []:
        if laden in LAEDEN and isinstance(w, dict) and isinstance(w.get("datum"), str) and DATUM_RE.match(w["datum"]) \
                and isinstance(w.get("min"), int) and 0 < w["min"] <= 120:
            ok[laden] = {"datum": w["datum"], "min": w["min"]}
        else:
            warnen(f"Wartezeit {laden}: {w!r} ungültig")
    return ok


def aktionen(liste, gruppen, warnen):
    """Sonderaktionen: [{"name", "von", "bis", "tage"?, "laden"?, "zeit_ab"?, "zeit_bis"?, "preise": {schlüssel: ["5,00"]}}].
    Gibt die gültigen zurück, Schlüssel umgestellt auf das data-k der Seite (Nummer oder Name)."""
    gerichte = {schluessel(gr["id"], ab["titel"], g): (g[0] or g[1], len(g[3]))
                for gr in gruppen for ab in gr["abschnitte"] for g in ab["gerichte"]}
    ok = []
    for a in liste if isinstance(liste, list) else []:
        if not (isinstance(a, dict) and _text_ok(a.get("name"), 60, leer=False)
                and all(isinstance(a.get(f), str) and DATUM_RE.match(a[f]) for f in ("von", "bis")) and a["von"] <= a["bis"]):
            warnen(f"Aktion {a!r} ungültig (Name, von, bis)")
            continue
        preise = {}
        for k, p in (a.get("preise") or {}).items() if isinstance(a.get("preise"), dict) else []:
            if k not in gerichte:
                continue  # Gericht gibt es nicht mehr: still überspringen
            if _preise_ok(p, gerichte[k][1]):
                preise[gerichte[k][0]] = list(p)
            else:
                warnen(f"Aktion {a['name']!r}: Preise für {k} ungültig")
        if not preise:
            warnen(f"Aktion {a['name']!r}: keine gültigen Gerichte")
            continue
        sauber = {"name": a["name"].strip(), "von": a["von"], "bis": a["bis"], "preise": preise}
        if a.get("art") == "mittag":
            sauber["art"] = "mittag"
        if isinstance(a.get("tage"), list) and a["tage"] and all(isinstance(x, int) and 0 <= x <= 6 for x in a["tage"]):
            sauber["tage"] = sorted(set(a["tage"]))
        if a.get("laden") in LAEDEN:
            sauber["laden"] = a["laden"]
        za, zb = a.get("zeit_ab"), a.get("zeit_bis")
        if za or zb:
            if isinstance(za, str) and isinstance(zb, str) and ZEIT_RE.match(za) and ZEIT_RE.match(zb) and _min(za) < _min(zb):
                sauber["zeit_ab"], sauber["zeit_bis"] = za, zb
            else:
                warnen(f"Aktion {a['name']!r}: Uhrzeit {za!r}–{zb!r} ungültig – gilt ganztags")
        ok.append(sauber)
    return ok


def nummern(gruppen, anp, warnen):
    """Andere Nummer für ein Gericht (nur Anzeige): {"gerichte": {"12": {"nr": "12a"}}} -> {"12": "12a"}.
    Intern bleibt die alte Nummer der Schlüssel (Varianten, Sperren, Aktionen hängen daran)."""
    aendern = anp.get("gerichte") if isinstance(anp.get("gerichte"), dict) else {}
    alle = [g[0] for gr in gruppen for ab in gr["abschnitte"] for g in ab["gerichte"] if g[0]]
    neu = {}
    for k, a in aendern.items():
        if not (isinstance(a, dict) and "nr" in a) or k not in alle:
            continue
        n = str(a["nr"]).strip()
        if n == k:
            continue
        if not re.match(r"^[0-9A-Za-z]{1,5}$", n):
            warnen(f"Gericht {k}: Nummer {n!r} ungültig – bleibt {k}")
            continue
        neu[k] = n
    angezeigt = [neu.get(n, n) for n in alle]
    for k, n in list(neu.items()):
        if angezeigt.count(n) > 1:
            warnen(f"Gericht {k}: Nummer {n} doppelt – bleibt {k}")
            del neu[k]
    return neu


WINTER_STANDARD = ("12-01", "03-15")   # Wintersaison Altenberg (Monat-Tag), gilt bei "auto"


def winter(wert, warnen):
    """Wintersaison Altenberg: "auto" (Standard, nach Datum), "an" oder "aus"."""
    if wert in (None, "auto", "an", "aus"):
        return wert or "auto"
    warnen(f"Wintersaison {wert!r} ungültig – automatisch")
    return "auto"


CODE_H_RE = re.compile(r"^[0-9a-f]{64}$")


def codes(liste, warnen, heute):
    """Firmen-Rabattcodes: [{"h": sha256("saray|CODE"), "name", "prozent", "laden"?, "zeit_ab"/"zeit_bis"?, "bis"?, "hinweis"?}].
    Der Code selbst steht nirgends – nur sein Prüfwert. Abgelaufene fallen weg."""
    ok = []
    for c in liste if isinstance(liste, list) else []:
        if not (isinstance(c, dict) and isinstance(c.get("h"), str) and CODE_H_RE.match(c["h"]) and _text_ok(c.get("name"), 60, leer=False)
                and isinstance(c.get("prozent"), int) and 1 <= c["prozent"] <= 50):
            warnen(f"Firmen-Code {c!r} ungültig")
            continue
        if c.get("bis") and not (isinstance(c["bis"], str) and DATUM_RE.match(c["bis"])):
            warnen(f"Firmen-Code {c['name']!r}: Datum ungültig")
            continue
        if c.get("bis") and c["bis"] < heute:
            continue
        x = {"h": c["h"], "name": c["name"].strip(), "prozent": c["prozent"]}
        if c.get("bis"):
            x["bis"] = c["bis"]
        if c.get("laden") in LAEDEN:
            x["laden"] = c["laden"]
        za, zb = c.get("zeit_ab"), c.get("zeit_bis")
        if isinstance(za, str) and isinstance(zb, str) and ZEIT_RE.match(za) and ZEIT_RE.match(zb) and _min(za) < _min(zb):
            x["za"], x["zb"] = _min(za), _min(zb)
        ok.append(x)
    return ok


PAUSE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T([01]\d|2[0-3]):[0-5]\d$")


def pause(d, warnen):
    """Bestell-Pause je Laden: {"freital": {"bis": "2026-10-22T19:30"}} – bis dahin keine Online-Bestellungen für heute."""
    ok = {}
    for laden, p in d.items() if isinstance(d, dict) else []:
        if laden in LAEDEN and isinstance(p, dict) and isinstance(p.get("bis"), str) and PAUSE_RE.match(p["bis"]):
            ok[laden] = {"bis": p["bis"]}
        else:
            warnen(f"Bestell-Pause {laden}: {p!r} ungültig")
    return ok


def pakete(liste, gruppen, warnen, heute):
    """Familien- und Party-Boxen: [{"name", "preis": "29,00", "inhalt": [{"k": "1", "q": 2}], "desc"?, "von"?, "bis"?}].
    "k" ist der Schlüssel des Gerichts (Nummer oder Name). Gibt die gültigen, nicht abgelaufenen zurück, mit Normalpreis."""
    gerichte = {}
    for gr in gruppen:
        for ab in gr["abschnitte"]:
            for g in ab["gerichte"]:
                gerichte[g[0] or g[1]] = g
                gerichte[schluessel(gr["id"], ab["titel"], g)] = g   # Chef-App-Schlüssel
    ok = []
    for p in liste if isinstance(liste, list) else []:
        if not (isinstance(p, dict) and _text_ok(p.get("name"), 40, leer=False) and isinstance(p.get("preis"), str) and PREIS_RE.match(p["preis"])
                and isinstance(p.get("inhalt"), list) and p["inhalt"]):
            warnen(f"Box {p!r} ungültig")
            continue
        inhalt = []
        for x in p["inhalt"][:12]:
            if isinstance(x, dict) and x.get("k") in gerichte and isinstance(x.get("q"), int) and 1 <= x["q"] <= 20:
                g = gerichte[x["k"]]
                inhalt.append({"k": g[0] or g[1], "q": x["q"]})
        if not inhalt:
            warnen(f"Box {p['name']!r}: keine gültigen Gerichte")
            continue
        for f in ("von", "bis"):
            if p.get(f) and not (isinstance(p[f], str) and DATUM_RE.match(p[f])):
                p = dict(p)
                p.pop(f)
        if p.get("bis") and p["bis"] < heute:
            continue
        normal = sum(int(gerichte[x["k"]][3][0].replace(",", "")) * x["q"] for x in inhalt)
        teile = [f'{x["q"]}× {(("Nr. " + gerichte[x["k"]][0] + " ") if gerichte[x["k"]][0] else "")}{gerichte[x["k"]][1]}' for x in inhalt]
        ok.append({"name": p["name"].strip(), "preis": p["preis"], "inhalt": inhalt, "text": ", ".join(teile), "normal": normal,
                   "desc": p.get("desc", "").strip() if _text_ok(p.get("desc", ""), 120) else "", "von": p.get("von", ""), "bis": p.get("bis", "")})
    return ok
