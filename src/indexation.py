"""Étape 3 : transformer les morceaux en vecteurs (Ollama) et les stocker dans Chroma.

À lancer une fois, puis à chaque ajout de contrats :
    python src/indexation.py
"""
import chromadb
import requests

from decoupage import decouper_contrat
from extraction import lire_dossier

OLLAMA_URL = "http://localhost:11434"
MODELE_EMBEDDING = "bge-m3"  # multilingue : français et arabe


def embed(textes: list[str]) -> list[list[float]]:
    """Demande à Ollama les vecteurs (embeddings) d'une liste de textes."""
    r = requests.post(f"{OLLAMA_URL}/api/embed",
                      json={"model": MODELE_EMBEDDING, "input": textes}, timeout=300)
    r.raise_for_status()
    return r.json()["embeddings"]


def get_collection():
    """Ouvre (ou crée) la base vectorielle, enregistrée dans le dossier base_vectorielle/."""
    client = chromadb.PersistentClient(path="base_vectorielle")
    return client.get_or_create_collection("contrats", metadata={"hnsw:space": "cosine"})


def indexer_contrat(nom: str, texte: str, collection=None) -> int:
    """Découpe un contrat, calcule les vecteurs et les enregistre. Renvoie le nombre de morceaux."""
    collection = collection or get_collection()
    morceaux = decouper_contrat(nom, texte)
    if not morceaux:
        return 0
    collection.upsert(  # upsert = ajoute, ou remplace si l'id existe déjà
        ids=[m["id"] for m in morceaux],
        documents=[m["texte"] for m in morceaux],
        metadatas=[m["metadata"] for m in morceaux],
        embeddings=embed([m["texte"] for m in morceaux]),
    )
    return len(morceaux)


if __name__ == "__main__":
    collection = get_collection()
    for nom, texte in lire_dossier("contrats").items():
        print(f"{nom} : {indexer_contrat(nom, texte, collection)} morceaux indexés")
    print("Total dans la base :", collection.count())
