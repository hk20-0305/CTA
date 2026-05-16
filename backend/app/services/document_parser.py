# backend/app/services/document_parser.py
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DocumentParser:
    """
    Parses patient records and clinical trial documents.
    Uses pdfminer for PDF text extraction and the NLP engine's
    NER model (scispaCy when available, keyword fallback otherwise)
    for medical entity recognition.
    """

    def __init__(self):
        self.laparams = LAParams(detect_vertical=True, all_texts=True)
        # Import here to avoid circular dependency; nlp_engine is a singleton
        from app.services.nlp_engine import nlp_engine
        self._nlp = nlp_engine

    # ------------------------------------------------------------------
    # PDF extraction
    # ------------------------------------------------------------------
    def extract_from_pdf(self, pdf_file) -> str:
        """Extract and clean text from an uploaded PDF file."""
        import io
        try:
            pdf_bytes = pdf_file.read()
            pdf_file.seek(0)
            text = extract_text(io.BytesIO(pdf_bytes), laparams=self.laparams)
            text = self._clean_text(text)
            logger.info(f"Extracted {len(text)} chars from PDF")
            return text
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return ""

    def _clean_text(self, text: str) -> str:
        """Normalise extracted text while preserving medically meaningful characters."""
        # Collapse multiple spaces/newlines but keep single newlines for structure
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Remove non-printable chars while keeping medical symbols
        text = re.sub(r"[^\w\s\-.,;:()/≥≤<>%°\n]", "", text)
        return text.strip()

    # ------------------------------------------------------------------
    # Patient data parsing
    # ------------------------------------------------------------------
    def parse_patient_data(self, text: str) -> Dict:
        """
        Parse patient information from free text.
        NER is used for conditions and medications;
        regex patterns handle structured fields (age, gender, lab values).
        """
        # Run NER extraction first
        ner_entities = self._nlp.extract_entities(text)

        # Merge NER conditions with pattern-extracted conditions
        regex_conditions = self._extract_conditions_regex(text)
        merged_conditions = list(
            {c.lower(): c for c in (ner_entities["conditions"] + regex_conditions)}.values()
        )

        # Merge NER medications with pattern-extracted medications
        regex_meds = self._extract_medications_regex(text)
        merged_meds = list(
            {m.lower(): m for m in (ner_entities["medications"] + regex_meds)}.values()
        )

        # Lab values: NER lab values + pattern extraction (patterns are more precise)
        lab_values = {**ner_entities["lab_values"], **self._extract_lab_values(text)}

        patient_data = {
            "name": self._extract_name(text),
            "age": self._extract_age(text),
            "gender": self._extract_gender(text),
            "conditions": merged_conditions,
            "medications": merged_meds,
            "lab_values": lab_values,
            "raw_text": text,
        }
        logger.info(
            f"Parsed patient: name={patient_data['name']}, age={patient_data['age']}, "
            f"conditions={len(merged_conditions)}, medications={len(merged_meds)}, "
            f"labs={list(lab_values.keys())}"
        )
        return patient_data

    # ------------------------------------------------------------------
    # Trial data parsing
    # ------------------------------------------------------------------
    def parse_trial_data(self, text: str) -> Dict:
        """Parse clinical trial criteria from text."""
        trial_data = {
            "title": self._extract_trial_title(text),
            "inclusion_criteria": self._extract_inclusion_criteria(text),
            "exclusion_criteria": self._extract_exclusion_criteria(text),
            "condition": self._extract_trial_condition(text),
            "raw_text": text,
        }
        logger.info(
            f"Parsed trial: title={trial_data['title']!r}, "
            f"inclusion_criteria={len(trial_data['inclusion_criteria'])}, "
            f"exclusion_criteria={len(trial_data['exclusion_criteria'])}"
        )
        return trial_data

    # ------------------------------------------------------------------
    # Patient field extractors
    # ------------------------------------------------------------------
    def _extract_name(self, text: str) -> Optional[str]:
        patterns = [
            r"(?:Patient\s+Name|Name|Patient)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
            r"(?:Mr\.|Mrs\.|Ms\.|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                return m.group(1).strip()
        return None

    def _extract_age(self, text: str) -> Optional[int]:
        patterns = [
            r"(?:Age|Patient\s+Age)[:\s]+(\d{1,3})\s*(?:years?|yrs?)?",
            r"(\d{1,3})\s*[- ]?year[- ]?old",
            r"(\d{1,3})\s*y/?o\b",
            r"DOB.*?(\d{2})/(\d{2})/(\d{4})",  # will calculate from DOB below
        ]
        for p in patterns[:3]:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                age = int(m.group(1))
                if 0 < age < 120:
                    return age
        # DOB fallback
        dob_m = re.search(r"DOB[:\s]+(\d{1,2})[/-](\d{1,2})[/-](\d{4})", text, re.IGNORECASE)
        if dob_m:
            try:
                from datetime import date
                birth_year = int(dob_m.group(3))
                age = date.today().year - birth_year
                if 0 < age < 120:
                    return age
            except Exception:
                pass
        return None

    def _extract_gender(self, text: str) -> Optional[str]:
        patterns = [
            r"(?:Sex|Gender)[:\s]+(Male|Female|M(?:\b)|F(?:\b))",
            r"\b(Male|Female)\b",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                raw = m.group(1).upper()
                return "Male" if raw in ("M", "MALE") else "Female"
        return None

    def _extract_conditions_regex(self, text: str) -> List[str]:
        """Regex-based condition extraction to supplement NER."""
        conditions: List[str] = []

        section_patterns = [
            r"(?:Diagnosis|Diagnos[ei]s|Comorbidities|Medical\s+History|Conditions?|PMH)[:\s]+([^\n]+)",
        ]
        for p in section_patterns:
            for m in re.finditer(p, text, re.IGNORECASE):
                for part in re.split(r"[,;]", m.group(1)):
                    part = part.strip()
                    if 3 < len(part) < 80:
                        conditions.append(part.title())
        return conditions

    def _extract_medications_regex(self, text: str) -> List[str]:
        """Regex-based medication extraction to supplement NER."""
        medications: List[str] = []

        section_patterns = [
            r"(?:Medications?|Current\s+Medications?|Drugs?|Rx)[:\s]+([^\n]+)",
        ]
        for p in section_patterns:
            for m in re.finditer(p, text, re.IGNORECASE):
                for part in re.split(r"[,;]", m.group(1)):
                    part = part.strip()
                    if 2 < len(part) < 60:
                        medications.append(part.title())
        return medications

    def _extract_lab_values(self, text: str) -> Dict:
        """
        Precise regex extraction of common lab values.
        More accurate than NER for structured numeric data.
        """
        labs: Dict = {}

        lab_patterns = {
            "hba1c": r"(?:HbA1c|Hemoglobin\s+A1c|A1C)[:\s]*([\d.]+)\s*%?",
            "fasting_glucose": r"(?:Fasting\s+(?:Plasma\s+)?Glucose|FPG)[:\s]*(\d+)\s*(?:mg/dL)?",
            "glucose": r"(?<!\w)Glucose[:\s]*(\d+)\s*(?:mg/dL)?",
            "bmi": r"BMI[:\s]*([\d.]+)",
            "systolic_bp": r"(?:Blood\s+Pressure|BP)[:\s]*(\d{2,3})/\d{2,3}",
            "diastolic_bp": r"(?:Blood\s+Pressure|BP)[:\s]*\d{2,3}/(\d{2,3})",
            "egfr": r"eGFR[:\s]*(\d+)\s*(?:mL/min)?",
            "creatinine": r"Creatinine[:\s]*([\d.]+)\s*(?:mg/dL)?",
            "cholesterol": r"(?:Total\s+)?Cholesterol[:\s]*(\d+)\s*(?:mg/dL)?",
            "ldl": r"LDL(?:-C)?[:\s]*(\d+)\s*(?:mg/dL)?",
            "hdl": r"HDL(?:-C)?[:\s]*(\d+)\s*(?:mg/dL)?",
            "triglycerides": r"Triglycerides?[:\s]*(\d+)\s*(?:mg/dL)?",
            "alt": r"\bALT[:\s]*(\d+)\s*(?:U/L)?",
            "ast": r"\bAST[:\s]*(\d+)\s*(?:U/L)?",
            "hemoglobin": r"Hemoglobin[:\s]*([\d.]+)\s*(?:g/dL)?",
            "o2_saturation": r"(?:O2\s+Sat|SpO2|Oxygen\s+Saturation)[:\s]*(\d+)\s*%?",
        }

        for key, pattern in lab_patterns.items():
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                try:
                    labs[key] = float(m.group(1))
                except ValueError:
                    pass

        return labs

    # ------------------------------------------------------------------
    # Trial field extractors
    # ------------------------------------------------------------------
    def _extract_trial_title(self, text: str) -> str:
        """Extract trial title — first substantial non-bullet line."""
        # Explicit title field
        m = re.search(r"(?:Title|Study\s+Title|Protocol\s+Title)[:\s]+([^\n]+)", text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        # First meaningful non-bullet line
        for line in text.split("\n")[:10]:
            line = line.strip()
            if len(line) > 20 and not line.startswith(("•", "-", "*", "1.", "2.")):
                return line
        return "Unknown Trial"

    def _extract_trial_condition(self, text: str) -> str:
        """Extract the primary condition the trial targets."""
        # Explicit field
        m = re.search(r"(?:Condition|Disease|Indication)[:\s]+([^\n]+)", text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        # Keyword scan
        from app.services.nlp_engine import _CONDITION_KEYWORDS
        text_lower = text.lower()
        for cond in _CONDITION_KEYWORDS:
            if cond in text_lower:
                return cond.title()
        return "Unknown"

    def _extract_inclusion_criteria(self, text: str) -> List[str]:
        """
        Extract inclusion criteria from the document.
        Handles:
          - Numbered lists:  1. Age ≥ 18 years
          - Bullet lists:    • Diagnosis of Type 2 Diabetes
          - Plain paragraphs within an Inclusion Criteria section
        """
        return self._extract_criteria_section(
            text,
            start_pattern=r"Inclusion\s+Criteria",
            stop_pattern=r"Exclusion\s+Criteria",
        )

    def _extract_exclusion_criteria(self, text: str) -> List[str]:
        """Extract exclusion criteria from the document."""
        return self._extract_criteria_section(
            text,
            start_pattern=r"Exclusion\s+Criteria",
            stop_pattern=r"(?:Endpoints?|Objectives?|Statistical|References?|Appendix|\Z)",
        )

    def _extract_criteria_section(
        self, text: str, start_pattern: str, stop_pattern: str
    ) -> List[str]:
        """Generic section extractor for criteria lists."""
        criteria: List[str] = []

        # Find section boundaries
        start_m = re.search(start_pattern, text, re.IGNORECASE)
        if not start_m:
            return criteria

        section_start = start_m.end()
        stop_m = re.search(stop_pattern, text[section_start:], re.IGNORECASE)
        section_text = (
            text[section_start: section_start + stop_m.start()]
            if stop_m
            else text[section_start:]
        )

        # Split on numbered items, bullets, or newlines
        items: List[str] = re.split(
            r"(?:\n\s*(?:\d+[.)]\s+|[•\-\*]\s+)|;\s*(?=\w))",
            section_text,
        )
        for item in items:
            item = item.strip().rstrip(";.,")
            # Filter out too-short fragments or header-only lines
            if len(item) > 10 and not re.match(
                r"^(?:Inclusion|Exclusion)\s+Criteria\s*:?$", item, re.IGNORECASE
            ):
                criteria.append(item)

        return criteria


document_parser = DocumentParser()