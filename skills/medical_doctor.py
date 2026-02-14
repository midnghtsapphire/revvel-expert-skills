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
        if param.lower() in reference_ranges:
            low, high = reference_ranges[param.lower()]
            status = 'normal' if low <= value <= high else 'low' if value < low else 'high'
            interpretations[param] = {
                'value': value,
                'reference_range': f'{low}-{high}',
                'status': status
            }
    
    return {
        'interpretations': interpretations,
        'patient_info': {'age': age, 'gender': gender},
        'flags': [k for k, v in interpretations.items() if v['status'] != 'normal']
    }


def generate_differential_diagnosis(symptoms: List[str], age: int, gender: str,
                                     medical_history: List[str] = None) -> List[Dict[str, Any]]:
    """Generate differential diagnosis based on symptoms."""
    symptom_disease_map = {
        'chest_pain': [
            {'condition': 'Acute Coronary Syndrome', 'probability': 0.3, 'urgency': 'emergent'},
            {'condition': 'Pulmonary Embolism', 'probability': 0.15, 'urgency': 'emergent'},
            {'condition': 'Costochondritis', 'probability': 0.2, 'urgency': 'routine'},
            {'condition': 'GERD', 'probability': 0.25, 'urgency': 'routine'},
            {'condition': 'Pneumothorax', 'probability': 0.1, 'urgency': 'emergent'}
        ],
        'headache': [
            {'condition': 'Tension Headache', 'probability': 0.4, 'urgency': 'routine'},
            {'condition': 'Migraine', 'probability': 0.3, 'urgency': 'routine'},
            {'condition': 'Subarachnoid Hemorrhage', 'probability': 0.05, 'urgency': 'emergent'},
            {'condition': 'Meningitis', 'probability': 0.05, 'urgency': 'emergent'},
            {'condition': 'Sinusitis', 'probability': 0.2, 'urgency': 'routine'}
        ],
        'abdominal_pain': [
            {'condition': 'Appendicitis', 'probability': 0.15, 'urgency': 'urgent'},
            {'condition': 'Cholecystitis', 'probability': 0.1, 'urgency': 'urgent'},
            {'condition': 'Gastritis', 'probability': 0.25, 'urgency': 'routine'},
            {'condition': 'Pancreatitis', 'probability': 0.1, 'urgency': 'urgent'},
            {'condition': 'IBS', 'probability': 0.2, 'urgency': 'routine'}
        ],
        'shortness_of_breath': [
            {'condition': 'Asthma', 'probability': 0.25, 'urgency': 'urgent'},
            {'condition': 'COPD Exacerbation', 'probability': 0.2, 'urgency': 'urgent'},
            {'condition': 'Heart Failure', 'probability': 0.15, 'urgency': 'emergent'},
            {'condition': 'Pneumonia', 'probability': 0.2, 'urgency': 'urgent'},
            {'condition': 'Anxiety', 'probability': 0.15, 'urgency': 'routine'}
        ]
    }
    
    differentials = []
    seen = set()
    for symptom in symptoms:
        symptom_key = symptom.lower().replace(' ', '_')
        if symptom_key in symptom_disease_map:
            for dx in symptom_disease_map[symptom_key]:
                if dx['condition'] not in seen:
                    differentials.append(dx)
                    seen.add(dx['condition'])
    
    # Adjust for age
    if age > 65:
        for dx in differentials:
            if dx['urgency'] == 'emergent':
                dx['probability'] = min(dx['probability'] * 1.3, 1.0)
    
    differentials.sort(key=lambda x: x['probability'], reverse=True)
    return differentials


def check_drug_interactions(medications: List[str]) -> List[Dict[str, Any]]:
    """Check for known drug interactions."""
    interaction_db = {
        ('warfarin', 'aspirin'): {'severity': 'major', 'effect': 'Increased bleeding risk'},
        ('metformin', 'contrast_dye'): {'severity': 'major', 'effect': 'Risk of lactic acidosis'},
        ('ssri', 'maoi'): {'severity': 'contraindicated', 'effect': 'Serotonin syndrome risk'},
        ('ace_inhibitor', 'potassium'): {'severity': 'major', 'effect': 'Hyperkalemia risk'},
        ('statin', 'grapefruit'): {'severity': 'moderate', 'effect': 'Increased statin levels'},
        ('methotrexate', 'nsaid'): {'severity': 'major', 'effect': 'Increased methotrexate toxicity'}
    }
    
    interactions = []
    med_lower = [m.lower() for m in medications]
    
    for (drug_a, drug_b), info in interaction_db.items():
        if drug_a in med_lower and drug_b in med_lower:
            interactions.append({
                'drug_a': drug_a,
                'drug_b': drug_b,
                'severity': info['severity'],
                'effect': info['effect']
            })
    
    return interactions


def lookup_icd10(search_term: str) -> List[Dict[str, str]]:
    """Look up ICD-10 codes by search term."""
    icd10_db = {
        'diabetes': [{'code': 'E11.9', 'description': 'Type 2 diabetes mellitus without complications'},
                     {'code': 'E10.9', 'description': 'Type 1 diabetes mellitus without complications'}],
        'hypertension': [{'code': 'I10', 'description': 'Essential (primary) hypertension'}],
        'heart_failure': [{'code': 'I50.9', 'description': 'Heart failure, unspecified'},
                          {'code': 'I50.20', 'description': 'Unspecified systolic heart failure'}],
        'pneumonia': [{'code': 'J18.9', 'description': 'Pneumonia, unspecified organism'}],
        'depression': [{'code': 'F32.9', 'description': 'Major depressive disorder, single episode, unspecified'}],
        'asthma': [{'code': 'J45.909', 'description': 'Unspecified asthma, uncomplicated'}]
    }
    
    results = []
    search_lower = search_term.lower()
    for key, codes in icd10_db.items():
        if search_lower in key:
            results.extend(codes)
    return results


class SkillEngine:
    """Medical Doctor / Physician Expert skill engine."""
    
    def __init__(self):
        self.name = SKILL_METADATA['name']
        self.version = SKILL_METADATA['version']
    
    def run(self, action: str, **kwargs) -> Dict[str, Any]:
        actions = {
            'differential_diagnosis': lambda: generate_differential_diagnosis(**kwargs),
            'interpret_cbc': lambda: interpret_cbc_results(**kwargs),
            'drug_interactions': lambda: check_drug_interactions(**kwargs),
            'icd10_lookup': lambda: lookup_icd10(**kwargs),
            'calculate_gfr': lambda: calculate_gfr(**kwargs),
            'calculate_meld': lambda: calculate_meld(**kwargs),
        }
        if action in actions:
            return actions[action]()
        return {'error': f'Unknown action: {action}'}


class TestMedicalDoctor(unittest.TestCase):
    """Unit tests for Medical Doctor skill."""
    
    def test_metadata(self):
        self.assertEqual(SKILL_METADATA['id'], 'medical_doctor')
    
    def test_cbc_interpretation(self):
        cbc = {'wbc': 7.5, 'hemoglobin': 14.0, 'platelets': 250}
        result = interpret_cbc_results(cbc, age=45, gender='male')
        self.assertIn('interpretations', result)
        self.assertEqual(len(result['flags']), 0)
    
    def test_cbc_abnormal(self):
        cbc = {'wbc': 15.0, 'hemoglobin': 8.0, 'platelets': 100}
        result = interpret_cbc_results(cbc, age=45, gender='male')
        self.assertGreater(len(result['flags']), 0)
    
    def test_differential_diagnosis(self):
        result = generate_differential_diagnosis(
            symptoms=['chest_pain'], age=55, gender='male'
        )
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
    
    def test_drug_interactions(self):
        result = check_drug_interactions(['warfarin', 'aspirin'])
        self.assertGreater(len(result), 0)
        self.assertEqual(result[0]['severity'], 'major')
    
    def test_no_drug_interactions(self):
        result = check_drug_interactions(['metformin', 'lisinopril'])
        self.assertEqual(len(result), 0)
    
    def test_icd10_lookup(self):
        result = lookup_icd10('diabetes')
        self.assertGreater(len(result), 0)
        self.assertIn('E11.9', [r['code'] for r in result])
    
    def test_meld_score(self):
        score = calculate_meld(bilirubin=2.0, creatinine=1.5, inr=1.5)
        self.assertIsInstance(score, float)
        self.assertGreater(score, 0)
    
    def test_skill_engine(self):
        engine = SkillEngine()
        self.assertEqual(engine.name, 'Medical Doctor / Physician Expert')
    
    def test_prompts_exist(self):
        self.assertGreater(len(EXPERT_PROMPTS), 0)


if __name__ == '__main__':
    unittest.main()