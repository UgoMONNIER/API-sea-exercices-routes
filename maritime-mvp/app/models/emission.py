from dataclasses import dataclass

@dataclass
class Emission:
    co2e_kg: float
    distance_km: float
    cargo_tonnes: float
    methode: str = "GLEC v3"

    @property
    def co2e_tonnes(self):
        return self.co2e_kg / 1000

    @property
    def intensite(self):
        if self.distance_km and self.cargo_tonnes:
            return self.co2e_kg / (self.distance_km * self.cargo_tonnes)
        return 0.0

    def __str__(self):
        return f"{self.co2e_tonnes:.2f} tonnes CO₂e ({self.methode})"
