import sqlite3
import urllib.request
import json
import time

# Wie viele Pokémon möchtest du laden? (z.B. 151 für Gen 1)
ANZAHL_POKEMON = 151

# Deutsche Typen-Übersetzung
TYPEN_DEUTSCH = {
    'normal': 'Normal', 'fire': 'Feuer', 'water': 'Wasser', 'grass': 'Pflanze',
    'electric': 'Elektro', 'ice': 'Eis', 'fighting': 'Kampf', 'poison': 'Gift',
    'ground': 'Boden', 'flying': 'Flug', 'psychic': 'Psycho', 'bug': 'Käfer',
    'rock': 'Gestein', 'ghost': 'Geist', 'dragon': 'Drache', 'steel': 'Stahl',
    'fairy': 'Fee', 'dark': 'Unlicht'
}

def get_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

conn = sqlite3.connect("pokedex.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS pokemon")

cursor.execute("""
CREATE TABLE pokemon (
    bild TEXT,
    id INTEGER PRIMARY KEY,
    name TEXT,
    typ1 TEXT,
    typ2 TEXT,
    groesse REAL,
    gewicht REAL,
    species TEXT,
    beschreibung TEXT
)
""")

print(f"Lade die ersten {ANZAHL_POKEMON} Pokémon auf Deutsch...")

for poke_id in range(1, ANZAHL_POKEMON + 1):
    try:
        # 1. Basis-Daten (Größe, Gewicht, Bild, Typen)
        data = get_json(f"https://pokeapi.co/api/v2/pokemon/{poke_id}")
        
        # 2. Deutscher Name, Species (Kategorie) und Beschreibung aus den Species-Daten
        species_data = get_json(f"https://pokeapi.co/api/v2/pokemon-species/{poke_id}")
        
        de_name = data['name'].capitalize()
        de_species = None      # z. B. "Samen-Pokémon"
        de_beschreibung = None # Flavor-Text

        # Deutscher Name
        for entry in species_data.get('names', []):
            if entry['language']['name'] == 'de':
                de_name = entry['name']
                break

        # Deutsche Species (Kategorie)
        for entry in species_data.get('genera', []):
            if entry['language']['name'] == 'de':
                de_species = entry['genus']
                break

        # Deutsche Beschreibung (Flavor-Text)
        # Wir nehmen den ersten deutschen Eintrag
        for entry in species_data.get('flavor_text_entries', []):
            if entry['language']['name'] == 'de':
                # Zeilenumbrüche und Sonderzeichen bereinigen
                text = entry['flavor_text'].replace('\f', ' ').replace('\n', ' ')
                de_beschreibung = text
                break

        # Typen ins Deutsche übersetzen
        raw_typ1 = data['types'][0]['type']['name']
        typ1 = TYPEN_DEUTSCH.get(raw_typ1, raw_typ1.capitalize())
        
        typ2 = None
        if len(data['types']) > 1:
            raw_typ2 = data['types'][1]['type']['name']
            typ2 = TYPEN_DEUTSCH.get(raw_typ2, raw_typ2.capitalize())

        groesse = data['height'] / 10
        gewicht = data['weight'] / 10
        bild = data['sprites']['front_default']
        
        if de_species and "-" in de_species:
            # Letzten Bindestrich finden
            parts = de_species.rsplit("-", 1)
            if len(parts) == 2:
                prefix, suffix = parts
                # suffix kleinschreiben und prüfen, ob es "pokémon" ist
                if suffix.lower() in ("pokémon", "pokemon"):
                    de_species = prefix

        cursor.execute("""
            INSERT OR REPLACE INTO pokemon 
            (bild, id, name, typ1, typ2, groesse, gewicht, species, beschreibung)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (bild, poke_id, de_name, typ1, typ2, groesse, gewicht, de_species, de_beschreibung))

        print(f"#{poke_id}: {de_name} ({typ1}) gespeichert.")
        
        # Kurze Pause, um die kostenlose API nicht zu überlasten
        time.sleep(0.05)

    except Exception as e:
        print(f"Fehler bei ID {poke_id}: {e}")

conn.commit()
conn.close()
print("\nFertig! 'pokedex.db' wurde erfolgreich erstellt.")