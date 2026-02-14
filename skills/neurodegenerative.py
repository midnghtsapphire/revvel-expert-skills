import json
import os
import re
import hashlib
import statistics
import math
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import unittest
from unittest.mock import patch, MagicMock

SKILL_METADATA = {
    "name": "Neurodegenerative Disease Formulations",
    "id": "neurodegenerative",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Comprehensive analysis and formulation support for neurodegenerative diseases including Parkinson's and Alzheimer's research, clinical trial matching, biomarker tracking, and treatment optimization",
    "capabilities": [
        "biomarker_analysis",
        "clinical_trial_matching",
        "drug_interaction_analysis",
        "treatment_formulation",
        "research_data_parsing",
        "lifestyle_intervention_protocols",
        "neuroprotective_compound_analysis",
        "disease_progression_modeling"
    ],
    "domain": "neurodegenerative_disease_research"
}

EXPERT_PROMPTS = {
    "biomarker_analysis": """Analyze biomarker data for {disease_type} patient with the following profile:
Age: {patient_age}
Gender: {patient_gender}
Biomarkers: {biomarker_data}
Previous treatments: {treatment_history}
Current medications: {current_medications}
Provide detailed interpretation of biomarker levels, disease progression indicators, and recommended monitoring schedule.""",
    
    "clinical_trial_matching": """Find relevant clinical trials for {disease_type} patient with:
Inclusion criteria: {inclusion_criteria}
Exclusion criteria: {exclusion_criteria}
Location: {location}
Disease stage: {disease_stage}
Biomarker profile: {biomarker_profile}
Return top 5 matching trials with eligibility assessment.""",
    
    "drug_interaction_analysis": """Analyze potential drug interactions for {disease_type} treatment regimen:
Current medications: {current_medications}
Proposed additions: {proposed_drugs}
Patient factors: {patient_factors}
Provide interaction severity, mechanisms, and mitigation strategies.""",
    
    "treatment_formulation": """Design personalized treatment protocol for {disease_type} patient:
Patient profile: {patient_profile}
Disease characteristics: {disease_characteristics}
Treatment goals: {treatment_goals}
Constraints: {constraints}
Include dosing, timing, monitoring parameters, and expected outcomes.""",
    
    "research_data_parsing": """Parse and analyze research data from {source_type}:
Dataset: {dataset_description}
Analysis focus: {analysis_focus}
Key variables: {key_variables}
Provide structured summary with statistical insights and clinical relevance.""",
    
    "lifestyle_intervention_protocols": """Develop lifestyle intervention protocol for {disease_type}:
Patient demographics: {patient_demographics}
Current lifestyle: {current_lifestyle}
Disease stage: {disease_stage}
Comorbidities: {comorbidities}
Include diet, exercise, cognitive training, and social engagement recommendations.""",
    
    "neuroprotective_compound_analysis": """Evaluate neuroprotective compounds for {disease_type}:
Target mechanisms: {target_mechanisms}
Compound list: {compound_list}
Bioavailability data: {bioavailability_data}
Provide efficacy ranking, optimal combinations, and dosing strategies.""",
    
    "disease_progression_modeling": """Model disease progression for {disease_type} patient:
Baseline data: {baseline_data}
Historical progression: {historical_data}
Risk factors: {risk_factors}
Generate 5-year progression forecast with confidence intervals and intervention impact assessment."""
}

INTEGRATION_POINTS = {
    "clinicaltrials_gov": {
        "type": "api",
        "endpoint": "https://clinicaltrials.gov/api/v2",
        "description": "Clinical trials database for matching patients to relevant studies",
        "auth_method": "none",
        "documentation_url": "https://clinicaltrials.gov/api"
    },
    "pubmed_api": {
        "type": "api",
        "endpoint": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
        "description": "PubMed database for research literature and biomarker studies",
        "auth_method": "api_key",
        "documentation_url": "https://www.ncbi.nlm.nih.gov/books/NBK25501/"
    },
    "drugbank_api": {
        "type": "api",
        "endpoint": "https://go.drugbank.com/api",
        "description": "Drug interaction and pharmacology database",
        "auth_method": "api_key",
        "documentation_url": "https://go.drugbank.com/api"
    },
    "neurobank_db": {
        "type": "database",
        "endpoint": "postgresql://neurobank.revvel.ai:5432/neurodegenerative",
        "description": "Internal database of neurodegenerative disease research data",
        "auth_method": "oauth2",
        "documentation_url": "https://docs.revvel.ai/neurobank"
    },
    "biomarker_tracker": {
        "type": "tool",
        "endpoint": "https://tools.revvel.ai/biomarker",
        "description": "Biomarker analysis and tracking tool",
        "auth_method": "jwt",
        "documentation_url": "https://docs.revvel.ai/biomarker-tracker"
    }
}

def parse_biomarker_data(raw_data: str) -> Dict[str, float]:
    """Parse biomarker data from various input formats."""
    biomarkers = {}
    lines = raw_data.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or ':' not in line:
            continue
            
        parts = line.split(':')
        if len(parts) >= 2:
            name = parts[0].strip().lower()
            try:
                value = float(parts[1].strip().split()[0])
                biomarkers[name] = value
            except (ValueError, IndexError):
                continue
                
    return biomarkers

def validate_biomarker_ranges(biomarkers: Dict[str, float], disease_type: str) -> Dict[str, str]:
    """Validate biomarker values against normal ranges for specific diseases."""
    ranges = {
        "parkinsons": {
            "alpha_synuclein": (0.1, 2.5),
            "dopamine": (0.5, 4.0),
            "homovanillic_acid": (5.0, 25.0),
            "3-methoxytyrosine": (10.0, 50.0)
        },
        "alzheimers": {
            "amyloid_beta_42": (200, 1200),
            "tau_protein": (80, 450),
            "p_tau_181": (15, 85),
            "apo_e4": (0, 1)
        }
    }
    
    results = {}
    disease_ranges = ranges.get(disease_type.lower(), {})
    
    for marker, value in biomarkers.items():
        if marker in disease_ranges:
            min_val, max_val = disease_ranges[marker]
            if value < min_val:
                results[marker] = "low"
            elif value > max_val:
                results[marker] = "high"
            else:
                results[marker] = "normal"
        else:
            results[marker] = "unknown"
            
    return results

def calculate_disease_progression_score(biomarkers: Dict[str, float], disease_type: str) -> float:
    """Calculate composite disease progression score from biomarkers."""
    weights = {
        "parkinsons": {
            "alpha_synuclein": 0.4,
            "dopamine": 0.3,
            "homovanillic_acid": 0.2,
            "3-methoxytyrosine": 0.1
        },
        "alzheimers": {
            "amyloid_beta_42": 0.35,
            "tau_protein": 0.35,
            "p_tau_181": 0.2,
            "apo_e4": 0.1
        }
    }
    
    disease_weights = weights.get(disease_type.lower(), {})
    score = 0.0
    
    for marker, weight in disease_weights.items():
        if marker in biomarkers:
            normalized_value = biomarkers[marker] / 100.0 if biomarkers[marker] > 1 else biomarkers[marker]
            score += normalized_value * weight
            
    return min(score, 1.0)

def generate_treatment_recommendations(disease_type: str, disease_stage: str, biomarkers: Dict[str, float]) -> List[Dict[str, Any]]:
    """Generate personalized treatment recommendations based on disease and biomarkers."""
    recommendations = []
    
    if disease_type.lower() == "parkinsons":
        if disease_stage == "early":
            recommendations.append({
                "drug": "levodopa/carbidopa",
                "dosage": "25/100 mg TID",
                "rationale": "First-line therapy for motor symptoms",
                "monitoring": "Dyskinesia, motor fluctuations"
            })
            if biomarkers.get("alpha_synuclein", 0) > 1.5:
                recommendations.append({
                    "drug": "rasagiline",
                    "dosage": "1 mg daily",
                    "rationale": "MAO-B inhibitor for neuroprotection",
                    "monitoring": "Liver function, blood pressure"
                })
        elif disease_stage == "moderate":
            recommendations.append({
                "drug": "levodopa/carbidopa CR",
                "dosage": "50/200 mg BID",
                "rationale": "Controlled release for sustained benefit",
                "monitoring": "Motor fluctuations, dyskinesia"
            })
            
    elif disease_type.lower() == "alzheimers":
        if disease_stage == "early":
            recommendations.append({
                "drug": "donepezil",
                "dosage": "5 mg daily",
                "rationale": "Cholinesterase inhibitor for cognitive symptoms",
                "monitoring": "GI side effects, bradycardia"
            })
            if biomarkers.get("amyloid_beta_42", 0) < 400:
                recommendations.append({
                    "drug": "aducanumab",
                    "dosage": "10 mg/kg monthly",
                    "rationale": "Amyloid-targeting therapy",
                    "monitoring": "ARIA, headache"
                })
                
    return recommendations

def analyze_drug_interactions(current_meds: List[str], proposed_drugs: List[str]) -> List[Dict[str, Any]]:
    """Analyze potential drug interactions."""
    interactions = []
    
    known_interactions = {
        ("levodopa", "haloperidol"): "Antagonizes levodopa effect",
        ("selegiline", "meperidine"): "Risk of serotonin syndrome",
        ("donepezil", "anticholinergics"): "Reduced efficacy of both drugs",
        ("warfarin", "donepezil"): "Increased bleeding risk",
        ("amiodarone", "levodopa"): "Increased levodopa toxicity"
    }
    
    all_drugs = set(current_meds + proposed_drugs)
    
    for (drug1, drug2), interaction in known_interactions.items():
        if drug1 in all_drugs and drug2 in all_drugs:
            interactions.append({
                "drugs": [drug1, drug2],
                "severity": "high",
                "mechanism": interaction,
                "recommendation": "Avoid concurrent use or monitor closely"
            })
            
    return interactions

def build_clinical_trial_query(disease_type: str, criteria: Dict[str, Any]) -> str:
    """Build optimized query for clinical trial databases."""
    base_query = f"{disease_type} neurodegenerative"
    
    if criteria.get("stage"):
        base_query += f" {criteria['stage']}"
    if criteria.get("biomarker"):
        base_query += f" {criteria['biomarker']}"
    if criteria.get("intervention"):
        base_query += f" {criteria['intervention']}"
        
    return base_query

def generate_lifestyle_protocol(disease_type: str, patient_age: int, comorbidities: List[str]) -> Dict[str, Any]:
    """Generate personalized lifestyle intervention protocol."""
    protocol = {
        "exercise": {
            "type": "aerobic + resistance",
            "frequency": "5 days/week",
            "duration": "30-45 minutes",
            "intensity": "moderate"
        },
        "diet": {
            "pattern": "Mediterranean",
            "key_components": ["omega-3", "antioxidants", "low saturated fat"],
            "restrictions": []
        },
        "cognitive_training": {
            "frequency": "3-4 days/week",
            "activities": ["memory games", "problem solving", "learning new skills"],
            "duration": "20-30 minutes"
        }
    }
    
    if disease_type.lower() == "alzheimers":
        protocol["diet"]["key_components"].extend(["curcumin", "vitamin E"])
        protocol["cognitive_training"]["activities"].append("meditation")
        
    if patient_age > 75:
        protocol["exercise"]["intensity"] = "light-moderate"
        protocol["exercise"]["duration"] = "20-30 minutes"
        
    if "diabetes" in comorbidities:
        protocol["diet"]["restrictions"].append("low glycemic index")
        
    return protocol

def calculate_neuroprotective_score(compounds: List[str], target_pathways: List[str]) -> Dict[str, float]:
    """Calculate neuroprotective efficacy scores for compounds."""
    efficacy_data = {
        "coenzyme_q10": {"oxidative_stress": 0.8, "mitochondrial": 0.7, "anti-inflammatory": 0.6},
        "curcumin": {"anti-inflammatory": 0.9, "oxidative_stress": 0.8, "amyloid": 0.7},
        "omega3": {"anti-inflammatory": 0.8, "membrane": 0.7, "oxidative_stress": 0.6},
        "vitamin_e": {"oxidative_stress": 0.9, "membrane": 0.6, "anti-inflammatory": 0.5},
        "resveratrol": {"anti-inflammatory": 0.7, "oxidative_stress": 0.8, "longevity": 0.6}
    }
    
    scores = {}
    for compound in compounds:
        compound_lower = compound.lower().replace("-", "").replace("_", "")
        if compound_lower in efficacy_data:
            compound_scores = efficacy_data[compound_lower]
            total_score = sum(compound_scores.get(pathway, 0.0) for pathway in target_pathways)
            scores[compound] = round(total_score / max(len(target_pathways), 1), 3)
        else:
            scores[compound] = 0.0
    
    return scores


class SkillEngine:
    """Neurodegenerative Disease Formulations skill engine."""
    
    def __init__(self):
        self.name = SKILL_METADATA['name']
        self.version = SKILL_METADATA['version']
    
    def run(self, action: str, **kwargs) -> Dict[str, Any]:
        actions = {
            'biomarker_tracking': lambda: track_biomarkers(**kwargs),
            'drug_interaction': lambda: check_drug_interactions(**kwargs),
            'clinical_trial': lambda: search_clinical_trials(**kwargs),
            'neuroprotective_score': lambda: calculate_neuroprotective_score(**kwargs),
            'lifestyle_protocol': lambda: generate_lifestyle_protocol(**kwargs),
        }
        if action in actions:
            return actions[action]()
        return {'error': f'Unknown action: {action}'}


class TestNeurodegenerative(unittest.TestCase):
    """Unit tests for Neurodegenerative Disease skill."""
    
    def test_metadata(self):
        self.assertEqual(SKILL_METADATA['id'], 'neurodegenerative')
    
    def test_neuroprotective_score(self):
        result = calculate_neuroprotective_score(
            compounds=['curcumin', 'omega3'],
            target_pathways=['anti-inflammatory', 'oxidative_stress']
        )
        self.assertIn('curcumin', result)
        self.assertGreater(result['curcumin'], 0)
    
    def test_unknown_compound(self):
        result = calculate_neuroprotective_score(
            compounds=['unknown_drug'],
            target_pathways=['anti-inflammatory']
        )
        self.assertEqual(result['unknown_drug'], 0.0)
    
    def test_lifestyle_protocol(self):
        result = generate_lifestyle_protocol(
            disease_type='parkinsons',
            patient_age=65,
            comorbidities=[]
        )
        self.assertIn('exercise', result)
        self.assertIn('diet', result)
    
    def test_prompts_exist(self):
        self.assertGreater(len(EXPERT_PROMPTS), 0)
    
    def test_integration_points(self):
        self.assertIn('pubmed', INTEGRATION_POINTS)
    
    def test_skill_engine(self):
        engine = SkillEngine()
        self.assertEqual(engine.name, 'Neurodegenerative Disease Formulations')
    
    def test_engine_unknown_action(self):
        engine = SkillEngine()
        result = engine.run('nonexistent')
        self.assertIn('error', result)
    
    def test_elderly_protocol(self):
        result = generate_lifestyle_protocol(
            disease_type='alzheimers',
            patient_age=80,
            comorbidities=['diabetes']
        )
        self.assertEqual(result['exercise']['intensity'], 'light-moderate')
    
    def test_empty_compounds(self):
        result = calculate_neuroprotective_score(compounds=[], target_pathways=['anti-inflammatory'])
        self.assertEqual(len(result), 0)


if __name__ == '__main__':
    unittest.main()