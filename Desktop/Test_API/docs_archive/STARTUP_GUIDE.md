# 🚀 Comment Démarrer le Système Complet

## Les 3 Méthodes (Choisir une)

### 🔥 Méthode 1 : Windows (Plus facile)

Double-cliquez sur :
```
start_all.bat
```

Cela va automatiquement :
- Vérifier l'environnement
- Créer répertoire logs/
- Créer .env s'il n'existe pas
- Lancer API + Dashboard

**Résultat :**
- Terminal se lance et affiche les logs
- API disponible : http://localhost:8000
- Dashboard disponible : http://localhost:8501

### 💻 Méthode 2 : Python (Universel)

```bash
python run_all.py
```

**Résultat :** Même que Méthode 1

### 🎯 Méthode 3 : Manuel (Pour débogage)

**Terminal 1 - API:**
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Dashboard:**
```bash
streamlit run dashboard.py
```

**Terminal 3 - Tests (optionnel):**
```bash
pytest test_complete_suite.py -v
```

---

## 🌐 Une fois démarré

### Accès Web

Ouvrir dans le navigateur :

| Service | URL | Rôle |
|---------|-----|------|
| Dashboard | `http://localhost:8501` | Interface Wow (graphiques) |
| API | `http://localhost:8000` | Backend API |
| Swagger Docs | `http://localhost:8000/docs` | Documentation interactive |
| Health Check | `http://localhost:8000/health` | Vérifier API active |

### Workflow Utilisateur

1. Ouvrir **http://localhost:8501**
2. Dans la sidebar à gauche :
   - Coller la clé API (défaut: `TGR-SECRET-KEY-12345`)
   - Choisir mode **AUTO** ou **USER**
3. Glisser-déposer un fichier CSV
4. Voir les résultats + graphiques en temps réel
5. Exporter CSV/JSON

### Fichiers Logs

```
logs/
├── app.log         ← Logs applicatifs (tous les appels)
└── security.log    ← Logs sécurité (accès API, clés invalides)
```

Consulter en temps réel :
```bash
# Terminal 4 - Logs applicatifs
tail -f logs/app.log

# Terminal 5 - Logs sécurité
tail -f logs/security.log
```

---

## 🧪 Tests Automatisés

Lancer la suite complète :
```bash
pytest test_complete_suite.py -v
```

Résultat attendu : **25+/35 tests réussis** (selon fonctionnalités)

Tests spécifiques :
```bash
# Seulement tests sécurité
pytest test_complete_suite.py -k security -v

# Seulement tests API
pytest test_complete_suite.py -k TestAPIRoutes -v

# Seulement un test
pytest test_complete_suite.py::TestSecurityAPIKey::test_missing_api_key -v
```

---

## 🔧 Troubleshooting

### "API Key invalide"

```
Vérifier la clé API dans .env ou le fichier :
cat .env
# Ou sur Windows :
type .env
```

Doit contenir :
```
TGR_API_KEY=TGR-SECRET-KEY-12345
```

### "Port 8000 déjà utilisé"

```bash
# Trouver processus sur port 8000
lsof -i :8000

# Sur Windows :
netstat -ano | findstr :8000

# Tuer le processus (Windows)
taskkill /PID <PID> /F
```

Puis redémarrer.

### "Module not found"

```bash
# Réinstaller les dépendances
pip install -r requirements.txt
```

Ou spécifiques :
```bash
pip install loguru python-dotenv pytest pytest-asyncio httpx streamlit plotly
```

### "Streamlit ne se connecte pas à l'API"

```bash
# Vérifier que l'API est active
curl http://localhost:8000/health
# Ou sur Windows :
Invoke-WebRequest http://localhost:8000/health
```

Si erreur, relancer l'API.

### "Logs non créés"

Dossier `logs/` créé automatiquement au premier appel API.

Si problème :
```bash
mkdir logs
chmod 755 logs
```

---

## 📊 Cas d'usage typiques

### Cas 1 : CSV Dense (Bon)

**Données :** 12 mois de 2024, tous les mois ont des valeurs

**Résultat AUTO :**
- ✅ Détecte 12 mois actifs
- ✅ Calcule durée sûre = 12/3 = 4 mois
- 📈 Prédiction 4 mois avec confiance élevée

### Cas 2 : CSV Épars (Détection sparsity)

**Données :** 72 mois (2020-2026) mais 2 jours seulement de données réelles

**Résultat AUTO :**
- ⚠️ Détecte sparsity (2.8% densité)
- ✂️ Réduit durée à 3 mois (minimale)
- ℹ️ Affiche raison : "Durée réduite (sparsity détectée)"

### Cas 3 : User demande trop (Sécurité)

**Données :** Épars + user demande 24 mois

**Résultat :**
- 🔒 Smart Duration réduit à 3 mois (sécurité)
- ℹ️ Raison affichée : "Durée réduite de 24 à 3 par sécurité"

---

## 📱 Format CSV attendu

### Minimal (2 colonnes)

```csv
date;amount
2024-01-01;10000
2024-02-01;12000
2024-03-01;11000
```

### Avec code ordinateur (3 colonnes)

```csv
date;ordinateur;montant
2024-01-01;146014;10000
2024-02-01;146014;12000
2024-01-01;146029;8000
```

---

## ⌨️ Commandes Utiles

```bash
# Tout démarrer
python run_all.py

# Vérification d'intégrité
python quick_test.py

# Tests complets
pytest test_complete_suite.py -v

# Vérifier syntaxe
python -m py_compile logic.py main.py dashboard.py

# Voir imports
python -c "import loguru, dotenv, pytest, streamlit, plotly; print('✓ OK')"

# Lire .env
cat .env
# Ou sur Windows :
type .env

# Voir logs en temps réel
tail -f logs/app.log

# Nettoyer (avant Git commit)
rm -rf logs/*.log __pycache__ .pytest_cache
# Ou sur Windows :
Remove-Item logs/*.log
Remove-Item -Recurse __pycache__, .pytest_cache
```

---

## 🎯 Points Clés

| Élément | Location | Rôle |
|---------|----------|------|
| **Configuration** | `.env` | Secrets + variables d'env |
| **Logging** | `logs/app.log` | Trace applicatif |
| **Sécurité** | `logs/security.log` | Audit trail accès |
| **API Key** | `.env` → `TGR_API_KEY` | Authentification |
| **Dashboard** | `http://localhost:8501` | Interface utilisateur |
| **API Docs** | `http://localhost:8000/docs` | Swagger interactif |

---

## ✅ Checklist Avant Présentation

- [ ] API démarre sans erreur (`python run_all.py`)
- [ ] Dashboard accessible à `http://localhost:8501`
- [ ] Upload CSV fonctionne
- [ ] Graphiques s'affichent correctement
- [ ] Export CSV/JSON possible
- [ ] Logs se créent dans `logs/`
- [ ] Tests passent (`pytest test_complete_suite.py -v`)
- [ ] .env présent et non sur Git

---

## 🎓 Pour Ton Rapport de Stage

### Démarrage du Système

"Le système démarre avec une seule commande (`python run_all.py`) qui lance :
- L'API FastAPI sur port 8000 (Uvicorn)
- Le Dashboard Streamlit sur port 8501
- Logging automatique dans logs/"

### Sécurité

"Authentification par API Key (header X-API-Key). Configuration via .env 
pour respect standards production. Logging sécurité séparé pour audit trail 
(security.log)."

### Interface

"Dashboard Streamlit offre UX professionnelle : graphiques Plotly, export 
CSV/JSON, affichage temps réel. Transformation JSON technique → visuel."

---

## 📞 Besoin d'aide ?

### Références Rapides

- **Loguru docs:** https://loguru.readthedocs.io/
- **FastAPI docs:** https://fastapi.tiangolo.com/
- **Streamlit docs:** https://docs.streamlit.io/
- **Pytest docs:** https://docs.pytest.org/

### Fichiers de Support

- `COMPLETE_GUIDE.md` - Guide détaillé complet
- `IMPROVEMENTS_v2.0.md` - Détails techniques v2.0
- `test_complete_suite.py` - Voir les tests comme exemples

---

**Bonne chance avec ton projet ! 🚀**

*Généré pour TGR API v2.0 | Janvier 2026*
