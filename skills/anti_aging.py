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