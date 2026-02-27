import streamlit as st
import folium
from streamlit_folium import st_folium
from app.services.geocoding import geocoder_port
from app.services.routing import calculer_route
import random

st.set_page_config(page_title="Bataille Navale", page_icon="⚓", layout="wide")
st.title("⚓ Bataille Navale Maritime")
st.markdown("Trouve le navire caché avant qu'il atteigne sa destination !")

# ---- DONNÉES ----
NAVIRES = [
    {"nom": "CMA CGM Marco Polo", "imo": "9454448", "emoji": "🚢"},
    {"nom": "MSC Oscar",          "imo": "9703291", "emoji": "🛳️"},
    {"nom": "Ever Given",         "imo": "9811000", "emoji": "⛴️"},
    {"nom": "Maersk Alabama",     "imo": "9164263", "emoji": "🚤"},
]

PORTS = [
    "Shanghai", "Rotterdam", "Singapore",
    "Dubai", "Los Angeles", "Hamburg",
    "Tokyo", "Marseille", "New York"
]

MAX_TENTATIVES = 5

# ---- SESSION STATE ----
def init_jeu():
    return {
        "actif": False,
        "navire": None,
        "port_depart": None,
        "port_arrivee": None,
        "coords_depart": None,   # ← coordonnées mises en cache
        "coords_arrivee": None,  # ← coordonnées mises en cache
        "route": None,
        "tentatives": 0,
        "score": 0,
        "historique": [],
        "trouve": False,
        "indice_niveau": 0,
    }

if "jeu" not in st.session_state:
    st.session_state.jeu = init_jeu()

jeu = st.session_state.jeu


# ---- FONCTIONS ----
def nouvelle_partie():
    """Démarre une nouvelle partie en conservant le score."""
    score_precedent = jeu["score"]

    navire      = random.choice(NAVIRES)
    depart_nom  = random.choice(PORTS)
    arrivee_nom = random.choice([p for p in PORTS if p != depart_nom])

    # Geocoding effectué UNE SEULE FOIS, résultat stocké en state
    coords_depart  = geocoder_port(depart_nom)
    coords_arrivee = geocoder_port(arrivee_nom)
    route = (
        calculer_route(coords_depart, coords_arrivee)
        if coords_depart and coords_arrivee
        else None
    )

    nouveau = init_jeu()
    nouveau.update({
        "actif": True,
        "navire": navire,
        "port_depart": depart_nom,
        "port_arrivee": arrivee_nom,
        "coords_depart": coords_depart,
        "coords_arrivee": coords_arrivee,
        "route": route,
        "score": score_precedent,
    })
    st.session_state.jeu = nouveau


def hemisphere(coords) -> str:
    """Retourne l'hémisphère Nord/Sud à partir des coordonnées."""
    if coords is None:
        return "inconnu"
    return "Nord" if coords.latitude >= 0 else "Sud"


def get_indice(jeu: dict, niveau: int) -> str:
    """Retourne un indice de difficulté croissante."""
    navire   = jeu["navire"]
    depart   = jeu["port_depart"]
    arrivee  = jeu["port_arrivee"]
    route    = jeu["route"]
    coords_d = jeu["coords_depart"]

    indices = [
        f"🌊 Le navire navigue dans l'**hémisphère {hemisphere(coords_d)}**",
        f"📏 La route fait environ **{round(route.distance_km / 1000) * 1000:.0f} km**"
            if route else "📏 Route très longue",
        f"🌍 Le port de départ commence par **{depart[0]}**",
        f"🚢 Le navire s'appelle **{navire['nom'][:8]}...**",
        f"🏁 Destination : un port commençant par **{arrivee[0]}**",
    ]
    return indices[min(niveau, len(indices) - 1)]


def afficher_carte(jeu: dict):
    """Affiche la carte Folium de la route — utilise les coords en cache."""
    coords_d = jeu["coords_depart"]
    coords_a = jeu["coords_arrivee"]

    centre_lat = (coords_d.latitude  + coords_a.latitude)  / 2
    centre_lon = (coords_d.longitude + coords_a.longitude) / 2

    m = folium.Map(location=[centre_lat, centre_lon], zoom_start=3)

    if jeu["route"]:
        coords = [(c[1], c[0]) for c in jeu["route"].geojson["coordinates"]]
        folium.PolyLine(coords, color="#FF6600", weight=4, opacity=0.9).add_to(m)

    folium.Marker(
        [coords_d.latitude, coords_d.longitude],
        popup=f"🟢 {jeu['port_depart']}",
        icon=folium.Icon(color="green"),
    ).add_to(m)
    folium.Marker(
        [coords_a.latitude, coords_a.longitude],
        popup=f"🔴 {jeu['port_arrivee']}",
        icon=folium.Icon(color="red"),
    ).add_to(m)

    st_folium(m, width=700, height=400)


def valider_reponse(navire_guess: str, port_guess: str):
    """Traite une tentative du joueur."""
    jeu["tentatives"] += 1
    correct_navire = navire_guess == jeu["navire"]["nom"]
    correct_port   = port_guess   == jeu["port_arrivee"]

    if correct_navire and correct_port:
        points = MAX_TENTATIVES - jeu["tentatives"] + 1
        jeu["score"]  += points
        jeu["trouve"]  = True
    else:
        feedback = f"❌ Tentative {jeu['tentatives']} : **{navire_guess}** → **{port_guess}**"
        if correct_navire:
            feedback += " ✅ Navire correct !"
        elif correct_port:
            feedback += " ✅ Destination correcte !"
        jeu["historique"].append(feedback)
        jeu["indice_niveau"] += 1


# ---- SIDEBAR ----
st.sidebar.header("⚓ Contrôles")

if st.sidebar.button("🎮 Nouvelle Partie", use_container_width=True):
    with st.spinner("Préparation de la partie..."):
        nouvelle_partie()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.metric("🏆 Score", jeu["score"])
tentatives_restantes = jeu["max_tentatives"] - jeu["tentatives"] if "max_tentatives" in jeu else MAX_TENTATIVES
st.sidebar.metric(
    "🎯 Tentatives restantes",
    f"{MAX_TENTATIVES - jeu['tentatives']}/{MAX_TENTATIVES}",
)


# ---- AFFICHAGE PRINCIPAL ----
if not jeu["actif"]:
    st.info("👈 Clique sur **Nouvelle Partie** pour commencer !")
    st.markdown("""
    ### 🎮 Comment jouer ?
    1. Un navire mystère part d'un port secret vers une destination inconnue
    2. Tu as **5 tentatives** pour deviner le navire ET sa destination
    3. Chaque mauvaise réponse te donne un **indice**
    4. Plus tu trouves vite, plus tu marques de points !
    """)

elif jeu["trouve"]:
    st.success(f"🎉 Bravo ! Tu as trouvé en {jeu['tentatives']} tentative(s) !")
    st.balloons()

    col1, col2 = st.columns(2)
    col1.metric("Points gagnés", f"+{MAX_TENTATIVES - jeu['tentatives'] + 1} pts")
    col2.metric("Score total", jeu["score"])

    if jeu["route"]:
        st.markdown("### 🗺️ La vraie route du navire")
        afficher_carte(jeu)  # ← plus de geocoding redondant
        st.info(
            f"**{jeu['navire']['emoji']} {jeu['navire']['nom']}** : "
            f"{jeu['port_depart']} → {jeu['port_arrivee']} "
            f"({jeu['route'].distance_km:.0f} km — {jeu['route'].duree_jours:.1f} jours)"
        )

    if st.button("🔄 Rejouer", use_container_width=True):
        with st.spinner("Nouvelle partie..."):
            nouvelle_partie()
        st.rerun()

elif jeu["tentatives"] >= MAX_TENTATIVES:
    st.error(f"💀 Perdu ! Le navire était : **{jeu['navire']['emoji']} {jeu['navire']['nom']}**")
    st.error(f"Route : **{jeu['port_depart']} → {jeu['port_arrivee']}**")

    if st.button("🔄 Réessayer", use_container_width=True):
        with st.spinner("Nouvelle partie..."):
            nouvelle_partie()
        st.rerun()

else:
    # ---- JEU EN COURS ----
    col_jeu, col_info = st.columns([2, 1])

    with col_jeu:
        st.markdown("### 🔍 Trouve le navire mystère !")

        if jeu["historique"]:
            st.markdown("**Tes tentatives :**")
            for h in jeu["historique"]:
                st.markdown(h)

        if jeu["indice_niveau"] > 0:
            st.info(f"💡 Indice : {get_indice(jeu, jeu['indice_niveau'] - 1)}")

        st.markdown("---")

        navire_guess = st.selectbox("🚢 Quel est le navire ?",      [n["nom"] for n in NAVIRES])
        port_guess   = st.selectbox("🏁 Quelle est la destination ?", sorted(PORTS))

        col_btn1, col_btn2 = st.columns(2)

        if col_btn1.button("✅ Valider ma réponse", use_container_width=True):
            valider_reponse(navire_guess, port_guess)
            st.rerun()

        if col_btn2.button("💡 Demander un indice", use_container_width=True):
            # L'indice ne coûte pas une tentative mais réduit le score max atteignable
            jeu["indice_niveau"] += 1
            if jeu["score"] > 0:
                jeu["score"] -= 1
            st.rerun()

    with col_info:
        st.markdown("### 📋 Indices disponibles")
        st.markdown("- 🌊 Hémisphère de navigation")
        st.markdown("- 📏 Distance approximative")
        st.markdown("- 🌍 Première lettre du départ")
        st.markdown("- 🚢 Début du nom du navire")
        st.markdown("- 🏁 Première lettre destination")

        st.markdown("---")
        st.markdown("### 🏆 Scoring")
        for i, pts in enumerate(range(MAX_TENTATIVES, 0, -1)):
            st.markdown(f"- Trouvé en {i+1} essai{'s' if i else ''} : **+{pts} pt{'s' if pts > 1 else ''}**")