# TGR Budget Prediction API

Plateforme de prédiction budgétaire (ORDONNATEUR) développée avec FastAPI + Streamlit.
Conteneurisée avec Docker et intégration continue via GitHub Actions.

## Fonctionnalités clés

- 📁 Endpoint `/predict/by-code` pour prédire sur sous-ensemble de données par code
- 🧠 Moteur "SmartPredictor" évaluant AR/MA/ARMA/ARIMA/SARIMA + modèles ML/Deep Learning
- 🔒 Authentification via clé API (X-API-Key)
- 🛠️ Tests unitaires et d'intégration automatisés (`pytest`)
- 🧩 Base SQLite pour historique + Docker Compose avec PostgreSQL pour production
- 🔁 CI/CD configurée (lint, tests, image Docker, sécurité)
- 📦 Conteneurs Docker pour API et UI Streamlit

## Installation locale (développement)

1. Cloner le dépôt et créer un environnement virtuel Python :
   ```powershell
   git clone https://github.com/AymanTN1/autoPredictionTGR.git
   cd autoPredictionTGR
   python -m venv venv
   venv\Scripts\activate
   pip install -e .[dev]
   ```

2. Lancer l'API :
   ```powershell
   uvicorn main:app --reload
   ```

3. Ouvrir l'interface Streamlit :
   ```powershell
   streamlit run dashboard.py
   ```

4. Exécuter les tests :
   ```powershell
   pytest tests/ -v
   ```

## Conteneurisation Docker

1. Installer [Docker Desktop](https://www.docker.com/products/docker-desktop) et démarrer.
2. Construire et lancer les services :
   ```sh
   docker-compose build
   docker-compose up -d
   ```
   - API disponible sur http://localhost:8000
   - UI Streamlit sur http://localhost:8501

3. Pour arrêter : `docker-compose down`.
4. Le service PostgreSQL et pgAdmin sont inclus (ports 5432 et 5050) ; volume `postgres_data` persiste les données.

5. Pour pousser l'image sur Docker Hub :
   ```sh
   docker login --username aymantantani
   docker build -t aymantantani/tgr-api:latest .
   docker push aymantantani/tgr-api:latest
   ```

(Mettez vos identifiants Docker Hub dans les secrets GitHub pour builds automatiques.)

## Déploiement

- Workflow GitHub Actions `ci.yml` : exécuté à chaque push/pull-request sur `main` ou `develop`.
- Tests unitaires (`-m unit`) s'exécutent automatiquement ; couverture envoyée à Codecov.
- Docker image est construite et poussée sur Docker Hub si les tests passent.
- Déploiement production placeholder (Fly.io, SSH, etc.) dans la job `deploy`.

Pour déployer en production gratuits, je recommande [Fly.io](https://fly.io) ou [Railway.app](https://railway.app) qui offrent des tiers gratuits pour conteneurs.

## Vérification CI

- Le pipeline est visible dans l'onglet **Actions** du dépôt GitHub.
- Chaque push déclenche lint, typage, tests et construction d'image.
- Ajoutez le badge suivant dans ce README (après configuration du repo) :

```md
![CI](https://github.com/AymanTN1/autoPredictionTGR/actions/workflows/ci.yml/badge.svg)
```

## Technologies utilisées

- Python 3.11
- FastAPI, Uvicorn, Streamlit
- pandas, statsmodels, scikit-learn
- SQLModel / SQLite / PostgreSQL
- Docker / Docker Compose
- GitHub Actions (CI/CD), pytest, Black, MyPy, Ruff, Bandit
- MLOps concepts : sélection de modèle automatique, gestion de versions, tests de régression
- AIOps : surveillance via logs, healthchecks dans Docker

## Liens utiles

- API Docs (Swagger) : http://localhost:8000/docs
- Dashboard Streamlit : http://localhost:8501


---

*Projet réalisé dans le cadre d'un stage Data Science / Machine Learning.*
