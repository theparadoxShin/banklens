"""





"""


import json
import logging
from io import BytesIO
from datetime import date


from pypdf import PdfReader
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser


from app.core.config import get_settings
from app.models.schemas import Transaction, TransactionCategory, StatementSummary

# logging configuration for prof debugging
# Data dog collecting
logger = logging.getLogger(__name__)

class BankStatementExtractor:
    """
    Classe responsable de l'extraction et classification des transactions.
    
    DESIGN PATTERN : Service Layer
    - Sépare la logique métier (extraction, classification) des routes HTTP
    - Testable indépendamment (tu peux tester le service sans FastAPI)
    - Réutilisable (le même service peut être appelé depuis un CLI, un worker, etc.)
    """
    
    def __init__(self):
        """
        Initialise la connexion à Claude via Bedrock.
        
        ChatBedrock : la classe LangChain pour les modèles chat sur Bedrock.
        - model_id : identifiant du modèle sur Bedrock
        - region_name : la région AWS (ca-central-1 pour le Canada)
        - model_kwargs : paramètres du modèle :
          → max_tokens : nombre max de tokens en sortie
          → temperature : 0 = déterministe (toujours la même réponse)
            C'est ce qu'on veut pour l'extraction de données financières.
            Pas de créativité, juste de la précision.
        """
        settings = get_settings()
        
        self.llm = ChatBedrock(
            model_id=settings.BEDROCK_MODEL_ID,
            region_name=settings.AWS_REGION,
            model_kwargs={
                "max_tokens": 4096,
                "temperature": 0,  # 0 = pas de random, extraction précise
            }
        )
        
        # Output parser qui force Claude à retourner du JSON valide
        self.json_parser = JsonOutputParser()
        
        # Le prompt template — le coeur de l'ingénierie de prompt
        self.extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """Tu es un expert en analyse de relevés bancaires canadiens.
Tu extrais les transactions d'un relevé bancaire et tu les classifies.

RÈGLES STRICTES :
1. Extrais CHAQUE transaction visible dans le relevé
2. Les montants négatifs sont des DÉPENSES, positifs sont des REVENUS
3. Classifie chaque transaction dans UNE catégorie :
   - "fixed_charge" : loyer, hypothèque, assurances, abonnements récurrents
   - "variable_expense" : épicerie, restaurants, essence, shopping
   - "income" : salaire, virement entrant, remboursement
   - "transfer" : virement entre comptes propres
   - "debt_payment" : paiement carte de crédit, prêt, ligne de crédit
   - "other" : tout ce qui ne correspond pas
4. Attribue un score de confiance entre 0.0 et 1.0 à chaque classification
5. Les dates doivent être au format YYYY-MM-DD

RETOURNE UNIQUEMENT du JSON valide, sans texte avant ou après.
Format attendu :
{{
  "transactions": [
    {{
      "date": "2026-08-15",
      "description": "METRO EPICERIE #1234",
      "amount": -67.89,
      "category": "variable_expense",
      "confidence": 0.95
    }}
  ]
}}"""),
            ("human", "Voici le texte extrait du relevé bancaire :\n\n{statement_text}")
        ])
    
    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """
        Extrait le texte brut d'un fichier PDF.
        
        BytesIO : transforme les bytes du fichier uploadé en un objet "fichier"
        que PdfReader peut lire (comme s'il ouvrait un fichier sur le disque).
        
        On concatène le texte de chaque page avec un séparateur de page
        pour que Claude puisse identifier les pages si nécessaire.
        """
        logger.info("Extraction du texte PDF en cours...")
        
        reader = PdfReader(BytesIO(pdf_content))
        
        text_parts = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:  # Certaines pages peuvent être des images (pas de texte)
                text_parts.append(f"--- PAGE {i + 1} ---\n{page_text}")
        
        full_text = "\n\n".join(text_parts)
        logger.info(f"Texte extrait : {len(full_text)} caractères sur {len(reader.pages)} pages")
        
        return full_text
    
    async def extract_and_classify(self, pdf_content: bytes) -> tuple[list[Transaction], StatementSummary]:
        """
        Pipeline principal : PDF → texte → Claude → transactions classifiées.
        
        async : cette fonction est asynchrone car l'appel à Bedrock
        peut prendre quelques secondes. En attendant la réponse, FastAPI
        peut traiter d'autres requêtes (non-bloquant).
        
        LANGCHAIN CHAIN :
        prompt | llm | parser
        C'est la syntaxe "pipe" de LangChain (LCEL - LangChain Expression Language)
        Les données passent de gauche à droite :
        1. Le prompt formate le texte en message pour Claude
        2. Le LLM envoie le message à Bedrock et reçoit la réponse
        3. Le parser convertit la réponse texte en JSON Python
        """
        # Étape 1 : Extraire le texte du PDF
        statement_text = self.extract_text_from_pdf(pdf_content)
        
        if not statement_text.strip():
            raise ValueError("Le PDF ne contient pas de texte extractible. "
                           "C'est peut-être un scan — l'OCR n'est pas encore implémenté.")
        
        # Étape 2 : Construire et exécuter la chaîne LangChain
        logger.info("Envoi du relevé à Claude pour extraction...")
        
        chain = self.extraction_prompt | self.llm | self.json_parser
        # ↑ C'est l'équivalent de :
        # formatted_prompt = self.extraction_prompt.format(statement_text=statement_text)
        # response = self.llm.invoke(formatted_prompt)
        # parsed = self.json_parser.parse(response.content)
        # Mais en plus propre et composable.
        
        result = await chain.ainvoke({"statement_text": statement_text})
        # ainvoke = appel asynchrone (le "a" = async)
        
        # Étape 3 : Parser et valider les transactions avec Pydantic
        transactions = []
        for t in result.get("transactions", []):
            try:
                transaction = Transaction(
                    date=t["date"],
                    description=t["description"],
                    amount=float(t["amount"]),
                    category=TransactionCategory(t.get("category", "other")),
                    confidence=float(t.get("confidence", 0.5))
                )
                transactions.append(transaction)
            except (ValueError, KeyError) as e:
                # Si Claude retourne une transaction mal formatée, on la skip
                # plutôt que de crasher tout le pipeline
                logger.warning(f"Transaction ignorée (format invalide) : {t} — {e}")
        
        logger.info(f"Extraction terminée : {len(transactions)} transactions extraites")
        
        # Étape 4 : Calculer le résumé
        summary = self._compute_summary(transactions)
        
        return transactions, summary
    
    def _compute_summary(self, transactions: list[Transaction]) -> StatementSummary:
        """
        Calcule les statistiques financières à partir des transactions.
        
        NOTE : Ce calcul est DÉTERMINISTE (pas d'AI).
        Les données financières critiques doivent être calculées par du code,
        pas par un LLM qui pourrait halluciner un montant.
        C'est le même principe que sur ton projet AURA : le score de risque
        est calculé par un rule engine, pas par l'AI.
        """
        total_income = sum(t.amount for t in transactions if t.amount > 0)
        total_expenses = sum(t.amount for t in transactions if t.amount < 0)
        
        # Grouper par catégorie
        categories: dict[str, float] = {}
        for t in transactions:
            cat = t.category.value
            categories[cat] = categories.get(cat, 0) + t.amount
        
        # Charges fixes et variables
        fixed_total = categories.get("fixed_charge", 0)
        variable_total = categories.get("variable_expense", 0)
        
        # Période du relevé
        dates = [t.date for t in transactions]
        period_start = min(dates) if dates else None
        period_end = max(dates) if dates else None
        
        return StatementSummary(
            total_income=round(total_income, 2),
            total_expenses=round(total_expenses, 2),
            net_balance=round(total_income + total_expenses, 2),
            fixed_charges_total=round(fixed_total, 2),
            variable_expenses_total=round(variable_total, 2),
            top_categories={k: round(v, 2) for k, v in categories.items()},
            period_start=period_start,
            period_end=period_end
        )