import requests

# L'URL qu'on appelle
url = "https://nominatim.openstreetmap.org/search"

# Les paramètres de la requête (ce qui va après le ? dans l'URL)
params = {
    "q": "Port of Hamburg",
    "format": "json"
}

# Les headers (informations qu'on envoie au serveur)
headers = {
    "User-Agent": "searoutes-training"
}

# 🚀 L'appel HTTP GET
response = requests.get(url, params=params, headers=headers)

# Afficher les infos de la réponse
print(f"📡 Status code : {response.status_code}")
print(f"📦 Type de contenu : {response.headers['Content-Type']}")

# Convertir la réponse JSON en dictionnaire Python
data = response.json()

# Afficher le premier résultat
premier = data[0]
print(f"\n✅ Port trouvé : {premier['display_name']}")
print(f"📍 Latitude    : {premier['lat']}")
print(f"📍 Longitude   : {premier['lon']}")