import json
import os
import re
import math
import hashlib
import requests
import statistics
import unittest
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
from urllib.parse import urlencode, quote

SKILL_METADATA = {
    "name": "Anti-Aging Research & Formulations",
    "id": "anti_aging",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Comprehensive analysis and formulation tools for anti-aging research including telomere biology, NAD+ precursors, senolytics, epigenetic clocks, and clinical trial data mining.",
    "capabilities": [
        "telomere_length_analysis",
        "nad_precursor_formulation",
        "senolytic_compound_analysis",
        "epigenetic_clock_calculation",
        "clinical_trial_search",
        "supplement_interaction_check",
        "peptide_therapy_research",
        "mitochondrial_support_analysis",
        "skin_aging_compound_evaluation",
        "caloric_restriction_mimetic profiling"
    ],
    "domain": "longevity_geroscience"
}

EXPERT_PROMPTS = {
    "telomere_analysis": """Analyze telomere length data for {sample_size} subjects aged {age_range} years.
    Data format: {data_format} (tsv/csv/json)
    Include statistical significance testing and correlation with {biomarkers}.
    Focus on {target_population} population.
    Output: comprehensive report with p-values, confidence intervals, and biological interpretation.""",
    
    "nad_formulation": """Design optimal NAD+ precursor formulation for {target_demographic} with {health_conditions}.
    Constraints: {constraints} (budget/dosage/form factor)
    Include synergistic compounds: {synergists}
    Avoid interactions: {avoid_list}
    Provide dosing schedule and expected biomarker changes.""",
    
    "senolytic_screening": """Screen {compound_library} for senolytic activity using {cell_lines} cell lines.
    Criteria: {selection_criteria} (IC50, selectivity index, toxicity threshold)
    Include validation assays: {validation_methods}
    Output: ranked list with mechanism of action and safety profile.""",
    
    "epigenetic_clock": """Calculate epigenetic age acceleration for {sample_id} using {clock_type} clock.
    Input data: {methylation_data} (450k/850k array formats)
    Include reference cohort: {reference_population}
    Report: age acceleration, confidence intervals, biological age interpretation.""",
    
    "clinical_trial_query": """Search ClinicalTrials.gov for {condition} trials with interventions {interventions}.
    Filters: phase {phase}, status {status}, age {age_range}, location {geography}
    Extract: primary endpoints, biomarkers, inclusion criteria, contact info
    Output: structured summary with risk assessment.""",
    
    "supplement_interaction": """Analyze interactions between {supplement_list} in {subject_profile}.
    Include pharmacokinetics, synergies, antagonisms, contraindications
    Dosing protocol: {dosing_schedule}
    Safety threshold: {safety_limit}
    Output: interaction matrix with clinical recommendations.""",
    
    "peptide_therapy": """Research peptide therapy protocol for {indication} in {patient_population}.
    Peptides of interest: {peptide_list}
    Include: mechanisms, dosing, cycling, side effects, monitoring biomarkers
    Reference studies: {study_criteria}
    Output: evidence-based protocol with safety profile.""",
    
    "mitochondrial_support": """Evaluate mitochondrial support compounds for {target_tissue} in {disease_state}.
    Compounds: {compound_list}
    Assess: bioavailability, tissue specificity, clinical evidence
    Include: dosing optimization, biomarker monitoring, combination strategies
    Output: ranked recommendations with mechanism rationale."""
}

INTEGRATION_POINTS = {
    "clinicaltrials_gov": {
        "type": "api",
        "endpoint": "https://clinicaltrials.gov/api/query/study_fields",
        "description": "Clinical trials database for aging interventions",
        "auth_method": "none",
        "documentation_url": "https://clinicaltrials.gov/api/"
    },
    "druggage_db": {
        "type": "database",
        "endpoint": "https://genomics.senescence.info/drugs/",
        "description": "Curated database of aging-related drugs",
        "auth_method": "none",
        "documentation_url": "https://genomics.senescence.info/drugs/help.html"
    },
    "hald_knowledge_graph": {
        "type": "api",
        "endpoint": "https://bis.zju.edu.cn/hald/api",
        "description": "Human aging and longevity knowledge graph",
        "auth_method": "api_key",
        "documentation_url": "https://bis.zju.edu.cn/hald/help"
    },
    "pubmed_search": {
        "type": "api",
        "endpoint": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        "description": "PubMed literature search for aging research",
        "auth_method": "none",
        "documentation_url": "https://www.ncbi.nlm.nih.gov/books/NBK25501/"
    }
}

def validate_telomere_data(data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """Validate telomere length measurement data format and completeness."""
    errors = []
    required_fields = ['subject_id', 'telomere_length', 'age', 'measurement_method']
    
    if not data:
        return False, ["No data provided"]
    
    for i, record in enumerate(data):
        for field in required_fields:
            if field not in record:
                errors.append(f"Record {i}: missing required field '{field}'")
        
        if 'telomere_length' in record:
            try:
                length = float(record['telomere_length'])
                if length <= 0 or length > 50:
                    errors.append(f"Record {i}: telomere_length {length} out of range (0-50 kb)")
            except (ValueError, TypeError):
                errors.append(f"Record {i}: invalid telomere_length value")
        
        if 'age' in record:
            try:
                age = float(record['age'])
                if age < 0 or age > 150:
                    errors.append(f"Record {i}: age {age} out of range")
            except (ValueError, TypeError):
                errors.append(f"Record {i}: invalid age value")
    
    return len(errors) == 0, errors


def calculate_biological_age(chronological_age: float, telomere_length: float,
                             epigenetic_clock: float = None, nad_level: float = None) -> Dict[str, Any]:
    """Estimate biological age from multiple biomarkers."""
    # Average telomere length at birth ~11kb, loses ~50bp/year
    telomere_age_estimate = (11.0 - telomere_length) / 0.05 if telomere_length > 0 else chronological_age
    
    estimates = [telomere_age_estimate]
    if epigenetic_clock is not None:
        estimates.append(epigenetic_clock)
    if nad_level is not None:
        # NAD+ declines ~50% by age 50
        nad_age_estimate = 50.0 * (1.0 - nad_level / 100.0) * 2
        estimates.append(nad_age_estimate)
    
    biological_age = sum(estimates) / len(estimates)
    age_difference = chronological_age - biological_age
    
    return {
        'chronological_age': chronological_age,
        'biological_age': round(biological_age, 1),
        'age_difference': round(age_difference, 1),
        'aging_status': 'younger' if age_difference > 0 else 'older',
        'telomere_age_estimate': round(telomere_age_estimate, 1),
        'estimates_used': len(estimates)
    }


def recommend_interventions(biological_age: float, chronological_age: float,
                            biomarkers: Dict[str, float] = None) -> List[Dict[str, Any]]:
    """Recommend anti-aging interventions based on biomarker analysis."""
    interventions = []
    
    if biological_age > chronological_age:
        interventions.append({
            'category': 'NAD+ Precursors',
            'compounds': ['NMN (250-500mg/day)', 'NR (300-600mg/day)'],
            'evidence_level': 'moderate',
            'mechanism': 'Restore NAD+ levels to support cellular repair'
        })
        interventions.append({
            'category': 'Senolytics',
            'compounds': ['Fisetin (500mg intermittent)', 'Quercetin + Dasatinib (intermittent)'],
            'evidence_level': 'emerging',
            'mechanism': 'Clear senescent cells that drive aging'
        })
    
    interventions.append({
        'category': 'Caloric Restriction Mimetics',
        'compounds': ['Rapamycin (low-dose, intermittent)', 'Metformin (500-1000mg/day)', 'Resveratrol (250-500mg/day)'],
        'evidence_level': 'moderate-strong',
        'mechanism': 'Activate longevity pathways (mTOR, AMPK, sirtuins)'
    })
    
    interventions.append({
        'category': 'Telomere Support',
        'compounds': ['TA-65', 'Astragaloside IV', 'Cycloastragenol'],
        'evidence_level': 'emerging',
        'mechanism': 'Support telomerase activity'
    })
    
    return interventions


def analyze_supplement_stack(supplements: List[Dict[str, str]]) -> Dict[str, Any]:
    """Analyze an anti-aging supplement stack for interactions and efficacy."""
    known_interactions = {
        ('metformin', 'berberine'): 'Both activate AMPK — may cause hypoglycemia together',
        ('rapamycin', 'metformin'): 'Both affect mTOR/AMPK — use with medical supervision',
        ('blood_thinners', 'omega3'): 'Increased bleeding risk'
    }
    
    warnings = []
    supplement_names = [s.get('name', '').lower() for s in supplements]
    
    for (a, b), warning in known_interactions.items():
        if a in supplement_names and b in supplement_names:
            warnings.append({'compounds': [a, b], 'warning': warning})
    
    return {
        'total_supplements': len(supplements),
        'interactions_found': len(warnings),
        'warnings': warnings,
        'supplements': supplements
    }


class SkillEngine:
    """Anti-Aging Research skill engine."""
    
    def __init__(self):
        self.name = SKILL_METADATA['name']
        self.version = SKILL_METADATA['version']
    
    def run(self, action: str, **kwargs) -> Dict[str, Any]:
        actions = {
            'validate_telomere': lambda: validate_telomere_data(**kwargs),
            'biological_age': lambda: calculate_biological_age(**kwargs),
            'interventions': lambda: recommend_interventions(**kwargs),
            'supplement_analysis': lambda: analyze_supplement_stack(**kwargs),
        }
        if action in actions:
            return actions[action]()
        return {'error': f'Unknown action: {action}'}


class TestAntiAging(unittest.TestCase):
    """Unit tests for Anti-Aging Research skill."""
    
    def test_metadata(self):
        self.assertEqual(SKILL_METADATA['id'], 'anti_aging')
    
    def test_validate_telomere_data(self):
        data = [{'subject_id': '001', 'telomere_length': 7.5, 'age': 45, 'measurement_method': 'qPCR'}]
        valid, errors = validate_telomere_data(data)
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_empty_data(self):
        valid, errors = validate_telomere_data([])
        self.assertFalse(valid)
    
    def test_biological_age(self):
        result = calculate_biological_age(chronological_age=50, telomere_length=7.0)
        self.assertIn('biological_age', result)
        self.assertIn('aging_status', result)
    
    def test_interventions(self):
        result = recommend_interventions(biological_age=55, chronological_age=50)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
    
    def test_supplement_analysis(self):
        supplements = [{'name': 'NMN', 'dose': '500mg'}, {'name': 'Resveratrol', 'dose': '250mg'}]
        result = analyze_supplement_stack(supplements)
        self.assertEqual(result['total_supplements'], 2)
    
    def test_skill_engine(self):
        engine = SkillEngine()
        self.assertEqual(engine.name, 'Anti-Aging Research & Formulations')
    
    def test_prompts_exist(self):
        self.assertGreater(len(EXPERT_PROMPTS), 0)


if __name__ == '__main__':
    unittest.main()