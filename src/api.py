"""Étape 5 : l'API FastAPI, la porte d'entrée pour le backend de l'application.

À lancer depuis la racine du projet :
    uvicorn api:app --app-dir src --reload
Documentation automatique : http://localhost:8000/docs
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel

from extraction import FORMATS_ACCEPTES, lire_fichier
from indexation import indexer_contrat
from rag import extraire_infos, repondre

DOSSIER = Path("contrats")
app = FastAPI(title="RAG contrats bancaires")


class Question(BaseModel):
    texte: str
    contrat: str | None = None  # ex. "contrat_02" pour chercher dans un seul contrat


@app.get("/contrats")
def lister_contrats():
    """Liste les contrats disponibles."""
    return sorted(f.stem for f in DOSSIER.iterdir() if f.suffix.lower() in FORMATS_ACCEPTES)


@app.post("/contrats")
def ajouter_contrat(fichier: UploadFile):
    """Reçoit un nouveau contrat (PDF ou TXT), l'enregistre et l'indexe."""
    nom = Path(fichier.filename).name  # évite les chemins dangereux
    if not nom.lower().endswith(FORMATS_ACCEPTES):
        raise HTTPException(400, "Format accepté : PDF ou TXT")
    chemin = DOSSIER / nom
    chemin.write_bytes(fichier.file.read())
    n = indexer_contrat(chemin.stem, lire_fichier(chemin))
    return {"contrat": chemin.stem, "morceaux_indexes": n}


@app.post("/question")
def poser_question(q: Question):
    """Pose une question, reçoit la réponse et ses sources."""
    return repondre(q.texte, q.contrat)


@app.post("/extraction/{contrat}")
def extraction(contrat: str):
    """Renvoie les informations clés d'un contrat en JSON."""
    fichiers = [f for f in DOSSIER.glob(f"{contrat}.*") if f.suffix.lower() in FORMATS_ACCEPTES]
    if not fichiers:
        raise HTTPException(404, f"Contrat introuvable : {contrat}")
    return extraire_infos(lire_fichier(fichiers[0]))
