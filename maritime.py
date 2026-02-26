import requests
import searoute as sr

def geocoder_port(nom_port):
    """Récupère les coordonnées d'un port via son nom"""
    
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": f"Port of {nom_port}",
        "format": "json"
    }
    headers = {"User-Agent": "searoutes-training"}
    
    response = requests.get(url, params=params, headers=headers)
    
    # Vérifier que la requête a bien fonctionné
    if response.status_code != 200:
        print(f"❌ Erreur {response.status_code} pour {nom_port}")
        return None
    
    data = response.json()
    
    if not data:
        print(f"❌ Port '{nom_port}' introuvable")
        return None
    
    premier = data[0]
    return {
        "nom": nom_port,
        "latitude": float(premier["lat"]),
        "longitude": float(premier["lon"])
    }


def calculer_route(port_depart, port_arrivee):
    """Calcule la route maritime entre deux ports"""
    
    # Geocoder les deux ports
    print(f"\n🔍 Recherche de {port_depart}...")
    depart = geocoder_port(port_depart)
    
    print(f"🔍 Recherche de {port_arrivee}...")
    arrivee = geocoder_port(port_arrivee)
    
    if not depart or not arrivee:
        return
    
    print(f"\n📍 {depart['nom']} → lon:{depart['longitude']} lat:{depart['latitude']}")
    print(f"📍 {arrivee['nom']} → lon:{arrivee['longitude']} lat:{arrivee['latitude']}")
    
    # Calculer la route maritime
    print(f"\n⏳ Calcul de la route en cours...")
    
    origine      = [depart['longitude'],  depart['latitude']]
    destination  = [arrivee['longitude'], arrivee['latitude']]
    
    route = sr.searoute(origine, destination)
    props = route['properties']
    
    # Afficher les résultats
    print(f"\n{'='*45}")
    print(f"🚢 Route : {port_depart} → {port_arrivee}")
    print(f"{'='*45}")
    print(f"📏 Distance     : {props['length']:.0f} km")
    print(f"⏱️  Durée         : {props['duration_hours']:.0f} heures ({props['duration_hours']/24:.1f} jours)")
    print(f"🗺️  Points GPS    : {len(route['geometry']['coordinates'])}")
    print(f"{'='*45}")


# --- PROGRAMME PRINCIPAL ---
calculer_route("Shanghai", "Rotterdam")
calculer_route("Marseille", "New York")