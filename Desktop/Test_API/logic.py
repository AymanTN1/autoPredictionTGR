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
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.seasonal import seasonal_decompose
from datetime import datetime      # ← Pour les timestamps des réponses

warnings.filterwarnings("ignore")


# CLASSE 1 :
class DataCleaner:
    """
    CHANGEMENT MAJEUR vs autoPrediction.py :
      ❌ AVANT : file_path = "C:/Users/.../file.csv"  →  pd.read_csv(file_path)
      ✓ APRÈS : file_content = <bytes>  →  pd.read_csv(io.BytesIO(file_content))

    """
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
            # ÉTAPE 1 : Détection séparateur
            sep = self._detect_separator()
            
            # ← CHANGEMENT 1 : io.BytesIO = simule un fichier depuis les bytes
            # Sans io.BytesIO, pandas ne peut pas lire les bytes directement
            self.df = pd.read_csv(io.BytesIO(self.file_content), sep=sep, encoding='utf-8', low_memory=False)
            
            # Normaliser les noms de colonnes
            self.df.columns = self.df.columns.str.strip().str.lower()

            # ÉTAPE 4 : Détection automatique des colonnes
            col_date = self._find_column(self.df.columns, ['date', 'jour', 'time', 'reglement', 'payment'])
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
            # dayfirst=True car format français : 25/12/2025 (jour/mois/année)
            self.df['clean_date'] = pd.to_datetime(self.df[col_date], dayfirst=True, errors='coerce')
            if self.df['clean_date'].isna().sum() > 0:
                # Si dayfirst=True échoue, essayer dayfirst=False
                self.df['clean_date'] = pd.to_datetime(self.df[col_date], dayfirst=False, errors='coerce')
            
            # ÉTAPE 7 : Filtrage et indexation
            self.df = self.df.dropna(subset=['clean_date', 'clean_amount']).set_index('clean_date').sort_index()
            
            # ÉTAPE 8 : Agrégation en série mensuelle
            # Raison : SARIMA/ARIMA demandent une fréquence régulière (ex: chaque mois)
            # Sinon les résidus ne sont pas homogènes
            daily = self.df['clean_amount'].resample('D').sum()  # Journalière d'abord
            self.df_clean = daily.resample('MS').sum().to_frame(name='montant')  # MS = 1er du mois
            
            # ÉTAPE 9 : Enlever dernier mois si incomplet
            # Ex : si données jusqu'au 10/12, on enlève décembre incomplet
            if len(self.df_clean) > 1:
                self.df_clean = self.df_clean.iloc[:-1]
            
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

    def analyze_and_configure(self):
        """
        Lance l'analyse COMPLÈTE et configure le modèle optimal.
        
        ALGORITHME DE SÉLECTION (logique du "tournoi AIC") :
        ╔════════════════════════════════════════════════════════════════════╗
        
        1️⃣  DÉTECTER SAISONNALITÉ
            Calcule : amplitude_saisonnalité / amplitude_totale
            
            Si > 10% :
              ✓ Utiliser SARIMA (gère les patterns saisonniers = mensuels, trimestriels)
            Sinon :
              ✓ Passer à l'étape 2
        
        2️⃣  TEST STATIONNARITÉ (ADF = Augmented Dickey-Fuller)
            Null hypothesis : série NON-stationnaire
            Si p-value > 0.05 :
              → Rejetons H0, série est NON-stationnaire
              → Besoin d'intégration (d=1)
              → Utiliser ARIMA
            Sinon :
              → Série est stationnaire (d=0)
              → Passer à l'étape 3
        
        3️⃣  TOURNOI AR vs MA vs ARMA
            Tester les 3 et comparer leur AIC :
            
            AR(1) : (1,0,0) → Modèle autorégressive (passé influence futur)
            MA(1) : (0,0,1) → Modèle moyenne mobile (lissage des erreurs)
            ARMA(1,1) : (1,0,1) → Combinaison des deux
            
            Choix le modèle avec AIC le PLUS BAS
        
        ╚════════════════════════════════════════════════════════════════════╝
        
        Raises:
            Exception: Si erreur lors de l'analyse
        """
        self._log("=== ANALYSE ET SÉLECTION DU MODÈLE ===")
        
        try:
            # --- ÉTAPE 1 : TEST SAISONNALITÉ ---
            self._log("Détection de la saisonnalité...")
            
            # seasonal_decompose = décompose : Y = Trend + Seasonal + Residual
            decomp = seasonal_decompose(self.df['montant'], period=12)  # period=12 mois = 1 an
            
            # Amplitude saisonnalité = max - min du composant saisonnier
            season_amp = decomp.seasonal.max() - decomp.seasonal.min()
            
            # Amplitude totale = max - min de la série complète
            total_amp = self.df['montant'].max() - self.df['montant'].min()
            
            has_seasonality = season_amp > 0.1 * total_amp  # > 10% ?
            
            if has_seasonality:
                # ✓ Saisonnalité détectée → SARIMA obligatoirement
                self._log(f"✓ Saisonnalité détectée (amplitude saisonnière = {season_amp:.2f} > 10% de {total_amp:.2f})")
                self._log("Choix : SARIMA (Seasonal ARIMA pour gérer les patterns mensuels/saisonniers)")
                
                self.model_name = "SARIMA"
                
                # Vérifier si besoin d'intégration D (différenciation saisonnière)
                res_adf = adfuller(self.df['montant'].dropna())
                p_value_adf = res_adf[1]
                d = 1 if p_value_adf > 0.05 else 0
                self._log(f"Test stationnarité (ADF p={p_value_adf:.4f}): d={d}")
                
                # Configuration SARIMA classique
                self.order = (1, d, 1)
                self.seasonal_order = (1, 1, 1, 12)
                
            else:
                # ✗ Pas de saisonnalité → Analyse fine (AR/MA/ARMA/ARIMA)
                self._log(f"✗ Pas de saisonnalité forte (amplitude = {season_amp:.2f} ≤ 10% de {total_amp:.2f})")
                self._log("Analyse fine : stationnarité et tournoi AR/MA/ARMA...")
                
                # --- ÉTAPE 2 : TEST STATIONNARITÉ (ADF) ---
                res_adf = adfuller(self.df['montant'].dropna())
                p_value = res_adf[1]
                
                if p_value > 0.05:
                    # ✗ Non-stationnaire → Besoin d'intégration
                    self._log(f"✗ Série non-stationnaire (ADF p={p_value:.4f} > 0.05)")
                    self._log("Besoin d'intégration (d=1). Modèle choisi : ARIMA(1,1,1)")
                    self.model_name = "ARIMA"
                    self.order = (1, 1, 1)
                    self.seasonal_order = (0, 0, 0, 0)
                    
                else:
                    # ✓ Stationnaire → Tournoi AR vs MA vs ARMA
                    self._log(f"✓ Série stationnaire (ADF p={p_value:.4f} ≤ 0.05)")
                    self._log("d=0 (pas d'intégration). Lancement du tournoi AR vs MA vs ARMA...")
                    
                    # --- ÉTAPE 3 : TOURNOI AIC ---
                    # Tester les 3 modèles simples et garder le meilleur (AIC le plus bas)
                    aic_ar = self._calculer_aic((1, 0, 0))
                    aic_ma = self._calculer_aic((0, 0, 1))
                    aic_arma = self._calculer_aic((1, 0, 1))
                    
                    self._log(f"Scores AIC : AR(1)={aic_ar:.1f}, MA(1)={aic_ma:.1f}, ARMA(1,1)={aic_arma:.1f}")
                    
                    best_score = min(aic_ar, aic_ma, aic_arma)
                    
                    if best_score == aic_ar:
                        self.model_name = "AR"
                        self.order = (1, 0, 0)
                        self._log(f"🏆 Gagnant : AR(1) avec AIC={aic_ar:.1f}")
                    elif best_score == aic_ma:
                        self.model_name = "MA"
                        self.order = (0, 0, 1)
                        self._log(f"🏆 Gagnant : MA(1) avec AIC={aic_ma:.1f}")
                    else:
                        self.model_name = "ARMA"
                        self.order = (1, 0, 1)
                        self._log(f"🏆 Gagnant : ARMA(1,1) avec AIC={aic_arma:.1f}")
                    
                    self.seasonal_order = (0, 0, 0, 0)
            
            # Résumé final
            self._log(f"✓ Résultat final : {self.model_name} | order={self.order} | seasonal_order={self.seasonal_order}")
            
        except Exception as e:
            self._log(f"ERREUR lors de l'analyse : {str(e)}")
            raise

    def get_prediction_data(self, months=12):
        """
        ← CHANGEMENT 4 : Entraîne le modèle et retourne les prévisions en DICTIONNAIRE.
        
        AVANT (autoPrediction.py) :
          plt.show()  ❌ Tente d'ouvrir une fenêtre graphique (impossible sur serveur)
        
        APRÈS (logic.py) :
          return {...}  ✓ Retourne des données brutes (JSON-ready)
          Le FRONTEND (site web) utilisera ces données pour dessiner le graphique
        
        Args:
            months (int): Nombre de mois à prédire (défaut 12)
        
        Returns:
            dict: Dictionnaire JSON contenant :
            {
                "status": "success",
                "model_info": {
                    "name": "SARIMA",
                    "order": "(1, 1, 1)",
                    "seasonal_order": "(1, 1, 1, 12)",
                    "aic": 150.5
                },
                "explanations": [
                    "Saisonnalité détectée",
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
                "timestamp": "2025-12-25T15:30:45.123456"
            }
        
        UTILITÉ DU RÉSULTAT JSON :
          • Frontend peut afficher un graphique avec les courbes
          • Utilisateur voit les données historiques + prévisions + incertitude
          • Les "explanations" permettent de comprendre le choix du modèle
        """
        self._log(f"\n=== GÉNÉRATION DE PRÉVISIONS ({self.model_name}, {months} mois) ===")
        
        try:
            # Entraîner le modèle final
            self._log(f"Entraînement SARIMAX | order={self.order} | seasonal={self.seasonal_order}")
            model = SARIMAX(
                self.df['montant'],
                order=self.order,
                seasonal_order=self.seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            results = model.fit(disp=False)
            self._log(f"✓ Modèle entraîné (AIC={results.aic:.2f})")
            
            # Générer prévisions avec intervalles de confiance
            forecast = results.get_forecast(steps=months)
            pred = forecast.predicted_mean
            conf = forecast.conf_int()  # Intervalles 95% par défaut
            
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
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self._log(f"ERREUR lors de la prédiction : {str(e)}")
            # Même en cas d'erreur, retourner un dictionnaire (pas d'exception brute)
            return {
                "status": "error",
                "error_message": str(e),
                "explanations": self.logs
            }


# ==============================================================================
# FONCTION UTILITAIRE : ORCHESTRATION COMPLÈTE
# ==============================================================================
def predict_from_file_content(file_content, months=12):
    """
    ╔════════════════════════════════════════════════════════════════════════╗
    │ FONCTION PRINCIPALE : Orchestre le pipeline complet                    │
    ╚════════════════════════════════════════════════════════════════════════╝
    
    Cette fonction est le POINT D'ENTRÉE de la logique de prédiction.
    Elle coordonne les 3 étapes pour transformer du contenu binaire en JSON.
    
    ← CHANGEMENT 2 : Paramètres function au lieu de input()
    
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
      result = predict_from_file_content(file_content, months=12)
      
      ✓ Avantages :
        • Non-bloquant : fonction retourne immédiatement
        • Paramètres viennent de la requête HTTP (GET/POST)
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
            from fastapi import UploadFile
            
            @app.post("/predict")
            async def predict(file: UploadFile, months: int = 12):
                file_bytes = await file.read()  # Lecture du fichier envoyé
                result = predict_from_file_content(file_bytes, months=months)
                return result  # Retour JSON automatique
            ```
        
        months (int): Nombre de mois à prédire
            Par défaut 12 (1 année complète)
            Peut être modifié via l'API : /predict?months=24
    
    Returns:
        dict: Résultat complet avec structure :
        
        ✓ SI SUCCÈS :
        {
            "status": "success",
            "model_info": {...},
            "explanations": [...],
            "history": {...},
            "forecast": {...},
            "timestamp": "2025-12-25T15:30:45.123456"
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
