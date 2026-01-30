@echo off
REM Wrapper pour docker-compose utilisant docker\docker-compose.yml
echo Lancement de docker-compose (fichier: docker\docker-compose.yml)
docker-compose -f "%~dp0docker\docker-compose.yml" %*
