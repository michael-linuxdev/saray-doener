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
  "hinweise":  [{"text": "...", "en": "...", "von": "2026-12-20", "bis": "2026-12-24"}]
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
