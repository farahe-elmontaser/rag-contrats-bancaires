# RAG contrats bancaires

Assistant qui répond aux questions sur des contrats de crédit (droit marocain, MAD)
et extrait leurs informations clés, avec un LLM local (Ollama). Aucune donnée ne quitte la machine.

## Architecture

```
Interface (Streamlit) / backend de l'application
        │  question
        ▼
API RAG (FastAPI)  ── recherche ──▶  Chroma (base vectorielle)
        │  articles + question
        ▼
Ollama (qwen2.5 + bge-m3)  ──▶  réponse avec sources
```

## Installation

```bash
pip install -r requirements.txt
ollama pull qwen2.5:7b      # ou qwen2.5:3b sur un PC modeste
ollama pull bge-m3
```

Placez les contrats (un fichier par contrat, PDF ou TXT) dans `contrats/`.

## Lancement (toujours depuis la racine du projet)

```bash
python src/indexation.py                      # 1. indexer les contrats
uvicorn api:app --app-dir src --reload        # 2. lancer l'API  → http://localhost:8000/docs
streamlit run interface.py                    # 3. lancer l'interface (autre terminal)
```

## Fichiers

| Fichier | Rôle |
|---|---|
| `src/extraction.py` | Lire les PDF / TXT |
| `src/decoupage.py` | Découper par article, ajouter le titre du contrat |
| `src/indexation.py` | Embeddings (Ollama) + stockage (Chroma) |
| `src/rag.py` | Recherche + prompt + appel au LLM, extraction JSON |
| `src/api.py` | API FastAPI |
| `interface.py` | Interface de démonstration |

Contrats fictifs, à usage de formation. L'assistant est une aide à la lecture
et ne remplace pas l'avis d'un juriste.
