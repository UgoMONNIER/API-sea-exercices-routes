import requests
from app.models.port import Port
from app.utils.cache import cache
from app.config import NOMINATIM_URL, HTTP_USER_AGENT, CACHE_TTL_PORT

def geocoder_port(nom: str) -> Port | None:
    """Cherche un port par nom et retourne un objet Port"""

    cached = cache.get(f"port:{nom}")
    if cached:
        return cached

    try:
        response = requests.get(
            NOMINATIM_URL,
            params={
                "q": nom,
                "format": "json",
                "limit": 1
            },
            headers={"User-Agent": HTTP_USER_AGENT},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()

        if not data:
            return None

        premier = data[0]
        port = Port(
            nom=nom,
            latitude=float(premier["lat"]),
            longitude=float(premier["lon"])
        )

        cache.set(f"port:{nom}", port, CACHE_TTL_PORT)
        return port

    except requests.RequestException as e:
        print(f"❌ Erreur geocoding {nom}: {e}")
        return None