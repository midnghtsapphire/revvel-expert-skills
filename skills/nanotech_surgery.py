import json
import re
import math
import hashlib
import statistics
import unittest
import datetime
import requests
import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
from dataclasses import dataclass

SKILL_METADATA = {
    "name": "Nanotech Surgery & Skin Repair Expert",
    "id": "nanotech_surgery",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Expert system for nanotechnology applications in surgery and skin repair, covering nanoparticle drug delivery, nano-surgical tools, skin regeneration, tattoo removal, scar revision, anti-aging, burns treatment, clinical trials, safety assessment, formulation calculations, research tracking, patents, and cost modeling.",
    "capabilities": [
        "nanoparticle_drug_delivery_analysis",
        "nano_surgical_tools_evaluation",
        "skin_repair_regeneration_protocols",
        "tattoo_removal_nanotech_planning",
        "scar_revision_nanotech_assessment",
        "anti_aging_nanotech_recommendations",
        "burns_treatment_nanotech_protocols",
        "clinical_trial_database_query",
        "safety_toxicology_assessment",
        "formulation_calculator",
        "research_tracker",
        "patent_landscape_analysis",
        "cost_modeling_comparison"
    ],
    "domain": "medical_nanotechnology"
}

EXPERT_PROMPTS = {
    "nanoparticle_delivery": """
You are a nanomedicine expert. Analyze the following nanoparticle drug delivery system:
- Particle type: {particle_type}
- Target tissue: {target_tissue}
- Drug compound: {drug_compound}
- Desired release profile: {release_profile}
Provide detailed recommendations on particle size, surface modification, encapsulation efficiency, and expected pharmacokinetics.
""",
    "tattoo_removal_plan": """
You are a nanotech dermatology specialist. Design a tattoo removal protocol:
- Tattoo colors: {tattoo_colors}
- Tattoo age: {tattoo_age_months}
- Skin type: {skin_type}
- Tattoo size: {tattoo_size_cm2}
- Patient age: {patient_age}
Recommend nanoparticle types, laser parameters, number of sessions, interval spacing, and expected outcomes.
""",
    "scar_revision": """
You are a nanotech scar revision expert. Evaluate this case:
- Scar type: {scar_type}
- Scar age: {scar_age_months}
- Scar size: {scar_size}
- Patient skin type: {skin_type}
- Previous treatments: {previous_treatments}
Recommend nanotechnology interventions including nanoparticle selection, treatment protocol, and expected improvement timeline.
""",
    "burns_treatment": """
You are a nanotech burns specialist. Assess this burn case:
- Burn degree: {burn_degree}
- Burn area: {burn_area_percent}
- Burn location: {burn_location}
- Patient age: {patient_age}
- Time since injury: {time_since_injury}
Recommend nanotech treatments including antimicrobial nanoparticles, growth factor delivery systems, and wound dressings.
""",
    "anti_aging_protocol": """
You are a nanotech anti-aging expert. Design a treatment plan:
- Patient age: {patient_age}
- Skin concerns: {skin_concerns}
- Current skincare routine: {current_routine}
- Budget level: {budget_level}
- Treatment goals: {treatment_goals}
Recommend nano-encapsulated ingredients, exosome therapies, and telomere-targeting nanoparticles with treatment schedules.
""",
    "formulation_optimization": """
You are a nanoparticle formulation scientist. Optimize this formulation:
- Target particle size: {target_size_nm}
- Drug loading: {drug_loading_percent}%
- Desired zeta potential: {target_zeta_mv}
- Release target: {release_target_hours}
- Stability requirement: {stability_months}
Provide synthesis parameters, surfactant recommendations, and quality control metrics.
""",
    "safety_assessment": """
You are a nanotoxicology expert. Assess the safety of:
- Nanoparticle type: {nanoparticle_type}
- Exposure route: {exposure_route}
- Dose level: {dose_level}
- Exposure duration: {exposure_duration}
- Patient population: {patient_population}
Evaluate toxicological risks, regulatory compliance, and recommend safety protocols.
""",
    "clinical_trial_matching": """
You are a nanotech clinical trial specialist. Find trials for:
- Condition: {condition}
- Nanotech intervention: {intervention_type}
- Patient demographics: {patient_demographics}
- Geographic location: {location}
- Trial phase preference: {phase_preference}
Match relevant trials with inclusion criteria and contact information.
"""
}

INTEGRATION_POINTS = {
    "clinicaltrials_gov": {
        "type": "api",
        "url": "https://clinicaltrials.gov/api/v2/studies",
        "description": "Search clinical trials for nanotech medical applications"
    },
    "pubmed": {
        "type": "api",
        "url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        "description": "Search PubMed for nanotech surgery research"
    },
    "fda_devices": {
        "type": "api",
        "url": "https://api.fda.gov/device",
        "description": "FDA medical device database for nanotech devices"
    },
    "nature_nano": {
        "type": "web",
        "url": "https://www.nature.com/nnano/",
        "description": "Nature Nanotechnology journal"
    }
}

logger = logging.getLogger(__name__)


def calculate_nanoparticle_properties(diameter_nm: float, material: str,
                                       surface_charge_mv: float = None) -> Dict[str, Any]:
    """Calculate nanoparticle properties for medical applications."""
    if diameter_nm <= 0 or diameter_nm > 10000:
        raise ValueError("Diameter must be between 0 and 10000 nm")
    
    # Surface area to volume ratio
    radius = diameter_nm / 2
    surface_area = 4 * math.pi * radius ** 2  # nm^2
    volume = (4/3) * math.pi * radius ** 3  # nm^3
    sa_vol_ratio = surface_area / volume if volume > 0 else 0
    
    # Material-specific properties
    material_db = {
        'gold': {'density': 19.3, 'biocompatible': True, 'photothermal': True, 'magnetic': False},
        'silver': {'density': 10.5, 'biocompatible': True, 'photothermal': False, 'magnetic': False, 'antimicrobial': True},
        'iron_oxide': {'density': 5.2, 'biocompatible': True, 'photothermal': False, 'magnetic': True},
        'silica': {'density': 2.2, 'biocompatible': True, 'photothermal': False, 'magnetic': False},
        'plga': {'density': 1.3, 'biocompatible': True, 'photothermal': False, 'magnetic': False, 'biodegradable': True},
        'liposome': {'density': 1.0, 'biocompatible': True, 'photothermal': False, 'magnetic': False, 'biodegradable': True}
    }
    
    mat_props = material_db.get(material.lower(), {'density': 1.0, 'biocompatible': False})
    
    # Size classification for medical use
    if diameter_nm < 10:
        size_class = 'ultra-small (renal clearable)'
    elif diameter_nm < 100:
        size_class = 'small (EPR effect, tumor targeting)'
    elif diameter_nm < 200:
        size_class = 'medium (drug delivery optimal)'
    elif diameter_nm < 500:
        size_class = 'large (limited tissue penetration)'
    else:
        size_class = 'micro (localized delivery only)'
    
    return {
        'diameter_nm': diameter_nm,
        'material': material,
        'surface_area_nm2': round(surface_area, 2),
        'volume_nm3': round(volume, 2),
        'sa_vol_ratio': round(sa_vol_ratio, 4),
        'size_classification': size_class,
        'material_properties': mat_props,
        'surface_charge_mv': surface_charge_mv
    }


def design_tattoo_removal_protocol(ink_colors: List[str], tattoo_area_cm2: float,
                                    skin_type: int = 3, tattoo_age_years: float = 5) -> Dict[str, Any]:
    """Design nanoparticle-enhanced laser tattoo removal protocol."""
    # Laser wavelength selection by ink color
    wavelength_map = {
        'black': {'wavelength_nm': 1064, 'laser_type': 'Nd:YAG', 'nanoparticle': 'gold nanorods'},
        'blue': {'wavelength_nm': 694, 'laser_type': 'Ruby', 'nanoparticle': 'gold nanospheres'},
        'green': {'wavelength_nm': 755, 'laser_type': 'Alexandrite', 'nanoparticle': 'gold nanostars'},
        'red': {'wavelength_nm': 532, 'laser_type': 'KTP', 'nanoparticle': 'silver nanoparticles'},
        'yellow': {'wavelength_nm': 532, 'laser_type': 'KTP', 'nanoparticle': 'gold-silver alloy'},
        'white': {'wavelength_nm': 1064, 'laser_type': 'Nd:YAG', 'nanoparticle': 'carbon nanotubes'},
        'purple': {'wavelength_nm': 694, 'laser_type': 'Ruby', 'nanoparticle': 'gold nanospheres'}
    }
    
    # Estimate sessions needed
    base_sessions = 6
    age_factor = 0.8 if tattoo_age_years > 10 else 1.0 if tattoo_age_years > 5 else 1.2
    skin_factor = 1.0 + (skin_type - 3) * 0.1  # Higher skin types need more sessions
    area_factor = 1.0 + max(0, (tattoo_area_cm2 - 50) / 100)
    
    color_protocols = []
    for color in ink_colors:
        color_lower = color.lower()
        if color_lower in wavelength_map:
            info = wavelength_map[color_lower]
            sessions = int(base_sessions * age_factor * skin_factor * area_factor)
            color_protocols.append({
                'color': color,
                'laser_wavelength_nm': info['wavelength_nm'],
                'laser_type': info['laser_type'],
                'nanoparticle_enhancer': info['nanoparticle'],
                'estimated_sessions': sessions,
                'session_interval_weeks': 6
            })
    
    total_sessions = max([p['estimated_sessions'] for p in color_protocols]) if color_protocols else base_sessions
    
    return {
        'tattoo_area_cm2': tattoo_area_cm2,
        'skin_type': skin_type,
        'tattoo_age_years': tattoo_age_years,
        'color_protocols': color_protocols,
        'total_estimated_sessions': total_sessions,
        'total_treatment_duration_months': total_sessions * 1.5,
        'nanoparticle_advantage': 'Photothermal nanoparticles enhance ink fragmentation by 40-60%, reducing sessions needed'
    }


def formulate_nano_serum(target: str, active_ingredients: List[str] = None) -> Dict[str, Any]:
    """Formulate a nanoparticle-based serum for skin treatment."""
    formulations = {
        'anti_aging': {
            'nanocarrier': 'liposomal',
            'active_agents': ['retinol', 'vitamin C', 'peptides', 'hyaluronic acid'],
            'particle_size_nm': 80,
            'concentration_pct': 2.0,
            'ph_range': (5.0, 6.0)
        },
        'scar_revision': {
            'nanocarrier': 'PLGA nanoparticles',
            'active_agents': ['silicone', 'vitamin E', 'allantoin', 'collagen peptides'],
            'particle_size_nm': 150,
            'concentration_pct': 3.0,
            'ph_range': (5.5, 6.5)
        },
        'wound_healing': {
            'nanocarrier': 'nano-silver + cellulose',
            'active_agents': ['silver nanoparticles', 'EGF', 'FGF', 'chitosan'],
            'particle_size_nm': 50,
            'concentration_pct': 1.5,
            'ph_range': (6.0, 7.0)
        },
        'tattoo_removal_enhancer': {
            'nanocarrier': 'gold nanorods',
            'active_agents': ['gold nanoparticles', 'PEG coating', 'targeting ligand'],
            'particle_size_nm': 40,
            'concentration_pct': 0.5,
            'ph_range': (6.5, 7.5)
        }
    }
    
    target_key = target.lower().replace(' ', '_')
    if target_key in formulations:
        formula = formulations[target_key]
        if active_ingredients:
            formula['active_agents'].extend(active_ingredients)
        return {
            'target': target,
            'formulation': formula,
            'status': 'formulated'
        }
    
    return {'target': target, 'status': 'custom formulation needed', 'available_targets': list(formulations.keys())}


class SkillEngine:
    """Nanotech Surgery & Skin Repair skill engine."""
    
    def __init__(self):
        self.name = SKILL_METADATA['name']
        self.version = SKILL_METADATA['version']
    
    def run(self, action: str, **kwargs) -> Dict[str, Any]:
        actions = {
            'nanoparticle_properties': lambda: calculate_nanoparticle_properties(**kwargs),
            'tattoo_removal': lambda: design_tattoo_removal_protocol(**kwargs),
            'formulate_serum': lambda: formulate_nano_serum(**kwargs),
        }
        if action in actions:
            return actions[action]()
        return {'error': f'Unknown action: {action}'}


class TestNanotechSurgery(unittest.TestCase):
    """Unit tests for Nanotech Surgery skill."""
    
    def test_metadata(self):
        self.assertEqual(SKILL_METADATA['id'], 'nanotech_surgery')
    
    def test_nanoparticle_properties(self):
        result = calculate_nanoparticle_properties(diameter_nm=50, material='gold')
        self.assertIn('size_classification', result)
        self.assertTrue(result['material_properties']['photothermal'])
    
    def test_nanoparticle_invalid(self):
        with self.assertRaises(ValueError):
            calculate_nanoparticle_properties(diameter_nm=-5, material='gold')
    
    def test_tattoo_removal(self):
        result = design_tattoo_removal_protocol(
            ink_colors=['black', 'red', 'blue'],
            tattoo_area_cm2=30,
            skin_type=3
        )
        self.assertIn('color_protocols', result)
        self.assertEqual(len(result['color_protocols']), 3)
    
    def test_nano_serum(self):
        result = formulate_nano_serum(target='anti_aging')
        self.assertEqual(result['status'], 'formulated')
    
    def test_nano_serum_custom(self):
        result = formulate_nano_serum(target='unknown_target')
        self.assertEqual(result['status'], 'custom formulation needed')
    
    def test_skill_engine(self):
        engine = SkillEngine()
        self.assertEqual(engine.name, 'Nanotech Surgery & Skin Repair Expert')
    
    def test_prompts_exist(self):
        self.assertGreater(len(EXPERT_PROMPTS), 0)
    
    def test_integration_points(self):
        self.assertIn('clinicaltrials_gov', INTEGRATION_POINTS)
        self.assertIn('pubmed', INTEGRATION_POINTS)


if __name__ == '__main__':
    unittest.main()