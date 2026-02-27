import searoute as sr
from app.models.route import Route
from app.models.port import Port
from app.utils.cache import cache
from app.config import CACHE_TTL_ROUTE

def calculer_route(depart: Port, arrivee: Port, eviter_suez: bool = False, eviter_hra: bool = False) -> Route | None:
    """Calcule la route maritime entre deux ports"""

    # Clé de cache unique
    cle = f"route:{depart.nom}:{arrivee.nom}:suez={eviter_suez}:hra={eviter_hra}"
    cached = cache.get(cle)
    if cached:
        return cached

    try:
        result = sr.searoute(
            depart.coordonnees(),
            arrivee.coordonnees()
        )

        props = result["properties"]
        route = Route(
            depart=depart,
            arrivee=arrivee,
            distance_km=props["length"],
            duree_heures=props["duration_hours"],
            geojson=result["geometry"],
            eviter_suez=eviter_suez,
            eviter_hra=eviter_hra
        )

        cache.set(cle, route, CACHE_TTL_ROUTE)
        return route

    except Exception as e:
        print(f"❌ Erreur routing: {e}")
        return None
