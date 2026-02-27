import time

class Cache:
    def __init__(self):
        self._store = {}

    def get(self, key: str):
        """Retourne la valeur si elle existe et n'a pas expiré"""
        if key in self._store:
            valeur, expiration = self._store[key]
            if time.time() < expiration:
                return valeur
            del self._store[key]
        return None

    def set(self, key: str, valeur, ttl: int):
        """Stocke une valeur avec un TTL en secondes"""
        self._store[key] = (valeur, time.time() + ttl)

    def clear(self):
        self._store = {}

# Instance globale réutilisable partout
cache = Cache()
