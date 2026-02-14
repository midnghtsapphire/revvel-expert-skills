# Revvel Expert Skills - 40 Custom Skills
# Auto-generated skill registry

import importlib
import os
import sys

SKILL_MODULES = [
    "advanced_manufacturing",
    "anti_aging",
    "biocomposites_formulation",
    "business_operations",
    "cardiovascular",
    "caselaw_expert",
    "cold_case_analysis",
    "dna_forensics",
    "drone_operator",
    "elite_cybersecurity",
    "epstein_files_intel",
    "expert_witness",
    "forensic_accounting",
    "fullstack_app_developer",
    "glaucoma_ophthalmology",
    "government_gis",
    "government_resources",
    "gpr_body_detection",
    "hawaiian_genealogy",
    "historical_research",
    "legal_brief_writing",
    "lexisnexis_integration",
    "lidar_expert",
    "mechanical_engineering",
    "medical_doctor",
    "medical_expert_witness",
    "nanotech_surgery",
    "neurodegenerative",
    "patent_ip",
    "portuguese_maori_genealogy",
    "precog_analysis",
    "satellite_remote_sensing",
    "stealth_inventory",
    "stealth_lead_gen",
    "tax_automation",
    "trafficking_intel",
    "transplant_surgery",
    "twilio_call_center",
    "victim_advocacy",
    "web_scraper",
]

_loaded_skills = {}
_load_errors = {}


def load_all_skills():
    """Load all skill modules and return loaded count."""
    global _loaded_skills, _load_errors
    _loaded_skills = {}
    _load_errors = {}
    
    for module_name in SKILL_MODULES:
        try:
            mod = importlib.import_module(f"skills.{module_name}")
            if hasattr(mod, 'SKILL_METADATA'):
                _loaded_skills[module_name] = mod
            else:
                _load_errors[module_name] = "Missing SKILL_METADATA"
        except Exception as e:
            _load_errors[module_name] = str(e)
    
    return len(_loaded_skills), len(_load_errors)


def get_skill(name):
    """Get a loaded skill module by name."""
    return _loaded_skills.get(name)


def get_all_skills():
    """Get all loaded skill modules."""
    return dict(_loaded_skills)


def get_errors():
    """Get all load errors."""
    return dict(_load_errors)


def get_skill_catalog():
    """Get catalog of all loaded skills."""
    catalog = []
    for name, mod in _loaded_skills.items():
        meta = mod.SKILL_METADATA
        catalog.append({
            "id": meta.get("id", name),
            "name": meta.get("name", name),
            "version": meta.get("version", "1.0.0"),
            "description": meta.get("description", ""),
            "capabilities": meta.get("capabilities", []),
        })
    return catalog
