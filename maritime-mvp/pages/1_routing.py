import streamlit as st
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
port_depart  = st.sidebar.text_input("🟢 Port de départ",  "Shanghai")
port_arrivee = st.sidebar.text_input("🔴 Port d'arrivée", "Rotterdam")
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
        route   = calculer_route(depart, arrivee)
        emission = calculer_emissions(route, cargo)

    st.session_state.route   = route
    st.session_state.emission = emission

# ---- AFFICHAGE ----
if st.session_state.route:
    route    = st.session_state.route
    emission = st.session_state.emission

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📏 Distance",  format_distance(route.distance_km))
    m2.metric("⏱️ Durée",     format_duree(route.duree_heures))
    m3.metric("🌍 CO₂",      format_co2(emission.co2e_kg))
    m4.metric("📍 Points GPS", route.points_gps)

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
