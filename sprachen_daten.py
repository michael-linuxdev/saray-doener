"""Weitere Sprachen der Seite. Je Sprache ein Wörterbuch Englisch -> Sprache in sprachen/<code>.json.

Die Seite schlägt jeden englischen Text nach; fehlt er, bleibt er Englisch. Zahlen im Text stehen im
Wörterbuch als {n} („{n} dishes found“), Platzhalter wie {zeit} oder {list} bleiben unübersetzt stehen.
Die Bestellung an den Laden bleibt immer deutsch. Liste der zu übersetzenden Texte: python3 sprachen_daten.py
"""
import json
import pathlib
import re

HIER = pathlib.Path(__file__).parent
LISTE = [["de", "Deutsch"], ["en", "English"], ["cs", "Čeština"], ["tr", "Türkçe"], ["ru", "Русский"], ["ar", "العربية"]]


# Texte, die der Code zusammensetzt (Zahlen als {n}, Platzhalter in geschweiften Klammern)
EXTRA = ["({ort} only)", "We would love a Google review for Saray Döner {ort}.", " · waiting time approx. {n} min",
         "Busy right now: earliest pickup in about {n} minutes.", "{n} dishes are not available at the chosen time. Please change them above.",
         "choose {n} more toppings", "Closed, opens tomorrow at {zeit}", "Closed, opens on {tag} at {zeit}", "Closed, opens today at {zeit}",
         "Open now, until {zeit}", "{list} sauce", "no {list}", "with {list}", "option {x}", "extra {x}", "and", "not available", "fries", "rice",
         "no sauce", "choose option", "choose topping", "No.", "Train {n} → pickup {n}", "Closing soon – open until {zeit}", "Closing soon: last pickup today at {n}.", "Code {x} does not apply to this pickup.", "{x}: {p} % off", "Online orders paused until {zeit} – please call", "Very busy right now: online orders for today are paused until {n}. Please call or pre-order for another day."]


def woerterbuecher():
    aus = {}
    for code, _ in LISTE[2:]:
        f = HIER / "sprachen" / f"{code}.json"
        aus[code] = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    return aus


def texte():
    """Alle englischen Texte der fertigen Seite (docs/), die übersetzt werden."""
    import html
    h = (HIER / "docs" / "index.html").read_text(encoding="utf-8")
    j = (HIER / "docs" / "js" / "main.js").read_text(encoding="utf-8")
    t = set()
    for attr in ("data-en", "data-en-aria", "data-en-ph", "data-en-title", "data-nen", "data-dn", "data-en-html"):
        t |= {html.unescape(x) for x in re.findall(attr + r'="([^"]*)"', h)}
    for en in re.findall(r"L\('(?:[^'\\]|\\.)*','((?:[^'\\]|\\.)*)'\)", j):
        t.add(en.encode().decode("unicode_escape").encode("latin-1").decode("utf-8"))
    for en in re.findall(r"T\('((?:[^'\\]|\\.)*)'\)", j):
        t.add(en)
    w = re.search(r"var W=\{(.*?)\};", j, re.S)
    t |= set(re.findall(r":'([^']*)'", w.group(1)))
    t |= set(EXTRA)
    norm = {re.sub(r"\d+(?:[.,:]\d+)*", "{n}", x) if re.search(r"\d", x) and not x.startswith("No.") else x for x in t}
    norm = {x for x in norm if not re.match(r"^Add .+ to my order$", x)} | {"Add {x} to my order"}
    return sorted(x for x in norm if x.strip() and re.search(r"[A-Za-z]", x))


if __name__ == "__main__":
    for code, _ in LISTE[2:]:
        d = woerterbuecher()[code]
        fehlt = [x for x in texte() if x not in d]
        print(f"{code}: {len(fehlt)} fehlen")
