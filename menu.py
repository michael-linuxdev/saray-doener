# Speisekarte Saray Döner Freital – abgeschrieben von der Karte (Stand: Foto vom 10.10.2026)
GRUNDSTAND = "01.02.2024"   # Preisstand der gedruckten Karte = Standard; in der Chef-App „Stand 01.02.2024“
# Format je Gericht: (Nr, Name, Beschreibung, [Preise])  – Preise als Text mit Komma.
# Bei Pizza zwei Preise: [24 cm, 30 cm].

GRUPPEN = [
    {
        "id": "doener", "titel": "Döner",
        "abschnitte": [
            {
                "titel": "Döner", "info": "Dönerfleisch aus Kalb und Pute",
                "gerichte": [
                    ("1", "Döner Kebap", "Fladenbrot, Fleisch, Salat", ["7,00"]),
                    ("2", "Döner mit Käse", "Fladenbrot, Fleisch, Salat, Käse, Soße", ["8,00"]),
                    ("3", "Döner vegetarisch", "Fladenbrot, Salat", ["6,00"]),
                    ("4", "Döner vegetarisch mit Käse", "Fladenbrot, Salat, Soße", ["7,00"]),
                    ("5", "Halloumi-Döner, vegetarisch", "Fladenbrot, Salat, Soße", ["7,00"]),
                    ("6", "Super Döner", "Fladenbrot, extra viel Fleisch, Salat, Soße", ["8,50"]),
                    ("7", "Super Döner mit Käse", "Fladenbrot, extra viel Fleisch, Salat, Soße, Käse", ["9,50"]),
                    ("8", "Döner Hawaii", "Fleisch, Ananas, Salat", ["8,00"]),
                    ("9", "Schnitzel-Döner", "Fladenbrot, Salat", ["7,00"]),
                    ("10", "Schnitzel-Döner mit Käse", "Fladenbrot, Salat, Soße", ["8,00"]),
                    ("11", "Falafel-Döner vegetarisch", "", ["7,00"]),
                    ("12", "Falafel-Döner vegetarisch mit Käse", "", ["8,00"]),
                ],
            },
            {
                "titel": "Hähnchen-Döner",
                "gerichte": [
                    ("30", "Hähnchen-Döner", "Fladenbrot, Hähnchenfleisch, Salat, Soße", ["7,00"]),
                    ("31", "Hähnchen-Döner mit Käse", "Fladenbrot, Hähnchenfleisch, Salat, Käse", ["8,00"]),
                    ("32", "Hähnchen Super Döner", "Fladenbrot, extra viel Hähnchenfleisch, Salat, Soße", ["8,50"]),
                    ("33", "Hähnchen Super Döner mit Käse", "Fladenbrot, extra viel Hähnchenfleisch, Salat, Soße, Käse", ["9,50"]),
                    ("34", "Hähnchen-Döner-Teller", "Salat, Soße", ["10,00"]),
                    ("35", "Hähnchen-Döner-Teller", "Pommes, Soße", ["10,00"]),
                    ("36", "Hähnchen-Döner-Teller", "Salat, Pommes, Soße", ["11,00"]),
                    ("37", "Hähnchen-Döner-Teller", "Salat, Pommes, Käse, Soße", ["12,00"]),
                    ("38", "Hähnchen-Döner überbacken", "Hähnchendöner, Nudeln, Soße, Käse", ["10,00"]),
                ],
            },
        ],
    },
    {
        "id": "duerum", "titel": "Dürüm",
        "abschnitte": [
            {
                "titel": "Dürüm", "info": "in der Teigrolle",
                "gerichte": [
                    ("50", "Dürüm", "Teigrolle, Fleisch, Salat, Soße", ["8,00"]),
                    ("51", "Dürüm mit Käse", "Teigrolle, Fleisch, Salat, Soße, Käse", ["9,00"]),
                    ("52", "Dürüm vegetarisch", "Teigrolle, Salat", ["7,00"]),
                    ("53", "Dürüm vegetarisch mit Käse", "Teigrolle, Salat, Soße", ["8,00"]),
                    ("54", "Super Dürüm", "Teigrolle, viel Fleisch, Salat, Soße", ["9,50"]),
                    ("55", "Super Dürüm mit Käse", "Teigrolle, viel Fleisch, Salat, Soße, Käse", ["10,50"]),
                    ("56", "Dürüm Hawaii", "Teigrolle, Fleisch, Ananas, Salat, Soße", ["9,00"]),
                    ("57", "Halloumi-Dürüm vegetarisch", "Teigrolle, Halloumikäse, Salat, Soße", ["8,00"]),
                    ("58", "Falafel-Dürüm vegetarisch", "Teigrolle, Falafel, Salat, Soße", ["8,00"]),
                ],
            },
            {
                "titel": "Hähnchen-Dürüm",
                "gerichte": [
                    ("40", "Hähnchen-Dürüm", "Teigrolle, Hähnchenfleisch, Salat, Soße", ["8,00"]),
                    ("41", "Hähnchen-Dürüm mit Käse", "Teigrolle, Hähnchenfleisch, Salat, Soße, Käse", ["9,00"]),
                    ("42", "Super Hähnchen-Dürüm", "Teigrolle, viel Hähnchenfleisch, Salat, Soße", ["9,50"]),
                    ("43", "Super Hähnchen-Dürüm mit Käse", "Teigrolle, Hähnchenfleisch, Salat, Soße, Käse", ["10,50"]),
                ],
            },
        ],
    },
    {
        "id": "teller", "titel": "Box & Teller",
        "abschnitte": [
            {
                "titel": "Dönerbox",
                "gerichte": [
                    ("13", "Döner-Box", "Dönerfleisch, Salat, Pommes", ["7,00"]),
                    ("14", "Döner-Box mit Käse", "Dönerfleisch, Salat, Pommes und Käse", ["8,00"]),
                    ("15", "Döner-Box Hähnchen", "Hähnchenfleisch, Salat, Pommes", ["7,00"]),
                    ("16", "Döner-Box Hähnchen mit Käse", "Hähnchenfleisch, Salat, Pommes und Käse", ["8,00"]),
                ],
            },
            {
                "titel": "Dönerteller", "notiz": "Wahlweise Reis statt Pommes.",
                "gerichte": [
                    ("21", "Döner-Teller", "Salat", ["10,00"]),
                    ("22", "Döner-Teller", "Pommes", ["10,00"]),
                    ("23", "Döner-Teller", "Salat, Pommes", ["11,00"]),
                    ("24", "Döner-Teller vegetarisch", "Salat, Pommes, Halloumi, Falafel, Peperoni, Oliven", ["11,00"]),
                    ("25", "Döner-Teller", "Salat, Pommes, Käse", ["12,00"]),
                    ("26", "Saray-Teller", "Döner- und Hähnchendöner, Reis, Pommes, Salat, Halloumikäse, Beilage", ["15,00"]),
                    ("28", "Döner überbacken", "Dönerfleisch, Nudeln, Käse, Soße", ["10,00"]),
                ],
            },
            {
                "titel": "Extra-Portion",
                "gerichte": [
                    ("", "Peperoni, Oliven oder Ananas", "", ["2,00"]),
                    ("", "Pommes, Salat, Halloumikäse, Käse oder Reis", "", ["2,50"]),
                ],
            },
        ],
    },
    {
        "id": "pizza", "titel": "Pizza",
        "abschnitte": [
            {
                "titel": "Pizza", "groessen": ["24 cm", "30 cm"],
                "gerichte": [
                    ("80", "Pizza Margherita", "Tomate, Käse", ["6,50", "7,50"]),
                    ("81", "Pizza Funghi", "Champignon", ["7,50", "8,50"]),
                    ("82", "Pizza Salami", "", ["8,50", "9,50"]),
                    ("83", "Pizza Schinken", "", ["8,50", "9,50"]),
                    ("84", "Pizza vegetarisch", "Paprika, Brokkoli, Champignon, Zwiebel", ["8,50", "9,50"]),
                    ("85", "Pizza Primavera", "Schinken, Champignon", ["8,50", "9,50"]),
                    ("86", "Pizza Toscana", "Salami, Champignon", ["8,50", "9,50"]),
                    ("87", "Pizza Tonno", "Thunfisch, Zwiebel", ["8,50", "9,50"]),
                    ("88", "Pizza Salami-Schinken", "", ["8,50", "9,50"]),
                    ("89", "Pizza Hawaii", "Schinken, Ananas", ["8,50", "9,50"]),
                    ("90", "Pizza Döner", "Dönerfleisch, Zwiebel, Tomate, Oliven", ["9,50", "10,50"]),
                    ("91", "Pizza Saray", "mit 3 Zutaten Ihrer Wahl", ["9,00", "10,00"]),
                    ("92", "Pizza Solino", "Salami, Schinken, Champignon", ["9,00", "10,00"]),
                    ("93", "Pizza 4 Käse", "mit 4 verschiedenen Käsesorten", ["9,00", "10,00"]),
                    ("94", "Pizza Frühling", "Schinken, frischer Paprika, Champignon", ["9,00", "10,00"]),
                    ("95", "Pizza Döner-Tasche", "Calzone, gefüllt mit Dönerfleisch, Fetakäse, Zwiebel", ["9,50", "10,50"]),
                    ("96", "Pizza Freital", "Salami, Schinken, Champignon, Paprika, Zwiebel, Peperoni", ["9,50", "10,50"]),
                    ("97", "Pizza Spezial", "Salami, Schinken, Champignon, Thunfisch", ["9,50", "10,50"]),
                    ("98", "Pizza Halloumi", "Fetakäse, Pizzakäse, Halloumikäse", ["8,50", "9,50"]),
                    ("99", "Pizza Potschappel", "Salami, Schinken, Champignon, Halloumi", ["9,50", "10,50"]),
                    ("100", "Pizza Dynamo", "Salami, Schinken, Oliven, Peperoni, Champignon, Zwiebeln", ["9,50", "10,50"]),
                    ("101", "Pizza 4 Jahreszeiten", "Salami, Schinken, Paprika, Champignon", ["9,50", "10,50"]),
                    ("102", "Pizza America", "Hähnchendönerfleisch, Paprika, Mais, Knoblauch", ["9,50", "10,50"]),
                    ("103", "Pizza Calzone", "Salami, Schinken, Käse", ["9,50", "10,50"]),
                    ("104", "Pizza Mozzarella", "Tomaten", ["8,00", "9,00"]),
                    ("105", "Pizza Rana", "Döner- oder Hähnchenfleisch, dazu eine dieser Varianten:", ["9,50", "10,50"],
                        [("A", "Brokkoli, Oliven, Zwiebel"), ("B", "Peperoni, Mais, Champignon"),
                         ("C", "Zwiebel, Peperoni, Champignon, Ei"), ("D", "Peperoni, Champignon, Tomate, Käse")]),
                ],
            },
            {
                "titel": "Extras auf die Pizza", "info": "je Zutat",
                "gerichte": [
                    ("", "Paprika, Zwiebel, Champignon, Tomate, Peperoni, Ananas, Oliven, Brokkoli oder Mais", "", ["1,50"]),
                    ("", "Schinken, Salami, Dönerfleisch oder Hähnchen-Dönerfleisch", "", ["2,00"]),
                    ("", "Käse, Halloumikäse oder Fetakäse", "", ["2,00"]),
                ],
            },
            {
                "titel": "Pizzabrötchen",
                "gerichte": [
                    ("125", "Pizzabrötchen", "mit Salami, Schinken, Dönerfleisch oder nach Wahl", ["7,50"]),
                ],
            },
        ],
    },
    {
        "id": "lahmacun", "titel": "Lahmacun",
        "abschnitte": [
            {
                "titel": "Türkische Pizza",
                "gerichte": [
                    ("120", "Lahmacun", "mit Hackfleisch", ["4,00"]),
                    ("121", "Lahmacun", "mit Hackfleisch, Salat", ["6,00"]),
                    ("122", "Lahmacun", "mit Dönerfleisch", ["7,00"]),
                    ("123", "Lahmacun", "mit Salat, Dönerfleisch", ["8,00"]),
                    ("124", "Lahmacun", "mit Salat, Dönerfleisch, Käse", ["9,00"]),
                ],
            },
        ],
    },
    {
        "id": "baguette", "titel": "Baguette",
        "abschnitte": [
            {
                "titel": "Baguette", "info": "alle mit Tomate, Eisbergsalat und Mayo",
                "gerichte": [
                    ("150", "Baguette Margherita", "", ["6,00"]),
                    ("151", "Baguette Salami", "", ["7,50"]),
                    ("152", "Baguette Schinken", "", ["7,50"]),
                    ("153", "Baguette Hawaii", "Schinken, Ananas", ["8,00"]),
                    ("154", "Baguette Tonno", "Thunfisch, Zwiebel", ["8,00"]),
                    ("156", "Baguette Schinken-Salami", "", ["7,50"]),
                    ("157", "Baguette Dönerfleisch", "mit Zwiebel", ["8,00"]),
                    ("158", "Baguette Halloumi", "", ["7,00"]),
                    ("159", "Baguette Schnitzel", "", ["7,00"]),
                    ("160", "Baguette vegetarisch", "Paprika, Peperoni, Oliven", ["7,00"]),
                ],
            },
            {
                "titel": "Fladenbrot",
                "gerichte": [
                    ("", "Fladenbrot mit Soße oder ganz", "", ["2,50"]),
                    ("", "Fladenbrot mit Soße und Käse", "", ["3,50"]),
                ],
            },
        ],
    },
    {
        "id": "salate", "titel": "Salate",
        "abschnitte": [
            {
                "titel": "Gemischte Salate", "info": "alle mit Soße",
                "gerichte": [
                    ("130", "Salat", "", ["5,00"]),
                    ("131", "Salat mit Fleisch", "", ["7,00"]),
                    ("132", "Salat mit Käse", "", ["6,50"]),
                    ("133", "Salat mit Fleisch und Käse", "", ["8,00"]),
                    ("134", "Salat mit Hähnchenfleisch", "", ["7,00"]),
                    ("135", "Salat mit Hähnchenfleisch und Käse", "", ["8,00"]),
                    ("136", "Salat Tonno", "mit Thunfisch", ["7,00"]),
                    ("137", "Salat Hawaii", "mit Ananas", ["6,50"]),
                    ("138", "Salat mit Schinken", "", ["6,50"]),
                    ("139", "Salat mit Schinken und Ananas", "", ["7,50"]),
                    ("140", "Bauernsalat", "Käse, Oliven, Peperoni", ["7,50"]),
                    ("141", "Salat mit Halloumi", "", ["7,00"]),
                    ("142", "Salat mit Falafel", "", ["7,00"]),
                    ("143", "Salat mit Mozzarella", "", ["7,00"]),
                ],
            },
        ],
    },
    {
        "id": "schnitzel", "titel": "Schnitzel & Nuggets",
        "abschnitte": [
            {
                "titel": "Schnitzel, Fisch und Pommes",
                "gerichte": [
                    ("70", "Schnitzel", "mit Pommes und Salat", ["10,00"]),
                    ("71", "Fischfilet (Seelachs)", "mit Pommes und Salat", ["10,00"]),
                    ("72", "Pommes, klein", "", ["3,00"]),
                    ("73", "Pommes, groß", "", ["4,00"]),
                ],
            },
            {
                "titel": "Chicken Nuggets",
                "gerichte": [
                    ("60", "Nuggets-Döner", "5 Stück, mit Salat und Soße", ["7,00"]),
                    ("61", "Nuggets-Döner mit Käse", "5 Stück, mit Salat und Soße", ["8,00"]),
                    ("62", "Nuggets-Teller", "7 Stück, mit Pommes", ["10,00"]),
                    ("63", "Nuggets-Teller", "7 Stück, mit Salat", ["10,00"]),
                    ("64", "Nuggets-Teller", "7 Stück, mit Pommes und Salat", ["11,00"]),
                    ("65", "Nuggets-Box", "5 Stück, mit Pommes und Salat", ["7,00"]),
                ],
            },
        ],
    },
    {
        "id": "kinder", "titel": "Für Kinder",
        "abschnitte": [
            {
                "titel": "Kindermenü",
                "gerichte": [
                    ("17", "Kindermenü", "Döner- oder Hähnchenfleisch, Pommes und Capri-Sonne", ["7,00"]),
                    ("18", "Kinderdöner", "Fladenbrot, Dönerfleisch, Salat, Soße", ["6,00"]),
                    ("19", "Kinder-Hähnchendöner", "Fladenbrot, Hähnchenfleisch, Salat, Soße", ["6,00"]),
                    ("20", "Kindermenü Nuggets", "4 Stück, mit Pommes und Capri-Sonne", ["7,00"]),
                ],
            },
        ],
    },
    {
        "id": "getraenke", "titel": "Getränke",
        "abschnitte": [
            {
                "titel": "Heiße Getränke",
                "gerichte": [
                    ("", "Tasse Kaffee", "", ["2,50"]),
                    ("", "Kännchen Kaffee", "", ["4,50"]),
                    ("", "Cappuccino", "", ["3,00"]),
                    ("", "Espresso", "", ["2,50"]),
                    ("", "Milchkaffee", "", ["3,00"]),
                    ("", "Latte macchiato", "", ["3,50"]),
                    ("", "Heiße Milch", "", ["2,20"]),
                    ("", "Heiße Schokolade", "", ["3,00"]),
                ],
            },
            {
                "titel": "Tee",
                "gerichte": [
                    ("", "Apfeltee (türkisch)", "", ["2,20"]),
                    ("", "Früchtetee", "", ["2,20"]),
                    ("", "Zimttee (türkisch)", "", ["2,20"]),
                    ("", "Schwarzer Tee (türkisch)", "", ["2,20"]),
                    ("", "Orangentee (türkisch)", "", ["2,20"]),
                    ("", "Pfefferminztee", "", ["2,20"]),
                    ("", "Kamillentee", "", ["2,20"]),
                ],
            },
            {
                "titel": "Kalte Getränke", "info": "zzgl. 0,25 € Pfand",
                "notiz": "Alle Getränke gibt es auch zum Mitnehmen.",
                "gerichte": [
                    ("", "Cola, Fanta, Sprite oder Wasser", "0,5 l", ["2,50"]),
                    ("", "Apfelschorle oder Mezzo Mix", "0,5 l", ["2,50"]),
                    ("", "Apfelsaft, Multivitaminsaft oder Orangensaft", "", ["2,50"]),
                ],
            },
        ],
    },
]


# ---------- Zutaten und Allergene – abgeschrieben von der gedruckten Karte („Gültig ab 01.02.2024“) ----------
# Zahlen = Bestandteile (ZUTATEN), Buchstaben = Allergene (ALLERGENE). Vom Inhaber bestätigt (Okt. 2026).
ALLERGENE = {
    "a": "Weizenmehl", "b": "Milch und Milcherzeugnisse", "c": "Sellerie, Senf, Soja", "d": "Erbsen",
    "e": "Süßmolkepulver", "f": "Hühnereiweißpulver", "g": "Sesam",
}
ALLERGENE_EN = {
    "a": "Wheat flour", "b": "Milk and milk products", "c": "Celery, mustard, soy", "d": "Peas",
    "e": "Sweet whey powder", "f": "Egg white powder", "g": "Sesame",
}
ZUTATEN = {
    "1": ("Döner", "Hackfleischdrehspieß mit Kalb- und Putenfleisch, gewürzt, z. T. fein zerkleinert, tiefgefroren. Zutaten: Kalbfleisch (68 %), Putenfleisch (22 %), WEIZEN GLUTEN, Zwiebel, Gewürze, (SENF), Zuckerstoffe, Kochsalz, Stabilisator E450. Kann SESAM, SOJA, EI enthalten."),
    "2": ("Chicken Döner", "Tiefgefroren. Zutaten: Hähnchenfleisch (Keule), Paprika, Gewürze (SENF, GLUTEN, SOJA, EI, SESAM), Kochsalz, Zuckerstoffe, Stabilisator E450, Säureregulator E262, E331."),
    "3": ("Gekochter Truthahnschinken", "Geformt, mit 1 % SOJAEIWEISS. Zutaten: Truthahnschinken 57 %, Wasser, Kartoffelstärke, Glukosesirup, Salz, Gewürze (enthält LAKTOSE), Stabilisator E451(i), Geliermittel E407, Antioxidationsmittel E301, Konservierungsstoffe E250–E262."),
    "4": ("Hähnchenschnitzel", "Geformt. Zutaten: Hähnchenbrustfleisch 65 %, Paniermehl (WEIZENMEHL), pflanzliches Öl, Säureregulator, Trinatriumcitrat, Würze, Gewürze, Gewürzextrakt, natürliche Aromen."),
    "5": ("Salami rein Rind", "Zutaten: Rindfleisch, Rindfleischfett, jodiertes Nitritpökelsalz, Konservierungsstoff (Natriumnitrit), Gewürzmischung, SENF, Dextrose, Maltodextrin, Saccharose, Würze, Antioxidationsmittel E301, Gewürzextrakte, Konservierungsstoff E202."),
    "6": ("Türkische Salami", "Zutaten: Rindfleisch, Rindfleischfett, Kochsalz, Gewürzmischung, Dextrose, Maltodextrin, Antioxidationsmittel (E301), Geschmacksverstärker (E621), Konservierungsstoff (E250), Säuerungsmittel, Citronensäure, Gewürzextrakt, Reifekultur."),
    "7": ("Fladenbrot", "Zutaten: WEIZENMEHL, Trinkwasser, Hefe, Verdickungsmittel (E412), Emulgator (E472e), Farbstoff (E170), Antioxidationsmittel (E300), Salz, SESAM."),
    "8": ("Soße", "Zutaten: 50 % Rapsöl, Wasser, Branntweinessig, Zucker, 2,7 % Eigelb, modifizierte Stärke, SENF, MAGERMILCHPULVER, Guarkernmehl, E385."),
    "9": ("Käse in Salzlake, 40 % Fett i. Tr.", "Zutaten: pasteurisierte Kuhmilch, Speisesalz, mikrobielles Lab, Milchsäurekulturen."),
}
# je Abschnitt (Titel wie oben): (Bestandteile, Allergene) – so wie auf der gedruckten Karte
KENNZEICHNUNG = {
    "Döner": ("1,7,8,9", "a,b,c,f,g"),
    "Hähnchen-Döner": ("2,7,8,9", "a,b,c,f,g"),
    "Dürüm": ("1,2,7,8,9", "a,b,c,f,g"),
    "Hähnchen-Dürüm": ("2,7,8,9", "a,b,c,f,g"),
    "Dönerbox": ("1,2,7,8,9", "a,b,c,f,g"),
    "Kindermenü": ("1,2,7,8,9", "a,b,c,f,g"),
    "Dönerteller": ("1,2,7,8,9", "a,b,c,f,g"),
    "Pizza": ("1,2,3,5,6,8,9", "a,b,c,f,g"),
    "Extras auf die Pizza": ("1,2,3,5,6,8,9", "a,b,c,f,g"),
    "Pizzabrötchen": ("1,2,3,5,6,8,9", "a,b,c,f,g"),
    "Türkische Pizza": ("1,2,7,8,9", "a,b,c,d,f,g"),
    "Baguette": ("1,2,3,5,6,7,8,9", "a,b,c,f,g"),
    "Gemischte Salate": ("1,2,7,8,9", "a,b,c,f,g"),
    "Schnitzel, Fisch und Pommes": ("1,2,4,7,8,9", "a,b,c,f,g"),
    "Chicken Nuggets": ("4,8", "a,b,c,f,g"),
}
SOSSEN = ("Knoblauch, Kräuter, Chili", "8", "b,c,e")

# Vegetarisch (ohne Fleisch und Fisch): Nummern bzw. Namen ohne Nummer. Getränke zählen immer dazu,
# neue Gerichte aus der Chef-App, wenn „vegetarisch“ im Namen steht.
VEGETARISCH = {
    "3", "4", "5", "11", "12", "24", "52", "53", "57", "58",
    "80", "81", "84", "93", "98", "104",
    "130", "132", "137", "140", "141", "142", "143",
    "150", "158", "160", "72", "73",
    "Peperoni, Oliven oder Ananas", "Pommes, Salat, Halloumikäse, Käse oder Reis",
    "Paprika, Zwiebel, Champignon, Tomate, Peperoni, Ananas, Oliven, Brokkoli oder Mais", "Käse, Halloumikäse oder Fetakäse",
    "Fladenbrot mit Soße oder ganz", "Fladenbrot mit Soße und Käse",
}

# Pescetarisch = vegetarisch plus Gerichte mit Fisch (ohne Fleisch)
FISCH = {"71", "87", "136", "154"}
