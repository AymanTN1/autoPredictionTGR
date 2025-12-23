import os
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

warnings.filterwarnings("ignore")


# ==============================================================================
# CLASSE 1 : LE NETTOYEUR (DataCleaner)
# Responsable du chargement, nettoyage et agrégation des données en série mensuelle
# ==============================================================================
class DataCleaner:
    """Charge un CSV, détecte colonnes date/montant, nettoie et agrège en mensuel.
    
    Utilise seulement les opérations pandas du cours : parsing, resampling, 
    nettoyage simple.
    """
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None

    def _detect_separator(self):
        """Détecte le séparateur CSV (';' ou ',')."""
        with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
            if ';' in f.readline():
                return ';'
            return ','

    def _find_column(self, cols, keywords):
        """Cherche la première colonne contenant un des keywords."""
        for c in cols:
            for key in keywords:
                if key in c:
                    return c
        return None

    def run(self):
        """Lance le pipeline complet : chargement -> nettoyage -> agrégation -> retour DataFrame."""
        print(f"--- 1. NETTOYAGE : {os.path.basename(self.file_path)} ---")
        
        sep = self._detect_separator()
        self.df = pd.read_csv(self.file_path, sep=sep, encoding='utf-8', low_memory=False)
        self.df.columns = self.df.columns.str.strip().str.lower()

        # Détection automatique colonnes
        col_date = self._find_column(self.df.columns, ['date', 'jour', 'time', 'reglement', 'payment'])
        col_amount = self._find_column(self.df.columns, ['montant', 'sum', 'prix', 'amount', 'valeur'])

        if not col_date or not col_amount:
            raise ValueError(f"Impossible de trouver Date/Montant. Colonnes : {list(self.df.columns)}")

        # Nettoyage montants (virgule décimale -> point)
        self.df['clean_amount'] = pd.to_numeric(
            self.df[col_amount].astype(str).str.replace('\u00A0', '').str.replace(' ', '').str.replace(',', '.'),
            errors='coerce'
        )
        
        # Parsing dates
        self.df['clean_date'] = pd.to_datetime(self.df[col_date], dayfirst=True, errors='coerce')
        if self.df['clean_date'].isna().sum() > 0:
            self.df['clean_date'] = pd.to_datetime(self.df[col_date], dayfirst=False, errors='coerce')
        
        # Filtrage et indexation
        self.df = self.df.dropna(subset=['clean_date', 'clean_amount']).set_index('clean_date').sort_index()
        
        # Agrégation : journalière puis mensuelle (MS = Month Start)
        daily = self.df['clean_amount'].resample('D').sum()
        self.df_clean = daily.resample('MS').sum().to_frame(name='montant')
        
        # Enlever dernier mois si incomplet
        if len(self.df_clean) > 1:
            self.df_clean = self.df_clean.iloc[:-1]
        
        print(f"   -> Données prêtes : {len(self.df_clean)} mois.")
        return self.df_clean


# ==============================================================================
# CLASSE 2 : LE PRÉDICTEUR INTELLIGENT (SmartPredictor)
# Responsable de la sélection modèle (AR vs MA vs ARMA vs ARIMA vs SARIMA)
# via un tournoi AIC, puis du fitting et prédiction.
# ==============================================================================
class SmartPredictor:
    """Sélectionne le meilleur modèle parmi AR, MA, ARMA, ARIMA, SARIMA en fonction
    de la stationnarité et saisonnalité, puis effectue la prédiction.
    
    La sélection entre AR/MA/ARMA/ARIMA utilise le score AIC (plus bas = meilleur).
    """
    
    def __init__(self, df_data):
        self.df = df_data
        self.model_name = "Inconnu"
        self.order = (0, 0, 0)
        self.seasonal_order = (0, 0, 0, 0)

    def _calculer_aic(self, order, seasonal_order=(0, 0, 0, 0)):
        """Helper : Teste un modèle et retourne son AIC.
        
        AIC (Akaike Information Criterion) = critère pour comparer la qualité
        des modèles. Plus bas = meilleur ajustement.
        """
        try:
            model = SARIMAX(
                self.df['montant'],
                order=order,
                seasonal_order=seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            results = model.fit(disp=False)
            return results.aic
        except Exception:
            return float('inf')  # Si ça plante, score très mauvais

    def plot_acf_pacf(self, lags=24):
        """Affiche ACF et PACF pour diagnostic (optionnel)."""
        series = self.df['montant'].dropna()
        plt.figure(figsize=(12, 4))
        plot_acf(series, lags=lags)
        plt.show()
        plt.figure(figsize=(12, 4))
        plot_pacf(series, lags=lags, method='ywm')
        plt.show()

    def analyze_and_configure(self):
        """Lance l'analyse et la sélection du modèle optimal.
        
        Étapes :
        1. Détecte la saisonnalité via seasonal_decompose
        2. Si saisonnalité -> SARIMA directement
        3. Si pas saisonnalité -> Test stationnarité (ADF)
           - Si non-stationnaire -> ARIMA (besoin d'intégration)
           - Si stationnaire -> Tournoi AR vs MA vs ARMA (via AIC)
        """
        print("\n--- 2. ANALYSE ET SÉLECTION DU MODÈLE (AR vs MA vs ARMA vs ARIMA vs SARIMA) ---")
        
        # --- ÉTAPE 1 : TEST SAISONNALITÉ ---
        decomp = seasonal_decompose(self.df['montant'], period=12)
        season_amp = decomp.seasonal.max() - decomp.seasonal.min()
        total_amp = self.df['montant'].max() - self.df['montant'].min()
        
        has_seasonality = season_amp > 0.1 * total_amp
        
        if has_seasonality:
            # Saisonnalité détectée -> SARIMA obligatoirement
            # (AR, MA, ARMA, ARIMA ne gèrent pas la saisonnalité)
            print("   -> Saisonnalité détectée (>10% de l'amplitude totale).")
            print("   -> On utilise SARIMA (seul modèle qui gère les saisons).")
            
            self.model_name = "SARIMA"
            
            # Vérifier si besoin d'intégration pour la partie ARIMA
            res_adf = adfuller(self.df['montant'].dropna())
            d = 1 if res_adf[1] > 0.05 else 0
            
            self.order = (1, d, 1)
            self.seasonal_order = (1, 1, 1, 12)
            
        else:
            # Pas de saisonnalité -> Choix entre AR, MA, ARMA, ARIMA
            print("   -> Pas de saisonnalité forte détectée.")
            print("   -> Analyse fine : stationnarité et tournoi AR/MA/ARMA/ARIMA...")
            
            # --- ÉTAPE 2 : TEST STATIONNARITÉ (ADF) ---
            res_adf = adfuller(self.df['montant'].dropna())
            p_value = res_adf[1]
            
            if p_value > 0.05:
                # Non-stationnaire -> Besoin d'intégration (I)
                # Donc ARIMA (AR/MA/ARMA exigent la stationnarité)
                print(f"   -> Série non-stationnaire (ADF p={p_value:.4f})")
                print("   -> Besoin d'intégration (d=1). Modèle : ARIMA")
                self.model_name = "ARIMA"
                self.order = (1, 1, 1)
                self.seasonal_order = (0, 0, 0, 0)
                
            else:
                # Stationnaire -> d=0
                # Tournoi : AR vs MA vs ARMA
                print(f"   -> Série stationnaire (ADF p={p_value:.4f})")
                print("   -> Pas besoin d'intégration (d=0). Tournoi AR vs MA vs ARMA...")
                
                aic_ar = self._calculer_aic((1, 0, 0))
                aic_ma = self._calculer_aic((0, 0, 1))
                aic_arma = self._calculer_aic((1, 0, 1))
                
                print(f"      AIC : AR={aic_ar:.1f}, MA={aic_ma:.1f}, ARMA={aic_arma:.1f}")
                
                best_score = min(aic_ar, aic_ma, aic_arma)
                
                if best_score == aic_ar:
                    self.model_name = "AR"
                    self.order = (1, 0, 0)
                elif best_score == aic_ma:
                    self.model_name = "MA"
                    self.order = (0, 0, 1)
                else:
                    self.model_name = "ARMA"
                    self.order = (1, 0, 1)
                
                self.seasonal_order = (0, 0, 0, 0)
        
        print(f"   -> RÉSULTAT : {self.model_name} order={self.order} seasonal_order={self.seasonal_order}")

    def predict(self, months=12, save_csv=True, out_path=None, dataset_name=None):
        """Entraîne le modèle sélectionné et produit les prévisions.
        
        Retourne un DataFrame avec colonnes : 'prévision', 'min_confiance', 'max_confiance'
        Optionnellement sauvegarde en CSV et affiche un graphique.
        """
        print(f"\n--- 3. PRÉDICTION ({self.model_name}, {months} mois) ---")
        
        # Inform exactly which model will be fitted (SARIMAX used as a generic fitter)
        print(f"   -> Fitting SARIMAX with order={self.order} seasonal_order={self.seasonal_order} (label={self.model_name})")
        model = SARIMAX(
            self.df['montant'],
            order=self.order,
            seasonal_order=self.seasonal_order,
            enforce_stationarity=False,
            enforce_invertibility=False
        )
        results = model.fit(disp=False)
        
        forecast = results.get_forecast(steps=months)
        pred = forecast.predicted_mean
        conf = forecast.conf_int()
        
        df_forecast = pd.DataFrame({
            'prévision': pred.values,
            'min_confiance': conf.iloc[:, 0].values,
            'max_confiance': conf.iloc[:, 1].values
        }, index=pred.index)
        
        # Sauvegarde CSV
        if save_csv:
            path = out_path or os.path.join(os.path.dirname(self.file_path) if hasattr(self, 'file_path') else '.', 'previsions_automatiques.csv')
            df_forecast.to_csv(path)
            print(f"   -> Prévisions sauvegardées : {path}")
        
        # Graphique
        plt.figure(figsize=(12, 6))
        plt.plot(self.df.index, self.df['montant'], label='Historique', marker='o')
        plt.plot(df_forecast.index, df_forecast['prévision'], label=f'Prévision {self.model_name}', color='red', marker='s')
        plt.fill_between(
            df_forecast.index,
            df_forecast['min_confiance'],
            df_forecast['max_confiance'],
            color='pink',
            alpha=0.3,
            label='IC 95%'
        )
        title = f'Prévision avec modèle {self.model_name}'
        if dataset_name:
            title = f"{dataset_name} — {title}"
        plt.title(title)
        plt.xlabel('Date')
        plt.ylabel('Montant')
        plt.legend()
        plt.grid(True)
        plt.show()
        
        return df_forecast


# ==============================================================================
# MAIN
# ==============================================================================
if __name__ == "__main__":
    import sys

    # Fichier de données (par défaut)
    file = os.path.join('dataSets', 'depensesEtat.csv')

    # Nombre de mois : si fourni en argument, on l'utilise, sinon on demande à l'utilisateur
    months = None
    if len(sys.argv) > 1:
        try:
            months = int(sys.argv[1])
        except Exception:
            months = None
#--------------------------------------------------------
    if months is None:
        # Prompt interactif (saisie manuelle) — défaut 12 si entrée vide
        while True:
            try:
                s = input('Entrez le nombre de mois à prédire (par ex. 12) [ENTER=12] : ').strip()
            except EOFError:
                # Cas non interactif : fallback à 12
                months = 12
                break
            if s == '':
                months = 12
                break
            if s.lower() in ('q', 'quit', 'exit'):
                print('Annulation par l\'utilisateur.')
                raise SystemExit(0)
            try:
                months = int(s)
                if months <= 0:
                    print('Veuillez entrer un entier positif.')
                    continue
                break
            except ValueError:
                print('Entrée invalide — veuillez entrer un entier (ou ENTER pour 12).')
    #--------------------------------------------------------
    try:
        # Étape 1 : Nettoyage
        cleaner = DataCleaner(file)
        df_propre = cleaner.run()
        
        # Étape 2 : Sélection et prédiction
        predictor = SmartPredictor(df_propre)
        predictor.analyze_and_configure()
        predictor.predict(months=months, save_csv=True)
        
        print('\n--- PRÉVISION TERMINÉE AVEC SUCCÈS ---')
        
    except Exception as e:
        print(f"ERREUR : {e}")
        import traceback
        traceback.print_exc()