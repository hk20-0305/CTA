# app/utils/normalization.py
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Example lookup tables - in practice, these would be loaded from RxNorm, SNOMED, etc.
DRUG_NORMALIZATION = {
    "carboplatin": "carboplatin",
    "carbo": "carboplatin",
    "carboplatinum": "carboplatin",
    "pemetrexed": "pemetrexed",
    "pem": "pemetrexed",
    "metformin": "metformin",
    "glucophage": "metformin",
    "glucophage xr": "metformin",
    "lisinopril": "lisinopril",
    "prinivil": "lisinopril",
    "zestril": "lisinopril",
    "atorvastatin": "atorvastatin",
    "lipitor": "atorvastatin",
    "atorva": "atorvastatin"
}

CONDITION_NORMALIZATION = {
    "lung cancer": "lung cancer",
    "nsclc": "non-small cell lung cancer",
    "non-small cell lung cancer": "non-small cell lung cancer",
    "diabetes": "diabetes mellitus",
    "type 2 diabetes": "diabetes mellitus type 2",
    "hypertension": "hypertension",
    "copd": "chronic obstructive pulmonary disease",
    "chronic obstructive pulmonary disease": "chronic obstructive pulmonary disease",
    "pneumonia": "pneumonia"
}

LAB_TEST_NORMALIZATION = {
    "hemoglobin": "hemoglobin",
    "hgb": "hemoglobin",
    "wbc": "white blood cell count",
    "white blood cells": "white blood cell count",
    "platelets": "platelets",
    "creatinine": "creatinine",
    "ast": "aspartate aminotransferase",
    "alt": "alanine aminotransferase",
    "glucose": "glucose"
}

def normalize_drug_name(name: str) -> str:
    """
    Normalize drug name to standard form.
    """
    name = name.lower().strip()
    # Remove common suffixes
    name = re.sub(r'\s*\([^)]*\)', '', name)  # Remove (tablet), (IV), etc.
    name = re.sub(r'\s*\d+.*$', '', name)      # Remove dosage info
    name = re.sub(r'\s*-\s*\w+', '', name)     # Remove -sodium, -potassium, etc.
    name = name.strip()
    
    # Map to standard name
    return DRUG_NORMALIZATION.get(name, name)

def normalize_condition(condition: str) -> str:
    """
    Normalize condition name to standard form.
    """
    condition = condition.lower().strip()
    condition = re.sub(r'\s*\([^)]*\)', '', condition)
    condition = re.sub(r'\s*\d+.*$', '', condition)
    condition = condition.strip()
    
    return CONDITION_NORMALIZATION.get(condition, condition)

def normalize_lab_test(test: str) -> str:
    """
    Normalize lab test name to standard form.
    """
    test = test.lower().strip()
    test = re.sub(r'\s*\([^)]*\)', '', test)
    test = re.sub(r'\s*\d+.*$', '', test)
    test = test.strip()
    
    return LAB_TEST_NORMALIZATION.get(test, test)

def normalize_medical_text(text: str, entity_type: str = "drug") -> str:
    """
    Normalize medical text based on entity type.
    """
    if entity_type == "drug":
        return normalize_drug_name(text)
    elif entity_type == "condition":
        return normalize_condition(text)
    elif entity_type == "lab":
        return normalize_lab_test(text)
    else:
        return text.lower().strip()

def batch_normalize_drugs(names: List[str]) -> List[str]:
    """
    Normalize a batch of drug names.
    """
    return [normalize_drug_name(name) for name in names]

def batch_normalize_conditions(conditions: List[str]) -> List[str]:
    """
    Normalize a batch of conditions.
    """
    return [normalize_condition(condition) for condition in conditions]

def batch_normalize_lab_tests(tests: List[str]) -> List[str]:
    """
    Normalize a batch of lab tests.
    """
    return [normalize_lab_test(test) for test in tests]
