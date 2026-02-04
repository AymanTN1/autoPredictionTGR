# 🚀 DOCUMENTATION COMPLÈTE - API Prédiction TGR v2.0

Ce document fusionne le guide complet du projet, les instructions de démarrage, la configuration, la sécurité, le fonctionnement interne (Smart Duration), la conduite des tests et la roadmap.

---

## 1. Vue d'ensemble

- Application : API REST FastAPI pour prédire les dépenses (ARIMA/SARIMA)
- Version : 2.0 (Industrielle)
- Architecture : logique (DataCleaner, SmartPredictor), API (main.py), Dashboard (Streamlit)

---

## 2. Démarrage rapide

- Activer l'environnement : `& .\venv\Scripts\Activate.ps1`
- Lancer l'API : `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- Lancer le dashboard : `streamlit run dashboard.py`
- Lancer l'intégralité : `python run_all.py`

---

## 3. Endpoints principaux

- `GET /health` : état (public)
- `GET /info` : description (public)
- `POST /predict` : prédiction hybride (🔒 X-API-Key)
- `POST /predict/auto` : mode AUTO (🔒 X-API-Key)
- `POST /predict/by-code` : prédiction pour un code (🔒 X-API-Key)

---

## 4. Sécurité

- Clé API (header `X-API-Key`) définie dans `.env` (`TGR_API_KEY`).
- Logs sécurité écrits dans `logs/security.log`.
- Validation taille fichier : maximum configurable via `.env` (default 50MB).

---

## 5. Smart Duration (résumé fonctionnel)

- Compte `active_months = (montant > 0)`.
- `safe_duration = int(active_months / 3)`.
- Clamping : `safe_duration = max(3, min(safe_duration, 24))`.
- Si `user_months` est None → MODE AUTO : retourner `safe_duration`.
- Si `user_months` > `safe_duration` → réduire pour sécurité.

---

## 6. Logging & Observabilité

- `logs/app.log` : logs applicatifs (DEBUG/INFO/etc.).
- `logs/security.log` : audit accès et tentatives.
- Loguru configuré avec rotation 500 MB et retention 7 jours.

---

## 7. Tests

- Tests automatisés (Pytest) : `tests/test_complete_suite.py`, `tests/test_logic.py`.
- Scripts de démonstration et cURL conservés dans `demos/` et `scripts/`.
- Lancer l'intégralité des tests : `pytest -q` ou `pytest tests -q`.

---

## 8. Structure recommandée du repo

```
/ (root)
├─ logic.py
├─ main.py
├─ dashboard.py
├─ run_all.py
├─ requirements.txt
├─ dataSets/
├─ logs/
├─ docs/                     ← DOCUMENTATION_FULL.md + DOCUMENTATION_BRIEF.md
├─ tests/                    ← tests pytest (automatisés)
├─ demos/                    ← scripts de démonstration (non-pytest)
├─ scripts/                  ← utilitaires (cURL wrapper, batch)
└─ docs_archive/             ← anciens docs (archivés)
```

---

## 9. Roadmap & bonnes pratiques

- Ajouter CI (GitHub Actions) pour exécuter `pytest` et linting.
- Ajouter Docker + Compose pour déploiement reproductible.
- Mettre en place un endpoint `/metrics` et exporter Prometheus.

---

