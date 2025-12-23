import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.stattools import adfuller, acf, pacf
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.seasonal import seasonal_decompose
from sklearn.metrics import mean_absolute_percentage_error
from datetime import timedelta
import warnings
import os

warnings.filterwarnings("ignore")

# ==============================================================================
# 1. CHARGEMENT ET NETTOYAGE
# ==============================================================================
print("--- 1. CHARGEMENT ET PRÉPARATION ---")

# Déterminer le chemin du CSV (compatible Google Colab et VS Code)
csv_path = os.path.join(os.path.dirname(__file__), 'dataSets', 'depensesEtat.csv')
df = pd.read_csv(csv_path, sep=';')
df.columns = df.columns.str.strip()

# Nettoyage Montant
col_source = 'SUM(MONTANT_A_REGLER)'
if col_source not in df.columns: col_source = df.columns[2]
df['montant'] = df[col_source].astype(str).str.replace(',', '.')
df['montant'] = pd.to_numeric(df['montant'], errors='coerce')

# Nettoyage Date
df['date'] = pd.to_datetime(df['DATE_REGLEMENT'], dayfirst=True, errors='coerce')
df = df.set_index('date').sort_index()

# Agrégation (Fusion des doublons journaliers)
df_journalier = df.groupby(df.index)['montant'].sum().to_frame(name='montant')

# Agrégation Mensuelle (Pour le modèle)
df_mensuel = df_journalier['montant'].resample('MS').sum().to_frame(name='montant')
df_mensuel = df_mensuel.iloc[:-1] # On supprime le mois en cours (incomplet)

print(f"-> Données prêtes : {len(df_mensuel)} mois d'historique.")

# ==============================================================================
# 2. ANALYSE (EDA) & DÉCOMPOSITION
# ==============================================================================
print("\n--- 2. ANALYSE EXPLORATOIRE ---")
# Décomposition pour prouver la saisonnalité
res = seasonal_decompose(df_mensuel['montant'], model='additive')
res.plot()
plt.show()

# Test Stationnarité (ADF)
result_adf = adfuller(df_mensuel['montant'])
print(f"p-value ADF (Brut) : {result_adf[1]:.5f}")

if result_adf[1] > 0.05:
    print("-> La série n'est pas stationnaire. Différenciation nécessaire (d=1, D=1).")

# ==============================================================================
# 3. CONTRÔLE MÉTIER (JOURS FÉRIÉS & DICHOTOMIE)
# ==============================================================================
print("\n--- 3. CONTRÔLE JOURS FÉRIÉS (DICHOTOMIE) ---")
# Liste simplifiée pour l'exemple (à compléter avec ta liste complète)
jours_feries_fixes = ["2024-01-01", "2024-01-11", "2024-05-01", "2024-07-30", "2024-08-14", "2024-08-20", "2024-08-21", "2024-11-06", "2024-11-18"]
jours_feries_dt = sorted([pd.to_datetime(d) for d in jours_feries_fixes])

def est_ferie_dichotomie(date_cible, liste_triee):
    debut, fin = 0, len(liste_triee) - 1
    while debut <= fin:
        milieu = (debut + fin) // 2
        if liste_triee[milieu] == date_cible: return True
        elif liste_triee[milieu] < date_cible: debut = milieu + 1
        else: fin = milieu - 1
    return False

def est_jour_ouvrable(date_verif):
    if date_verif.weekday() >= 5: return False # Samedi/Dimanche
    if est_ferie_dichotomie(date_verif, jours_feries_dt): return False
    return True

# Test rapide
test_date = pd.to_datetime("2024-01-11")
print(f"Test du 11 Janvier 2024 (Férié) : Est ouvrable ? -> {est_jour_ouvrable(test_date)}")

# ==============================================================================
# 4. MODÉLISATION SARIMA (1,1,1)(1,1,1,12)
# ==============================================================================
print("\n--- 4. ENTRAÎNEMENT SARIMA & VALIDATION ---")

# Train / Test Split
train = df_mensuel.iloc[:-12]
test = df_mensuel.iloc[-12:]

# Modèle
model = SARIMAX(train['montant'], order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
results = model.fit(disp=False)

# Validation
predictions = results.get_forecast(steps=len(test))
pred_vals = predictions.predicted_mean
mape = mean_absolute_percentage_error(test['montant'], pred_vals)

print(f"-> Marge d'erreur moyenne (MAPE) sur 2024/2025 : {mape:.2%}")

# Graphique de Validation
plt.figure(figsize=(12, 6))
plt.plot(train.index, train['montant'], label='Train')
plt.plot(test.index, test['montant'], label='Réalité (Test)', color='green')
plt.plot(pred_vals.index, pred_vals, label='Prédiction SARIMA', color='red', linestyle='--')
plt.title('Validation du Modèle (Backtest)')
plt.legend()
plt.show()

# ==============================================================================
# 5. PRÉDICTION FINALE 2026
# ==============================================================================
print("\n--- 5. PRÉDICTION FINALE 2026 ---")
full_model = SARIMAX(df_mensuel['montant'], order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
full_results = full_model.fit(disp=False)

# Prédiction sur 18 mois (Fin 2026)
forecast_2026 = full_results.get_forecast(steps=18)
forecast_vals = forecast_2026.predicted_mean
conf_int = forecast_2026.conf_int()

# Graphique Final
plt.figure(figsize=(14, 7))
plt.plot(df_mensuel.index, df_mensuel['montant'], label='Historique')
plt.plot(forecast_vals.index, forecast_vals, label='Prévision 2026', color='red', marker='o')
plt.fill_between(forecast_vals.index, conf_int.iloc[:, 0], conf_int.iloc[:, 1], color='pink', alpha=0.3)
plt.title('Prévision des Dépenses TGR jusqu\'en 2026')
plt.grid(True)
plt.legend()
plt.show()

print("Terminé. Modèle validé et prédictions générées.")