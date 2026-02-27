from app.models.emission import Emission
from app.models.route import Route
from app.config import CO2_KG_PER_TONNE_KM, DEFAULT_CARGO_WEIGHT_TONNES

def calculer_emissions(route: Route, cargo_tonnes: float = None) -> Emission:
    """Calcule les émissions CO₂ pour une route donnée"""

    if cargo_tonnes is None:
        cargo_tonnes = DEFAULT_CARGO_WEIGHT_TONNES

    co2e_kg = route.distance_km * cargo_tonnes * CO2_KG_PER_TONNE_KM

    return Emission(
        co2e_kg=co2e_kg,
        distance_km=route.distance_km,
        cargo_tonnes=cargo_tonnes
    )

def comparer_emissions(route_a: Route, route_b: Route, cargo_tonnes: float = None) -> dict:
    """Compare les émissions de deux routes"""

    emission_a = calculer_emissions(route_a, cargo_tonnes)
    emission_b = calculer_emissions(route_b, cargo_tonnes)

    delta_kg = emission_b.co2e_kg - emission_a.co2e_kg
    delta_pct = (delta_kg / emission_a.co2e_kg) * 100

    return {
        "emission_a": emission_a,
        "emission_b": emission_b,
        "delta_kg": delta_kg,
        "delta_pct": delta_pct
    }
