"""Étape 6 : l'interface de démonstration (Streamlit). Elle appelle l'API.

À lancer (l'API doit déjà tourner) :
    streamlit run interface.py
"""
import requests
import streamlit as st

API = "http://localhost:8000"
TOUS = "Tous les contrats"

st.set_page_config(page_title="Assistant contrats de crédit", page_icon="🏦")
st.title("Assistant contrats de crédit")
st.write("Posez une question sur les contrats ou extrayez leurs informations clés.")

try:
    contrats = requests.get(f"{API}/contrats", timeout=10).json()
except requests.ConnectionError:
    st.error("L'API ne répond pas. Lancez-la avec : uvicorn api:app --app-dir src --reload")
    st.stop()

with st.sidebar:
    st.header("Ajouter un contrat")
    fichier = st.file_uploader("Fichier PDF ou TXT", type=["pdf", "txt"])
    if fichier and st.button("Indexer le contrat"):
        with st.spinner("Indexation en cours…"):
            r = requests.post(f"{API}/contrats", files={"fichier": (fichier.name, fichier.getvalue())})
        if r.ok:
            st.success(f"Contrat indexé : {r.json()['morceaux_indexes']} morceaux")
            st.rerun()
        else:
            st.error(r.json().get("detail", "Échec de l'indexation"))

onglet_questions, onglet_extraction = st.tabs(["Questions", "Extraction"])

with onglet_questions:
    choix = st.selectbox("Chercher dans", [TOUS] + contrats)
    question = st.text_input("Votre question",
                             placeholder="Quelles sont les pénalités de remboursement anticipé ?")
    if st.button("Poser la question") and question:
        with st.spinner("Recherche dans les contrats…"):
            data = requests.post(f"{API}/question", timeout=600, json={
                "texte": question, "contrat": None if choix == TOUS else choix}).json()
        st.markdown(data["reponse"])
        st.caption("Sources : " + ", ".join(
            f"{s['contrat']} (article {s['article']})" for s in data["sources"]))

with onglet_extraction:
    if not contrats:
        st.info("Ajoutez un contrat dans le menu de gauche pour commencer.")
    else:
        contrat = st.selectbox("Contrat à analyser", contrats)
        if st.button("Extraire les informations"):
            with st.spinner("Lecture du contrat…"):
                st.json(requests.post(f"{API}/extraction/{contrat}", timeout=600).json())
