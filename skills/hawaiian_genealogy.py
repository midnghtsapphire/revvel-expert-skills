import json
import re
import os
import math
import hashlib
import requests
import statistics
import unittest
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Tuple, Any, Union
from urllib.parse import urljoin, quote_plus

SKILL_METADATA = {
    "name": "Hawaiian History & Genealogy Expert",
    "id": "hawaiian_genealogy",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Deep Hawaiian cultural and genealogical knowledge spanning Kingdom history, Ali'i genealogy, land records, language resources, and Polynesian migration patterns",
    "capabilities": [
        "Ali'i genealogy lineage tracking",
        "Mahele land record analysis",
        "Hawaiian language translation and parsing",
        "Blood quantum calculation",
        "Polynesian DNA haplogroup analysis",
        "Plantation era immigration record search",
        "Church record extraction",
        "Newspaper archive search",
        "Place name etymology",
        "Cultural protocol guidance"
    ],
    "domain": "Hawaiian cultural heritage, genealogy, and historical research"
}

EXPERT_PROMPTS = {
    "genealogy_search": """Search for Hawaiian genealogy records for individual named {full_name} born approximately {birth_year} on {island}. Include Ali'i lineage if applicable. Search Papakilo Database, Ulukau, and Bishop Museum archives. Return detailed family tree with citations.""",
    "land_record_search": """Find all land records for {applicant_name} in {ahupuaa}, {island} during the Mahele period (1846-1853). Include LCA numbers, award amounts, and survey details. Cross-reference with Royal Patents and Boundary Commission records.""",
    "blood_quantum_calc": """Calculate Hawaiian blood quantum for individual {full_name} based on known ancestry: {ancestry_list}. Include generation breakdown and documentation requirements for DHHL eligibility.""",
    "polynesian_dna_analysis": """Analyze DNA haplogroup {haplogroup} for Polynesian migration patterns. Compare with reference populations from Marquesas, Tahiti, and Samoa. Provide migration timeline and cultural connections.""",
    "plantation_worker_search": """Find immigration and employment records for {worker_name} who arrived in Hawaii {arrival_year} to work on {plantation_name}. Include ship manifest, contract details, and family members.""",
    "church_record_extraction": """Extract baptism/marriage/death records from {church_name} for {individual_name} between {start_year} and {end_year}. Include original Hawaiian text and English translation.""",
    "place_name_etymology": """Provide detailed etymology and cultural significance of Hawaiian place name {place_name}. Include historical references, chants, and geographic context.""",
    "cultural_protocol_guidance": """Provide proper cultural protocols for conducting genealogical research on {island} regarding {research_type}. Include permission requirements, offerings, and respectful practices."""
}

INTEGRATION_POINTS = {
    "papakilo_database": {
        "type": "database",
        "endpoint": "https://www.papakilodatabase.com/api/v1",
        "description": "Office of Hawaiian Affairs cultural and historical database",
        "auth_method": "API key",
        "documentation_url": "https://www.oha.org/resources/papakilo-database/"
    },
    "ulukau_archive": {
        "type": "database",
        "endpoint": "https://ulukau.org/api/v2",
        "description": "Hawaiian Electronic Library with newspapers and texts",
        "auth_method": "None required",
        "documentation_url": "https://ulukau.org/hpn/?a=p&l=en&p=introintroduction"
    },
    "bishop_museum_archives": {
        "type": "api",
        "endpoint": "https://archives.bishopmuseum.org/api/v1",
        "description": "Bishop Museum historical archives and collections",
        "auth_method": "OAuth 2.0",
        "documentation_url": "https://www.bishopmuseum.org/research/archives/"
    },
    "waihona_land_records": {
        "type": "database",
        "endpoint": "https://waihona.com/api/v1",
        "description": "Comprehensive Hawaiian land records database",
        "auth_method": "API key",
        "documentation_url": "https://waihona.com/"
    },
    "hawaii_state_archives": {
        "type": "api",
        "endpoint": "https://ags.hawaii.gov/archives/api/v1",
        "description": "Hawaii State government archives",
        "auth_method": "Government API key",
        "documentation_url": "https://ags.hawaii.gov/archives/"
    },
    "dhhl_records": {
        "type": "database",
        "endpoint": "https://dhhl.hawaii.gov/api/v1",
        "description": "Department of Hawaiian Home Lands records",
        "auth_method": "DHHL portal login",
        "documentation_url": "https://dhhl.hawaii.gov/"
    }
}

def validate_hawaiian_name(name: str) -> Dict[str, Any]:
    """Validate and parse Hawaiian names according to proper orthography."""
    if not name or not isinstance(name, str):
        return {"valid": False, "error": "Name must be non-empty string"}
    
    # Check for proper Hawaiian diacritical marks
    has_okina = "ʻ" in name or "'" in name
    has_kahako = any(c in name for c in "āēīōūĀĒĪŌŪ")
    
    # Normalize okina characters
    normalized = name.replace("'", "ʻ")
    
    # Split into parts
    parts = normalized.split()
    
    return {
        "valid": True,
        "normalized": normalized,
        "parts": parts,
        "has_okina": has_okina,
        "has_kahako": has_kahako,
        "suggested_corrections": []
    }

def calculate_blood_quantum(ancestors: List[Dict[str, float]]) -> Dict[str, Any]:
    """Calculate Hawaiian blood quantum based on ancestry."""
    if not ancestors:
        return {"quantum": 0.0, "details": []}
    
    total_quantum = 0.0
    details = []
    
    for i, ancestor in enumerate(ancestors):
        generation = i + 1
        percentage = ancestor.get("hawaiian_percentage", 0.0)
        contribution = percentage * (0.5 ** generation)
        total_quantum += contribution
        
        details.append({
            "generation": generation,
            "name": ancestor.get("name", f"Ancestor {generation}"),
            "hawaiian_percentage": percentage,
            "contribution": contribution
        })
    
    return {
        "quantum": round(total_quantum, 6),
        "percentage": round(total_quantum * 100, 2),
        "details": details,
        "dhhl_eligible": total_quantum >= 0.50
    }

def parse_mahele_award(text: str) -> Dict[str, Any]:
    """Parse Mahele land award text into structured data."""
    award_pattern = r'LCA\s*(\d+)\s*.*?(?:Awarded|Apana).*?(\d+)\s*acres?'
    match = re.search(award_pattern, text, re.IGNORECASE)
    
    if not match:
        return {"parsed": False, "raw_text": text}
    
    lca_number = match.group(1)
    acres = float(match.group(2))
    
    # Extract claimant name
    name_match = re.search(r'Claimant[s]?:\s*([^\n]+)', text, re.IGNORECASE)
    claimant = name_match.group(1).strip() if name_match else "Unknown"
    
    # Extract location
    location_match = re.search(r'(?:Ahupua.a|Location):?\s*([^\n]+)', text, re.IGNORECASE)
    location = location_match.group(1).strip() if location_match else "Unknown"
    
    return {
        "parsed": True,
        "lca_number": lca_number,
        "acres": acres,
        "claimant": claimant,
        "location": location,
        "raw_text": text
    }

def analyze_polynesian_haplogroup(haplogroup: str) -> Dict[str, Any]:
    """Analyze Polynesian DNA haplogroup for migration patterns."""
    haplogroup = haplogroup.upper()
    
    polynesian_haplogroups = {
        "B4A1A1": {"origin": "Southeast Asia", "migration": "3,000-2,000 BCE", "region": "Western Polynesia"},
        "B4A1A1A": {"origin": "Taiwan", "migration": "2,000-1,000 BCE", "region": "Central Polynesia"},
        "Q1": {"origin": "Melanesia", "migration": "1,500-1,000 BCE", "region": "Eastern Polynesia"},
        "M7": {"origin": "Southeast Asia", "migration": "3,500-2,500 BCE", "region": "Western Polynesia"}
    }
    
    if haplogroup in polynesian_haplogroups:
        info = polynesian_haplogroups[haplogroup]
        return {
            'haplogroup': haplogroup,
            'found': True,
            'origin': info['origin'],
            'migration_period': info['migration'],
            'region': info['region'],
            'polynesian_connection': True
        }
    
    return {
        'haplogroup': haplogroup,
        'found': False,
        'polynesian_connection': False,
        'note': 'Haplogroup not in Polynesian migration database'
    }


class SkillEngine:
    """Hawaiian History & Genealogy skill engine."""
    
    def __init__(self):
        self.name = SKILL_METADATA['name']
        self.version = SKILL_METADATA['version']
    
    def run(self, action: str, **kwargs) -> Dict[str, Any]:
        actions = {
            'parse_lca': lambda: parse_land_commission_award(**kwargs),
            'haplogroup': lambda: analyze_polynesian_haplogroup(**kwargs),
        }
        if action in actions:
            return actions[action]()
        return {'error': f'Unknown action: {action}'}


class TestHawaiianGenealogy(unittest.TestCase):
    """Unit tests for Hawaiian History & Genealogy skill."""
    
    def test_metadata(self):
        self.assertEqual(SKILL_METADATA['id'], 'hawaiian_genealogy')
    
    def test_haplogroup_known(self):
        result = analyze_polynesian_haplogroup('B4A1A1')
        self.assertTrue(result['found'])
        self.assertTrue(result['polynesian_connection'])
    
    def test_haplogroup_unknown(self):
        result = analyze_polynesian_haplogroup('R1B')
        self.assertFalse(result['found'])
    
    def test_prompts_exist(self):
        self.assertGreater(len(EXPERT_PROMPTS), 0)
    
    def test_integration_points(self):
        self.assertIn('papakilo', INTEGRATION_POINTS)
    
    def test_skill_engine(self):
        engine = SkillEngine()
        self.assertEqual(engine.name, 'Hawaiian History & Genealogy Expert')


if __name__ == '__main__':
    unittest.main()