import json
import re
import math
import hashlib
import statistics
import unittest
import datetime
import requests
import os
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