"""


comments

"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import statements


# COnfigure le logging pour data dog

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    # Ce format est structuré pour être parsé par Datadog :
    # - asctime : quand ça s'est passé
    # - name : quel module (app.services.extractor)
    # - levelname : INFO, WARNING, ERROR, CRITICAL
    # - message : le message en texte
)
logger = logging.getLogger(__name__)

settings = get_settings()

print(f"MODEL ID UTILISÉ : {settings.BEDROCK_MODEL_ID}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gère le cycle de vie de l'application (startup / shutdown).
    
    Le code AVANT yield s'exécute au démarrage.
    Le code APRÈS yield s'exécute à l'arrêt.
    
    C'est ici qu'on initialise les connexions DB, les caches, etc.
    Et qu'on les ferme proprement à l'arrêt.
    """
    # === STARTUP ===
    logger.info(f" {settings.APP_NAME} v{settings.APP_VERSION} démarrage...")
    logger.info(f"   Région AWS : {settings.AWS_REGION}")
    logger.info(f"   Modèle Bedrock : {settings.BEDROCK_MODEL_ID}")
    logger.info(f"   Environnement Datadog : {settings.DD_ENV}")
    
    yield  # L'application tourne ici
    
    # === SHUTDOWN ===
    logger.info(f"👋 {settings.APP_NAME} arrêt propre.")


# Crée l'instance FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API d'extraction et classification de relevés bancaires",
    lifespan=lifespan,
    docs_url="/docs",       # Swagger UI : http://localhost:8000/docs
    redoc_url="/redoc",     # ReDoc : http://localhost:8000/redoc
    openapi_url="/openapi.json"  # Schéma OpenAPI (machine-readable)
)

# === MIDDLEWARE CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # Origines autorisées
    allow_credentials=True,                # Autorise les cookies
    allow_methods=["GET", "POST"],         # Méthodes HTTP autorisées
    allow_headers=["*"],                   # Headers autorisés
    # En production bancaire, on restreint aussi les headers
    # et on ajoute des headers de sécurité supplémentaires
)


# === ROUTES ===
app.include_router(statements.router)


# === HEALTH CHECKS ===
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check — utilisé par Kubernetes et les load balancers.
    
    Kubernetes utilise deux types de probes :
    - readinessProbe : vérifie que le pod est PRÊT à recevoir du trafic
      → Si échoue, K8s retire le pod du Service (plus de trafic envoyé)
    - livenessProbe : vérifie que le pod est VIVANT
      → Si échoue, K8s KILL et redémarre le pod
    
    Ce endpoint simple retourne 200 OK si l'app tourne.
    En production, on pourrait aussi vérifier :
    - La connexion à la base de données
    - La disponibilité de Bedrock
    - L'espace disque
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "service": settings.APP_NAME
    }


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness check — le pod est-il PRÊT ?
    Plus détaillé que le health check : vérifie les dépendances.
    """
    # TODO: ajouter la vérification DB et Bedrock
    return {"status": "ready"}