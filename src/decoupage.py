"""Étape 2 : découper chaque contrat en morceaux, article par article.

Chaque morceau garde le titre du contrat (dans le texte ET dans les métadonnées),
pour que la recherche sache toujours à quel contrat il appartient.
"""
import re

from langchain_text_splitters import RecursiveCharacterTextSplitter

# Repère le début d'un article : "Article 1", "ARTICLE 12"... (à adapter si besoin)
MOTIF_ARTICLE = re.compile(r"(?=^\s*Art(?:icle|\.)?\s*\d+)", re.MULTILINE | re.IGNORECASE)
# Si un article est trop long, on le redécoupe en blocs d'environ 1000 caractères
decoupeur = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)


def titre_contrat(texte: str) -> str:
    """Le titre = la première ligne non vide du contrat."""
    for ligne in texte.splitlines():
        if ligne.strip():
            return ligne.strip()
    return "Contrat sans titre"


def decouper_contrat(nom_fichier: str, texte: str) -> list[dict]:
    """Renvoie une liste de morceaux : {id, texte, metadata}."""
    titre = titre_contrat(texte)
    morceaux = []

    for partie in MOTIF_ARTICLE.split(texte):
        partie = partie.strip()
        if not partie:
            continue
        m = re.match(r"Art(?:icle|\.)?\s*(\d+)", partie, re.IGNORECASE)
        article = m.group(1) if m else "préambule"

        for bout in decoupeur.split_text(partie):
            morceaux.append({
                "id": f"{nom_fichier}_{len(morceaux)}",
                # Le titre est collé au texte : la recherche "voit" le nom du contrat
                "texte": f"{titre} | {bout}",
                "metadata": {"contrat": nom_fichier, "titre": titre, "article": article},
            })
    return morceaux


if __name__ == "__main__":
    from extraction import lire_dossier

    for nom, texte in lire_dossier().items():
        morceaux = decouper_contrat(nom, texte)
        print(f"{nom} : {len(morceaux)} morceaux")
        if morceaux:
            print("   exemple :", morceaux[1 if len(morceaux) > 1 else 0]["texte"][:150], "...")
