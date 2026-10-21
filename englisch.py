"""Englische Texte für die Speisekarte (Namen, Beschreibungen, Überschriften)."""
import re

NAMEN = {
    "Döner vegetarisch": "Vegetarian döner", "Döner vegetarisch mit Käse": "Vegetarian döner with cheese",
    "Halloumi-Döner, vegetarisch": "Halloumi döner (vegetarian)", "Super Döner": "Super döner",
    "Super Döner mit Käse": "Super döner with cheese", "Döner Hawaii": "Döner Hawaii",
    "Schnitzel-Döner": "Schnitzel döner", "Schnitzel-Döner mit Käse": "Schnitzel döner with cheese",
    "Falafel-Döner vegetarisch": "Falafel döner (vegetarian)", "Falafel-Döner vegetarisch mit Käse": "Falafel döner with cheese (vegetarian)",
    "Hähnchen-Döner": "Chicken döner", "Hähnchen-Döner mit Käse": "Chicken döner with cheese",
    "Hähnchen Super Döner": "Chicken super döner", "Hähnchen Super Döner mit Käse": "Chicken super döner with cheese",
    "Hähnchen-Döner-Teller": "Chicken döner plate", "Hähnchen-Döner überbacken": "Chicken döner au gratin",
    "Dürüm vegetarisch": "Vegetarian dürüm", "Dürüm vegetarisch mit Käse": "Vegetarian dürüm with cheese",
    "Super Dürüm": "Super dürüm", "Super Dürüm mit Käse": "Super dürüm with cheese",
    "Halloumi-Dürüm vegetarisch": "Halloumi dürüm (vegetarian)", "Falafel-Dürüm vegetarisch": "Falafel dürüm (vegetarian)",
    "Hähnchen-Dürüm": "Chicken dürüm", "Hähnchen-Dürüm mit Käse": "Chicken dürüm with cheese",
    "Super Hähnchen-Dürüm": "Super chicken dürüm", "Super Hähnchen-Dürüm mit Käse": "Super chicken dürüm with cheese",
    "Döner-Box": "Döner box", "Döner-Box mit Käse": "Döner box with cheese", "Döner-Box Hähnchen": "Chicken döner box",
    "Döner-Box Hähnchen mit Käse": "Chicken döner box with cheese", "Döner-Teller": "Döner plate",
    "Döner-Teller vegetarisch": "Vegetarian döner plate", "Saray-Teller": "Saray plate", "Döner überbacken": "Döner au gratin",
    "Peperoni, Oliven oder Ananas": "Hot peppers, olives or pineapple",
    "Pommes, Salat, Halloumikäse, Käse oder Reis": "Fries, salad, halloumi, cheese or rice",
    "Pizza vegetarisch": "Vegetarian pizza", "Pizza Schinken": "Pizza ham", "Pizza Salami-Schinken": "Pizza salami & ham",
    "Pizza 4 Käse": "Four cheese pizza", "Pizza Döner-Tasche": "Döner calzone", "Pizza 4 Jahreszeiten": "Four seasons pizza",
    "Paprika, Zwiebel, Champignon, Tomate, Peperoni, Ananas, Oliven, Brokkoli oder Mais": "Bell pepper, onion, mushrooms, tomato, hot peppers, pineapple, olives, broccoli or corn",
    "Schinken, Salami, Dönerfleisch oder Hähnchen-Dönerfleisch": "Ham, salami, döner meat or chicken döner meat",
    "Käse, Halloumikäse oder Fetakäse": "Cheese, halloumi or feta", "Pizzabrötchen": "Pizza rolls",
    "Baguette Schinken": "Baguette ham", "Baguette Schinken-Salami": "Baguette ham & salami",
    "Baguette Dönerfleisch": "Baguette döner meat", "Baguette vegetarisch": "Vegetarian baguette",
    "Fladenbrot mit Soße oder ganz": "Flatbread with sauce or plain", "Fladenbrot mit Soße und Käse": "Flatbread with sauce and cheese",
    "Salat": "Salad", "Salat mit Fleisch": "Salad with meat", "Salat mit Käse": "Salad with cheese",
    "Salat mit Fleisch und Käse": "Salad with meat and cheese", "Salat mit Hähnchenfleisch": "Salad with chicken",
    "Salat mit Hähnchenfleisch und Käse": "Salad with chicken and cheese", "Salat Tonno": "Salad tonno", "Salat Hawaii": "Salad Hawaii",
    "Salat mit Schinken": "Salad with ham", "Salat mit Schinken und Ananas": "Salad with ham and pineapple",
    "Bauernsalat": "Farmer's salad", "Salat mit Halloumi": "Salad with halloumi", "Salat mit Falafel": "Salad with falafel",
    "Salat mit Mozzarella": "Salad with mozzarella", "Fischfilet (Seelachs)": "Fish fillet (pollock)",
    "Pommes, klein": "Fries, small", "Pommes, groß": "Fries, large", "Nuggets-Döner": "Nuggets döner",
    "Nuggets-Döner mit Käse": "Nuggets döner with cheese", "Nuggets-Teller": "Nuggets plate", "Nuggets-Box": "Nuggets box",
    "Kindermenü": "Kids' meal", "Kinderdöner": "Kids' döner", "Kinder-Hähnchendöner": "Kids' chicken döner",
    "Kindermenü Nuggets": "Kids' meal nuggets", "Tasse Kaffee": "Cup of coffee", "Kännchen Kaffee": "Pot of coffee",
    "Milchkaffee": "Milky coffee", "Heiße Milch": "Hot milk", "Heiße Schokolade": "Hot chocolate",
    "Apfeltee (türkisch)": "Turkish apple tea", "Früchtetee": "Fruit tea", "Zimttee (türkisch)": "Turkish cinnamon tea",
    "Schwarzer Tee (türkisch)": "Turkish black tea", "Orangentee (türkisch)": "Turkish orange tea",
    "Pfefferminztee": "Peppermint tea", "Kamillentee": "Chamomile tea",
    "Cola, Fanta, Sprite oder Wasser": "Cola, Fanta, Sprite or water", "Apfelschorle oder Mezzo Mix": "Apple spritzer or Mezzo Mix",
    "Apfelsaft, Multivitaminsaft oder Orangensaft": "Apple, multivitamin or orange juice",
}

SAETZE = {
    "mit 3 Zutaten Ihrer Wahl": "with 3 toppings of your choice",
    "mit 4 verschiedenen Käsesorten": "with 4 kinds of cheese",
    "0,5 l": "0.5 l",
    "Calzone, gefüllt mit Dönerfleisch, Fetakäse, Zwiebel": "Calzone filled with döner meat, feta, onion",
    "Döner- oder Hähnchenfleisch, dazu eine dieser Varianten:": "Döner or chicken meat, plus one of these variants:",
    "Döner- oder Hähnchenfleisch, Pommes und Capri-Sonne": "Döner or chicken meat, fries and Capri-Sun",
    "4 Stück, mit Pommes und Capri-Sonne": "4 pieces, with fries and Capri-Sun",
    "mit Salat, Dönerfleisch oder nach Wahl": "with salami, ham, döner meat or of your choice",
    "mit Salami, Schinken, Dönerfleisch oder nach Wahl": "with salami, ham, döner meat or of your choice",
}

WOERTER = {
    "Fladenbrot": "flatbread", "Fleisch": "meat", "Salat": "salad", "Soße": "sauce", "Käse": "cheese",
    "extra viel Fleisch": "extra meat", "viel Fleisch": "extra meat", "extra viel Hähnchenfleisch": "extra chicken",
    "viel Hähnchenfleisch": "extra chicken", "Hähnchenfleisch": "chicken", "Ananas": "pineapple", "Teigrolle": "wrap",
    "Pommes": "fries", "Reis": "rice", "Halloumikäse": "halloumi", "Halloumi": "halloumi", "Falafel": "falafel",
    "Peperoni": "hot peppers", "Oliven": "olives", "Nudeln": "pasta", "Dönerfleisch": "döner meat",
    "Hähnchendöner": "chicken döner", "Döner- und Hähnchendöner": "döner and chicken döner", "Beilage": "side",
    "Tomate": "tomato", "Tomaten": "tomatoes", "Champignon": "mushrooms", "Paprika": "bell pepper",
    "frischer Paprika": "fresh bell pepper", "Brokkoli": "broccoli", "Zwiebel": "onion", "Zwiebeln": "onions",
    "Thunfisch": "tuna", "Schinken": "ham", "Salami": "salami", "Mais": "corn", "Knoblauch": "garlic", "Ei": "egg",
    "Fetakäse": "feta", "Pizzakäse": "pizza cheese", "Hähnchendönerfleisch": "chicken döner meat",
    "Hähnchen-Dönerfleisch": "chicken döner meat", "mit Hackfleisch": "with minced meat", "Hackfleisch": "minced meat",
    "mit Dönerfleisch": "with döner meat", "mit Salat": "with salad", "mit Salat und Soße": "with salad and sauce",
    "mit Pommes": "with fries", "mit Pommes und Salat": "with fries and salad", "Pommes und Käse": "fries and cheese",
    "Salat, Pommes und Käse": "salad, fries and cheese", "mit Thunfisch": "with tuna", "mit Ananas": "with pineapple",
    "mit Zwiebel": "with onion", "türkisch": "Turkish", "0,5 l": "0.5 l", "Salat und Soße": "salad and sauce",
    "Pommes und Salat": "fries and salad", "mit Pommes und Capri-Sonne": "with fries and Capri-Sun",
}

UEBERSCHRIFTEN = {
    "Döner": "Döner", "Hähnchen-Döner": "Chicken döner", "Dürüm": "Dürüm", "Hähnchen-Dürüm": "Chicken dürüm",
    "Box & Teller": "Boxes & plates", "Dönerbox": "Döner box", "Dönerteller": "Döner plates", "Extra-Portion": "Extra portion",
    "Pizza": "Pizza", "Extras auf die Pizza": "Pizza toppings", "Pizzabrötchen": "Pizza rolls", "Lahmacun": "Lahmacun",
    "Türkische Pizza": "Turkish pizza", "Baguette": "Baguette", "Fladenbrot": "Flatbread", "Salate": "Salads",
    "Gemischte Salate": "Mixed salads", "Schnitzel & Nuggets": "Schnitzel & nuggets",
    "Schnitzel, Fisch und Pommes": "Schnitzel, fish and fries", "Chicken Nuggets": "Chicken nuggets",
    "Für Kinder": "For kids", "Kindermenü": "Kids' meals", "Getränke": "Drinks", "Heiße Getränke": "Hot drinks",
    "Tee": "Tea", "Kalte Getränke": "Cold drinks",
    "Dönerfleisch aus Kalb und Pute": "Döner meat made from veal and turkey", "in der Teigrolle": "rolled in a wrap",
    "je Zutat": "per topping", "alle mit Tomate, Eisbergsalat und Mayo": "all with tomato, iceberg lettuce and mayo",
    "alle mit Soße": "all with sauce", "zzgl. 0,25 € Pfand": "plus 0,25 € deposit",
    "Wahlweise Reis statt Pommes.": "Rice instead of fries on request.",
    "Alle Getränke gibt es auch zum Mitnehmen.": "All drinks are also available to take away.",
}


def name(de):
    if de in NAMEN:
        return NAMEN[de]
    return de.replace(" mit Käse", " with cheese")


def text(de):
    if not de:
        return ""
    if de in SAETZE:
        return SAETZE[de]
    teile = [t.strip() for t in de.split(",")]
    aus = []
    for t in teile:
        m = re.match(r"(\d+) Stück$", t)
        if m:
            aus.append(f"{m.group(1)} pieces"); continue
        aus.append(WOERTER.get(t, t))
    s = ", ".join(aus)
    return s[:1].upper() + s[1:]


def titel(de):
    return UEBERSCHRIFTEN.get(de, de)
