"""

configurations


"""


import uuid
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, status

from app.services.extractor import BankStatementExtractor
from app.models.schemas import StatementUploadResponse


# Traces/logs Configuration Data dog for Prod monitoring instrumentation 
logger = logging.getLogger(__name__)

# APIRouter : regroupe les routes par domaine fonctionnel
# prefix="/api/v1/statements" : toutes les routes commencent par ce chemin
# tags=["Statements"] : groupement dans la documentation Swagger
router = APIRouter(
    prefix="/api/v1/statements",
    tags=["Statements"]
)

# Instance du service d'extraction
# En production, on utiliserait l'injection de dépendances FastAPI (Depends)
extractor = BankStatementExtractor()


@router.post(
    "/upload",
    response_model=StatementUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload et analyse un relevé bancaire",
    description="Accepte un fichier PDF, extrait les transactions via Claude (Bedrock), "
                "classifie chaque dépense, et retourne un résumé financier."
)
async def upload_statement(
    file: UploadFile = File(
        ...,
        description="Fichier PDF du relevé bancaire",
        media_type="application/pdf"
    )
):
    """
    Endpoint principal : upload d'un relevé bancaire.
    
    UploadFile : type FastAPI pour les fichiers uploadés.
    - file.filename : nom original du fichier
    - file.content_type : type MIME (devrait être application/pdf)
    - file.read() : lit le contenu du fichier en bytes
    
    File(...) : le ... signifie "obligatoire" (pas de valeur par défaut)
    """
    
    # Validation du type de fichier
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seuls les fichiers PDF sont acceptés."
        )
    
    # Limite de taille (10 MB max — les relevés bancaires font rarement plus)
    content = await file.read()
    max_size = 10 * 1024 * 1024  # 10 MB en bytes
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Le fichier dépasse la taille maximale de 10 MB."
        )
    
    try:
        # Appel au service d'extraction
        transactions, summary = await extractor.extract_and_classify(content)
        
        # Génère un ID unique pour ce relevé
        statement_id = str(uuid.uuid4())
        
        return StatementUploadResponse(
            statement_id=statement_id,
            filename=file.filename,
            total_transactions=len(transactions),
            transactions=transactions,
            summary=summary
        )
    
    except ValueError as e:
        # Erreur métier (PDF vide, format non supporté)
        logger.warning(f"Erreur d'extraction : {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        # Erreur inattendue — on log le détail mais on ne l'expose PAS au client
        # (risque de fuite d'information : stack traces, chemins internes, etc.)
        logger.error(f"Erreur inattendue lors de l'extraction : {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur interne est survenue. Veuillez réessayer."
        )
