```markdown
# 🚀 DEPLOYMENT GUIDE - Déploiement production TGR API

## 📋 Table des matières

1. [Prérequis](#prérequis)
2. [Déploiement local avec Docker Compose](#déploiement-local-avec-docker-compose)
3. [Déploiement production](#déploiement-production)
4. [Monitoring et logs](#monitoring-et-logs)
5. [Backup et recovery](#backup-et-recovery)
6. [Troubleshooting](#troubleshooting)

---

## 🔧 Prérequis

### Environnement local
- Python 3.9+
- Docker + Docker Compose
- Git
- jq (pour parsing JSON)

### Environnement production
- Serveur Linux (Ubuntu 20.04+ recommandé)
- Docker + Docker Compose
- PostgreSQL 12+ (ou utiliser image Docker)
- Reverse proxy (Nginx recommandé)
- SSL/TLS certificate (Let's Encrypt)
- Git

---

## 🐳 Déploiement local avec Docker Compose

### Step 1: Cloner et préparer

```bash
git clone https://github.com/YOUR_ORG/tgr-api.git
cd tgr-api

# Copier et adapter la config
cp .env.example .env

# Adapter si nécessaire
nano .env  # ou vim, code, etc.
```

### Step 2: Démarrer les services

```bash
# Démarrer tous les services (API + PostgreSQL + PgAdmin)
docker-compose up -d

# Vérifier que tout est OK
docker-compose ps

# OUTPUT attendu:
# NAME          STATUS              PORTS
# tgr-api       Up (healthy)        0.0.0.0:8000->8000/tcp
# tgr-postgres  Up (healthy)        0.0.0.0:5432->5432/tcp
# tgr-pgadmin   Up                  0.0.0.0:5050->80/tcp
```

### Step 3: Initialiser la BD

```bash
# L'initialisation est automatique au premier démarrage
# Mais tester :
curl -X POST http://localhost:8000/api/db/init

# OUTPUT attendu:
# {"status": "success", "message": "✅ Base de données initialisée"}
```

### Step 4: Test rapide

```bash
# Health check
curl http://localhost:8000/health

# Créer utilisateur (clé API)
API_KEY=$(curl -s -X POST \
  "http://localhost:8000/api/db/users/register?organization=TestLocal" | jq -r '.api_key')
echo "Votre clé API : $API_KEY"

# Uploader et prédire
curl -X POST http://localhost:8000/predict \
  -H "X-API-Key: $API_KEY" \
  -F "file=@demo_sample.csv" | jq '.anomalies | length'
```

### Step 5: Accéder aux interfaces

```
API Swagger UI   : http://localhost:8000/docs
PostgreSQL Admin : http://localhost:5050
  - Email: admin@tgr.gov.ma
  - Password: admin

API Health       : http://localhost:8000/health
DB Init          : http://localhost:8000/api/db/init
```

### Step 6: Arrêter (quand fini)

```bash
docker-compose down
# Ou avec suppression volumes :
docker-compose down -v
```

---

## 🌍 Déploiement production

### Architecture recommandée

```
Internet
   │
   ↓
[nginx] ← SSL/TLS, reverse proxy, load balancing
   │
   ├─→ [tgr-api:8000]     ← Container 1
   ├─→ [tgr-api:8001]     ← Container 2 (optionnel)
   └─→ [tgr-api:8002]     ← Container 3 (optionnel)
           │
           ↓
      [PostgreSQL:5432]    ← Persévérant données
           │
           ↓
      [/var/lib/postgresql/data] ← Backup régulier
```

### Step 1: Préparation serveur

```bash
# Installer dépendances
sudo apt-get update
sudo apt-get install -y docker.io docker-compose nginx

# Ajouter utilisateur au groupe docker
sudo usermod -aG docker $USER
newgrp docker

# Créer répertoire app
mkdir -p /opt/tgr-api
cd /opt/tgr-api
```

### Step 2: Cloner le repo

```bash
# Si repo privé, utiliser SSH
git clone git@github.com:YOUR_ORG/tgr-api.git .

# Checkout release stable
git checkout v2.0.0
```

### Step 3: Configurer environnement production

```bash
# Copier .env.example et éditer
cp .env.example .env.production

# Setter des valeurs SÉCURISÉES :
nano .env.production

# 🔐 Valeurs critiques à changer :
TGR_API_KEY=<generate-strong-key>     # Générer : openssl rand -hex 32
DATABASE_URL=postgresql://tgr_user:STRONG_PASSWORD@postgres:5432/tgr_api
LOG_LEVEL=WARNING  # Pas DEBUG en production
```

### Step 4: Configurer Nginx (reverse proxy)

```nginx
# /etc/nginx/sites-available/tgr-api
server {
    listen 80;
    server_name api.tgr.gov.ma;

    # Redirection HTTP → HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.tgr.gov.ma;

    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/api.tgr.gov.ma/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.tgr.gov.ma/privkey.pem;

    # SSL config
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Timeouts
    proxy_connect_timeout 600s;
    proxy_send_timeout 600s;
    proxy_read_timeout 600s;

    # Reverse proxy vers API
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Activer :
```bash
sudo ln -s /etc/nginx/sites-available/tgr-api /etc/nginx/sites-enabled/
sudo nginx -t  # Test
sudo systemctl restart nginx
```

### Step 5: SSL avec Let's Encrypt

```bash
# Installer certbot
sudo apt-get install certbot python3-certbot-nginx

# Générer certificat
sudo certbot certonly --nginx -d api.tgr.gov.ma

# Auto-renewal (cron job)
sudo certbot renew --dry-run
```

### Step 6: Démarrer avec docker-compose

```bash
# Depuis /opt/tgr-api
docker-compose -f docker-compose.yml up -d

# Vérifier
docker-compose ps
docker-compose logs -f api
```

### Step 7: Activer systemd service (optionnel)

```ini
# /etc/systemd/system/tgr-api.service
[Unit]
Description=TGR API Service
After=network.target

[Service]
Type=simple
User=docker
WorkingDirectory=/opt/tgr-api
ExecStart=/usr/bin/docker-compose up
ExecStop=/usr/bin/docker-compose down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Activation :
```bash
sudo systemctl daemon-reload
sudo systemctl enable tgr-api
sudo systemctl start tgr-api
```

---

## 📊 Monitoring et logs

### Vérifier santé

```bash
# Health check
curl https://api.tgr.gov.ma/health

# Vérifier DB
curl https://api.tgr.gov.ma/api/db/init

# Logs API
docker-compose logs -f api --tail=100

# Logs PostgreSQL
docker-compose logs -f postgres --tail=50
```

### Metrics

```bash
# CPU/Memory usage
docker stats tgr-api tgr-postgres

# Database size
docker-compose exec postgres psql -U tgr_user -d tgr_api \
  -c "SELECT pg_size_pretty(pg_database_size('tgr_api'));"

# API latency
time curl https://api.tgr.gov.ma/health
```

### Alerting (optionnel)

```bash
# Simple check every 5 minutes
*/5 * * * * curl -f https://api.tgr.gov.ma/health || \
  echo "API DOWN" | mail -s "Alert: TGR API" admin@tgr.gov.ma
```

---

## 💾 Backup et recovery

### Backup régulier

```bash
#!/bin/bash
# backup.sh - À lancer quotidiennement

BACKUP_DIR=/backups/tgr-api
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 1. Backup BD PostgreSQL
docker-compose exec -T postgres pg_dump -U tgr_user tgr_api | \
  gzip > $BACKUP_DIR/tgr_api_$DATE.sql.gz

# 2. Backup volume données
tar -czf $BACKUP_DIR/api_data_$DATE.tar.gz ./logs/

# 3. Nettoyer vieux backups (>30j)
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "✅ Backup completed: $DATE"
```

Ajouter au crontab :
```bash
0 2 * * * /opt/tgr-api/backup.sh >> /var/log/tgr-backup.log 2>&1
```

### Restore depuis backup

```bash
# 1. Arrêter l'API
docker-compose down

# 2. Restaurer BD
gunzip < backups/tgr_api_20240101_120000.sql.gz | \
  docker-compose exec -T postgres psql -U tgr_user tgr_api

# 3. Redémarrer
docker-compose up -d
```

---

## 🆘 Troubleshooting

### API ne démarre pas

```bash
# Vérifier logs
docker-compose logs api

# Vérifier port libre
sudo lsof -i :8000

# Vérifier BD connection
docker-compose logs postgres
```

### BD ne démarre pas

```bash
# Vérifier volume mounted
docker volume ls | grep tgr

# Si corrompue, recréer :
docker-compose down -v
docker-compose up -d

# ⚠️ Cela supprime les données !
```

### Out of memory

```bash
# Voir utilisation
docker stats

# Limiter resources (docker-compose.yml)
services:
  api:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: 1.0
```

### SSL certificate expiration

```bash
# Renouveler (Let's Encrypt auto en général)
sudo certbot renew

# Vérifier expiration
echo | openssl s_client -servername api.tgr.gov.ma -connect api.tgr.gov.ma:443 2>/dev/null | openssl x509 -noout -dates
```

---

## ✅ Production Checklist

- [ ] SSL/TLS configuré
- [ ] Nginx reverse proxy OK
- [ ] PostgreSQL persistent avec backup
- [ ] Monitoring actif
- [ ] Logs centralisés
- [ ] Firewall OK (SSH, HTTP, HTTPS seulement)
- [ ] Auto-renewal certificat
- [ ] Backup schedule défini
- [ ] Disaster recovery plan
- [ ] Équipe alertée de l'endpoint

---

## 🎊 Vous êtes prêt pour production !

Questions ? Consulter :
- API Docs : https://api.tgr.gov.ma/docs
- Guide complet : KILLER_FEATURES_GUIDE.md
- Logs : docker-compose logs -f

Bonne chance ! 🚀
```
