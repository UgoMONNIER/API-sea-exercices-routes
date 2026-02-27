from dataclasses import dataclass
from app.models.port import Port

@dataclass
class Route:
    depart: Port
    arrivee: Port
    distance_km: float
    duree_heures: float
    geojson: dict
    eviter_suez: bool = False
    eviter_hra: bool = False

    @property
    def duree_jours(self):
        return self.duree_heures / 24

    @property
    def points_gps(self):
        return len(self.geojson.get("coordinates", []))

    @property
    def label(self):
        suez = " (sans Suez)" if self.eviter_suez else ""
        return f"{self.depart.nom} → {self.arrivee.nom}{suez}"

    def __str__(self):
        return f"{self.label} | {self.distance_km:.0f} km | {self.duree_jours:.1f} jours"
