"""
logic.py - Moteur de prédiction des dépenses (API-ready)

╔════════════════════════════════════════════════════════════════════════════╗
║                      TRANSFORMATIONS MAJEURES                              ║
║              De autoPrediction.py (Scripts) à logic.py (API)               ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 CHANGEMENT 1 : FICHIER → BYTES EN MÉMOIRE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  AVANT (autoPrediction.py) :
    file_path = "C:/Users/.../depensesEtat.csv"  # Chemin sur le disque
    df = pd.read_csv(file_path)                  # Lecture du disque
  
  APRÈS (logic.py) :
    file_content = <bytes binaires du fichier>   # Reçu de l'API (upload)
    df = pd.read_csv(io.BytesIO(file_content))   # Lecture depuis la RAM ✨
  
  POURQUOI ?
    • Dans une API web, les fichiers arrivent sous forme de bytes (flux binaire)
    • Lire depuis la RAM est 10x plus rapide que depuis le disque
    • Sécurité : pas d'écriture sur le disque du serveur
    • Scalabilité : plusieurs utilisateurs simultanément sans conflit de fichiers

🔧 CHANGEMENT 2 : input() → PARAMÈTRES FUNCTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  AVANT (autoPrediction.py) :
    while True:
        months = input("Combien de mois ? ")  # Bloque l'exécution
        predict(months)
  
  APRÈS (logic.py) :
    def predict_from_file_content(file_content, months=12):
        # months est un PARAMÈTRE, pas une question interactive
  
  POURQUOI ?
    • Une API ne peut pas avoir de console interactive
    • Les paramètres viennent de la requête HTTP (GET/POST)
    • C'est non-bloquant : le serveur peut traiter d'autres demandes

📋 CHANGEMENT 3 : print() → LOGS EN LISTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  AVANT (autoPrediction.py) :
    print("Saisonnalité détectée")      # Affichage console uniquement
    print("Choix : SARIMA")             # Personne ne voit (serveur headless)
  
  APRÈS (logic.py) :
    self.logs.append("Saisonnalité détectée")  # Stocké dans une liste
    self.logs.append("Choix : SARIMA")         # Retourné à l'utilisateur
  
  POURQUOI ?
    • Le serveur API n'a pas d'écran pour afficher des messages
    • L'utilisateur final doit COMPRENDRE pourquoi tel modèle a été choisi
    • Ces logs vont dans la réponse JSON pour transparence ✨

📊 CHANGEMENT 4 : plt.show() → DICTIONNAIRE JSON
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  AVANT (autoPrediction.py) :
    plt.show()  # Tente d'ouvrir une fenêtre graphique
                # IMPOSSIBLE sur un serveur headless (sans écran) ❌
  
  APRÈS (logic.py) :
    return {
        "forecast": {
            "dates": [...],      # Timestamps de prévision
            "values": [...],     # Valeurs prédites
            "upper": [...],      # Intervalle confiance sup.
            "lower": [...]       # Intervalle confiance inf.
        }
    }  # Retourne des DONNÉES (pas un graphique)
  

"""

import warnings
import pandas as pd
import numpy as np
import io                          # ← CHANGEMENT 1 : Pour lire bytes depuis RAM
from loguru import logger          # ← NOUVEAU : Logging professionnel
import os
from dotenv import load_dotenv
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tools.sm_exceptions import ConvergenceWarning
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime      # ← Pour les timestamps des réponses

warnings.filterwarnings("ignore")

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION LOGURU (Logging Professionnel)
# ═══════════════════════════════════════════════════════════════════════════
load_dotenv()

# Créer le répertoire logs s'il n'existe pas
os.makedirs("logs", exist_ok=True)

# Configuration Loguru
logger.remove()  # Supprimer handler par défaut
logger.add(
    "logs/app.log",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=os.getenv("LOG_LEVEL", "INFO"),
    rotation="500 MB",  # Rotation si fichier > 500 MB
    retention="7 days"  # Garder logs 7 jours
)

app_logger = logger  # Alias pour clarté


# CLASSE 1 :
class DataCleaner:
    """
    CHANGEMENT MAJEUR vs autoPrediction.py :
      ❌ AVANT : file_path = "C:/Users/.../file.csv"  →  pd.read_csv(file_path)
      ✓ APRÈS : file_content = <bytes>  →  pd.read_csv(io.BytesIO(file_content))

    """
    MAX_FILE_SIZE = 50 * 1024 * 1024  # ← SÉCURITÉ : Max 50 MB par fichier
    
    def __init__(self, file_content):
        
        self.file_content = file_content
        self.df = None
        self.logs = []  # ← CHANGEMENT : On collecte les logs au lieu de les afficher

    def _log(self, msg):
        """
        ← CHANGEMENT 3 : Au lieu de print(), on enregistre dans une liste.
        Cela permet à l'API de retourner les explications à l'utilisateur.
        Args:
            msg (str): Message à enregistrer
        """
        self.logs.append(msg)

    def _detect_separator(self):
        try:
            first_line = self.file_content.split(b'\n')[0].decode('utf-8', errors='ignore')
            return ';' if ';' in first_line else ','
        except Exception:
            return ','

    def _find_column(self, cols, keywords):
        """
        LOGIQUE :
          Parcourt cols et cherche le premier qui contient un keyword
        """
        for c in cols:
            for key in keywords:
                if key in c:
                    return c
        return None

    def run(self):
        """
        Lance le pipeline COMPLET de nettoyage.
        
        ÉTAPES :
        1️⃣  Détecte séparateur (';' ou ',')
        2️⃣  Lit le CSV depuis les BYTES vers mémoire (io.BytesIO)
        3️⃣  Normalise les noms de colonnes (lowercase, trim)
        4️⃣  Détecte automatiquement colonnes date et montant
        5️⃣  Convertit montants (virgule décimale → point)
        6️⃣  Parse les dates (intelligemment : dayfirst, etc.)
        7️⃣  Filtre les valeurs valides (élimine NaN)
        8️⃣  Agrège en série MENSUELLE (important pour SARIMA/ARIMA)
        9️⃣  Enlève dernier mois s'il est incomplet
        
        Returns:
            pd.DataFrame: Index = dates (mensuel), Colonne 'montant' = valeurs
        
        EXEMPLE OUTPUT :
            Index : 2020-01-01, 2020-02-01, 2020-03-01, ...
            Colonne 'montant' : 1000.00, 1500.50, 1200.75, ...
        """
        self._log(f"Chargement du fichier CSV...")
        
        try:
            # Validation : fichier vide / taille maximale
            if not self.file_content or len(self.file_content) == 0:
                raise ValueError("Fichier vide ou contenu invalide")
            if len(self.file_content) > self.MAX_FILE_SIZE:
                raise ValueError("trop volumineux")

            # ÉTAPE 1 : Détection séparateur
            sep = self._detect_separator()
            
            # ← CHANGEMENT 1 : io.BytesIO = simule un fichier depuis les bytes
            # Sans io.BytesIO, pandas ne peut pas lire les bytes directement
            self.df = pd.read_csv(io.BytesIO(self.file_content), sep=sep, encoding='utf-8', low_memory=False)
            
            # Normaliser les noms de colonnes
            self.df.columns = self.df.columns.str.strip().str.lower()

            # ÉTAPE 4 : Détection automatique des colonnes
            # Accepter plusieurs variantes (fr/en) courantes pour "date"
            col_date = self._find_column(self.df.columns, ['date', 'jour', 'mois', 'month', 'time', 'reglement', 'payment'])
            col_amount = self._find_column(self.df.columns, ['montant', 'sum', 'prix', 'amount', 'valeur'])

            if not col_date or not col_amount:
                raise ValueError(f"Impossible de trouver colonnes Date/Montant. Colonnes disponibles : {list(self.df.columns)}")

            self._log(f"Colonnes détectées : date='{col_date}', montant='{col_amount}'")

            # ÉTAPE 5 : Nettoyage montants
            # Conversion : "1 000,50" → "1000.50" → 1000.50 (float)
            self.df['clean_amount'] = pd.to_numeric(
                self.df[col_amount].astype(str).str.replace('\u00A0', '').str.replace(' ', '').str.replace(',', '.'),
                errors='coerce'  # Erreur = NaN (sera supprimée après)
            )
            
            # ÉTAPE 6 : Parsing dates
            # Prioriser dayfirst=False car de nombreux CSV utilisent le format ISO (YYYY-MM-DD)
            # Silence spécifique des UserWarning de pandas "Could not infer format..." pour éviter de polluer les tests
            with warnings.catch_warnings():
                # Ignorer plusieurs messages UserWarning provenant de pandas sur l'inférence de format
                warnings.filterwarnings("ignore", message="Could not infer format.*", category=UserWarning)
                warnings.filterwarnings("ignore", message="Parsing dates in .* when dayfirst=False.*", category=UserWarning)
                self.df['clean_date'] = pd.to_datetime(self.df[col_date], dayfirst=False, errors='coerce')
                if self.df['clean_date'].isna().sum() > 0:
                    # Si dayfirst=False échoue (ex: format français dd/mm/YYYY), essayer dayfirst=True
                    self.df['clean_date'] = pd.to_datetime(self.df[col_date], dayfirst=True, errors='coerce')
            
            # ÉTAPE 7 : Filtrage et indexation
            self.df = self.df.dropna(subset=['clean_date', 'clean_amount']).set_index('clean_date').sort_index()
            
            # ÉTAPE 8 : Agrégation en série mensuelle
            # Raison : SARIMA/ARIMA demandent une fréquence régulière (ex: chaque mois)
            # Sinon les résidus ne sont pas homogènes
            daily = self.df['clean_amount'].resample('D').sum()  # Journalière d'abord
            self.df_clean = daily.resample('MS').sum().to_frame(name='montant')  # MS = 1er du mois
            
            # ÉTAPE 9 : Enlever dernier mois si incomplet
            # Ex : si les données s'arrêtent avant la fin du dernier mois, on l'enlève
            if len(self.df_clean) > 1:
                last_month_start = self.df_clean.index[-1]
                last_month_end = last_month_start + pd.offsets.MonthEnd(0)
                last_original_date = self.df.index.max()
                if last_original_date < last_month_end:
                    self.df_clean = self.df_clean.iloc[:-1]

            # SÉCURITÉ : Vérifier qu'il reste au moins une ligne
            if self.df_clean.empty:
                self._log("ERREUR : Pas de dates valides après parsing.")
                raise ValueError("Aucune date valide trouvée après parsing")

            self._log(f"Données prêtes : {len(self.df_clean)} mois (de {self.df_clean.index[0].strftime('%Y-%m-%d')} à {self.df_clean.index[-1].strftime('%Y-%m-%d')})")
            return self.df_clean
            
        except Exception as e:
            self._log(f"ERREUR lors du nettoyage : {str(e)}")
            raise


# ==============================================================================
# CLASSE 2 : LE PRÉDICTEUR INTELLIGENT (SmartPredictor) - VERSION API
# ==============================================================================
class SmartPredictor:
    """
    ╔════════════════════════════════════════════════════════════════════════╗
    │ SmartPredictor - Analyse les données et sélectionne le meilleur modèle │
    ╚════════════════════════════════════════════════════════════════════════╝
    
    RÔLE :
      1. Analyse la série temporelle (saisonnalité, stationnarité)
      2. Sélectionne le modèle optimal parmi : AR, MA, ARMA, ARIMA, SARIMA
      3. Entraîne le modèle
      4. Génère des prévisions avec intervalles de confiance
      5. Retourne tout en dictionnaire JSON (pas de graphiques)
    
    MÉTHODES DE SÉLECTION :
      • Saisonnalité > 10% ? → SARIMA
      • Pas saisonnalité + Non-stationnaire ? → ARIMA
      • Pas saisonnalité + Stationnaire ? → Tournoi AR/MA/ARMA (AIC)
    
    CHANGEMENTS vs autoPrediction.py :
      ❌ AVANT : print("Saisonnalité détectée")  →  Affichage console
      ✓ APRÈS : self.logs.append("Saisonnalité détectée")  →  Stocké pour API
      
      ❌ AVANT : plt.show()  →  Tente d'ouvrir une fenêtre graphique
      ✓ APRÈS : return {...}  →  Retourne les données (brutes) en JSON
    """
    
    def __init__(self, df_data):
        """
        Constructeur : initialise le prédicteur avec des données propres.
        
        Args:
            df_data (pd.DataFrame): DataFrame avec :
                - Index : dates (mensuel)
                - Colonne 'montant' : valeurs à prédire
        """
        self.df = df_data
        self.model_name = "Inconnu"
        self.order = (0, 0, 0)
        self.seasonal_order = (0, 0, 0, 0)
        self.logs = []  # ← CHANGEMENT : On collecte les explications

    def _log(self, msg):
        """
        ← CHANGEMENT 3 : Au lieu de print(), on enregistre pour l'API.
        
        Ces logs seront retournés à l'utilisateur pour qu'il comprenne
        pourquoi SARIMA a été choisi plutôt qu'ARIMA, par exemple.
        
        Args:
            msg (str): Message à enregistrer
        """
        self.logs.append(msg)

    def _calculer_aic(self, order, seasonal_order=(0, 0, 0, 0)):
        """
        Teste un modèle SARIMAX et retourne son critère AIC.
        
        AIC (Akaike Information Criterion) :
          • Mesure la qualité d'ajustement d'un modèle
          • Pénalise les modèles trop complexes
          • PLUS BAS = MEILLEUR (c'est un critère à minimiser, comme l'erreur)
        
        UTILITÉ :
          • Comparer AR vs MA vs ARMA sans expertise humaine
          • Choix objectif et reproductible
        
        Args:
            order (tuple): (p, d, q) pour la partie ARIMA
                - p : AR (AutoRegression) = mémoire du passé
                - d : I (Integration) = différenciation pour stationnarité
                - q : MA (Moving Average) = lissage des erreurs
            
            seasonal_order (tuple): (P, D, Q, s) pour la saisonnalité
                - P, D, Q : comme p, d, q mais pour les saisons
                - s : période (12 pour données mensuelles = 1 an)
        
        Returns:
            float: Valeur AIC (ou inf si erreur)
        
        Exemples :
          • AR(1) : order=(1,0,0) → AIC=150.5
          • MA(1) : order=(0,0,1) → AIC=148.2  ← Meilleur (plus bas)
          • ARMA(1,1) : order=(1,0,1) → AIC=149.8
        """
        try:
            # Créer et entraîner le modèle
            model = SARIMAX(
                self.df['montant'],
                order=order,
                seasonal_order=seasonal_order,
                enforce_stationarity=False,  # Permet de tester même si non-stationnaire
                enforce_invertibility=False  # Permet de tester même si non-inversible
            )
            results = model.fit(disp=False)  # disp=False = pas d'affichage
            return results.aic
        except Exception as e:
            self._log(f"Erreur lors du calcul AIC pour order={order} : {str(e)}")
            return float('inf')  # Si erreur, ce modèle est pénalisé (AIC=∞)

    def _fit_holtwinters(self, seasonal_periods=12):
        """
        Entraîne un modèle Holt-Winters (ExponentialSmoothing) et retourne
        une métrique de sélection (ici AIC si disponible, sinon MSE).
        """
        try:
            model = ExponentialSmoothing(
                self.df['montant'],
                seasonal='add',
                trend='add',
                seasonal_periods=seasonal_periods,
            )
            res = model.fit(optimized=True)
            # statsmodels HWResults may not always exposer .aic; fallback to mse
            aic = getattr(res, 'aic', None)
            if aic is not None:
                return float(aic)
            # fallback: compute in-sample MSE
            fitted = res.fittedvalues
            mse = float(((self.df['montant'] - fitted) ** 2).mean())
            return mse
        except Exception as e:
            self._log(f"HoltWinters error: {e}")
            return float('inf')

    def _fit_lstm(self, look_back=12, epochs=10, batch_size=16):
        """
        Optionnel : petit modèle LSTM si `tensorflow` est installé.
        Retourne une métrique de validation (MSE) ou inf si indisponible.
        """
        try:
            import numpy as _np
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, Dense
            from tensorflow.keras.optimizers import Adam
        except Exception:
            self._log("TensorFlow non installé – LSTM ignoré")
            return float('inf')

    def _fit_gru(self, look_back=12, epochs=10, batch_size=16):
        """
        Optionnel : modèle GRU (Gated Recurrent Unit) si TensorFlow disponible.
        Retourne une métrique de validation (MSE) ou inf si indisponible.
        """
        try:
            import numpy as _np
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import GRU, Dense
            from tensorflow.keras.optimizers import Adam
        except Exception:
            self._log("TensorFlow non installé – GRU ignoré")
            return float('inf')

        try:
            series = self.df['montant'].astype('float32').values
            if len(series) < look_back * 2:
                self._log("Pas assez de données pour GRU")
                return float('inf')

            scaler = MinMaxScaler()
            series_s = scaler.fit_transform(series.reshape(-1, 1)).flatten()

            # Préparer windows
            X, y = [], []
            for i in range(len(series_s) - look_back):
                X.append(series_s[i:i + look_back])
                y.append(series_s[i + look_back])
            X = _np.array(X)
            y = _np.array(y)

            # split train/val
            split = int(len(X) * 0.8)
            X_train, X_val = X[:split], X[split:]
            y_train, y_val = y[:split], y[split:]

            X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
            X_val = X_val.reshape((X_val.shape[0], X_val.shape[1], 1))

            model = Sequential([
                GRU(32, input_shape=(look_back, 1)),
                Dense(1)
            ])
            model.compile(optimizer=Adam(learning_rate=0.01), loss='mse')
            model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=0)
            val_pred = model.predict(X_val, verbose=0).flatten()
            mse = float(((y_val - val_pred) ** 2).mean())
            return mse
        except Exception as e:
            self._log(f"GRU training error: {e}")
            return float('inf')

    def _fit_rnn(self, look_back=12, epochs=10, batch_size=16):
        """
        Optionnel : modèle RNN vanilla (SimpleRNN) si TensorFlow disponible.
        Retourne une métrique de validation (MSE) ou inf si indisponible.
        """
        try:
            import numpy as _np
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import SimpleRNN, Dense
            from tensorflow.keras.optimizers import Adam
        except Exception:
            self._log("TensorFlow non installé – RNN ignoré")
            return float('inf')

        try:
            series = self.df['montant'].astype('float32').values
            if len(series) < look_back * 2:
                self._log("Pas assez de données pour RNN")
                return float('inf')

            scaler = MinMaxScaler()
            series_s = scaler.fit_transform(series.reshape(-1, 1)).flatten()

            # Préparer windows
            X, y = [], []
            for i in range(len(series_s) - look_back):
                X.append(series_s[i:i + look_back])
                y.append(series_s[i + look_back])
            X = _np.array(X)
            y = _np.array(y)

            # split train/val
            split = int(len(X) * 0.8)
            X_train, X_val = X[:split], X[split:]
            y_train, y_val = y[:split], y[split:]

            X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
            X_val = X_val.reshape((X_val.shape[0], X_val.shape[1], 1))

            model = Sequential([
                SimpleRNN(32, input_shape=(look_back, 1)),
                Dense(1)
            ])
            model.compile(optimizer=Adam(learning_rate=0.01), loss='mse')
            model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=0)
            val_pred = model.predict(X_val, verbose=0).flatten()
            mse = float(((y_val - val_pred) ** 2).mean())
            return mse
        except Exception as e:
            self._log(f"RNN training error: {e}")
            return float('inf')

    def _fit_sarimax_exog(self):
        """
        Optionnel : modèle SARIMAX avec variables exogènes (trend).
        Retourne AIC ou inf si erreur.
        """
        try:
            # Créer une variable exogène (trend)
            trend = np.arange(len(self.df))
            
            model = SARIMAX(
                self.df['montant'],
                exog=trend.reshape(-1, 1),
                order=(1, 1, 1),
                seasonal_order=(1, 1, 1, 12),
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=ConvergenceWarning)
                results = model.fit(disp=False)
            self._log(f"SARIMAX exog (trend) fitted: AIC={results.aic:.2f}")
            return float(results.aic)
        except Exception as e:
            self._log(f"SARIMAX exog error: {e}")
            return float('inf')

    def _fit_var(self):
        """
        Optionnel : modèle VAR (Vector Autoregression).
        Utilise montant et une deuxième variable construite (ou tendance).
        Retourne AIC ou inf si indisponible/erreur.
        """
        try:
            from statsmodels.tsa.api import VAR
        except Exception:
            self._log("VAR non disponible (statsmodels version)")
            return float('inf')

        try:
            # Créer une variable auxiliaire (ex: moyenne mobile)
            aux_var = self.df['montant'].rolling(window=3, min_periods=1).mean()
            data = pd.DataFrame({'montant': self.df['montant'], 'trend': aux_var})
            data = data.dropna()
            
            if len(data) < 10:
                self._log("Pas assez de données pour VAR")
                return float('inf')
            
            model = VAR(data)
            results = model.fit(maxlags=1, ic='aic')
            self._log(f"VAR(1) fitted: AIC={results.aic:.2f}")
            return float(results.aic)
        except Exception as e:
            self._log(f"VAR error: {e}")
            return float('inf')

    def _fit_varma(self):
        """
        Optionnel : modèle VARMA (Vector ARMA).
        Retourne AIC ou inf si indisponible/erreur.
        """
        try:
            from statsmodels.tsa.statespace.varmax import VARMAX
        except Exception:
            self._log("VARMAX non disponible (statsmodels version)")
            return float('inf')

        try:
            # Créer variables
            aux_var = self.df['montant'].rolling(window=3, min_periods=1).mean()
            data = pd.DataFrame({'montant': self.df['montant'], 'trend': aux_var})
            data = data.dropna()
            
            if len(data) < 10:
                self._log("Pas assez de données pour VARMA")
                return float('inf')
            
            model = VARMAX(data, order=(1, 1))
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore")
                results = model.fit(disp=False)
            self._log(f"VARMA(1,1) fitted: AIC={results.aic:.2f}")
            return float(results.aic)
        except Exception as e:
            self._log(f"VARMA error: {e}")
            return float('inf')

    def _fit_prophet(self):
        """
        Entraîne un modèle Prophet si disponible. Retourne MSE in-sample.
        """
        try:
            from prophet import Prophet
        except Exception:
            self._log("Prophet non installé – ignoré")
            return float('inf')

        try:
            df_prop = self.df.reset_index().rename(columns={self.df.index.name or 'clean_date': 'ds', 'montant': 'y'})
            df_prop = df_prop[['ds', 'y']]
            m = Prophet()
            m.fit(df_prop)
            # in-sample prediction
            pred = m.predict(df_prop)
            y_true = df_prop['y'].values
            y_pred = pred['yhat'].values
            mse = float(((y_true - y_pred) ** 2).mean())
            return mse
        except Exception as e:
            self._log(f"Prophet error: {e}")
            return float('inf')

    def _forecast_prophet(self, steps):
        try:
            from prophet import Prophet
        except Exception:
            raise RuntimeError("Prophet non installé")

        df_prop = self.df.reset_index().rename(columns={self.df.index.name or 'clean_date': 'ds', 'montant': 'y'})
        df_prop = df_prop[['ds', 'y']]
        m = Prophet()
        m.fit(df_prop)
        future = m.make_future_dataframe(periods=steps, freq='MS')
        forecast = m.predict(future)
        # take tail
        pred = forecast.tail(steps)
        dates = pd.to_datetime(pred['ds']).dt.strftime('%Y-%m-%d').tolist()
        values = pred['yhat'].tolist()
        upper = pred['yhat_upper'].tolist() if 'yhat_upper' in pred else values
        lower = pred['yhat_lower'].tolist() if 'yhat_lower' in pred else values
        return dates, values, upper, lower

    def _fit_cnn(self, look_back=12, epochs=10, batch_size=16):
        """Simple 1D-CNN for time series using TensorFlow/Keras if available.
        Returns validation MSE or inf if unavailable.
        """
        try:
            import numpy as _np
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import Conv1D, GlobalAveragePooling1D, Dense
            from tensorflow.keras.optimizers import Adam
        except Exception:
            self._log("TensorFlow non installé – CNN ignoré")
            return float('inf')

        try:
            series = self.df['montant'].astype('float32').values
            if len(series) < look_back * 2:
                self._log("Pas assez de données pour CNN")
                return float('inf')

            scaler = MinMaxScaler()
            series_s = scaler.fit_transform(series.reshape(-1, 1)).flatten()

            X, y = [], []
            for i in range(len(series_s) - look_back):
                X.append(series_s[i:i + look_back])
                y.append(series_s[i + look_back])
            X = _np.array(X)
            y = _np.array(y)

            split = int(len(X) * 0.8)
            X_train, X_val = X[:split], X[split:]
            y_train, y_val = y[:split], y[split:]

            # Reshape to (samples, timesteps, features)
            X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
            X_val = X_val.reshape((X_val.shape[0], X_val.shape[1], 1))

            model = Sequential([
                Conv1D(filters=16, kernel_size=3, activation='relu', padding='same', input_shape=(look_back, 1)),
                Conv1D(filters=8, kernel_size=3, activation='relu', padding='same'),
                GlobalAveragePooling1D(),
                Dense(1)
            ])

            model.compile(optimizer=Adam(learning_rate=0.01), loss='mse')
            model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=0)
            val_pred = model.predict(X_val, verbose=0).flatten()
            mse = float(((y_val - val_pred) ** 2).mean())
            return mse
        except Exception as e:
            self._log(f"CNN training error: {e}")
            return float('inf')

    def select_best_model(self):
        """Évalue plusieurs modèles (SARIMAX, HoltWinters, Prophet, LSTM, CNN)
        et choisit le meilleur selon un classement par rang (lower is better).
        Met à jour `self.model_name`, `self.order`, `self.seasonal_order` si besoin.
        """
        self._log("Lancement de la sélection étendue de modèles (inclut HoltWinters/Prophet/DL si disponibles)")
        scores = {}

        # SARIMAX score (AIC)
        try:
            scores['SARIMAX'] = self._calculer_aic(self.order, self.seasonal_order)
        except Exception:
            scores['SARIMAX'] = float('inf')

        # SARIMAX avec variables exogènes
        scores['SARIMAX_EXOG'] = self._fit_sarimax_exog()

        # VAR (Vector Autoregression)
        scores['VAR'] = self._fit_var()

        # VARMA (Vector ARMA)
        scores['VARMA'] = self._fit_varma()

        # Holt-Winters
        scores['HOLTWINTERS'] = self._fit_holtwinters(seasonal_periods=12)

        # Prophet
        scores['PROPHET'] = self._fit_prophet()

        # LSTM
        scores['LSTM'] = self._fit_lstm()

        # GRU
        scores['GRU'] = self._fit_gru()

        # RNN
        scores['RNN'] = self._fit_rnn()

        # CNN
        scores['CNN'] = self._fit_cnn()

        # Convert scores to ranks (1 = best)
        # lower score is better for all our metrics (AIC or MSE)
        ranked = sorted(scores.items(), key=lambda x: (float('inf') if x[1] is None else x[1]))
        ranks = {name: idx + 1 for idx, (name, _) in enumerate(ranked)}

        self._log(f"Scores modèles : {scores}")
        self._log(f"Ranks modèles : {ranks}")

        # Choose best by rank
        best = min(ranks.items(), key=lambda x: x[1])[0]
        self._log(f"Meilleur modèle selon sélection étendue : {best}")

        if best == 'HOLTWINTERS':
            self.model_name = 'HOLTWINTERS'
            self.order = (0, 0, 0)
            self.seasonal_order = (0, 0, 0, 0)
        elif best == 'PROPHET':
            self.model_name = 'PROPHET'
            self.order = (0, 0, 0)
            self.seasonal_order = (0, 0, 0, 0)
        elif best == 'LSTM':
            self.model_name = 'LSTM'
        elif best == 'CNN':
            self.model_name = 'CNN'
        else:
            # Keep SARIMAX/AR/ARMA/ARIMA selection
            self._log("Conserver la sélection SARIMAX/ARIMA classique")

        try:
            series = self.df['montant'].astype('float32').values
            if len(series) < look_back * 2:
                self._log("Pas assez de données pour LSTM")
                return float('inf')

            scaler = MinMaxScaler()
            series_s = scaler.fit_transform(series.reshape(-1, 1)).flatten()

            # Préparer windows
            X, y = [], []
            for i in range(len(series_s) - look_back):
                X.append(series_s[i:i + look_back])
                y.append(series_s[i + look_back])
            X = _np.array(X)
            y = _np.array(y)

            # split train/val
            split = int(len(X) * 0.8)
            X_train, X_val = X[:split], X[split:]
            y_train, y_val = y[:split], y[split:]

            X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
            X_val = X_val.reshape((X_val.shape[0], X_val.shape[1], 1))

            model = Sequential([
                LSTM(32, input_shape=(look_back, 1)),
                Dense(1)
            ])
            model.compile(optimizer=Adam(learning_rate=0.01), loss='mse')
            model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=0)
            val_pred = model.predict(X_val, verbose=0).flatten()
            mse = float(((y_val - val_pred) ** 2).mean())
            return mse
        except Exception as e:
            self._log(f"LSTM training error: {e}")
            return float('inf')

    def calculate_and_validate_duration(self, user_months=None):
        """
        ╔═══════════════════════════════════════════════════════════════════╗
        │ SMART DURATION : Détecte la sparsity et valide la durée requise   │
        ╚═══════════════════════════════════════════════════════════════════╝
        
        PROBLÈME RÉSOLU :
        ────────────────
        Un utilisateur uploade un CSV avec données du 29-01-2020 et 29-01-2026.
        Différence : 6 ans = ~72 mois.
        
        Mais en réalité, il y a que 2 jours de données (29 janv 2020 + 29 janv 2026).
        Le fichier est TRÈS SPARSE (creux) !
        
        Si on utilise 72 mois pour SARIMA, les prévisions seront:
          ❌ Peu fiables (prédire 12 mois de futur avec seulement 2 jours de données)
          ❌ Surapprendissage (overfitting)
          ❌ Intervalles de confiance énormes (incertitude très haute)
        
        SOLUTION "INTELLIGENTE" :
        ───────────────────────
        Compter les mois RÉELS où le montant > 0 (data density).
        Diviser par 3 pour une durée sûre (conservative approach).
        Appliquer des bornes (min 3, max 24 mois).
        
        ALGORITHME (4 ÉTAPES) :
        ──────────────────────
        
        📊 ÉTAPE A : Détecter la sparsity
          • Compter les mois WHERE montant > 0
          • Calculer : densité = n_active / total_months
          • Si densité < 20%, alerter l'utilisateur
        
        🔢 ÉTAPE B : Calculer durée sûre
          • Formula : safe_duration = int(n_active / 3)
          • Ratio 1/3 = règle statistique (minimum 3 observations par paramètre)
          • SARIMA(1,1,1)(1,1,1,12) = 8 paramètres → besoin d'au moins 24 obs
          • Donc : n_active=72 → safe=24 mois ✓
        
        📏 ÉTAPE C : Appliquer les bornes
          • Minimum : 3 mois (sinon pas assez de données)
          • Maximum : 24 mois (sinon prédictions trop loin = unreliable)
          • safe_duration = clamp(safe_duration, 3, 24)
        
        🎯 ÉTAPE D : Décider (selon user_months)
          • Si user_months = None (mode AUTO)
            → Retourner safe_duration (le système décide)
          
          • Si user_months > safe_duration
            → Log un avertissement 🔶 avec explication
            → Retourner safe_duration (sécurité > demande utilisateur)
          
          • Si user_months <= safe_duration
            → Log approuvé ✓
            → Retourner user_months (faire confiance à l'utilisateur)
        
        Args:
            user_months (int, optional): Durée demandée par l'utilisateur.
                Si None, mode AUTO (système décide).
        
        Returns:
            int: Nombre de mois approuvés pour la prédiction.
        
        Examples:
            df avec 24 mois actifs, user_months=None
              → safe_duration = 24/3 = 8 → clamped = 8
              → return 8  ✓
            
            df avec 72 mois actifs, user_months=36
              → safe_duration = 72/3 = 24
              → user_months (36) > safe_duration (24)
              → Log avertissement 🔶
              → return 24  (refuse la demande pour raison statistique)
            
            df avec 12 mois actifs, user_months=6
              → safe_duration = 12/3 = 4 → clamped = 4
              → user_months (6) > safe_duration (4)
              → Log avertissement 🔶
              → return 4
        """
        self._log("\n" + "="*70)
        self._log("📊 ANALYSE DE LA DENSITÉ DES DONNÉES (Smart Duration)")
        self._log("="*70)
        
        try:
            # ÉTAPE A : Détection sparsity
            # ─────────────────────────────
            total_months = len(self.df)
            active_months = (self.df['montant'] > 0).sum()  # Compter montant > 0
            data_density = (active_months / total_months) * 100 if total_months > 0 else 0
            
            self._log(f"📈 Période couverte : {total_months} mois")
            self._log(f"📊 Mois ACTIFS (montant > 0) : {active_months}")
            self._log(f"📉 Densité : {data_density:.1f}%")
            
            if data_density < 20:
                self._log(f"⚠️  ATTENTION : Données TRÈS SPARSE (< 20%) - Prévisions peu fiables")
                logger.warning(f"⚠️  Sparse data detected: {data_density:.1f}% active months")
            
            # ÉTAPE B : Calculer durée sûre (règle 1/3)
            # ──────────────────────────────────────────
            safe_duration = int(active_months / 3)
            self._log(f"\n🔢 Durée brute (active_months / 3) : {active_months} / 3 = {safe_duration} mois")
            
            # ÉTAPE C : Appliquer bornes (min 3, max 24)
            # ─────────────────────────────────────────
            MIN_MONTHS = 3
            MAX_MONTHS = 24
            safe_duration = max(MIN_MONTHS, min(safe_duration, MAX_MONTHS))
            
            if safe_duration != int(active_months / 3):
                self._log(f"📏 Après clamping [3, 24] : {safe_duration} mois")
            
            # ÉTAPE D : Décision finale
            # ───────────────────────────
            # Construire une raison lisible (sera utile pour l'API)
            reason_base = "MODE AUTO" if user_months is None else f"USER REQUEST ({user_months})"

            if user_months is None:
                # Mode AUTO
                final_reason = reason_base
                if data_density < 20:
                    final_reason += " - sparsity detected"
                self._log(f"\n✅ MODE AUTO : Durée sélectionnée = {safe_duration} mois")
                self._log(f"💡 (Utilisateur n'a pas spécifié)")
                self._last_duration_reason = final_reason
                return safe_duration

            # --- MODE UTILISATEUR : Autoriser si raisonnable ---
            try:
                requested = int(user_months)
            except Exception:
                self._log("⚠️  Valeur months non numérique : rejetée")
                self._last_duration_reason = f"INVALID USER REQUEST ({user_months})"
                return safe_duration

            # Si la demande est inférieure ou égale à la durée sûre → ok
            if requested <= safe_duration:
                self._log(f"\n✅ APPROUVÉ : {requested} mois (≤ durée sûre {safe_duration})")
                self._last_duration_reason = f"USER OVERRIDE ({requested} <= safe {safe_duration})"
                return requested

            # Si la demande est raisonnable (<= MAX_MONTHS) et ne dépasse pas l'historique → accepter
            MAX_MONTHS = 24
            total_months = total_months = len(self.df)
            if requested <= MAX_MONTHS and requested <= total_months:
                self._log(f"\n✅ APPROUVÉ (USER OVERRIDE) : {requested} mois (dans limites et historique suffisant)")
                self._last_duration_reason = f"USER OVERRIDE ({requested})"
                return requested

            # Sinon, réduire à safe_duration
            self._log(f"\n⚠️  SÉCURITÉ STATISTIQUE ✂️  Durée réduite")
            self._log(f"   • Demande : {requested} mois")
            self._log(f"   • Limite sûre : {safe_duration} mois")
            self._log(f"   • Raison : Données insuffisantes pour prédire {requested} mois")
            self._log(f"   • Décision : Utiliser {safe_duration} mois (rejette {requested})")
            logger.info(f"✂️  Duration reduced: {requested} → {safe_duration} (safety threshold)")
            self._last_duration_reason = f"USER REQUEST REDUCED ({requested} → {safe_duration})"
            return safe_duration
                
        except Exception as e:
            self._log(f"\n❌ Erreur lors de calculate_and_validate_duration : {str(e)}")
            self._log(f"⚠️  Utiliser durée par défaut : 12 mois")
            return 12

    def analyze_and_configure(self):
        """
        ╔════════════════════════════════════════════════════════════════════════╗
        │ SÉLECTION AUTOMATIQUE & INTELLIGENTE DE MODÈLE                         │
        │ (Classique ARIMA/SARIMA + Deep Learning: HW, Prophet, LSTM, CNN)       │
        ╚════════════════════════════════════════════════════════════════════════╝
        
        ALGORITHME :
        ───────────
        1️⃣  Diagnostique : ACF/PACF, stationnarité (ADF), saisonnalité
        2️⃣  Évaluer TOUS les modèles : SARIMA/ARIMA/AR/MA/ARMA + HW + Prophet + LSTM + CNN
        3️⃣  Classer par métrique (AIC/MSE), choisir le MEILLEUR automatiquement
        
        Raises:
            Exception: Si erreur lors de l'analyse
        """
        self._log("╔════════════════════════════════════════════════════════════════╗")
        self._log("║ SÉLECTION AUTOMATIQUE & INTELLIGENTE DE MODÈLE                 ║")
        self._log("║ (Classique + Deep Learning)                                    ║")
        self._log("╚════════════════════════════════════════════════════════════════╝")
        
        try:
            # --- ÉTAPE 0 : Diagnostique initial ---
            self._log("\n📊 ÉTAPE 1 : DIAGNOSTIQUE DE LA SÉRIE")
            self._log("─" * 60)
            
            # Test ADF (stationnarité)
            res_adf = adfuller(self.df['montant'].dropna())
            p_adf = res_adf[1]
            is_stationary = p_adf <= 0.05
            self._log(f"Test ADF: p-value = {p_adf:.4f} → {'Stationnaire ✓' if is_stationary else 'Non-stationnaire ✗'}")
            
            # Saisonnalité
            has_seasonality = False
            season_amp = 0
            if len(self.df) >= 24:
                try:
                    decomp = seasonal_decompose(self.df['montant'], period=12)
                    season_amp = decomp.seasonal.max() - decomp.seasonal.min()
                    total_amp = self.df['montant'].max() - self.df['montant'].min()
                    has_seasonality = season_amp > 0.1 * total_amp
                    self._log(f"Saisonnalité: {'Oui ✓' if has_seasonality else 'Non ✗'} (amplitude={season_amp:.0f})")
                except Exception:
                    self._log("⚠️  Impossible de calculer saisonnalité")
            else:
                self._log("⚠️  Pas assez de données pour saisonnalité (< 24 mois)")
            
            # --- ÉTAPE 1 : ÉVALUER TOUS LES MODÈLES ---
            self._log("\n📈 ÉTAPE 2 : ÉVALUATION DE TOUS LES MODÈLES")
            self._log("─" * 60)
            
            model_scores = {}
            
            # 1a) Modèles ARIMA/SARIMA
            self._log("1️⃣  Modèles ARIMA/SARIMA...")
            if has_seasonality and len(self.df) >= 24:
                aic_sarima = self._calculer_aic((1, 0, 1), seasonal_order=(1, 1, 1, 12))
                model_scores['SARIMA(1,0,1)(1,1,1,12)'] = aic_sarima
                self._log(f"   • SARIMA(1,0,1)(1,1,1,12): AIC={aic_sarima:.1f}")
            
            if not is_stationary:
                aic_arima = self._calculer_aic((1, 1, 1))
                model_scores['ARIMA(1,1,1)'] = aic_arima
                self._log(f"   • ARIMA(1,1,1): AIC={aic_arima:.1f}")
            else:
                # Tournoi AR/MA/ARMA
                aic_ar = self._calculer_aic((1, 0, 0))
                aic_ma = self._calculer_aic((0, 0, 1))
                aic_arma = self._calculer_aic((1, 0, 1))
                model_scores['AR(1)'] = aic_ar
                model_scores['MA(1)'] = aic_ma
                model_scores['ARMA(1,1)'] = aic_arma
                self._log(f"   • AR(1): AIC={aic_ar:.1f}")
                self._log(f"   • MA(1): AIC={aic_ma:.1f}")
                self._log(f"   • ARMA(1,1): AIC={aic_arma:.1f}")
            
            # 1b) Holt-Winters
            self._log("2️⃣  Holt-Winters...")
            hw_score = self._fit_holtwinters()
            model_scores['HoltWinters'] = hw_score
            self._log(f"   • HoltWinters: AIC/MSE={hw_score:.1f}")
            
            # 1c) Prophet
            self._log("3️⃣  Prophet...")
            prophet_score = self._fit_prophet()
            if prophet_score < float('inf'):
                model_scores['Prophet'] = prophet_score
                self._log(f"   • Prophet: MSE={prophet_score:.6f}")
            else:
                self._log(f"   • Prophet: non disponible")
            
            # 1d) Deep Learning (LSTM)
            self._log("4️⃣  Deep Learning (LSTM)...")
            lstm_score = self._fit_lstm(look_back=12, epochs=10)
            if lstm_score < float('inf'):
                model_scores['LSTM'] = lstm_score
                self._log(f"   • LSTM: Validation MSE={lstm_score:.6f}")
            else:
                self._log(f"   • LSTM: non disponible")
            
            # 1e) Deep Learning (CNN)
            self._log("5️⃣  Deep Learning (CNN)...")
            cnn_score = self._fit_cnn(look_back=12, epochs=10)
            if cnn_score < float('inf'):
                model_scores['CNN'] = cnn_score
                self._log(f"   • CNN: Validation MSE={cnn_score:.6f}")
            else:
                self._log(f"   • CNN: non disponible")
            
            # 1f) Deep Learning (GRU)
            self._log("6️⃣  Deep Learning (GRU)...")
            gru_score = self._fit_gru(look_back=12, epochs=10)
            if gru_score < float('inf'):
                model_scores['GRU'] = gru_score
                self._log(f"   • GRU: Validation MSE={gru_score:.6f}")
            else:
                self._log(f"   • GRU: non disponible")
            
            # 1g) Deep Learning (RNN)
            self._log("7️⃣  Deep Learning (RNN)...")
            rnn_score = self._fit_rnn(look_back=12, epochs=10)
            if rnn_score < float('inf'):
                model_scores['RNN'] = rnn_score
                self._log(f"   • RNN: Validation MSE={rnn_score:.6f}")
            else:
                self._log(f"   • RNN: non disponible")
            
            # 1h) SARIMAX avec exogène
            self._log("8️⃣  SARIMAX (with exogenous trend)...")
            sarimax_exog_score = self._fit_sarimax_exog()
            if sarimax_exog_score < float('inf'):
                model_scores['SARIMAX_EXOG'] = sarimax_exog_score
                self._log(f"   • SARIMAX_EXOG: AIC={sarimax_exog_score:.1f}")
            else:
                self._log(f"   • SARIMAX_EXOG: non disponible")
            
            # 1i) VAR (Vector Autoregression)
            self._log("9️⃣  VAR (Vector Autoregression)...")
            var_score = self._fit_var()
            if var_score < float('inf'):
                model_scores['VAR'] = var_score
                self._log(f"   • VAR: AIC={var_score:.1f}")
            else:
                self._log(f"   • VAR: non disponible")
            
            # 1j) VARMA (Vector ARMA)
            self._log("🔟 VARMA (Vector ARMA)...")
            varma_score = self._fit_varma()
            if varma_score < float('inf'):
                model_scores['VARMA'] = varma_score
                self._log(f"   • VARMA: AIC={varma_score:.1f}")
            else:
                self._log(f"   • VARMA: non disponible")
            
            # --- ÉTAPE 2 : CLASSEMENT & CHOIX ---
            self._log("\n🏆 ÉTAPE 3 : CLASSEMENT & CHOIX DU MEILLEUR MODÈLE")
            self._log("─" * 60)
            
            # Trier par score (ascending)
            sorted_models = sorted(model_scores.items(), key=lambda x: x[1] if x[1] < float('inf') else float('inf'))
            
            self._log("Classement (meilleur → pire):")
            for idx, (name, score) in enumerate(sorted_models, 1):
                if score < float('inf'):
                    if score > 100:
                        self._log(f"   {idx}. {name}: {score:.1f}")
                    else:
                        self._log(f"   {idx}. {name}: {score:.6f}")
                else:
                    self._log(f"   {idx}. {name}: N/A (non disponible)")
            
            # Choix final
            best_model_name, best_score = sorted_models[0] if sorted_models else ("SARIMAX_DEFAULT", float('inf'))
            self._log(f"\n🎯 MEILLEUR MODÈLE CHOISI : {best_model_name} (score={best_score:.1f})")
            
            # Set model_name, order, seasonal_order based on choice
            if 'SARIMA' in best_model_name:
                self.model_name = "SARIMA"
                self.order = (1, 0, 1)
                self.seasonal_order = (1, 1, 1, 12)
            elif 'ARIMA' in best_model_name:
                self.model_name = "ARIMA"
                self.order = (1, 1, 1)
                self.seasonal_order = (0, 0, 0, 0)
            elif 'AR(' in best_model_name:
                self.model_name = "AR"
                self.order = (1, 0, 0)
                self.seasonal_order = (0, 0, 0, 0)
            elif 'MA(' in best_model_name:
                self.model_name = "MA"
                self.order = (0, 0, 1)
                self.seasonal_order = (0, 0, 0, 0)
            elif 'ARMA' in best_model_name:
                self.model_name = "ARMA"
                self.order = (1, 0, 1)
                self.seasonal_order = (0, 0, 0, 0)
            elif 'HoltWinters' in best_model_name:
                self.model_name = "HoltWinters"
                self.order = (0, 0, 0)
                self.seasonal_order = (0, 0, 0, 0)
            elif 'Prophet' in best_model_name:
                self.model_name = "Prophet"
                self.order = (0, 0, 0)
                self.seasonal_order = (0, 0, 0, 0)
            elif 'LSTM' in best_model_name:
                self.model_name = "LSTM"
                self.order = (0, 0, 0)
                self.seasonal_order = (0, 0, 0, 0)
            elif 'CNN' in best_model_name:
                self.model_name = "CNN"
                self.order = (0, 0, 0)
                self.seasonal_order = (0, 0, 0, 0)
            
            self._log(f"\n✓ Configuration finale : model={self.model_name}, order={self.order}, seasonal={self.seasonal_order}")
            
        except Exception as e:
            self._log(f"❌ ERREUR lors de l'analyse : {str(e)}")
            # Fallback
            self.model_name = "SARIMAX"
            self.order = (1, 0, 1)
            self.seasonal_order = (1, 1, 1, 12)
            raise

    def get_prediction_data(self, months=None):
        """
        ← CHANGEMENT 4 : Entraîne le modèle et retourne les prévisions en DICTIONNAIRE.
        Intègre également la validation intelligente de la durée (Smart Duration).
        
        AVANT (autoPrediction.py) :
          plt.show()  ❌ Tente d'ouvrir une fenêtre graphique (impossible sur serveur)
        
        APRÈS (logic.py) :
          return {...}  ✓ Retourne des données brutes (JSON-ready)
          Le FRONTEND (site web) utilisera ces données pour dessiner le graphique
        
        Args:
            months (int, optional): Nombre de mois à prédire.
                - Si None : Mode AUTO (utilise calculate_and_validate_duration)
                - Si int : Mode UTILISATEUR (mais sera validé par Smart Duration)
        
        Returns:
            dict: Dictionnaire JSON contenant :
            
            ✓ SI SUCCÈS :
            {
                "status": "success",
                "model_info": {
                    "name": "SARIMA",
                    "order": "(1, 1, 1)",
                    "seasonal_order": "(1, 1, 1, 12)",
                    "aic": 150.5
                },
                "explanations": [
                    "Saisonnalité détectée",                    venv\\Scripts\\Activate.ps1
                    streamlit run dashboard.py
                    "Choix : SARIMA",
                    ...
                ],
                "history": {
                    "dates": ["2020-01-01", "2020-02-01", ...],
                    "values": [1000.0, 1500.5, 1200.0, ...]
                },
                "forecast": {
                    "dates": ["2024-01-01", "2024-02-01", ...],
                    "values": [1400.0, 1450.0, ...],  # Valeurs prédites
                    "confidence_upper": [1500.0, 1550.0, ...],  # Intervalle sup. (95%)
                    "confidence_lower": [1300.0, 1350.0, ...]   # Intervalle inf. (95%)
                },
                "timestamp": "2025-12-25T15:30:45.123456",
                "duration_info": {
                    "requested_months": 12,
                    "validated_months": 12,
                    "reason": "MODE AUTO"
                }
            }
            
            ✗ SI ERREUR :
            {
                "status": "error",
                "error_message": "Description détaillée de l'erreur",
                "explanations": [...]
            }
        
        WORKFLOW :
        ──────────
        1. Valider la durée (via calculate_and_validate_duration)
        2. Entraîner le modèle SARIMAX
        3. Générer prévisions + intervalles confiance
        4. Retourner dict JSON
        """
        # Valider et ajuster la durée (Smart Duration)
        # ─────────────────────────────────────────────
        validated_months = self.calculate_and_validate_duration(user_months=months)
        
        # Utiliser la raison calculée par calculate_and_validate_duration si disponible
        reason = getattr(self, '_last_duration_reason', None)
        if not reason:
            reason = "MODE AUTO" if months is None else f"USER OVERRIDE ({months} → {validated_months})"
        self._log(f"\n📌 Durée FINALE pour prédiction : {validated_months} mois ({reason})")
        
        self._log(f"\n=== GÉNÉRATION DE PRÉVISIONS ({self.model_name}, {validated_months} mois) ===")
        
        try:
            # Entraîner le modèle final
            self._log(f"Entraînement SARIMAX | order={self.order} | seasonal={self.seasonal_order}")

            # FALLBACK : si la série est constante (variance nulle), éviter SARIMAX et renvoyer une prévision naive
            if self.df['montant'].nunique() <= 1:
                last_value = float(self.df['montant'].iloc[-1])
                forecast_dates = [(self.df.index[-1] + pd.offsets.MonthBegin(i+1)).strftime('%Y-%m-%d') for i in range(validated_months)]
                return {
                    "status": "success",
                    "model_info": {
                        "name": "NAIVE_CONSTANT",
                        "order": str(self.order),
                        "seasonal_order": str(self.seasonal_order),
                        "aic": 0.0
                    },
                    "explanations": self.logs,
                    "history": {
                        "dates": [d.strftime('%Y-%m-%d') for d in self.df.index],
                        "values": self.df['montant'].tolist()
                    },
                    "forecast": {
                        "dates": forecast_dates,
                        "values": [last_value] * validated_months,
                        "confidence_upper": [last_value] * validated_months,
                        "confidence_lower": [last_value] * validated_months
                    },
                    "timestamp": datetime.now().isoformat(),
                    "duration_info": {
                        "requested_months": months,  # None si MODE AUTO
                        "validated_months": validated_months,
                        "reason": reason
                    }
                }

            model = SARIMAX(
                self.df['montant'],
                order=self.order,
                seasonal_order=self.seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            # Supprimer les ConvergenceWarning lors du fit (capturés et transformés en logs)
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=ConvergenceWarning)
                results = model.fit(disp=False)
            self._log(f"✓ Modèle entraîné (AIC={results.aic:.2f})")
            
            # Générer prévisions avec intervalles de confiance
            forecast = results.get_forecast(steps=validated_months)
            pred = forecast.predicted_mean
            conf = forecast.conf_int()  # Intervalles 95% par défaut
            
            # ← KILLER FEATURE 1 : Détection d'anomalies (AI for Audit)
            # Utilise les résidus du modèle pour détecter les écarts anormaux
            anomalies = self._detect_anomalies(results)
            
            # Préparer le dictionnaire retour (JSON-ready)
            return {
                "status": "success",
                "model_info": {
                    "name": self.model_name,
                    "order": str(self.order),
                    "seasonal_order": str(self.seasonal_order),
                    "aic": float(results.aic)
                },
                "explanations": self.logs,
                "history": {
                    "dates": [d.strftime('%Y-%m-%d') for d in self.df.index],
                    "values": self.df['montant'].tolist()
                },
                "forecast": {
                    "dates": [d.strftime('%Y-%m-%d') for d in pred.index],
                    "values": pred.tolist(),
                    "confidence_upper": conf.iloc[:, 1].tolist(),
                    "confidence_lower": conf.iloc[:, 0].tolist()
                },
                "anomalies": anomalies,
                "timestamp": datetime.now().isoformat(),
                "duration_info": {
                    "requested_months": months,  # None si MODE AUTO
                    "validated_months": validated_months,
                    "reason": reason
                }
            }
            
        except Exception as e:
            self._log(f"ERREUR lors de la prédiction : {str(e)}")
            # Même en cas d'erreur, retourner un dictionnaire (pas d'exception brute)
            return {
                "status": "error",
                "error_message": str(e),
                "explanations": self.logs
            }


    def _detect_anomalies(self, results):
        """
        ╔════════════════════════════════════════════════════════════════════════╗
        │ KILLER FEATURE 1 : Détection d'Anomalies (AI for Audit)                │
        │ Concept : Comparer l'historique réel avec ce qu'il AURAIT dû être      │
        ╚════════════════════════════════════════════════════════════════════════╝

        LOGIQUE :
        ────────
        La TGR est un organisme de contrôle. Leur plus grande peur : erreur/fraude.
        
        Au lieu de seulement prédire le FUTUR, on scanne le PASSÉ.
        
        Pour chaque mois historique :
          • Valeur réelle = montant enregistré
          • Valeur prédite = ce que le modèle aurait prédit (fitted values)
          • Écart (résidu) = réel - prédit
        
        Si l'écart sort du "tunnel de sécurité" (> 2σ ou 3σ), c'est SUSPECT.
        
        Exemple (données réelles TGR) :
          Janvier 2023 :
            Dépense réelle : 5 millions DH
            Dépense normale : 3 millions DH (selon modèle)
            Écart : 2 millions DH (2.5 écarts-types)
            → ANOMALIE DÉTECTÉE : "Dépense 67% anormale"

        TECHNO :
        ───────
        Utilise les résidus du modèle SARIMA (déjà entraîné).
        Résidus = erreurs du modèle = l'information "anormale".
        
        Seuils :
          • 1σ (68% confiance) : Normal dans variation
          • 2σ (95% confiance) : MOYEN (worth investigating)
          • 3σ (99.7% confiance) : ÉLEVÉ (definite anomaly)

        Args:
            results: Objet results du SARIMAX entraîné

        Returns:
            list: Liste d'anomalies détectées
            
            Format d'une anomalie :
            {
                "date": "2023-03-01",
                "actual_value": 5000000.0,
                "predicted_value": 3000000.0,
                "residual": 2000000.0,
                "std_deviations": 2.5,
                "severity": "HIGH",
                "description": "Dépense 67% supérieure à la normale - Investigation recommandée"
            }
        """
        try:
            self._log("\n" + "=" * 70)
            self._log("🔍 DÉTECTION D'ANOMALIES (AI for Audit)")
            self._log("=" * 70)

            anomalies = []

            # Obtenir les résidus et les valeurs ajustées du modèle
            residuals = results.resid
            fitted_values = results.fittedvalues

            # Calculer l'écart-type des résidus (mesure de variation "normale")
            std_residuals = residuals.std()
            mean_residuals = residuals.mean()

            self._log(f"📊 Statistiques des résidus :")
            self._log(f"   • Moyenne : {mean_residuals:.2f}")
            self._log(f"   • Écart-type : {std_residuals:.2f}")

            if std_residuals == 0:
                self._log("⚠️  Écart-type = 0. Pas d'anomalies détectables.")
                return anomalies

            # Définir les seuils de sévérité
            # seuil_bas = 2σ (95% confiance)
            # seuil_haut = 3σ (99.7% confiance)
            threshold_medium = 2 * std_residuals
            threshold_high = 3 * std_residuals

            anomaly_count = 0

            # Parcourir tous les mois historiques
            for date, actual in self.df['montant'].items():
                # Récupérer la valeur prédite (fitted value)
                # Note : fitted_values a le même index que self.df
                if date in fitted_values.index:
                    predicted = fitted_values[date]
                    residual = actual - predicted

                    # Calculer l'écart en nombre d'écarts-types
                    abs_residual_std = abs(residual) / std_residuals

                    # Classifier la sévérité
                    if abs_residual_std >= threshold_high / std_residuals:
                        severity = "HIGH"
                        emoji = "🔴"
                    elif abs_residual_std >= threshold_medium / std_residuals:
                        severity = "MEDIUM"
                        emoji = "🟡"
                    else:
                        severity = "LOW"
                        emoji = "🟢"

                    # Marquer comme anomalie si sévérité >= MEDIUM (> 2σ)
                    if abs_residual_std >= threshold_medium / std_residuals:
                        # Calculer un % de déviation lisible
                        pct_deviation = (abs(residual) / predicted * 100) if predicted != 0 else 0

                        description = (
                            f"{emoji} Dépense {pct_deviation:.0f}% "
                            f"{'supérieure' if residual > 0 else 'inférieure'} à la normale"
                        )

                        anomaly = {
                            "date": date.strftime('%Y-%m-%d'),
                            "actual_value": float(actual),
                            "predicted_value": float(predicted),
                            "residual": float(residual),
                            "std_deviations": float(abs_residual_std),
                            "severity": severity,
                            "description": description,
                        }
                        anomalies.append(anomaly)
                        anomaly_count += 1

                        self._log(f"  {emoji} {date.strftime('%B %Y')} : {description}")

            # Log résumé
            if anomaly_count == 0:
                self._log(f"\n✅ Aucune anomalie détectée (tous les résidus < 2σ)")
            else:
                self._log(f"\n⚠️  {anomaly_count} anomalie(s) détectée(s)")

            # Trier les anomalies par sévérité (HIGH en premier)
            severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
            anomalies.sort(key=lambda x: (severity_order.get(x["severity"], 3), x["std_deviations"]), reverse=True)

            return anomalies

        except Exception as e:
            self._log(f"❌ Erreur lors de la détection d'anomalies : {str(e)}")
            return []



def predict_from_file_content(file_content, months=None):
    """
    ╔════════════════════════════════════════════════════════════════════════╗
    │ FONCTION PRINCIPALE : Orchestre le pipeline complet                    │
    ╚════════════════════════════════════════════════════════════════════════╝
    
    Cette fonction est le POINT D'ENTRÉE de la logique de prédiction.
    Elle coordonne les 3 étapes pour transformer du contenu binaire en JSON.
    
    ← CHANGEMENT 2 : Paramètres function au lieu de input()
    ← CHANGEMENT : months est maintenant OPTIONNEL (None = MODE AUTO)
    
    AVANT (autoPrediction.py) :
      while True:
          file_path = input("Chemin du fichier ? ")
          months = input("Mois à prédire ? ")
          predict(file_path, months)
      
      ❌ Problèmes :
        • Bloque l'exécution (while True)
        • Demande l'input à l'utilisateur (pas adapté à une API)
        • Pas de gestion d'erreur structurée
    
    APRÈS (logic.py) :
      result = predict_from_file_content(file_content, months=None)
      
      ✓ Avantages :
        • Non-bloquant : fonction retourne immédiatement
        • Paramètres viennent de la requête HTTP (GET/POST)
        • Mode AUTO intelligent : durée calculée selon la densité des données
        • Gestion d'erreur centralisée
        • Retour structuré (dictionnaire JSON)
    
    PIPELINE COMPLET :
    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
    │ file_content │ --> │  DataCleaner │ --> │SmartPredictor│ --> │  Result  │
    │   (bytes)    │     │ (nettoyage)  │     │ (prédiction) │     │  (JSON)  │
    └──────────────┘     └──────────────┘     └──────────────┘     └──────────┘
         INPUT              ÉTAPE 1               ÉTAPE 2            OUTPUT
    
    Args:
        file_content (bytes): Contenu binaire du fichier CSV
            Exemple d'utilisation dans l'API :
            ```python
            from fastapi import UploadFile, Query
            from typing import Optional
            
            @app.post("/predict")
            async def predict(
                file: UploadFile,
                months: Optional[int] = Query(None, ge=1, le=60)
            ):
                file_bytes = await file.read()  # Lecture du fichier envoyé
                result = predict_from_file_content(file_bytes, months=months)
                return result  # Retour JSON automatique
            ```
        
        months (int, optional): Nombre de mois à prédire
            - Si None (défaut) : MODE AUTO
              • Système analyse densité des données
              • Calcule durée sûre automatiquement
              • Utilisateur n'a pas à se préoccuper de la durée
            
            - Si int (ex: 12, 24) : MODE UTILISATEUR
              • Utilisateur demande une durée spécifique
              • Système valide via Smart Duration
              • Peut être réduit si données insuffisantes
    
    Returns:
        dict: Résultat complet avec structure :
        
        ✓ SI SUCCÈS :
        {
            "status": "success",
            "model_info": {...},
            "explanations": [...],
            "history": {...},
            "forecast": {...},
            "timestamp": "2025-12-25T15:30:45.123456",
            "duration_info": {
                "requested_months": null (ou int),
                "validated_months": 12,
                "reason": "MODE AUTO" ou "USER OVERRIDE"
            }
        }
        
        ✗ SI ERREUR :
        {
            "status": "error",
            "error_message": "Description détaillée de l'erreur",
            "explanations": [...]
        }
    
    GESTION DES ERREURS :
      • Try/except englobant tout le pipeline
      • Les erreurs à chaque étape sont capturées
      • Un dictionnaire JSON est TOUJOURS retourné (jamais d'exception brute)
      • Utile pour le frontend : il peut afficher l'erreur à l'utilisateur
    
    Raises:
        Rien ! (toutes les exceptions sont capturées et retournées en JSON)
    """
    try:
        # Étape 1️⃣  : NETTOYAGE ET PRÉPARATION DES DONNÉES
        # ═════════════════════════════════════════════════════════════════════
        # Rôle : Transformer les bytes bruts en DataFrame propre (mensuel)
        # Sortie : DataFrame avec index=dates, colonne 'montant'=valeurs
        cleaner = DataCleaner(file_content)
        df_clean = cleaner.run()
        
        # Étape 2️⃣  : ANALYSE ET SÉLECTION DU MODÈLE
        # ═════════════════════════════════════════════════════════════════════
        # Rôle : Analyser la série et choisir le meilleur modèle
        # Sorties : model_name, order, seasonal_order + logs
        predictor = SmartPredictor(df_clean)
        predictor.analyze_and_configure()
        
        # Combiner les logs des deux étapes pour transparence maximale
        all_logs = cleaner.logs + predictor.logs
        
        # Étape 3️⃣  : GÉNÉRATION DE PRÉVISIONS
        # ═════════════════════════════════════════════════════════════════════
        # Rôle : Entraîner le modèle et générer les prévisions
        # Sortie : Dictionnaire avec historique + prévisions + intervalles
        result = predictor.get_prediction_data(months=months)
        
        # Ajouter tous les logs au résultat final
        result["explanations"] = all_logs
        
        return result
        
    except Exception as e:
        # ❌ ERREUR : Retourner une structure JSON d'erreur (pas d'exception levée)
        return {
            "status": "error",
            "error_message": str(e),
            "explanations": []
        }
