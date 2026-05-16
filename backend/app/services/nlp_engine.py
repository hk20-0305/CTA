# backend/app/services/nlp_engine.py
from sentence_transformers import SentenceTransformer, util
import torch
import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Medical synonym map — used by matching engine for keyword normalisation
# ---------------------------------------------------------------------------
MEDICAL_SYNONYMS: Dict[str, List[str]] = {
    "type 2 diabetes": ["t2dm", "t2d", "diabetes mellitus type 2", "niddm", "adult-onset diabetes", "diabetes"],
    "type 1 diabetes": ["t1dm", "t1d", "diabetes mellitus type 1", "iddm", "juvenile diabetes"],
    "hypertension": ["high blood pressure", "htn", "elevated blood pressure"],
    "heart failure": ["chf", "congestive heart failure", "cardiac failure"],
    "chronic kidney disease": ["ckd", "chronic renal failure", "renal insufficiency"],
    "copd": ["chronic obstructive pulmonary disease", "emphysema", "chronic bronchitis"],
    "myocardial infarction": ["heart attack", "mi", "ami", "coronary event"],
    "atrial fibrillation": ["afib", "af", "a-fib"],
    "hba1c": ["hemoglobin a1c", "glycated hemoglobin", "glycosylated hemoglobin", "a1c"],
    "bmi": ["body mass index"],
    "egfr": ["estimated glomerular filtration rate", "renal function"],
    "metformin": ["glucophage", "biguanide"],
    "insulin": ["basal insulin", "bolus insulin", "nph insulin", "insulin glargine"],
    "aspirin": ["asa", "acetylsalicylic acid"],
}

# Extended keyword lists for fallback NER
_CONDITION_KEYWORDS = [
    "type 2 diabetes", "t2dm", "type 1 diabetes", "t1dm", "diabetes mellitus",
    "hypertension", "high blood pressure", "heart failure", "copd",
    "chronic kidney disease", "ckd", "asthma", "cancer", "obesity",
    "atrial fibrillation", "stroke", "myocardial infarction", "heart attack",
    "liver disease", "hepatitis", "cirrhosis", "dyslipidemia", "hyperlipidemia",
    "hypercholesterolaemia", "neuropathy", "retinopathy", "nephropathy",
    "arthritis", "rheumatoid arthritis", "osteoporosis", "depression", "anxiety",
]

_MEDICATION_KEYWORDS = [
    "metformin", "insulin", "glargine", "detemir", "aspart", "lispro",
    "sitagliptin", "saxagliptin", "alogliptin", "linagliptin",
    "empagliflozin", "dapagliflozin", "canagliflozin",
    "semaglutide", "liraglutide", "dulaglutide", "exenatide",
    "glimepiride", "glipizide", "glyburide", "glibenclamide",
    "amlodipine", "lisinopril", "losartan", "valsartan", "ramipril",
    "atorvastatin", "rosuvastatin", "simvastatin", "pravastatin",
    "aspirin", "clopidogrel", "warfarin", "apixaban", "rivaroxaban",
    "omeprazole", "pantoprazole", "levothyroxine", "allopurinol",
]


class NLPEngine:
    def __init__(self):
        # --- Sentence Transformer for semantic similarity ---
        self.embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.embedding_model = SentenceTransformer(self.embedding_model_name)

        # --- scispaCy for biomedical NER (optional — graceful fallback) ---
        self.ner_model = None
        self._load_scispacy()

        logger.info(
            f"NLPEngine ready | embeddings={self.embedding_model_name} | "
            f"medical_NER={'scispaCy' if self.ner_model else 'keyword-fallback'}"
        )

    # ------------------------------------------------------------------
    # scispaCy loader
    # ------------------------------------------------------------------
    def _load_scispacy(self):
        """Try to load scispaCy en_core_sci_sm; silently fall back on failure."""
        try:
            import spacy
            self.ner_model = spacy.load("en_core_sci_sm")
            logger.info("scispaCy en_core_sci_sm loaded successfully")
        except Exception as e:
            logger.warning(
                f"scispaCy not available ({e}). Using keyword-based NER fallback. "
                "Install with: pip install scispacy && "
                "pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.3/en_core_sci_sm-0.5.3.tar.gz"
            )
            self.ner_model = None

    # ------------------------------------------------------------------
    # Entity extraction — NER-first, keyword fallback
    # ------------------------------------------------------------------
    def extract_entities(self, text: str) -> Dict:
        """
        Extract clinical entities from free text.
        Uses scispaCy when available; falls back to keyword matching.
        Returns: { conditions, medications, lab_values, ner_spans }
        """
        if self.ner_model is not None:
            return self._extract_with_scispacy(text)
        return self._extract_with_keywords(text)

    def _extract_with_scispacy(self, text: str) -> Dict:
        """NER extraction using scispaCy biomedical model."""
        doc = self.ner_model(text[:100_000])  # cap doc length

        # Collect all entity spans
        raw_spans = [ent.text.lower().strip() for ent in doc.ents]

        # Classify spans into conditions vs medications using keyword overlap
        conditions: List[str] = []
        medications: List[str] = []
        other_entities: List[str] = []

        text_lower = text.lower()

        for span in raw_spans:
            if any(med in span or span in med for med in _MEDICATION_KEYWORDS):
                medications.append(span)
            elif any(cond in span or span in cond for cond in _CONDITION_KEYWORDS):
                conditions.append(span)
            else:
                other_entities.append(span)

        # Also do keyword sweep to catch common terms the NER might miss
        kw_conditions = [c for c in _CONDITION_KEYWORDS if c in text_lower]
        kw_medications = [m for m in _MEDICATION_KEYWORDS if m in text_lower]

        # Merge and deduplicate
        all_conditions = list({c.title() for c in set(conditions + kw_conditions)})
        all_medications = list({m.title() for m in set(medications + kw_medications)})

        return {
            "conditions": all_conditions,
            "medications": all_medications,
            "lab_values": self._extract_labs(text),
            "ner_spans": list(set(raw_spans + other_entities)),
        }

    def _extract_with_keywords(self, text: str) -> Dict:
        """Keyword-based fallback extraction when scispaCy is unavailable."""
        text_lower = text.lower()
        conditions = [c.title() for c in _CONDITION_KEYWORDS if c in text_lower]
        medications = [m.title() for m in _MEDICATION_KEYWORDS if m in text_lower]
        return {
            "conditions": list(set(conditions)),
            "medications": list(set(medications)),
            "lab_values": self._extract_labs(text),
            "ner_spans": [],
        }

    # ------------------------------------------------------------------
    # Lab value extraction
    # ------------------------------------------------------------------
    def _extract_labs(self, text: str) -> Dict:
        """Extract common laboratory values using regex."""
        labs: Dict = {}

        patterns = {
            "hba1c": r"hba1c\s*[:\-]?\s*(\d+\.?\d*)\s*%?",
            "fasting_glucose": r"(?:fasting\s+(?:plasma\s+)?glucose|fpg)\s*[:\-]?\s*(\d+)\s*(?:mg/dl)?",
            "glucose": r"glucose\s*[:\-]?\s*(\d+)\s*(?:mg/dl)?",
            "bmi": r"bmi\s*[:\-]?\s*(\d+\.?\d*)",
            "systolic_bp": r"(?:blood\s+pressure|bp)\s*[:\-]?\s*(\d+)/\d+",
            "diastolic_bp": r"(?:blood\s+pressure|bp)\s*[:\-]?\s*\d+/(\d+)",
            "egfr": r"egfr\s*[:\-]?\s*(\d+)",
            "creatinine": r"creatinine\s*[:\-]?\s*(\d+\.?\d*)\s*(?:mg/dl)?",
            "cholesterol": r"(?:total\s+)?cholesterol\s*[:\-]?\s*(\d+)\s*(?:mg/dl)?",
            "ldl": r"ldl\s*[:\-]?\s*(\d+)\s*(?:mg/dl)?",
            "hdl": r"hdl\s*[:\-]?\s*(\d+)\s*(?:mg/dl)?",
            "triglycerides": r"triglycerides?\s*[:\-]?\s*(\d+)\s*(?:mg/dl)?",
            "alt": r"alt\s*[:\-]?\s*(\d+)\s*(?:u/l)?",
            "ast": r"ast\s*[:\-]?\s*(\d+)\s*(?:u/l)?",
            "hemoglobin": r"hemoglobin\s*[:\-]?\s*(\d+\.?\d*)\s*(?:g/dl)?",
            "o2_saturation": r"(?:o2\s+sat|spo2|oxygen\s+saturation)\s*[:\-]?\s*(\d+)\s*%?",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    labs[key] = float(match.group(1))
                except ValueError:
                    pass

        return labs

    # ------------------------------------------------------------------
    # Synonym expansion — used by matching engine
    # ------------------------------------------------------------------
    def expand_synonyms(self, text: str) -> str:
        """
        Expand medical abbreviations/synonyms in text so keyword matching
        works regardless of which term is used.
        E.g. 'T2DM' → 'T2DM type 2 diabetes t2d'
        """
        text_lower = text.lower()
        additions: List[str] = []
        for canonical, synonyms in MEDICAL_SYNONYMS.items():
            # If any form appears, add all forms
            all_forms = [canonical] + synonyms
            if any(f in text_lower for f in all_forms):
                additions.extend(all_forms)
        if additions:
            text = text + " " + " ".join(additions)
        return text

    # ------------------------------------------------------------------
    # Embedding & similarity utilities
    # ------------------------------------------------------------------
    def compute_embeddings(self, texts: List[str]) -> torch.Tensor:
        """Compute sentence embeddings for a list of texts."""
        return self.embedding_model.encode(texts, convert_to_tensor=True)

    def compute_similarity(self, text1: str, text2: str) -> float:
        """Cosine similarity between two texts (0–1)."""
        # Expand synonyms before encoding
        t1 = self.expand_synonyms(text1)
        t2 = self.expand_synonyms(text2)
        embeddings = self.embedding_model.encode([t1, t2], convert_to_tensor=True)
        sim = util.pytorch_cos_sim(embeddings[0], embeddings[1])
        return float(sim.item())

    def batch_similarity(self, query_text: str, candidate_texts: List[str]) -> List[float]:
        """
        Compute cosine similarity between a single query and multiple candidates.
        Much faster than N individual compute_similarity() calls.
        """
        if not candidate_texts:
            return []
        # Synonym-expand all texts
        query = self.expand_synonyms(query_text)
        candidates = [self.expand_synonyms(c) for c in candidate_texts]

        query_emb = self.embedding_model.encode(query, convert_to_tensor=True)
        cand_embs = self.embedding_model.encode(candidates, convert_to_tensor=True)
        similarities = util.pytorch_cos_sim(query_emb, cand_embs)
        return [float(s.item()) for s in similarities[0]]

    def normalize_medical_text(self, text: str) -> str:
        """Normalise medical text."""
        text = text.lower()
        text = text.replace("&", "and")
        return text


# Singleton
nlp_engine = NLPEngine()