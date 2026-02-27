from dataclasses import dataclass

@dataclass
class Port:
    nom: str
    latitude: float
    longitude: float
    locode: str = ""
    pays: str = ""

    def coordonnees(self) -> list:
        return [self.longitude, self.latitude]

    def __str__(self):
        return f"{self.nom} ({self.locode})" if self.locode else self.nom
