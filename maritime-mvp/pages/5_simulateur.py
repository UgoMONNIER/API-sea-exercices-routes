import streamlit as st
import folium
from streamlit_folium import st_folium
from app.services.geocoding import geocoder_port
from app.services.routing import calculer_route
from app.services.emissions import calculer_emissions
import random
import math

st.set_page_config(page_title="Maritime Survival", page_icon="🏢", layout="wide")

# =====================================================
#  CONSTANTES
# =====================================================

MAX_TOURS       = 10
BUDGET_INIT     = 10_000_000
REPUTATION_INIT = 100
FUEL_BASE       = 600
REPAIR_COST_PT  = 15_000   # $ par point de santé à réparer

FLOTTE_INIT = [
    {"id": "v1", "nom": "Nordic Star",    "emoji": "🚢", "type": "Container", "capacite": 500, "sante": 100},
    {"id": "v2", "nom": "Pacific Dragon", "emoji": "🛳️", "type": "Bulk",      "capacite": 800, "sante": 100},
    {"id": "v3", "nom": "Euro Express",   "emoji": "⛴️", "type": "Tanker",    "capacite": 300, "sante": 100},
]

MISSIONS_POOL = [
    {"id": "m1", "depart": "Shanghai",  "arrivee": "Rotterdam",   "reward": 2_000_000, "co2_max": 250},
    {"id": "m2", "depart": "Singapore", "arrivee": "Hamburg",     "reward": 1_800_000, "co2_max": 220},
    {"id": "m3", "depart": "Tokyo",     "arrivee": "Los Angeles", "reward": 1_500_000, "co2_max": 200},
    {"id": "m4", "depart": "Dubai",     "arrivee": "New York",    "reward": 1_700_000, "co2_max": 210},
    {"id": "m5", "depart": "Marseille", "arrivee": "Singapore",   "reward": 1_600_000, "co2_max": 190},
    {"id": "m6", "depart": "Hamburg",   "arrivee": "Shanghai",    "reward": 1_900_000, "co2_max": 240},
    {"id": "m7", "depart": "Rotterdam", "arrivee": "Tokyo",       "reward": 2_100_000, "co2_max": 260},
    {"id": "m8", "depart": "New York",  "arrivee": "Dubai",       "reward": 1_400_000, "co2_max": 175},
]

EVENEMENTS_DEF = [
    {
        "id":             "pirates",
        "nom":            "🏴‍☠️ Attaque de pirates !",
        "condition":      "hra",
        "proba":          0.45,
        "delta_budget":   -800_000,
        "delta_sante":    -25,
        "delta_rep":      -10,
        "message":        "Cargaison partiellement pillée. Équipage sain et sauf.",
    },
    {
        "id":             "tempete",
        "nom":            "⛈️ Tempête violente !",
        "condition":      "random",
        "proba":          0.25,
        "delta_budget":   -400_000,
        "delta_sante":    -15,
        "delta_rep":      -5,
        "message":        "Dommages structurels. Retard de 3 jours.",
    },
    {
        "id":             "panne",
        "nom":            "⚙️ Panne moteur critique !",
        "condition":      "random",
        "proba":          0.20,
        "delta_budget":   -600_000,
        "delta_sante":    -20,
        "delta_rep":      -8,
        "message":        "Réparations d'urgence en mer.",
    },
    {
        "id":             "ong",
        "nom":            "🌿 Boycott ONG environnementale !",
        "condition":      "co2_depasse",
        "proba":          1.0,          # ← certain si CO₂ dépassé
        "delta_budget":   -500_000,
        "delta_sante":    0,
        "delta_rep":      -20,
        "message":        "Amende environnementale + campagne médiatique.",
    },
    {
        "id":             "canal",
        "nom":            "🚧 Canal bloqué !",
        "condition":      "canal",
        "proba":          0.15,
        "delta_budget":   -300_000,
        "delta_sante":    0,
        "delta_rep":      -5,
        "message":        "Déroutement forcé. Surcoût carburant.",
    },
    {
        "id":             "cyber",
        "nom":            "💻 Cyberattaque !",
        "condition":      "random",
        "proba":          0.12,
        "delta_budget":   -700_000,
        "delta_sante":    -10,
        "delta_rep":      -15,
        "message":        "Systèmes hors ligne 48h.",
    },
    {
        "id":             "eco_bonus",
        "nom":            "🏆 Prix Eco-Shipping !",
        "condition":      "co2_ok",
        "proba":          0.80,
        "delta_budget":   300_000,
        "delta_sante":    0,
        "delta_rep":      +15,
        "message":        "Excellent bilan carbone. Nouveau client premium !",
    },
]


# =====================================================
#  FONCTIONS PURES — Calculs embarqués
# =====================================================

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance orthodromique entre deux points GPS."""
    R    = 6371
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a    = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def co2_embarque(distance_km: float, capacite: float) -> float:
    """Calcul CO₂e fallback si service indisponible."""
    return distance_km * capacite * 0.015 / 1000


def cout_fuel(distance_km: float, capacite: float, prix_fuel: float) -> float:
    """Coût carburant — représente 30-40% du reward."""
    consommation = 0.0003   # tonne fuel / (tonne cargo × km)
    return distance_km * capacite * consommation * prix_fuel


def evaluer_evenements(
    option: str,
    co2_depasse: bool,
) -> list[dict]:
    """
    Fonction PURE — évalue les événements, retourne une liste de deltas.
    Ne mute aucun état global.
    """
    resultats = []
    hra   = option == "rapide"
    canal = option == "rapide"

    for ev in EVENEMENTS_DEF:
        declenche = False

        if   ev["condition"] == "hra"          and hra          and random.random() < ev["proba"]:
            declenche = True
        elif ev["condition"] == "canal"         and canal        and random.random() < ev["proba"]:
            declenche = True
        elif ev["condition"] == "co2_depasse"   and co2_depasse  and random.random() < ev["proba"]:
            declenche = True
        elif ev["condition"] == "co2_ok"        and not co2_depasse and random.random() < ev["proba"]:
            declenche = True
        elif ev["condition"] == "random"        and random.random() < ev["proba"]:
            declenche = True

        if declenche:
            resultats.append({
                "nom":          ev["nom"],
                "message":      ev["message"],
                "delta_budget": ev["delta_budget"],
                "delta_sante":  ev["delta_sante"],
                "delta_rep":    ev["delta_rep"],
            })

    return resultats


def appliquer_deltas(game: dict, navire_id: str, deltas: list[dict]) -> None:
    """Applique les deltas sur l'état du jeu — séparé de evaluer_evenements."""
    navire = next(n for n in game["flotte"] if n["id"] == navire_id)
    for delta in deltas:
        game["budget"]    += delta["delta_budget"]
        game["reputation"] = max(0, min(100, game["reputation"] + delta["delta_rep"]))
        navire["sante"]    = max(0, navire["sante"] + delta["delta_sante"])


def resoudre_mission(mission: dict, navire: dict, option: str, game: dict) -> dict:
    """
    Encapsule toute la logique d'une traversée.
    Retourne un ResultatMission dict.
    """
    cd = game["coords_cache"].get(mission["depart"])
    ca = game["coords_cache"].get(mission["arrivee"])

    route    = None
    dist_km  = 0.0
    co2_t    = 0.0

    if cd and ca:
        route = calculer_route(cd, ca, eviter_suez=(option == "sure"))
        if route:
            dist_km = route.distance_km
            em      = calculer_emissions(route, navire["capacite"])
            co2_t   = em.co2e_tonnes if em else co2_embarque(dist_km, navire["capacite"])
        else:
            dist_km = haversine_km(cd.latitude, cd.longitude, ca.latitude, ca.longitude)
            co2_t   = co2_embarque(dist_km, navire["capacite"])
    else:
        dist_km = 10_000
        co2_t   = co2_embarque(dist_km, navire["capacite"])

    fuel_cout   = cout_fuel(dist_km, navire["capacite"], game["fuel_prix"])
    co2_depasse = co2_t > mission["co2_max"]
    deltas      = evaluer_evenements(option, co2_depasse)

    # Reward net
    reward = mission["reward"]
    if option == "sure":
        reward = int(reward * 0.85)

    deficit_fuel = max(0, int(fuel_cout) - reward)
    reward       = max(0, reward - int(fuel_cout))

    return {
        "mission":      mission,
        "navire":       navire,
        "option":       option,
        "route":        route,
        "dist_km":      dist_km,
        "co2_t":        co2_t,
        "co2_depasse":  co2_depasse,
        "fuel_cout":    fuel_cout,
        "deficit_fuel": deficit_fuel,
        "deltas":       deltas,
        "reward":       reward,
    }


def fluctuer_fuel(prix: float) -> float:
    """Prix du fuel fluctue de ±15% par tour, borné entre 400 et 900."""
    variation = random.uniform(-0.15, 0.15)
    return round(max(400, min(900, prix * (1 + variation))), 2)


def navires_disponibles(flotte: list) -> list:
    """Retourne uniquement les navires opérationnels (santé > 0)."""
    return [n for n in flotte if n["sante"] > 0]


def check_game_over(game: dict) -> tuple[bool, bool, str]:
    """
    Retourne (game_over, victoire, message).
    Fix v3 : >= MAX_TOURS pour détecter le dernier tour correctement.
    """
    if game["budget"] < 0:
        return True, False, "💸 FAILLITE ! Ton budget est épuisé."
    if game["reputation"] <= 0:
        return True, False, "📉 GAME OVER ! Ta réputation est détruite."
    if game["tour"] >= MAX_TOURS:
        return True, True, "victoire"
    return False, False, ""


# =====================================================
#  INIT STATE
# =====================================================

def init_game() -> dict:
    return {
        "actif":          False,
        "tour":           1,
        "budget":         BUDGET_INIT,
        "reputation":     REPUTATION_INIT,
        "co2_total":      0.0,
        "fuel_prix":      FUEL_BASE,
        "flotte":         [dict(n) for n in FLOTTE_INIT],
        "missions":       [],
        "assignments":    {},
        "options_routes": {},
        "resultats_tour": [],
        "log":            [],
        "phase":          "assign",
        "game_over":      False,
        "game_over_msg":  "",
        "victoire":       False,
        "coords_cache":   {},
    }


if "game" not in st.session_state:
    st.session_state.game = init_game()


# =====================================================
#  UTILITAIRES UI
# =====================================================

def g() -> dict:
    """Accès toujours frais au state — évite la référence périmée après st.rerun()."""
    return st.session_state.game


def get_coords(nom: str):
    if nom not in g()["coords_cache"]:
        g()["coords_cache"][nom] = geocoder_port(nom)
    return g()["coords_cache"][nom]


def fmt_budget(val: float) -> str:
    signe = "🟢" if val >= 0 else "🔴"
    return f"{signe} ${val / 1_000_000:.2f}M"


def statut_color(sante: int) -> str:
    if sante > 70: return "🟢"
    if sante > 40: return "🟡"
    if sante > 0:  return "🔴"
    return "💀"


def navire_by_id(navire_id: str) -> dict | None:
    return next((n for n in g()["flotte"] if n["id"] == navire_id), None)


# =====================================================
#  SIDEBAR
# =====================================================

st.sidebar.header("🏢 ShipCo HQ")

if g()["actif"] and not g()["game_over"]:
    st.sidebar.metric("💰 Budget",       f"${g()['budget'] / 1_000_000:.2f}M")
    st.sidebar.metric("⭐ Réputation",   g()["reputation"])
    st.sidebar.metric("🌍 CO₂ total",   f"{g()['co2_total']:.1f} t")
    st.sidebar.metric("⛽ Prix fuel",    f"${g()['fuel_prix']:.0f}/t")
    st.sidebar.metric("📅 Tour",         f"{g()['tour']}/{MAX_TOURS}")

    st.sidebar.markdown("---")
    st.sidebar.markdown("**🚢 État de la flotte :**")
    for nav in g()["flotte"]:
        label = f"{statut_color(nav['sante'])} {nav['emoji']} **{nav['nom']}** — {nav['sante']}%"
        if nav["sante"] == 0:
            label += " *(hors service)*"
        st.sidebar.markdown(label)

    st.sidebar.markdown("---")
    st.sidebar.progress(
        min(100, int(g()["budget"] / BUDGET_INIT * 100)),
        text=f"Budget : {int(g()['budget'] / BUDGET_INIT * 100)}%"
    )
    st.sidebar.progress(
        min(100, g()["reputation"]),
        text=f"Réputation : {g()['reputation']}%"
    )

if st.sidebar.button("🎮 Nouvelle Partie", use_container_width=True):
    new_g              = init_game()
    new_g["actif"]     = True
    new_g["missions"]  = random.sample(MISSIONS_POOL, 3)
    st.session_state.game = new_g
    st.rerun()


# =====================================================
#  ÉCRAN ACCUEIL
# =====================================================

if not g()["actif"]:
    st.markdown("""
    # 🚢 Maritime Survival Simulator
    **Tu es le CEO de ShipCo.** Gère ta flotte, choisis tes routes, survive aux crises.

    ---
    ### 🎯 Objectif
    Survive **10 tours** sans faillite ni réputation à zéro.

    ### 🚢 Ta flotte
    | Navire | Type | Capacité | Santé |
    |--------|------|----------|-------|
    | 🚢 Nordic Star | Container | 500 TEU | 100% |
    | 🛳️ Pacific Dragon | Bulk | 800 T | 100% |
    | ⛴️ Euro Express | Tanker | 300 T | 100% |

    ### ⚡ Événements possibles
    | Événement | Déclencheur | Impact |
    |-----------|-------------|--------|
    | 🏴‍☠️ Pirates | Route rapide | -$800K, -25% santé |
    | ⛈️ Tempête | Aléatoire | -$400K, -15% santé |
    | ⚙️ Panne | Aléatoire | -$600K, -20% santé |
    | 🌿 ONG | CO₂ dépassé (certain) | -$500K, -20 rep |
    | 🚧 Canal bloqué | Route rapide | -$300K |
    | 💻 Cyberattaque | Aléatoire | -$700K, -15 rep |
    | 🏆 Prix Eco | CO₂ faible | +$300K, +15 rep |

    ### 💡 Stratégies clés
    - **Route rapide** ⚡ = profit max, mais pirates + canal risqués
    - **Route sûre** 🛡️ = -15% profit, peu d'incidents
    - **Surveille le fuel** ⛽ — il fluctue chaque tour de ±15%
    - **Répare tes navires** 🔧 avant qu'ils tombent à 0%
    - **Dépasse le CO₂ max** → ONG garantie 🌿
    """)
    st.info("👈 Clique sur **Nouvelle Partie** pour commencer !")
    st.stop()


# =====================================================
#  GAME OVER
# =====================================================

if g()["game_over"]:
    if g()["victoire"]:
        st.success("🏆 VICTOIRE ! Tu as survécu aux 10 tours !")
        st.balloons()

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Budget final",  f"${g()['budget'] / 1_000_000:.2f}M")
        col2.metric("⭐ Réputation",    g()["reputation"])
        col3.metric("🌍 CO₂ total",     f"{g()['co2_total']:.1f} t")

        budget_final = g()["budget"]
        if budget_final > 18_000_000:
            st.success("💎 Rang : TYCOON MARITIME — Légendaire !")
        elif budget_final > 14_000_000:
            st.info("🥇 Rang : CAPITAINE EXPERT")
        elif budget_final > 11_000_000:
            st.warning("🥈 Rang : MARIN COMPÉTENT")
        else:
            st.error("🥉 Rang : SURVIVANT — Ouf, de justesse !")
    else:
        st.error(f"💥 {g()['game_over_msg']}")
        st.markdown(f"**Tu as survécu {g()['tour'] - 1} tours sur {MAX_TOURS}.**")

    st.markdown("---")
    st.markdown("### 📜 Historique de la partie")
    for entry in g()["log"]:
        st.markdown(entry)

    st.stop()


# =====================================================
#  PHASE 1 — ASSIGNATION
# =====================================================

if g()["phase"] == "assign":
    st.markdown(f"## 📋 Tour {g()['tour']}/{MAX_TOURS} — Assigne tes navires")

    # Info fuel
    tendance = "📈 En hausse" if g()["fuel_prix"] > FUEL_BASE else "📉 En baisse"
    st.info(f"⛽ Prix du fuel ce tour : **${g()['fuel_prix']:.0f}/tonne** ({tendance})")

    # ---- RÉPARATIONS ----
    navires_endommages = [n for n in g()["flotte"] if 0 < n["sante"] < 100]
    if navires_endommages:
        st.markdown("### 🔧 Réparations disponibles")
        for nav in navires_endommages:
            repair_cost = (100 - nav["sante"]) * REPAIR_COST_PT
            col_r1, col_r2 = st.columns([3, 1])
            col_r1.markdown(
                f"{statut_color(nav['sante'])} **{nav['emoji']} {nav['nom']}** — "
                f"Santé : {nav['sante']}% | "
                f"Coût : `${repair_cost / 1_000:.0f}K`"
            )
            if col_r2.button("🔧 Réparer", key=f"repair_{nav['id']}_{g()['tour']}"):
                if g()["budget"] >= repair_cost:
                    g()["budget"]  -= repair_cost
                    nav["sante"]    = 100
                    st.success(f"✅ {nav['nom']} remis à 100% !")
                    st.rerun()
                else:
                    st.error(f"❌ Budget insuffisant — besoin de ${repair_cost / 1_000:.0f}K")
        st.markdown("---")

    # ---- VÉRIFICATION FLOTTE ----
    dispos = navires_disponibles(g()["flotte"])
    if not dispos:
        g()["game_over"]     = True
        g()["game_over_msg"] = "💀 Toute ta flotte est détruite !"
        st.rerun()

    col_map, col_assign = st.columns([2, 1])

    with col_map:
        st.markdown("### 🗺️ Missions disponibles")
        m           = folium.Map(location=[20, 0], zoom_start=2)
        couleurs_hex = ["#0066CC", "#CC0000", "#00AA44"]
        couleurs_ico = ["blue",    "red",     "green"]

        for i, mission in enumerate(g()["missions"]):
            cd = get_coords(mission["depart"])
            ca = get_coords(mission["arrivee"])
            if cd and ca:
                folium.Marker(
                    [cd.latitude, cd.longitude],
                    popup=f"🟢 {mission['depart']}",
                    icon=folium.Icon(color=couleurs_ico[i], icon="ship", prefix="fa")
                ).add_to(m)
                folium.Marker(
                    [ca.latitude, ca.longitude],
                    popup=f"🏁 {mission['arrivee']} (+${mission['reward'] / 1e6:.1f}M)",
                    icon=folium.Icon(color=couleurs_ico[i])
                ).add_to(m)
                folium.PolyLine(
                    [[cd.latitude, cd.longitude], [ca.latitude, ca.longitude]],
                    color=couleurs_hex[i], weight=2, dash_array="5 5"
                ).add_to(m)

        st_folium(m, width=650, height=400)

    with col_assign:
        st.markdown("### ⚙️ Assignations")

        navires_options  = {n["id"]: f"{n['emoji']} {n['nom']} ({n['sante']}%)" for n in dispos}
        assignments      = {}
        options_routes   = {}
        navires_utilises = set()
        valid            = True

        for i, mission in enumerate(g()["missions"]):
            st.markdown("---")
            st.markdown(f"**Mission {i + 1}** : {mission['depart']} → {mission['arrivee']}")
            st.markdown(
                f"💰 `+${mission['reward'] / 1e6:.1f}M` | "
                f"🌍 CO₂ max : `{mission['co2_max']} t`"
            )

            navire_id = st.selectbox(
                "Navire",
                options=list(navires_options.keys()),
                format_func=lambda x: navires_options[x],
                key=f"nav_{mission['id']}_{g()['tour']}"
            )

            option = st.radio(
                "Route",
                ["rapide", "sure"],
                format_func=lambda x: "🚀 Rapide (risquée)" if x == "rapide" else "🛡️ Sûre (-15% profit)",
                horizontal=True,
                key=f"opt_{mission['id']}_{g()['tour']}"
            )

            if navire_id in navires_utilises:
                st.error("⚠️ Ce navire est déjà assigné à une autre mission !")
                valid = False
            else:
                navires_utilises.add(navire_id)

            assignments[mission["id"]]    = navire_id
            options_routes[mission["id"]] = option

        st.markdown("---")
        if not valid:
            st.error("Assigne un navire différent à chaque mission.")
        else:
            if st.button("⚡ Lancer le tour !", use_container_width=True, type="primary"):
                g()["assignments"]    = assignments
                g()["options_routes"] = options_routes
                g()["phase"]          = "resolution"
                st.rerun()


# =====================================================
#  PHASE 2 — RÉSOLUTION
# =====================================================

elif g()["phase"] == "resolution":
    st.markdown(f"## ⚡ Tour {g()['tour']} — Traversées en cours...")

    resultats = []

    for mission in g()["missions"]:
        navire_id = g()["assignments"].get(mission["id"])
        navire    = navire_by_id(navire_id)
        option    = g()["options_routes"].get(mission["id"], "sure")

        if not navire:
            continue

        # Résoudre la mission (fonction encapsulée)
        res = resoudre_mission(mission, navire, option, g())

        # Appliquer les deltas sur le state
        appliquer_deltas(g(), navire_id, res["deltas"])

        # Appliquer reward et deficit fuel
        g()["budget"]     += res["reward"]
        if res["deficit_fuel"] > 0:
            g()["budget"] -= res["deficit_fuel"]

        # +3 réputation par livraison réussie, plafonné à 100
        g()["reputation"]  = min(100, g()["reputation"] + 3)
        g()["co2_total"]  += res["co2_t"]

        # Log
        g()["log"].append(
            f"Tour {g()['tour']} | {navire['emoji']} {navire['nom']} : "
            f"{mission['depart']} → {mission['arrivee']} | "
            f"+${res['reward'] / 1e6:.2f}M | "
            f"CO₂ : {res['co2_t']:.1f}t | "
            f"Fuel : -${res['fuel_cout'] / 1e3:.0f}K | "
            f"Incidents : {len(res['deltas'])}"
        )

        resultats.append(res)

    g()["resultats_tour"] = resultats
    g()["fuel_prix"]      = fluctuer_fuel(g()["fuel_prix"])

    # Check game over — Fix v3 : >= MAX_TOURS
    over, victoire, msg = check_game_over(g())
    if over:
        g()["game_over"]     = True
        g()["victoire"]      = victoire
        g()["game_over_msg"] = msg

    g()["phase"] = "recap"
    st.rerun()


# =====================================================
#  PHASE 3 — RÉCAP
# =====================================================

elif g()["phase"] == "recap":
    st.markdown(f"## 📊 Tour {g()['tour']} — Récapitulatif")

    for res in g()["resultats_tour"]:
        mission = res["mission"]
        navire  = res["navire"]
        deltas  = res["deltas"]

        # Couleur de l'expander
        a_incident = any(d["delta_budget"] < 0 for d in deltas)
        icon       = "🔴" if a_incident else "🟢"

        with st.expander(
            f"{icon} {navire['emoji']} {navire['nom']} : "
            f"{mission['depart']} → {mission['arrivee']}",
            expanded=True
        ):
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("💰 Revenu net",  f"${res['reward'] / 1e6:.2f}M")
            col2.metric(
                "🌍 CO₂",
                f"{res['co2_t']:.1f} t",
                delta="✅ OK" if not res["co2_depasse"] else "❌ Dépassé",
                delta_color="normal" if not res["co2_depasse"] else "inverse"
            )
            col3.metric("⛽ Fuel",         f"-${res['fuel_cout'] / 1e3:.0f}K")
            col4.metric("🛡️ Santé",        f"{navire['sante']}%")

            route_label = "⚡ Rapide" if res["option"] == "rapide" else "🛡️ Sûre"
            st.caption(f"📏 {res['dist_km']:.0f} km | Route {route_label}")

            if res["deficit_fuel"] > 0:
                st.warning(f"⛽ Surcoût fuel : -${res['deficit_fuel'] / 1e3:.0f}K déduit du budget")

            if deltas:
                st.markdown("**Événements :**")
                for d in deltas:
                    if d["delta_budget"] < 0 or d["delta_rep"] < 0:
                        st.warning(
                            f"{d['nom']} — {d['message']} | "
                            f"Budget : ${d['delta_budget'] / 1e3:.0f}K | "
                            f"Réputation : {d['delta_rep']:+d}"
                        )
                    else:
                        st.success(
                            f"{d['nom']} — {d['message']} | "
                            f"+${d['delta_budget'] / 1e3:.0f}K | "
                            f"Réputation : {d['delta_rep']:+d}"
                        )
            else:
                st.success("✅ Traversée sans incident !")

    # Carte des routes du tour
    st.markdown("### 🗺️ Routes de ce tour")
    m        = folium.Map(location=[20, 0], zoom_start=2)
    couleurs = ["#0066CC", "#CC0000", "#00AA44"]

    for i, res in enumerate(g()["resultats_tour"]):
        if res["route"]:
            coords = [(c[1], c[0]) for c in res["route"].geojson["coordinates"]]
            folium.PolyLine(
                coords,
                color=couleurs[i % len(couleurs)],
                weight=3,
                tooltip=f"{res['navire']['nom']} : {res['mission']['depart']} → {res['mission']['arrivee']}"
            ).add_to(m)

    st_folium(m, width=700, height=350)

    # Bilan global
    st.markdown("---")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("💰 Budget",          f"${g()['budget'] / 1e6:.2f}M")
    col2.metric("⭐ Réputation",      g()["reputation"])
    col3.metric("🌍 CO₂ total",       f"{g()['co2_total']:.1f} t")
    col4.metric("⛽ Fuel prochain",   f"${g()['fuel_prix']:.0f}/t")
    col5.metric("📅 Tours restants",  max(0, MAX_TOURS - g()["tour"]))

    st.markdown("---")

    if not g()["game_over"]:
        if st.button("➡️ Tour suivant", use_container_width=True, type="primary"):
            g()["tour"]           += 1
            g()["missions"]        = random.sample(MISSIONS_POOL, 3)
            g()["phase"]           = "assign"
            g()["resultats_tour"]  = []
            st.rerun()
    else:
        if st.button("📊 Résultats finaux", use_container_width=True, type="primary"):
            st.rerun()