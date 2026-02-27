def format_distance(km: float) -> str:
    """1852 km → '1 852 km'"""
    return f"{km:,.0f} km".replace(",", " ")

def format_duree(heures: float) -> str:
    """431.5 → '17 jours 23h'"""
    jours = int(heures // 24)
    h = int(heures % 24)
    return f"{jours} jours {h}h"

def format_co2(kg: float) -> str:
    """1842.5 → '1.84 tonnes CO₂e'"""
    return f"{kg/1000:.2f} tonnes CO₂e"

def format_vitesse(noeuds: float) -> str:
    return f"{noeuds} nœuds ({noeuds * 1.852:.1f} km/h)"
