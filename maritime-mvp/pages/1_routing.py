import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
from app.services.geocoding import geocoder_port
from app.services.routing import calculer_route
from app.services.emissions import calculer_emissions
from app.components.map import creer_carte
from app.components.charts import graphique_emission_detail
from app.utils.formatters import format_distance, format_duree, format_co2

st.set_page_config(page_title="Routing Maritime", page_icon="🚢", layout="wide")
st.title("🚢 Routing Maritime + CO₂")

# ---- SESSION STATE ----
if "route" not in st.session_state:
    st.session_state.route = None
if "emission" not in st.session_state:
    st.session_state.emission = None

# ---- SIDEBAR ----
st.sidebar.header("Paramètres")

# Routes prédéfinies
st.sidebar.markdown("**Routes rapides :**")
routes_predefinies = {
    "🇨🇳→🇳🇱 Shanghai → Rotterdam": ("Shanghai", "Rotterdam"),
    "🇫🇷→🇺🇸 Marseille → New York": ("Marseille", "New York"),
    "🇯🇵→🇺🇸 Tokyo → Los Angeles": ("Tokyo", "Los Angeles"),
    "🇨🇳→🇦🇪 Shanghai → Dubai": ("Shanghai", "Dubai"),
}

choix = st.sidebar.selectbox("Choisir une route", ["-- Saisie manuelle --"] + list(routes_predefinies.keys()))

if choix != "-- Saisie manuelle --":
    port_depart, port_arrivee = routes_predefinies[choix]
else:
    port_depart  = "Shanghai"
    port_arrivee = "Rotterdam"

st.sidebar.markdown("---")
port_depart  = st.sidebar.text_input("🟢 Port de départ",  port_depart)
port_arrivee = st.sidebar.text_input("🔴 Port d'arrivée", port_arrivee)
cargo        = st.sidebar.number_input("📦 Cargo (tonnes)", min_value=1, value=10)

if st.sidebar.button("🚀 Calculer", use_container_width=True):
    with st.spinner("Geocoding..."):
        depart  = geocoder_port(port_depart)
        arrivee = geocoder_port(port_arrivee)

    if not depart:
        st.error(f"❌ Port '{port_depart}' introuvable")
        st.stop()
    if not arrivee:
        st.error(f"❌ Port '{port_arrivee}' introuvable")
        st.stop()

    with st.spinner("Calcul de la route..."):
        route    = calculer_route(depart, arrivee)
        emission = calculer_emissions(route, cargo)

    st.session_state.route    = route
    st.session_state.emission = emission

# ---- AFFICHAGE ----
if st.session_state.route:
    route    = st.session_state.route
    emission = st.session_state.emission

    # Métriques
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📏 Distance",   format_distance(route.distance_km))
    m2.metric("⏱️ Durée",      format_duree(route.duree_heures))
    m3.metric("🌍 CO₂",       format_co2(emission.co2e_kg))
    m4.metric("📍 Points GPS", route.points_gps)

    # ---- EXPORT CSV ----
    st.markdown("---")

    df = pd.DataFrame([{
        "Port départ":         route.depart.nom,
        "Port arrivée":        route.arrivee.nom,
        "Distance (km)":       round(route.distance_km, 2),
        "Distance (nm)":       round(route.distance_km / 1.852, 2),
        "Durée (heures)":      round(route.duree_heures, 2),
        "Durée (jours)":       round(route.duree_jours, 2),
        "Cargo (tonnes)":      emission.cargo_tonnes,
        "CO₂e (kg)":           round(emission.co2e_kg, 2),
        "CO₂e (tonnes)":       round(emission.co2e_tonnes, 2),
        "Intensité CO₂ (kg/t-km)": round(emission.intensite, 4),
        "Méthode":             emission.methode,
        "Via Suez":            not route.eviter_suez,
        "Eviter HRA":          route.eviter_hra,
    }])

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Exporter en CSV",
        data=csv,
        file_name=f"route_{route.depart.nom}_{route.arrivee.nom}.csv",
        mime="text/csv",
        use_container_width=True
    )

    st.markdown("---")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 🗺️ Carte")
        carte = creer_carte([route])
        st_folium(carte, width=700, height=450)

    with col2:
        st.markdown("### 🌍 Émissions")
        st.plotly_chart(graphique_emission_detail(emission), use_container_width=True)

else:
    st.info("👈 Entre deux ports et clique sur Calculer !")