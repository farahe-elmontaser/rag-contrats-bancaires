"""Étape 4 : le RAG. Chercher les bons articles, puis demander à Ollama de répondre."""
import json

import requests

from indexation import OLLAMA_URL, embed, get_collection

MODELE_LLM = "qwen2.5:7b"  # sur un PC modeste : "qwen2.5:3b" ou "llama3.2"
OPTIONS = {"temperature": 0, "num_ctx": 8192}  # réponses stables + assez de place pour le texte

PROMPT_SYSTEME = """Tu es un assistant d'analyse de contrats de crédit marocains.
Règles :
1. Si le message est une salutation ou une conversation courante (bonjour, ça va, merci...),
   réponds poliment en une ou deux phrases et propose ton aide sur les contrats.
2. Si la question porte sur les contrats, réponds uniquement à partir des extraits fournis
   et cite le contrat et le numéro de l'article.
3. Si la réponse n'est pas dans les extraits, réponds : "Cette information ne figure pas dans les contrats fournis."
4. N'invente jamais un taux, un montant ou une pénalité.
Réponds uniquement en JSON : {"reponse": "...", "utilise_extraits": true ou false}
"utilise_extraits" vaut true seulement si ta réponse s'appuie sur les extraits."""


def rechercher(question: str, contrat: str | None = None, k: int = 4) -> list[dict]:
    """Renvoie les k morceaux les plus proches de la question (filtrés par contrat si demandé)."""
    res = get_collection().query(
        query_embeddings=embed([question]),
        n_results=k,
        where={"contrat": contrat} if contrat else None,
    )
    return [{"texte": d, **m} for d, m in zip(res["documents"][0], res["metadatas"][0])]


def appeler_llm(messages: list[dict], format_json: bool = False) -> str:
    """Envoie les messages à Ollama et renvoie le texte de la réponse."""
    corps = {"model": MODELE_LLM, "messages": messages, "stream": False, "options": OPTIONS}
    if format_json:
        corps["format"] = "json"
    r = requests.post(f"{OLLAMA_URL}/api/chat", json=corps, timeout=600)
    r.raise_for_status()
    return r.json()["message"]["content"]


def repondre(question: str, contrat: str | None = None) -> dict:
    """Le RAG complet : recherche + prompt + LLM."""
    passages = rechercher(question, contrat)
    contexte = "\n\n".join(f"[Article {p['article']}] {p['texte']}" for p in passages)
    brut = appeler_llm([
        {"role": "system", "content": PROMPT_SYSTEME},
        {"role": "user", "content": f"Extraits :\n{contexte}\n\nMessage : {question}"},
    ], format_json=True)

    try:
        data = json.loads(brut)
        reponse = data.get("reponse", "")
        utilise = str(data.get("utilise_extraits")).lower() == "true"
    except json.JSONDecodeError:
        reponse, utilise = brut, True

    sources = []
    if utilise:  # les sources seulement si la réponse vient des contrats
        for p in passages:
            s = {"contrat": p["contrat"], "article": p["article"]}
            if s not in sources:  # pas de doublons
                sources.append(s)
    return {"reponse": reponse, "sources": sources}


def extraire_infos(texte_contrat: str) -> dict:
    """Lit un contrat entier et renvoie ses informations clés en JSON."""
    consigne = """Extrais les informations de ce contrat de crédit.
Réponds uniquement en JSON avec ces clés (null si absente) :
preteur, emprunteur, type_contrat, montant_mad, duree_mois, taux_nominal,
teg, echeance_mad, frais_dossier, assurance, garanties, remboursement_anticipe."""
    reponse = appeler_llm(
        [{"role": "system", "content": consigne},
         {"role": "user", "content": texte_contrat}],
        format_json=True,
    )
    try:
        return json.loads(reponse)
    except json.JSONDecodeError:
        return {"erreur": "Réponse du modèle illisible", "brut": reponse}


if __name__ == "__main__":
    resultat = repondre("Quelles sont les pénalités de remboursement anticipé ?")
    print(resultat["reponse"])
    print("Sources :", resultat["sources"])
