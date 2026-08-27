"""

Comments


"""

from pydantic import BaseModel, Field
# `date` est importé sous un alias : le modèle Transaction a un champ nommé
# `date`, qui masquerait le type et casserait la résolution de l'annotation.
from datetime import date as DateType
from enum import Enum

class TransactionCategory(str, Enum):
    """
    Catégories de transactions — l'AI classifiera chaque transaction dans une de ces catégories.
    
    str, Enum : hérite de str ET Enum, ce qui permet de l'utiliser
    comme string dans le JSON tout en ayant l'autocomplétion dans l'IDE.
    """
    FIXED_CHARGE = "fixed_charge"          # Loyer, assurance, abonnements
    VARIABLE_EXPENSE = "variable_expense"  # Épicerie, restaurants, shopping
    INCOME = "income"                      # Salaire, remboursements
    TRANSFER = "transfer"                  # Virements entre comptes
    DEBT_PAYMENT = "debt_payment"          # Paiements de carte de crédit, prêts
    OTHER = "other"                        # Non classifiable


class Transaction(BaseModel):
    """
    Représente UNE transaction extraite du relevé bancaire.
    
    Field() permet de :
    - Ajouter des métadonnées pour la documentation
    - Définir des contraintes de validation
    - Fournir des exemples pour la doc Swagger
    """
    date: DateType = Field(..., description="Date de la transaction", examples=["2026-08-15"])
    description: str = Field(..., description="Description de la transaction", examples=["METRO EPICERIE"])
    amount: float = Field(..., description="Montant (négatif = dépense, positif = revenu)", examples=[-45.67])
    category: TransactionCategory = Field(
        default=TransactionCategory.OTHER,
        description="Catégorie classifiée par l'AI"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,  # ge = greater than or equal (≥ 0)
        le=1.0,  # le = less than or equal (≤ 1)
        description="Score de confiance de la classification (0.0 à 1.0)"
    )


class StatementUploadResponse(BaseModel):
    """Réponse après l'upload et l'analyse d'un relevé bancaire."""
    statement_id: str = Field(..., description="Identifiant unique du relevé")
    filename: str
    total_transactions: int
    transactions: list[Transaction]
    summary: "StatementSummary"


class StatementSummary(BaseModel):
    """Résumé financier calculé à partir des transactions extraites."""
    total_income: float = Field(..., description="Total des revenus")
    total_expenses: float = Field(..., description="Total des dépenses")
    net_balance: float = Field(..., description="Balance nette (revenus - dépenses)")
    fixed_charges_total: float = Field(..., description="Total des charges fixes")
    variable_expenses_total: float = Field(..., description="Total des dépenses variables")
    top_categories: dict[str, float] = Field(
        ...,
        description="Montant total par catégorie",
        examples=[{"fixed_charge": -1500.00, "variable_expense": -800.00}],
    )
    period_start: DateType | None = None
    period_end: DateType | None = None


# Nécessaire pour la forward reference "StatementSummary" dans StatementUploadResponse
StatementUploadResponse.model_rebuild()


class HealthResponse(BaseModel):
    """Réponse du endpoint de health check — utilisé par Kubernetes pour
    savoir si le pod est vivant et prêt à recevoir du trafic."""
    status: str = "healthy"
    version: str
    service: str