import streamlit as st
from streamlit_folium import st_folium
from app.services.vessel import get_vessel_info
from app.components.map import creer_carte_vessel
from app.utils.formatters import format_vitesse

st.set_page_config(page_title="Vessel Tracker", page_icon="📡", layout="wide")
st.title("📡 Vessel Tracker")
st.markdown("Suivre un navire en temps réel via son numéro IMO")

# ---- SESSION STATE ----
if "vessel" not in st.session_state:
    st.session_state.vessel = None

# ---- SIDEBAR ----
st.sidebar.header("Paramètres")
imo = st.sidebar.text_input("🔢 Numéro IMO", "9454448")
st.sidebar.markdown("*Exemple : 9454448 = CMA CGM Marco Polo*")

if st.sidebar.button("🔍 Rechercher", use_container_width=True):
    with st.spinner("Recherche du navire..."):
        vessel = get_vessel_info(imo)

    if not vessel:
        st.error("❌ Navire introuvable")
        st.stop()

    st.session_state.vessel = vessel

# ---- AFFICHAGE ----
if st.session_state.vessel:
    v = st.session_state.vessel

    if v.get("simule"):
        st.warning("⚠️ Données simulées — clé API VesselFinder requise pour les données réelles")

    st.markdown(f"### 🚢 {v.get('nom', 'Navire inconnu')}")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🏴 Pavillon",    v.get("pavillon", "—"))
    m2.metric("🚢 Type",        v.get("type", "—"))
    m3.metric("💨 Vitesse",     format_vitesse(v.get("vitesse", 0)))
    m4.metric("🧭 Cap",         f"{v.get('cap', 0)}°")

    st.markdown("---")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 🗺️ Position actuelle")
        carte = creer_carte_vessel(v)
        st_folium(carte, width=700, height=450)

    with col2:
        st.markdown("### 📋 Détails")
        st.info(f"**Destination :** {v.get('destination', '—')}")
        st.info(f"**ETA :** {v.get('eta', '—')}")
        st.info(f"**Statut :** {v.get('statut', '—')}")
        st.info(f"**Position :** {v.get('latitude', 0):.4f}, {v.get('longitude', 0):.4f}")
        st.info(f"**IMO :** {v.get('imo', '—')}")

else:
    st.info("👈 Entre un numéro IMO et clique sur Rechercher !")
