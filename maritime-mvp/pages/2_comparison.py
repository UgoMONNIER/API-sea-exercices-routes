import streamlit as st
from streamlit_folium import st_folium
from app.services.geocoding import geocoder_port
from app.services.routing import calculer_route
from app.services.emissions import calculer_emissions, comparer_emissions
from app.components.map import creer_carte
from app.components.charts import graphique_comparaison
from app.utils.formatters import format_distance, format_duree, format_co2

st.set_page_config(page_title="Comparaison Routes", page_icon="⚖️", layout="wide")
st.title("⚖️ Comparaison de Routes")
st.markdown("Compare la route normale vs route alternative (ex: contournement Suez)")

# ---- SESSION STATE ----
if "routes" not in st.session_state:
    st.session_state.routes = None
if "emissions" not in st.session_state:
    st.session_state.emissions = None

# ---- SIDEBAR ----
st.sidebar.header("Paramètres")
port_depart  = st.sidebar.text_input("🟢 Port de départ",  "Shanghai")
port_arrivee = st.sidebar.text_input("🔴 Port d'arrivée", "Rotterdam")
cargo        = st.sidebar.number_input("📦 Cargo (tonnes)", min_value=1, value=10)

st.sidebar.markdown("---")
st.sidebar.markdown("**Options route B :**")
eviter_suez = st.sidebar.checkbox("Éviter Suez (Mer Rouge)", value=True)
eviter_hra  = st.sidebar.checkbox("Éviter zones pirates (HRA)", value=False)

if st.sidebar.button("🚀 Comparer", use_container_width=True):
    with st.spinner("Geocoding..."):
        depart  = geocoder_port(port_depart)
        arrivee = geocoder_port(port_arrivee)

    if not depart or not arrivee:
        st.error("❌ Port introuvable")
        st.stop()

    with st.spinner("Calcul des deux routes..."):
        route_a = calculer_route(depart, arrivee)
        route_b = calculer_route(depart, arrivee, eviter_suez=eviter_suez, eviter_hra=eviter_hra)
        emission_a = calculer_emissions(route_a, cargo)
        emission_b = calculer_emissions(route_b, cargo)

    st.session_state.routes   = [route_a, route_b]
    st.session_state.emissions = [emission_a, emission_b]

# ---- AFFICHAGE ----
if st.session_state.routes:
    route_a, route_b     = st.session_state.routes
    emission_a, emission_b = st.session_state.emissions

    # Métriques comparatives
    st.markdown("### 📊 Comparaison")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Route A — Normale**")
        st.metric("📏 Distance", format_distance(route_a.distance_km))
        st.metric("⏱️ Durée",    format_duree(route_a.duree_heures))
        st.metric("🌍 CO₂",     format_co2(emission_a.co2e_kg))

    with col2:
        st.markdown("**Route B — Alternative**")
        delta_dist = route_b.distance_km - route_a.distance_km
        delta_co2  = emission_b.co2e_kg - emission_a.co2e_kg
        st.metric("📏 Distance", format_distance(route_b.distance_km), f"+{format_distance(delta_dist)}")
        st.metric("⏱️ Durée",    format_duree(route_b.duree_heures))
        st.metric("🌍 CO₂",     format_co2(emission_b.co2e_kg), f"+{format_co2(delta_co2)}")

    with col3:
        st.markdown("**Impact**")
        pct_dist = (delta_dist / route_a.distance_km) * 100
        pct_co2  = (delta_co2 / emission_a.co2e_kg) * 100
        st.metric("📏 Surcoût distance", f"+{pct_dist:.1f}%")
        st.metric("🌍 Surcoût CO₂",      f"+{pct_co2:.1f}%")

    st.markdown("---")
    col_carte, col_graph = st.columns([2, 1])

    with col_carte:
        st.markdown("### 🗺️ Les deux routes")
        carte = creer_carte(st.session_state.routes)
        st_folium(carte, width=700, height=450)

    with col_graph:
        st.markdown("### 📈 Graphique")
        fig = graphique_comparaison(
            st.session_state.routes,
            st.session_state.emissions
        )
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👈 Entre deux ports et clique sur Comparer !")
