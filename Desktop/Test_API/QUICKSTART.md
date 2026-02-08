```markdown
# ⚡ Quick Start - Les 4 Killer Features en 10 minutes

## 🚀 Installation rapide

### Step 1: Installer les dépendances

```bash
# Créer environnement (optionnel mais recommandé)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer
pip install -r requirements.txt

# Installation des outils dev (Black, MyPy)
pip install -e ".[dev]"
```

### Step 2: Lancer l'API

```bash
# Démarrer le serveur
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# ✅ API prête sur : http://localhost:8000/docs
```

### Step 3: Initialiser la base de données

```bash
# (Automatique au startup, mais peut être à faire manuellement)
# Ouvrir http://localhost:8000/api/db/init (POST)
# Ou via curl:
curl -X POST "http://localhost:8000/api/db/init"
```

---

## 🎯 Test des 4 features en 5 minutes

### Feature 1️⃣ : Détection d'Anomalies

```bash
# 1. Obtenir une clé API (enregistrer l'org)
API_KEY=$(curl -s -X POST "http://localhost:8000/api/db/users/register?organization=TestTGR" | jq -r .api_key)
echo "Votre clé API : $API_KEY"

# 2. Uploader et récupérer prédictions + anomalies
curl -X POST "http://localhost:8000/predict" \
  -H "X-API-Key: $API_KEY" \
  -F "file=@demo_sample.csv" \
  | jq '.anomalies'

# ✅ Vous voyez les anomalies détectées !
```

### Feature 2️⃣ : Persistance BD (SQLModel)

```bash
# 1. Lister vos fichiers uploadés
curl "http://localhost:8000/api/db/files/list?api_key=$API_KEY" | jq

# 2. Lister vos prédictions
curl "http://localhost:8000/api/db/predictions/list?api_key=$API_KEY" | jq

# 3. Voir les stats
curl "http://localhost:8000/api/db/stats/overview?api_key=$API_KEY" | jq

# ✅ Tout est persisté !
```

### Feature 3️⃣ : Qualité Industrielle (Black + MyPy)

```bash
# 1. Formater le code
black .
# ✅ Code reformaté selon PEP 8

# 2. Vérifier types statiques
mypy . --ignore-missing-imports
# ✅ Aucune erreur de type

# 3. Exécuter linter
ruff check .
# ✅ Code quality OK
```

### Feature 4️⃣ : CI/CD GitHub Actions

```bash
# 1. Créer un repo GitHub
git init
git add .
git commit -m "feat: add 4 killer features"

# 2. Push vers GitHub
git remote add origin https://github.com/YOUR_USERNAME/tgr-api.git
git push -u origin main

# 3. Aller sur GitHub → Actions
# ✅ Voyez le pipeline s'exécuter automatiquement!
```

---

## 📊 Curl commands de démo

### Exemple complet : Enregistrer → Uploader → Consulter

```bash
#!/bin/bash
set -e

echo "🚀 Quick Start Demo - Les 4 Killer Features"
echo "==========================================="
echo ""

# Step 1: Enregistrer
echo "📝 Step 1 : Créer un utilisateur..."
RESPONSE=$(curl -s -X POST \
  "http://localhost:8000/api/db/users/register?organization=TestDemoTGR&email=demo@tgr.gov.ma")
API_KEY=$(echo $RESPONSE | jq -r '.api_key')
USER_ID=$(echo $RESPONSE | jq -r '.user_id')
echo "✅ Utilisateur créé : user_id=$USER_ID"
echo "✅ API Key : $API_KEY"
echo ""

# Step 2: Uploader et prédire
echo "📤 Step 2 : Upload et prédiction..."
PREDICT_RESPONSE=$(curl -s -X POST \
  "http://localhost:8000/predict" \
  -H "X-API-Key: $API_KEY" \
  -F "file=@demo_sample.csv")

MODEL=$(echo $PREDICT_RESPONSE | jq -r '.model_info.name')
ANOMALIES_COUNT=$(echo $PREDICT_RESPONSE | jq '.anomalies | length')
echo "✅ Prédiction réussie : Model=$MODEL"
echo "✅ Anomalies détectées : $ANOMALIES_COUNT"
echo ""

# Step 3: Consulter infos utilisateur
echo "👤 Step 3 : Consulter profil..."
curl -s -X GET \
  "http://localhost:8000/api/db/users/info?api_key=$API_KEY" | jq '.stats'
echo ""

# Step 4: Lister anomalies
echo "🔍 Step 4 : Lister les anomalies..."
curl -s -X GET \
  "http://localhost:8000/api/db/anomalies/list?api_key=$API_KEY" | jq '.anomalies[0:2]'
echo ""

# Step 5: Stats
echo "📊 Step 5 : Statistiques d'utilisation..."
curl -s -X GET \
  "http://localhost:8000/api/db/stats/overview?api_key=$API_KEY" | jq '.usage'
echo ""

echo "✅ Demo terminée ! Consultez les 4 features en action."
```

Exécuter :
```bash
chmod +x quick_demo.sh
./quick_demo.sh
```

---

## 🔍 Tester chaque feature individuellement

### Test 1: Anomalies

```bash
# Voir les anomalies dans la réponse /predict
curl -s -X POST "http://localhost:8000/predict" \
  -H "X-API-Key: $API_KEY" \
  -F "file=@demo_sample.csv" | jq '.anomalies | .[0]'

# Résultat attendu:
# {
#   "date": "2023-03-01",
#   "actual_value": 5000000,
#   "predicted_value": 3000000,
#   "residual": 2000000,
#   "std_deviations": 2.5,
#   "severity": "HIGH",
#   "description": "Dépense 67% supérieure à la normale..."
# }
```

### Test 2: BD (SQLModel)

```bash
# Vérifier fichiers
curl -s "http://localhost:8000/api/db/files/list?api_key=$API_KEY" | jq '.files | length'

# Vérifier prédictions
curl -s "http://localhost:8000/api/db/predictions/list?api_key=$API_KEY" | jq '.predictions | length'

# Vérifier anomalies
curl -s "http://localhost:8000/api/db/anomalies/list?api_key=$API_KEY" | jq '.total_anomalies'

# Tous les 3 doivent être > 0 ✅
```

### Test 3: Black + MyPy

```bash
# Formater
black . --check  # Vérify sans modif

# Vérifier types
mypy . --ignore-missing-imports --no-error-summary 2>&1 | head -5

# Résultat : aucune erreur ✅
```

### Test 4: GitHub Actions

```bash
# Depuis GitHub.com :
# 1. Aller sur votre repo
# 2. Cliquer "Actions" tab
# 3. Voir le workflow "CI/CD Pipeline - TGR API"
# 4. Cliquer pour voir détails

# Chaque job doit être ✅ green
```

---

## 🎁 Fichier de données de test

Si vous n'avez pas `demo_sample.csv`, créer un :

```bash
cat > test_data.csv << 'EOF'
date,montant
2020-01-01,1000000
2020-02-01,1100000
2020-03-01,1050000
2020-04-01,1200000
2020-05-01,5000000
2020-06-01,1150000
2020-07-01,1100000
2020-08-01,1300000
2020-09-01,1250000
2020-10-01,1200000
2020-11-01,1150000
2020-12-01,2000000
2021-01-01,1000000
2021-02-01,1100000
2021-03-01,1050000
EOF

# Utiliser :
curl -X POST "http://localhost:8000/predict" \
  -H "X-API-Key: $API_KEY" \
  -F "file=@test_data.csv"
```

---

## 🆘 Troubleshooting

### Port 8000 déjà utilisé?
```bash
# Utiliser autre port
uvicorn main:app --port 8001
```

### Erreur SQLModel import?
```bash
pip install sqlmodel sqlalchemy
```

### GitHub Actions ne démarre pas?
```bash
# Vérifier que .github/workflows/ci.yml existe
ls -la .github/workflows/

# S'assure que c'est pushé
git add .github/workflows/ci.yml
git commit -m "add CI/CD"
git push
```

---

## ✅ Checklist pour avoir 4/4 features

- [ ] **Feature 1** : API `/predict` retourne un champ `"anomalies"` avec données
- [ ] **Feature 2** : Endpoints `/api/db/...` marchent et retournent des données
- [ ] **Feature 3** : `black --check` et `mypy` passent sans erreur
- [ ] **Feature 4** : Un workflow GitHub Actions s'est exécuté (vert ✅)

---

## 📚 Documentation complète

Consulter le [guide complet](KILLER_FEATURES_GUIDE.md) pour plus de détails.

---

## 🎬 Prochains pas

1. **Intégrez à votre CI/CD** : Push vers GitHub et regarder GitHub Actions s'exécuter
2. **Testez les anomalies** : Uploader des données réelles TGR et vérifier détection
3. **Explorez la BD** : Faire des requêtes SQL sur `tgr_api.db` pour audits
4. **Phase 2** : Ajouter modèles DL (DeepAR, CNN) quand vous êtes prêt

---

Happy coding! 🚀
```
