"""

Comments


"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """
    Chaque attribut correspond à une variable d'environnement.
    Ex: APP_NAME → os.environ["APP_NAME"]
    
    Les valeurs par défaut sont utilisées si la variable n'existe pas.
    Les champs sans valeur par défaut sont OBLIGATOIRES.
    """
    
    # === Application ===
    APP_NAME: str = "BankLens"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False  # JAMAIS True en production
    
    # === Base de données ===
    # Format: postgresql+asyncpg://user:password@host:port/dbname
    DATABASE_URL: str = "postgresql+asyncpg://banklens:banklens_pwd@localhost:5432/banklens_db"
    
    # === AWS Bedrock (Claude) ===
    AWS_REGION: str = "ca-central-1"  # Canada — souveraineté des données
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-haiku-20240307-v1:0"
    # Haiku pour le dev (moins cher), Sonnet pour la prod (plus précis)
    
    # === Sécurité ===
    SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION"  # Pour signer les JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # === CORS ===
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    # CORS = Cross-Origin Resource Sharing
    # Le frontend (port 3000) et le backend (port 8000) sont sur des ports différents
    # Sans CORS, le navigateur bloque les requêtes du frontend vers le backend
    # On autorise UNIQUEMENT les origines connues (pas de "*" en production)
    
    # === Datadog ===
    DD_SERVICE: str = "banklens-api"
    DD_ENV: str = "development"
    DD_VERSION: str = "1.0.0"
    # Ces tags Datadog identifient ton service dans les dashboards :
    # - DD_SERVICE : nom du service (apparaît dans la service map)
    # - DD_ENV : environnement (dev, staging, prod) — filtre dans Datadog
    # - DD_VERSION : version du code — permet de comparer les perfs entre versions
    
    model_config = SettingsConfigDict(
        env_file=".env",       # Charge automatiquement le fichier .env
        case_sensitive=True,   # Les noms de variables sont sensibles à la casse
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Retourne une instance unique de Settings (singleton via cache).
    
    @lru_cache() : mémorise le résultat du premier appel.
    Les appels suivants retournent directement l'objet en cache.
    Sans ça, chaque requête HTTP créerait un nouvel objet Settings
    et relirait le fichier .env → gaspillage de ressources.
    """
    return Settings()