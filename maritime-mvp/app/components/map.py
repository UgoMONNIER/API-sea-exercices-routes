import folium
from app.models.route import Route
from app.models.port import Port

def creer_carte(routes: list[Route] = None, centre: list = [20, 0], zoom: int = 3) -> folium.Map:
    """Crée une carte Folium avec les routes maritimes"""

    m = folium.Map(location=centre, zoom_start=zoom)

    if not routes:
        return m

    couleurs = ["#0066CC", "#FF6600", "#00AA44", "#CC0000"]

    for i, route in enumerate(routes):
        couleur = couleurs[i % len(couleurs)]

        # Tracer la route
        coords = [(c[1], c[0]) for c in route.geojson["coordinates"]]
        folium.PolyLine(
            coords,
            color=couleur,
            weight=3,
            opacity=0.8,
            tooltip=route.label
        ).add_to(m)

        # Marqueur départ (uniquement pour la première route)
        if i == 0:
            folium.Marker(
                [route.depart.latitude, route.depart.longitude],
                popup=f"🟢 {route.depart.nom}",
                icon=folium.Icon(color="green")
            ).add_to(m)

            folium.Marker(
                [route.arrivee.latitude, route.arrivee.longitude],
                popup=f"🔴 {route.arrivee.nom}",
                icon=folium.Icon(color="red")
            ).add_to(m)

    return m


def creer_carte_vessel(vessel: dict) -> folium.Map:
    """Crée une carte avec la position d'un navire"""

    lat = vessel.get("latitude", 0)
    lon = vessel.get("longitude", 0)

    m = folium.Map(location=[lat, lon], zoom_start=5)

    folium.Marker(
        [lat, lon],
        popup=f"🚢 {vessel.get('nom', 'Navire')}",
        tooltip=f"Cap: {vessel.get('cap')}° | Vitesse: {vessel.get('vitesse')} kn",
        icon=folium.Icon(color="blue", icon="ship", prefix="fa")
    ).add_to(m)

    return m
