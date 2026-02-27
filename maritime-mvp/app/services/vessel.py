import requests
from app.utils.cache import cache
from app.config import CACHE_TTL_VESSEL

def get_vessel_info(imo: str) -> dict | None:
    """Récupère les infos d'un navire via son numéro IMO"""

    cle = f"vessel:{imo}"
    cached = cache.get(cle)
    if cached:
        return cached

    try:
        # On utilise l'API publique VesselFinder
        response = requests.get(
            f"https://api.vesselfinder.com/vessels",
            params={"userkey": "demo", "imo": imo},
            timeout=5
        )

        # Si l'API est indisponible on retourne des données simulées
        if response.status_code != 200:
            return _donnees_simulees(imo)

        data = response.json()
        cache.set(cle, data, CACHE_TTL_VESSEL)
        return data

    except Exception:
        return _donnees_simulees(imo)


def _donnees_simulees(imo: str) -> dict:
    """Données fictives pour le développement sans clé API"""
    return {
        "imo": imo,
        "nom": "CMA CGM MARCO POLO",
        "type": "Container Ship",
        "pavillon": "France",
        "latitude": 1.2655,
        "longitude": 103.8198,
        "vitesse": 18.4,
        "cap": 247,
        "destination": "DEHAM",
        "eta": "2024-03-15T14:00:00Z",
        "statut": "Under way",
        "simule": True
    }
