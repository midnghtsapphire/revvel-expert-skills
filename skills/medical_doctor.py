import json
import re
import os
import math
import hashlib
import statistics
import requests
import datetime
import collections
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import unittest
import logging

SKILL_METADATA = {
    "name": "Medical Doctor / Physician Expert",
    "id": "medical_doctor",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Comprehensive medical diagnostic reasoning engine with differential diagnosis generation, ICD/CPT coding, drug interaction checking, lab interpretation, radiology/pathology analysis, clinical guidelines, and evidence-based medicine search capabilities.",
    "capabilities": [
        "differential_diagnosis",
        "icd_code_lookup",
        "cpt_code_analysis",
        "drug_interaction_check",
        "lab_result_interpretation",
        "radiology_report_interpretation",
        "pathology_report_analysis",
        "medical_record_review",
        "treatment_protocol_lookup",
        "clinical_guidelines_search",
        "pharmacology_reference",
        "anatomy_reference",
        "surgical_procedure_lookup",
        "medical_terminology_decode",
        "patient_history_analysis",
        "vital_signs_trending",
        "medical_calculators",
        "evidence_based_medicine_search",
        "telemedicine_protocols"
    ],
    "domain": "healthcare"
}

EXPERT_PROMPTS = {
    "differential_diagnosis": """You are a board-certified physician. Given the following clinical presentation:
Chief Complaint: {chief_complaint}
History of Present Illness: {hpi}
Past Medical History: {pmh}
Current Medications: {medications}
Vital Signs: {vitals}
Physical Exam Findings: {exam_findings}
Laboratory Results: {lab_results}
Imaging Results: {imaging_results}

Generate a ranked differential diagnosis list with:
1. Most likely diagnoses with reasoning
2. Less likely but important diagnoses
3. Life-threatening conditions to rule out
4. Recommended diagnostic workup
5. Initial management considerations""",

    "lab_interpretation": """You are a clinical pathologist. Interpret the following laboratory results:
Patient Demographics: {demographics}
CBC: {cbc_results}
CMP: {cmp_results}
Lipid Panel: {lipid_results}
Thyroid Panel: {thyroid_results}
Other Labs: {other_labs}

Provide:
1. Abnormal values identification
2. Clinical significance of abnormalities
3. Possible underlying causes
4. Recommendations for further evaluation
5. Trending considerations if previous results available""",

    "drug_interaction_analysis": """You are a clinical pharmacologist. Analyze potential drug interactions for:
Patient Medications: {current_medications}
New Medication to Add: {new_medication}
Patient Factors: {patient_factors}

Assess:
1. Drug-drug interactions with severity levels
2. Contraindications and precautions
3. Dosing adjustments needed
4. Monitoring requirements
5. Alternative medication suggestions""",

    "radiology_report_analysis": """You are a radiologist. Interpret the following imaging study:
Study Type: {study_type}
Clinical Indication: {indication}
Technical Quality: {technical_quality}
Findings: {findings}

Provide:
1. Key positive and negative findings
2. Clinical correlation recommendations
3. Follow-up imaging suggestions
4. Urgent findings requiring immediate attention
5. Differential diagnosis based on imaging""",

    "clinical_guidelines_query": """You are an evidence-based medicine expert. For the following clinical scenario:
Diagnosis: {diagnosis}
Patient Characteristics: {patient_characteristics}
Clinical Question: {clinical_question}

Search and summarize:
1. Relevant clinical practice guidelines (NICE, AHA, ACS, NCCN)
2. Grade of evidence and recommendation strength
3. Treatment algorithms and protocols
4. Quality metrics and performance indicators
5. Controversies or areas of uncertainty""",

    "medical_record_review": """You are a physician conducting a comprehensive medical record review:
Patient Records: {medical_records}
Review Purpose: {review_purpose}
Time Period: {time_period}

Analyze:
1. Medical history chronology and continuity
2. Medication reconciliation and adherence
3. Preventive care compliance
4. Quality of care indicators
5. Potential gaps or discrepancies
6. Recommendations for care optimization""",

    "pathology_report_interpretation": """You are a pathologist interpreting a surgical pathology report:
Specimen Type: {specimen_type}
Gross Description: {gross_description}
Microscopic Description: {microscopic_description}
Immunohistochemistry: {ihc_results}
Special Stains: {special_stains}

Provide:
1. Diagnosis and histologic grade
2. Margins and extent of disease
3. Prognostic markers and significance
4. Recommendations for additional testing
5. Clinical correlation and next steps""",

    "surgical_procedure_lookup": """You are a surgical specialist. Provide detailed information about:
Procedure: {procedure_name}
Indication: {indication}
Patient Factors: {patient_factors}

Include:
1. Step-by-step surgical approach
2. Key anatomical considerations
3. Potential complications and management
4. Postoperative care protocol
5. Outcomes and prognosis data""",

    "emergency_medicine_evaluation": """You are an emergency medicine physician. Evaluate this case:
Presenting Complaint: {presenting_complaint}
Vital Signs: {vitals}
Primary Survey: {primary_survey}
Secondary Survey: {secondary_survey}
Initial Diagnostics: {initial_diagnostics}

Assess:
1. Emergency severity index and triage level
2. Life-threatening conditions to rule out
3. Immediate interventions required
4. Disposition and admission criteria
5. Follow-up and discharge instructions"""
}

INTEGRATION_POINTS = {
    "fda_drug_api": {
        "type": "api",
        "endpoint": "https://api.fda.gov/drug/label.json",
        "description": "FDA Drug Label Database for medication information and interactions",
        "auth_method": "none",
        "documentation_url": "https://open.fda.gov/apis/drug/label/"
    },
    "pubmed_api": {
        "type": "api",
        "endpoint": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
        "description": "PubMed database for medical literature search",
        "auth_method": "api_key",
        "documentation_url": "https://www.ncbi.nlm.nih.gov/books/NBK25501/"
    },
    "icd_api": {
        "type": "api",
        "endpoint": "https://id.who.int/icd/release/11/2023-01/mms",
        "description": "WHO ICD-11 API for disease classification",
        "auth_method": "oauth2",
        "documentation_url": "https://icd.who.int/icdapi"
    },
    "clinical_guidelines_db": {
        "type": "database",
        "endpoint": "internal_guidelines_db",
        "description": "Internal database of clinical practice guidelines",
        "auth_method": "internal",
        "documentation_url": "internal"
    },
    "lab_reference_db": {
        "type": "database",
        "endpoint": "internal_lab_references",
        "description": "Laboratory reference ranges and interpretation guidelines",
        "auth_method": "internal",
        "documentation_url": "internal"
    },
    "drug_interaction_db": {
        "type": "database",
        "endpoint": "internal_drug_interactions",
        "description": "Drug interaction database with severity classifications",
        "auth_method": "internal",
        "documentation_url": "internal"
    }
}

class VitalSigns:
    def __init__(self, temperature: float = None, heart_rate: int = None, 
                 blood_pressure_systolic: int = None, blood_pressure_diastolic: int = None,
                 respiratory_rate: int = None, oxygen_saturation: float = None):
        self.temperature = temperature
        self.heart_rate = heart_rate
        self.blood_pressure_systolic = blood_pressure_systolic
        self.blood_pressure_diastolic = blood_pressure_diastolic
        self.respiratory_rate = respiratory_rate
        self.oxygen_saturation = oxygen_saturation

class LabResults:
    def __init__(self, cbc: Dict = None, cmp: Dict = None, lipid: Dict = None, 
                 thyroid: Dict = None, other: Dict = None):
        self.cbc = cbc or {}
        self.cmp = cmp or {}
        self.lipid = lipid or {}
        self.thyroid = thyroid or {}
        self.other = other or {}

def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """Calculate Body Mass Index (BMI) from weight and height."""
    if weight_kg <= 0 or height_cm <= 0:
        raise ValueError("Weight and height must be positive values")
    height_m = height_cm / 100
    return weight_kg / (height_m ** 2)

def calculate_gfr(age: int, gender: str, creatinine: float, race: str = "other") -> float:
    """Calculate estimated glomerular filtration rate (eGFR) using CKD-EPI equation."""
    if age <= 0 or creatinine <= 0:
        raise ValueError("Age and creatinine must be positive values")
    
    gender = gender.lower()
    race = race.lower()
    
    if gender == "female":
        k = 0.7
        a = -0.329
        factor = 1.018 if race == "black" else 1.0
    else:
        k = 0.9
        a = -0.411
        factor = 1.159 if race == "black" else 1.0
    
    min_ratio = min(creatinine / k, 1)
    max_ratio = max(creatinine / k, 1)
    
    egfr = 141 * (min_ratio ** a) * (max_ratio ** -1.209) * (0.993 ** age) * factor
    return round(egfr, 1)

def calculate_meld(bilirubin: float, creatinine: float, inr: float, sodium: float = None) -> float:
    """Calculate MELD score for liver disease severity."""
    if bilirubin < 0 or creatinine < 0 or inr < 0:
        raise ValueError("Lab values cannot be negative")
    
    creatinine = min(creatinine, 4.0)
    
    if sodium is not None:
        # MELD-Na
        meld = 10 * (0.957 * math.log(creatinine) + 0.378 * math.log(bilirubin) + 1.120 * math.log(inr) + 0.643)
        if sodium < 125:
            meld += 1.32 * (125 - sodium) - 0.033 * meld * (125 - sodium)
        elif sodium > 140:
            meld += 1.32 * (sodium - 140)
    else:
        # Standard MELD
        meld = 10 * (0.957 * math.log(creatinine) + 0.378 * math.log(bilirubin) + 1.120 * math.log(inr)) + 6.43
    
    return round(max(meld, 6), 1)

def interpret_cbc_results(cbc: Dict[str, float], age: int, gender: str) -> Dict[str, Any]:
    """Interpret Complete Blood Count results."""
    reference_ranges = {
        "wbc": (4.0, 11.0),  # x10^9/L
        "rbc": (4.2, 5.9) if gender.lower() == "male" else (3.8, 5.2),  # x10^12/L
        "hemoglobin": (13.5, 17.5) if gender.lower() == "male" else (12.0, 15.5),  # g/dL
        "hematocrit": (41, 53) if gender.lower() == "male" else (36, 46),  # %
        "mcv": (80, 100),  # fL
        "platelets": (150, 450)  # x10^9/L
    }
    
    interpretations = {}
    for param, value in cbc.items():
        if param.lower