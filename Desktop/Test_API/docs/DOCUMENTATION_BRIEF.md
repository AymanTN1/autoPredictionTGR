# DOCUMENTATION BRÈVE - API Prédiction TGR v2.0

**Version** : 2.0 — Production ready

- Objectif : Prévoir dépenses via modèles ARIMA/SARIMA.
- Authentification : `X-API-Key` (header). Routes sensibles : `/predict`, `/predict/auto`, `/predict/by-code`.
- Smart Duration : calcul automatique de la durée sûre basée sur les mois actifs (bornes : 3–24 mois).
- Endpoints clés :
  - `GET /health` (public)
  - `GET /info` (public)
  - `POST /predict` (hybride, months optional, 🔒)
  - `POST /predict/auto` (auto, 🔒)
- Tests : Utiliser `pytest tests -q` (suites `test_complete_suite.py` et `test_logic.py`).
- Démarrage : `python run_all.py` ou `uvicorn main:app --reload`.

---

*Usage : fichier de référence rapide — pas d'exemples ni commandes détaillées.*