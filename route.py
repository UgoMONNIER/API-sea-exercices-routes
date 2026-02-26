import searoute as sr

# Coordonnées [longitude, latitude]
shanghai  = [121.4737, 31.2304]
rotterdam = [4.4777,   51.9244]

# Calculer la route maritime
route = sr.searoute(shanghai, rotterdam)

# Afficher les résultats
props = route['properties']

print("✅ Route calculée avec succès !")
print(f"📏 Distance    : {props['length']:.0f} km")
print(f"⏱️  Durée estimée : {props['duration_hours']:.0f} heures")
print(f"🚢 Nb de points : {len(route['geometry']['coordinates'])} points GPS")