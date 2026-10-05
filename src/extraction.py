"""Étape 1 : lire les contrats (PDF ou TXT) et en extraire le texte brut."""
from pathlib import Path

import pymupdf  # bibliothèque PyMuPDF

FORMATS_ACCEPTES = (".pdf", ".txt")


def lire_fichier(chemin) -> str:
    """Renvoie le texte d'un fichier PDF ou TXT."""
    chemin = Path(chemin)
    if chemin.suffix.lower() == ".pdf":
        with pymupdf.open(chemin) as doc:
            return "\n".join(page.get_text() for page in doc)
    return chemin.read_text(encoding="utf-8")


def lire_dossier(dossier="contrats") -> dict[str, str]:
    """Lit tous les contrats d'un dossier. Renvoie {nom_du_fichier: texte}."""
    return {
        f.stem: lire_fichier(f)
        for f in sorted(Path(dossier).iterdir())
        if f.suffix.lower() in FORMATS_ACCEPTES
    }


if __name__ == "__main__":
    for nom, texte in lire_dossier().items():
        print(f"{nom} : {len(texte)} caractères")
