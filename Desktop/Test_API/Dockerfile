FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de configuration et le code
COPY pyproject.toml requirements.txt ./
COPY . .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Exposer les ports de l'API et de l'UI Streamlit
EXPOSE 8000
EXPOSE 8501

# Commande de lancement par défaut (API)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

