# === ÉTAPE 1 : Image de base ===
# python:3.12-slim : une image Debian légère avec Python pré-installé
# "slim" = version minimale (~150MB au lieu de ~900MB pour l'image complète)
# On utilise slim pour réduire la taille de l'image → déploiement plus rapide
FROM python:3.12-slim AS base

# Définit le répertoire de travail DANS le container
# Toutes les commandes suivantes s'exécutent dans /app
WORKDIR /app

# Variables d'environnement Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
# PYTHONDONTWRITEBYTECODE=1 : pas de fichiers .pyc (inutiles dans un container)
# PYTHONUNBUFFERED=1 : les logs Python sortent immédiatement (pas mis en buffer)
#   → CRUCIAL pour voir les logs en temps réel dans Docker/K8s/Datadog

# === ÉTAPE 2 : Installation des dépendances ===
# On copie SEULEMENT requirements.txt d'abord, PAS tout le code
# POURQUOI ? Docker utilise un système de CACHE par couche (layer caching) :
# - Si requirements.txt n'a pas changé, Docker réutilise le cache
# - L'installation des packages (lente) n'est PAS refaite
# - Seul le code source (qui change souvent) est recopié
# → Builds beaucoup plus rapides en développement
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# --no-cache-dir : ne garde pas le cache pip (réduit la taille de l'image)

# === ÉTAPE 3 : Copie du code source ===
COPY app/ app/

# === ÉTAPE 4 : Sécurité — utilisateur non-root ===
# Par défaut, les containers tournent en root (admin).
# C'est une FAILLE DE SÉCURITÉ : si un attaquant exploite ton app,
# il a les permissions root dans le container.
# On crée un utilisateur dédié avec des permissions limitées.
RUN adduser --disabled-password --gecos "" appuser
USER appuser
# À partir d'ici, tout s'exécute en tant que "appuser", pas "root"

# === ÉTAPE 5 : Exposition du port ===
# EXPOSE ne publie PAS le port — c'est de la documentation
# Il dit "ce container écoute sur le port 8000"
# La publication réelle se fait avec -p 8000:8000 ou dans K8s
EXPOSE 8000

# === ÉTAPE 6 : Commande de démarrage ===
# CMD définit la commande exécutée quand le container démarre
# On utilise ddtrace-run pour instrumenter automatiquement l'app avec Datadog
# ddtrace-run intercepte les appels FastAPI, les requêtes DB, etc.
# et envoie les traces à l'agent Datadog
CMD ["ddtrace-run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# SANS Datadog, la commande serait simplement :
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
