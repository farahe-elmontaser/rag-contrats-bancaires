"""Évaluation du RAG à partir du tableau récapitulatif des 30 contrats.

À lancer depuis la racine du projet (l'indexation doit être faite) :
    python src/evaluation.py
Résultats affichés à l'écran et enregistrés dans resultats_evaluation.csv
"""
import csv
import time

from rag import rechercher, repondre

# (question, réponse attendue, contrat attendu) — valeurs tirées du tableau récapitulatif
QUESTIONS = [
    ("Quel est le TEG du prêt personnel non affecté ?", "12,20", "contrat_07"),
    ("Quel est le montant de l'échéance finale (ballon) du crédit automobile avec échéance finale majorée ?", "54000", "contrat_18"),
    ("Quelle est la durée en mois du prêt immobilier pour construction de villa ?", "300", "contrat_02"),
    ("Quelle est la marge de la Mourabaha automobile ?", "7,00", "contrat_29"),
    ("Quel est le montant du crédit de promotion immobilière ?", "12000000", "contrat_25"),
    ("Quel est le TEG du rachat de crédit immobilier ?", "6,52", "contrat_05"),
    ("Quelle est la mensualité du prêt immobilier à taux fixe pour acquisition ?", "6006,86", "contrat_01"),
    ("Quel est le montant du prêt d'équipement pour auto-entrepreneur ?", "100000", "contrat_24"),
    ("Quelle est l'indemnité de remboursement anticipé du crédit d'investissement PME ?", "3%", "contrat_22"),
    ("Quel est le taux nominal du crédit véhicule électrique à taux bonifié ?", "5,90", "contrat_17"),
    ("Quel est le TEG du crédit deux-roues ?", "12,81", "contrat_16"),
    ("Quel est le montant du prêt au logement social avec garantie publique ?", "250000", "contrat_04"),
]

# Questions dont la réponse n'est PAS dans les contrats : le système doit refuser
QUESTIONS_PIEGES = [
    "Quel est le numéro de téléphone du service client de Banque Zénith Maroc ?",
    "Quelle est la couleur du véhicule financé par le crédit deux-roues ?",
    "Quel est le salaire mensuel de l'emprunteuse du rachat de crédit immobilier ?",
]

MOTS_REFUS = ["ne figure pas", "spécialisé"]


def normaliser(texte: str) -> str:
    """Rend les nombres comparables : '12.20 %' et '12,20%' deviennent '12,20%'."""
    for espace in (" ", "\u00a0", "\u202f"):  # espaces normales et insécables
        texte = texte.replace(espace, "")
    return texte.replace(".", ",").lower()


def evaluer():
    lignes, debut = [], time.time()
    bonnes_reponses = bon_contrat = 0

    print("=== Questions avec réponse attendue ===\n")
    for i, (question, attendu, contrat) in enumerate(QUESTIONS, 1):
        trouves = [p["contrat"] for p in rechercher(question)]
        reponse = repondre(question)["reponse"]
        ok_reponse = normaliser(attendu) in normaliser(reponse)
        ok_contrat = contrat in trouves
        bonnes_reponses += ok_reponse
        bon_contrat += ok_contrat
        print(f"[{i}/{len(QUESTIONS)}] {'✅' if ok_reponse else '❌'} réponse | "
              f"{'✅' if ok_contrat else '❌'} contrat | {question}")
        if not ok_reponse:
            print(f"      attendu : {attendu} | obtenu : {reponse[:150]}")
        lignes.append([question, attendu, reponse, ok_reponse, contrat, ok_contrat])

    print("\n=== Questions pièges (le système doit refuser) ===\n")
    refus_corrects = 0
    for question in QUESTIONS_PIEGES:
        reponse = repondre(question)["reponse"]
        ok = any(mot in reponse.lower() for mot in MOTS_REFUS)
        refus_corrects += ok
        print(f"{'✅' if ok else '❌'} {question}")
        if not ok:
            print(f"      obtenu : {reponse[:150]}")
        lignes.append([question, "(refus)", reponse, ok, "", ""])

    n, p = len(QUESTIONS), len(QUESTIONS_PIEGES)
    print("\n=== Résultats (à copier dans le README) ===\n")
    print("| Indicateur | Résultat |")
    print("|---|---|")
    print(f"| Questions testées | {n + p} |")
    print(f"| Bonnes réponses | {bonnes_reponses} / {n} ({100 * bonnes_reponses // n} %) |")
    print(f"| Bon contrat retrouvé par la recherche | {bon_contrat} / {n} ({100 * bon_contrat // n} %) |")
    print(f"| Refus correct quand l'information est absente | {refus_corrects} / {p} |")
    print(f"\nDurée totale : {time.time() - debut:.0f} s")

    with open("resultats_evaluation.csv", "w", newline="", encoding="utf-8") as f:
        ecrivain = csv.writer(f, delimiter=";")
        ecrivain.writerow(["question", "attendu", "reponse", "reponse_ok", "contrat_attendu", "contrat_ok"])
        ecrivain.writerows(lignes)
    print("Détails enregistrés dans resultats_evaluation.csv")


if __name__ == "__main__":
    evaluer()
