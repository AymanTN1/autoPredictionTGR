"""
dashboard.py - Interface Streamlit "Wow" pour API Prédiction TGR

🎨 FONCTIONNALITÉS :
  📊 Tableau de bord professionnel avec historique + prédiction
  📈 Graphiques avec zones d'incertitude (confiance 95%)
  🔐 Connexion sécurisée par API Key
  📁 Upload de fichiers avec drag & drop
  ⚡ Affichage temps réel des résultats
  🎯 Détail Smart Duration (détection sparsity)

💻 USAGE :
  streamlit run dashboard.py --logger.level=error
"""

import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import io
import os
from dotenv import load_dotenv

# ═══════════════════════════════════════════════════════════════════════════
# ⚙️  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

load_dotenv()

API_URL = "http://localhost:8000"
API_KEY = os.getenv("TGR_API_KEY", "TGR-SECRET-KEY-12345")

# Configuration Streamlit
st.set_page_config(
    page_title="Prédiction Dépenses TGR",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS
st.markdown("""
<style>
    .metric-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 15px;
        border-radius: 5px;
        color: #155724;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 15px;
        border-radius: 5px;
        color: #856404;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        padding: 15px;
        border-radius: 5px;
        color: #721c24;
    }
    header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# 🏠 PAGE PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; color: white;'>
<h1>🚀 Système de Prédiction des Dépenses - TGR v2.0</h1>
<p>Interface intelligente pour prévoir les dépenses de l'État Tunisien</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# SIDEBAR : Paramètres
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.subheader("🔐 Authentification")
    api_key_input = st.text_input(
        "Clé API",
        value=API_KEY,
        type="password",
        help="Clé API pour accéder aux routes sécurisées"
    )
    
    st.subheader("📊 Mode Prédiction")
    prediction_mode = st.radio(
        "Mode de prédiction",
        ["AUTO (Intelligent)", "USER (Manuel)"],
        help="AUTO: système choisit durée optimale | USER: vous spécifiez"
    )
    
    months_param = None
    if prediction_mode == "USER (Manuel)":
        months_param = st.slider(
            "Durée de prédiction (mois)",
            min_value=1,
            max_value=60,
            value=12,
            step=1,
            help="Nombre de mois à prédire. Peut être réduit par Smart Duration pour sécurité."
        )
    
    st.subheader("📈 Affichage")
    show_raw_json = st.checkbox("Afficher JSON brut (DEBUG)", value=False)
    show_logs = st.checkbox("Afficher les logs de traitement", value=True)
    
    st.divider()
    st.info("💡 Astuce: Glissez-déposez un fichier CSV pour démarrer")

# ═══════════════════════════════════════════════════════════════════════════
# 📁 UPLOAD FICHIER
# ═══════════════════════════════════════════════════════════════════════════

st.subheader("📁 Charger vos données")

col1, col2 = st.columns(2)

with col1:
    st.write("**Formats acceptés:** CSV, XLS")
    uploaded_file = st.file_uploader(
        "Glissez-déposez ou cliquez pour sélectionner",
        type=["csv", "xls", "xlsx"],
        key="file_uploader"
    )

with col2:
    if uploaded_file:
        st.success(f"✅ Fichier chargé: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")

# ═══════════════════════════════════════════════════════════════════════════
# 🔄 TRAITEMENT & AFFICHAGE
# ═══════════════════════════════════════════════════════════════════════════

if uploaded_file:
    st.markdown("---")
    st.subheader("⚡ Traitement en cours...")
    
    try:
        # Préparer le fichier
        file_content = uploaded_file.read()
        files = {"file": (uploaded_file.name, file_content)}
        headers = {"X-API-Key": api_key_input}
        
        # Sélectionner endpoint
        if prediction_mode == "AUTO (Intelligent)":
            endpoint = f"{API_URL}/predict/auto"
            params = None
        else:
            endpoint = f"{API_URL}/predict"
            params = {"months": months_param}
        
        # Appel API
        with st.spinner("🔄 Appel API..."):
            response = requests.post(
                endpoint,
                files=files,
                params=params,
                headers=headers,
                timeout=60
            )
        
        # Gestion réponse
        if response.status_code == 200:
            st.markdown("---")
            st.subheader("✅ Résultats")
            
            data = response.json()
            
            # Afficher JSON brut si demandé
            if show_raw_json:
                with st.expander("📋 JSON Brut"):
                    st.json(data)
            
            # Smart Duration Info
            duration_info = data.get("duration_info", {})
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div class='metric-box'>
                    <div style='font-size: 0.8em; opacity: 0.8;'>DURÉE DEMANDÉE</div>
                    <div style='font-size: 2em;'>{duration_info.get('requested_months', 'AUTO')}</div>
                    <div style='font-size: 0.7em;'>mois</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class='metric-box'>
                    <div style='font-size: 0.8em; opacity: 0.8;'>DURÉE VALIDÉE</div>
                    <div style='font-size: 2em;'>{duration_info.get('validated_months')}</div>
                    <div style='font-size: 0.7em;'>mois (Smart Duration)</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class='metric-box'>
                    <div style='font-size: 0.8em; opacity: 0.8;'>MODE</div>
                    <div style='font-size: 1.5em;'>{prediction_mode.split('(')[1][:-1]}</div>
                    <div style='font-size: 0.7em;'>Prédiction</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Raison Smart Duration
            reason = duration_info.get('reason', '')
            if 'réduit' in reason.lower() or 'sparsity' in reason.lower():
                st.markdown(f"""
                <div class='warning-box'>
                    ⚠️ <strong>Smart Duration Info:</strong> {reason}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class='success-box'>
                    ✅ <strong>Smart Duration:</strong> {reason}
                </div>
                """, unsafe_allow_html=True)
            
            # Logs de traitement
            if show_logs and data.get("logs"):
                with st.expander("📝 Logs de traitement"):
                    for log in data.get("logs", []):
                        st.write(f"• {log}")
            
            st.markdown("---")
            st.subheader("📈 Visualisation")
            
            # Extraire données pour graphiques
            forecast = data.get("forecast", {})
            
            if forecast and forecast.get("dates") and forecast.get("values"):
                dates = pd.to_datetime(forecast["dates"])
                values = forecast["values"]
                upper = forecast.get("upper", [None] * len(values))
                lower = forecast.get("lower", [None] * len(values))
                
                # Créer graphique Plotly
                fig = go.Figure()
                
                # Historique (bleu)
                if data.get("historical"):
                    hist_dates = pd.to_datetime(data["historical"]["dates"])
                    hist_values = data["historical"]["values"]
                    fig.add_trace(go.Scatter(
                        x=hist_dates,
                        y=hist_values,
                        name="Historique",
                        mode="lines",
                        line=dict(color="rgb(31, 119, 180)", width=2),
                        fill="tozeroy",
                        fillcolor="rgba(31, 119, 180, 0.1)"
                    ))
                
                # Prédiction (orange)
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=values,
                    name="Prédiction",
                    mode="lines+markers",
                    line=dict(color="rgb(255, 127, 14)", width=3),
                    marker=dict(size=6)
                ))
                
                # Zones d'incertitude (gris)
                if upper[0] is not None:
                    fig.add_trace(go.Scatter(
                        x=dates.tolist() + dates[::-1].tolist(),
                        y=upper + lower[::-1],
                        fill='toself',
                        fillcolor='rgba(128, 128, 128, 0.2)',
                        line=dict(color='rgba(255,255,255,0)'),
                        name='Zone confiance (95%)'
                    ))
                
                fig.update_layout(
                    title="📊 Historique et Prédiction des Dépenses",
                    xaxis_title="Date",
                    yaxis_title="Montant (DT)",
                    hovermode='x unified',
                    height=500,
                    template="plotly_white"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Statistiques
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Dernière valeur historique",
                        f"{data.get('historical', {}).get('values', [0])[-1]:,.0f} DT"
                    )
                
                with col2:
                    st.metric(
                        "Moyenne prédiction",
                        f"{np.mean(values):,.0f} DT"
                    )
                
                with col3:
                    st.metric(
                        "Amplitude variation",
                        f"{max(values) - min(values):,.0f} DT"
                    )
            
            # Tableau détaillé
            st.markdown("---")
            st.subheader("📋 Détails de la prédiction")
            
            df_forecast = pd.DataFrame({
                'Date': dates,
                'Prédiction (DT)': [f"{v:,.2f}" for v in values],
                'Confiance Min': [f"{l:,.2f}" if l else "N/A" for l in lower],
                'Confiance Max': [f"{u:,.2f}" if u else "N/A" for u in upper]
            })
            
            st.dataframe(df_forecast, use_container_width=True)
            
            # Options téléchargement
            st.markdown("---")
            st.subheader("💾 Exporter les résultats")
            
            col1, col2 = st.columns(2)
            
            with col1:
                csv = df_forecast.to_csv(index=False, sep=';')
                st.download_button(
                    label="📥 Télécharger CSV",
                    data=csv,
                    file_name=f"prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                json_str = str(data).encode()
                st.download_button(
                    label="📥 Télécharger JSON",
                    data=json_str,
                    file_name=f"prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        elif response.status_code == 401:
            st.markdown("""
            <div class='error-box'>
                🔐 <strong>Erreur Authentification:</strong> Clé API invalide ou manquante
            </div>
            """, unsafe_allow_html=True)
        
        else:
            st.markdown(f"""
            <div class='error-box'>
                ❌ <strong>Erreur API:</strong> Status {response.status_code}
                <br/>Détail: {response.text[:200]}
            </div>
            """, unsafe_allow_html=True)
    
    except requests.exceptions.ConnectionError:
        st.markdown("""
        <div class='error-box'>
            🚨 <strong>Erreur Connexion:</strong> Impossible de joindre l'API
            <br/>Vérifiez que le serveur est démarré: <code>python -m uvicorn main:app --reload</code>
        </div>
        """, unsafe_allow_html=True)
    
    except Exception as e:
        st.markdown(f"""
        <div class='error-box'>
            ⚠️ <strong>Erreur:</strong> {str(e)}
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# 📚 FOOTER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("🎯 **Mode AUTO** : Smart Duration détecte automatiquement la durée optimale")

with col2:
    st.info("🔒 **Sécurisé** : Toutes les requêtes nécessitent une clé API valide")

with col3:
    st.info("📊 **Professionnel** : Logging détaillé et zones de confiance (95%)")

st.markdown("""
---
<div style='text-align: center; color: gray; margin-top: 30px;'>
  <p>TGR API v2.0 | Système de Prédiction des Dépenses | © 2026</p>
  <p>Powered by FastAPI + Loguru + Streamlit + Plotly</p>
</div>
""", unsafe_allow_html=True)
