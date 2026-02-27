import streamlit as st

st.set_page_config(
    page_title="Maritime MVP",
    page_icon="🚢",
    layout="wide"
)

st.title("🚢 Maritime MVP — Powered by Searoutes")
st.markdown("---")

st.markdown("""
## Bienvenue sur le Maritime Dashboard

Ce dashboard permet de :

- 🚢 **Routing Maritime** — Calculer une route entre deux ports avec distance, durée et CO₂
- ⚖️ **Comparaison de Routes** — Comparer deux scénarios (ex: via Suez vs Cap de Bonne Espérance)
- 📡 **Vessel Tracker** — Suivre un navire en temps réel via son numéro IMO

---

### 👈 Utilise le menu à gauche pour naviguer
""")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("### 🚢 Routing\nCalcule la route optimale entre deux ports avec émissions CO₂")

with col2:
    st.info("### ⚖️ Comparaison\nCompare deux routes — idéal pour simuler la crise Mer Rouge")

with col3:
    st.info("### 📡 Vessel Tracker\nSuis n'importe quel navire dans le monde via son IMO")
