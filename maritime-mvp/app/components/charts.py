import plotly.graph_objects as go
from app.models.route import Route
from app.models.emission import Emission

def graphique_comparaison(routes: list[Route], emissions: list[Emission]) -> go.Figure:
    """Graphique comparant distance et CO₂ de plusieurs routes"""

    labels = [r.label for r in routes]
    distances = [r.distance_km for r in routes]
    co2 = [e.co2e_tonnes for e in emissions]
    durees = [r.duree_jours for r in routes]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Distance (km)",
        x=labels,
        y=distances,
        marker_color="#0066CC",
        text=[f"{d:,.0f} km" for d in distances],
        textposition="auto"
    ))

    fig.add_trace(go.Bar(
        name="CO₂ (tonnes)",
        x=labels,
        y=co2,
        marker_color="#FF6600",
        text=[f"{c:.1f} t" for c in co2],
        textposition="auto"
    ))

    fig.add_trace(go.Bar(
        name="Durée (jours)",
        x=labels,
        y=durees,
        marker_color="#00AA44",
        text=[f"{d:.1f} j" for d in durees],
        textposition="auto"
    ))

    fig.update_layout(
        barmode="group",
        title="Comparaison des routes",
        height=400,
        margin=dict(t=40, b=20)
    )

    return fig


def graphique_emission_detail(emission: Emission) -> go.Figure:
    """Graphique détail d'une émission"""

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=emission.co2e_tonnes,
        title={"text": "CO₂e (tonnes)"},
        gauge={
            "axis": {"range": [0, 500]},
            "bar": {"color": "#FF6600"},
            "steps": [
                {"range": [0, 100],   "color": "#00AA44"},
                {"range": [100, 300], "color": "#FFCC00"},
                {"range": [300, 500], "color": "#CC0000"}
            ]
        }
    ))

    fig.update_layout(height=300, margin=dict(t=40, b=20))
    return fig
