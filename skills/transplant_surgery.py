import json
import re
import os
import math
import hashlib
import statistics
import unittest
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, namedtuple
import requests

SKILL_METADATA = {
    "name": "Transplant Surgery & Reconstructive Expert",
    "id": "transplant_surgery",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Comprehensive transplant and reconstructive surgery knowledge engine covering organ transplants, face/hand VCA procedures, reconstructive microsurgery, and cutting-edge regenerative medicine techniques.",
    "capabilities": [
        "organ_allocation_analysis",
        "donor_recipient_matching",
        "immunosuppression_protocols",
        "rejection_monitoring",
        "vca_surgical_planning",
        "microsurgical_planning",
        "outcome_prediction",
        "clinical_trial_tracker",
        "rehabilitation_planning",
        "ethical_framework_analysis"
    ],
    "domain": "transplant_surgery_reconstructive"
}

EXPERT_PROMPTS = {
    "organ_allocation": """Analyze organ allocation for {organ_type} transplant in {region} as of {date}.
Patient details: {patient_demographics}
Current MELD/PELD: {meldpeld_score}
Blood type: {blood_type}
HLA typing: {hla_typing}
PRA: {pra_level}%
Donor considerations: {donor_criteria}
Provide allocation probability, wait time estimates, and optimization strategies.""",
    
    "vca_planning": """Create comprehensive surgical plan for {vca_type} transplant.
Patient: {patient_age}yo {gender}, {injury_description}
3D imaging: {imaging_data}
Vascular anatomy: {vascular_details}
Nerve mapping: {nerve_data}
Donor matching: {donor_characteristics}
Include surgical approach, microvascular anastomosis plan, nerve coaptation strategy, and immunosuppression protocol.""",
    
    "rejection_risk": """Calculate rejection risk for {transplant_type} recipient.
Time post-transplant: {time_post_tx}
Current immunosuppression: {current_is}
DSA levels: {dsa_data}
Biopsy results: {biopsy_results}
Infection history: {infection_history}
Provide risk stratification and adjustment recommendations.""",
    
    "microsurgical_planning": """Design microsurgical reconstruction for {defect_type}.
Defect size: {defect_dimensions}cm
Location: {anatomical_location}
Available donor sites: {donor_sites}
Patient factors: {comorbidities}
Create flap selection rationale, pedicle geometry, and post-op monitoring plan.""",
    
    "rehabilitation_protocol": """Develop rehabilitation protocol for {procedure_type} recipient.
Days post-op: {postop_day}
Current function: {current_function}
Rejection episodes: {rejection_history}
Psychosocial factors: {psychosocial_status}
Design phased rehabilitation with milestones and therapy interventions.""",
    
    "clinical_trial_match": """Find relevant clinical trials for {condition} in {patient_population}.
Inclusion criteria: {inclusion_criteria}
Exclusion criteria: {exclusion_criteria}
Geographic preference: {location_preference}
Provide matching trials with enrollment status and contact information.""",
    
    "ethical_consult": """Evaluate ethical considerations for {procedure_type}.
Patient capacity: {capacity_assessment}
Donor consent: {donor_consent_status}
Risk-benefit ratio: {risk_benefit_analysis}
Alternative options: {alternatives}
Provide ethical framework and decision support.""",
    
    "outcome_prediction": """Predict 1-year and 5-year outcomes for {transplant_type}.
Patient factors: {patient_factors}
Donor factors: {donor_factors}
Surgical factors: {surgical_factors}
Immunologic factors: {immunologic_factors}
Provide probability estimates with confidence intervals."""
}

INTEGRATION_POINTS = {
    "unos_database": {
        "type": "api",
        "endpoint": "https://optn.transplant.hrsa.gov/data",
        "description": "UNOS/OPTN transplant database with waitlist and outcomes data",
        "auth_method": "api_key",
        "documentation_url": "https://optn.transplant.hrsa.gov/developers"
    },
    "srtr_reports": {
        "type": "database",
        "endpoint": "https://srtr.transplant.hrsa.gov/adr",
        "description": "Scientific Registry of Transplant Recipients annual data reports",
        "auth_method": "public",
        "documentation_url": "https://srtr.transplant.hrsa.gov/adr"
    },
    "clinicaltrials_gov": {
        "type": "api",
        "endpoint": "https://clinicaltrials.gov/api/v2",
        "description": "Clinical trials database for transplant and reconstructive studies",
        "auth_method": "public",
        "documentation_url": "https://clinicaltrials.gov/api"
    },
    "vca_registry": {
        "type": "database",
        "endpoint": "https://consort-transplant.org/registry",
        "description": "CONSORT VCA transplant registry for face and hand transplants",
        "auth_method": "oauth2",
        "documentation_url": "https://consort-transplant.org/api-docs"
    }
}

# Data structures
Patient = namedtuple('Patient', ['age', 'weight', 'height', 'blood_type', 'hla', 'pra', 'diagnosis'])
Donor = namedtuple('Donor', ['age', 'weight', 'height', 'blood_type', 'hla', 'kdpi', 'cod', 'dcd'])
MatchResult = namedtuple('MatchResult', ['compatibility_score', 'hla_mismatches', 'pra_risk', 'wait_time_estimate'])

class TransplantCalculator:
    """Core transplant calculation utilities."""
    
    @staticmethod
    def calculate_meld_score(bilirubin: float, inr: float, creatinine: float, sodium: Optional[float] = None) -> int:
        """Calculate MELD score for liver transplant priority."""
        if any(v < 0 for v in [bilirubin, inr, creatinine]):
            raise ValueError("Lab values must be non-negative")
        
        creatinine = min(creatinine, 4.0)
        bilirubin = max(bilirubin, 1.0)
        inr = max(inr, 1.0)
        
        meld = 0.957 * math.log(creatinine) + 0.378 * math.log(bilirubin) + 1.120 * math.log(inr) + 0.643
        
        if sodium and sodium < 125:
            meld += 1.32 * (135 - sodium) - 0.033 * meld * (135 - sodium)
        
        return round(max(meld * 10, 6))
    
    @staticmethod
    def calculate_kdpi(donor_age: int, height: float, weight: float, htn: bool, dm: bool, 
                      creatinine: float, hcv: bool, death_cause: str) -> float:
        """Calculate Kidney Donor Profile Index."""
        variables = {
            'age': donor_age,
            'height': height,
            'weight': weight,
            'htn': 1 if htn else 0,
            'dm': 1 if dm else 0,
            'creatinine': creatinine,
            'hcv': 1 if hcv else 0,
            'cerebrovascular': 1 if death_cause == 'stroke' else 0
        }
        
        # Simplified KDPI calculation
        score = (
            0.13 * variables['age'] +
            0.11 * variables['htn'] +
            0.15 * variables['dm'] +
            0.12 * variables['creatinine'] +
            0.10 * variables['hcv'] +
            0.08 * variables['cerebrovascular']
        )
        
        return min(score * 100, 100)
    
    @staticmethod
    def calculate_hla_compatibility(patient_hla: List[str], donor_hla: List[str]) -> Dict[str, Any]:
        """Calculate HLA compatibility between patient and donor."""
        if not patient_hla or not donor_hla:
            raise ValueError("HLA typing required for both patient and donor")
        
        mismatches = 0
        loci = ['A', 'B', 'C', 'DR', 'DQ', 'DP']
        
        for locus in loci:
            patient_alleles = [h for h in patient_hla if h.startswith(locus)]
            donor_alleles = [h for h in donor_hla if h.startswith(locus)]
            
            if patient_alleles and donor_alleles:
                # Count mismatches at each locus
                patient_set = set(patient_alleles)
                donor_set = set(donor_alleles)
                mismatches += len(patient_set.symmetric_difference(donor_set))
        
        compatibility_score = max(0, 100 - (mismatches * 8.33))
        
        return {
            'compatibility_score': round(compatibility_score, 1),
            'hla_mismatches': mismatches,
            'match_grade': 'Excellent' if compatibility_score > 90 else 'Good' if compatibility_score > 75 else 'Fair' if compatibility_score > 50 else 'Poor'
        }
    
    @staticmethod
    def calculate_pra_risk(pra_level: float, donor_hla: List[str], unacceptable_antigens: List[str]) -> Dict[str, Any]:
        """Calculate PRA-based rejection risk."""
        if pra_level < 0 or pra_level > 100:
            raise ValueError("PRA level must be between 0 and 100")
        
        risk_factors = []
        risk_score = 0
        
        if pra_level > 80:
            risk_factors.append("High PRA (>80%)")
            risk_score += 3
        elif pra_level > 50:
            risk_factors.append("Moderate PRA (>50%)")
            risk_score += 2
        elif pra_level > 20:
            risk_factors.append("Low PRA (>20%)")
            risk_score += 1
        
        # Check for unacceptable antigens
        donor_specific = [hla for hla in donor_hla if hla in unacceptable_antigens]
        if donor_specific:
            risk_factors.append(f"DSA present: {donor_specific}")
            risk_score += 5
        
        risk_level = "Low" if risk_score <= 1 else "Moderate" if risk_score <= 3 else "High"
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'desensitization_needed': risk_score >= 3
        }

class VCAPlanner:
    """Vascularized Composite Allotransplantation planning utilities."""
    
    @staticmethod
    def plan_face_transplant(defect_map: Dict[str, Any], donor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate surgical plan for face transplant."""
        if not defect_map or not donor_data:
            raise ValueError("Defect map and donor data required")
        
        # Calculate tissue requirements
        tissue_volume = defect_map.get('volume_cc', 0)
        vascular_pedicles = defect_map.get('vascular_pedicles', [])
        nerve_targets = defect_map.get('nerve_targets', [])
        
        # Donor matching
        donor_height = donor_data.get('height_cm', 170)
        donor_gender = donor_data.get('gender', 'unknown')
        
        # Surgical approach
        approach = "Full face" if tissue_volume > 500 else "Partial face"
        
        # Vascular anastomosis plan
        anastomosis_plan = []
        for pedicle in vascular_pedicles:
            anastomosis_plan.append({
                'vessel': pedicle,
                'donor_length_cm': 3.0,
                'recipient_site': f"Facial {pedicle}",
                'technique': 'end-to-end'
            })
        
        # Nerve coaptation
        nerve_plan = []
        for nerve in nerve_targets:
            nerve_plan.append({
                'nerve': nerve,
                'donor_length_cm': 5.0,
                'coaptation_site': f"Facial {nerve}",
                'graft_needed': True
            })
        
        return {
            'approach': approach,
            'tissue_volume_cc': tissue_volume,
            'anastomosis_plan': anastomosis_plan,
            'nerve_plan': nerve_plan,
            'estimated_ischemia_time_min': 180,
            'immunosuppression_induction': 'rATG + methylprednisolone',
            'maintenance': 'Tacrolimus + MMF + prednisone'
        }
    
    @staticmethod
    def plan_hand_transplant(level: str, laterality: str, donor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate surgical plan for hand transplant."""
        valid_levels = ['wrist', 'forearm', 'elbow', 'above_elbow']
        if level not in valid_levels:
            raise ValueError(f"Level must be one of {valid_levels}")
        
        # Bone fixation strategy
        fixation_map = {
            'wrist': 'radius_ulna_plating',
            'forearm': 'radius_ulna_plating',
            'elbow': 'humerus_plating',
            'above_elbow': 'humerus_plating'
        }
        
        # Tendon repair count
        tendon_count = {
            'wrist': 12,
            'forearm': 16,
            'elbow': 20,
            'above_elbow': 24
        }
        
        return {
            'level': level,
            'laterality': laterality,
            'bone_fixation': fixation_map[level],
            'tendon_repairs': tendon_count[level],
            'vascular_anastomoses': ['radial_artery', 'ulnar_artery', 'cephalic_vein', 'basilic_vein'],
            'nerve_coaptations': ['median_nerve', 'ulnar_nerve', 'radial_nerve'],
            'estimated_ischemia_time_min': 240,
            'rehabilitation_timeline_months': 18
        }

class ReconstructivePlanner:
    """Reconstructive surgery planning utilities."""
    
    @staticmethod
    def select_free_flap(defect_size: Tuple[float, float, float], location: str, 
                        patient_factors: Dict[str, Any]) -> Dict[str, Any]:
        """Select optimal free flap for reconstruction."""
        length, width, depth = defect_size
        volume = length * width * depth
        
        # Flap selection matrix
        flap_options = {
            'ALT': {'volume': 500, 'pedicle': 'descending_branch_lateral_circumflex', 'donor_site': 'thigh'},
            'DIEP': {'volume': 800, 'pedicle': 'deep_inferior_epigastric', 'donor_site': 'abdomen'},
            'Fibula': {'volume': 200, 'pedicle': 'peroneal_artery', 'donor_site': 'leg'},
            'Radial_forearm': {'volume': 150, 'pedicle': 'radial_artery', 'donor_site': 'forearm'}
        }
        
        # Selection criteria
        selected_flap = None
        if location in ['head_neck', 'oral_cavity']:
            selected_flap = 'Radial_forearm' if volume < 200 else 'ALT'
        elif location in ['breast', 'chest_wall']:
            selected_flap = 'DIEP'
        elif location in ['mandible', 'maxilla']:
            selected_flap = 'Fibula'
        else:
            selected_flap = 'ALT'
        
        flap_data = flap_options[selected_flap]
        
        return {
            'selected_flap': selected_flap,
            'flap_volume_cc': flap_data['volume'],
            'vascular_pedicle': flap_data['pedicle'],
            'donor_site': flap_data['donor_site'],
            'estimated_ischaemia_time': 120,
            'donor_site_morbidity': 'low' if selected_flap in ['Radial_forearm', 'Fibula'] else 'moderate'
        }
    
    @staticmethod
    def calculate_tissue_expansion(defect_area: float, expansion_ratio: float = 2.5) -> Dict[str, Any]:
        """Calculate tissue expansion parameters."""
        if defect_area <= 0:
            raise ValueError("Defect area must be positive")
        
        required_expansion = defect_area * expansion_ratio
        expander_volume = required_expansion * 0.5  # 0.5cc per cm2
        fill_frequency = 7  # days
        total_fill_volume = expander_volume * 0.8  # 80% of expander capacity
        
        # Timeline calculation
        weeks_to_fill = math.ceil(total_fill_volume / 50)  # 50cc per week
        consolidation_weeks = 4
        
        return {
            'expander_volume_cc': round(expander_volume, 1),
            'total_fill_volume_cc': round(total_fill_volume, 1),
            'fill_frequency_days': fill_frequency,
            'weeks_to_fill': weeks_to_fill,
            'consolidation_weeks': consolidation_weeks,
            'total_treatment_weeks': weeks_to_fill + consolidation_weeks
        }

class ClinicalTrialTracker:
    """Clinical trial search and analysis utilities."""
    
    @staticmethod
    def search_trials(condition: str, phase: str = "all", location: str = "US") -> List[Dict[str, Any]]:
        """Search ClinicalTrials.gov for relevant trials."""
        base_url = "https://clinicaltrials.gov/api/v2"
        params = {
            'query.cond': condition,
            'query.locn': location,
            'query.spons': 'NIH',
            'filter.overallStatus': 'Recruiting,Not yet recruiting',
            'format': 'json'
        }
        
        # Mock response for testing
        mock_trials = [
            {
                'nct_id': 'NCT12345678',
                'title': f'Phase II Study of {condition} Transplant Innovation',
                'phase': 'Phase 2',
                'status': 'Recruiting',
                'location': 'Multiple US Sites',
                'contact': 'transplant.study@example.com',
                'enrollment': 150,
                'estimated_completion': '2026-12-31'
            },
            {
                'nct_id': 'NCT87654321',
                'title': f'Long-term Outcomes in {condition} Recipients',
                'phase': 'Phase 3',
                'status': 'Recruiting',
                'location': 'US, Canada',
                'contact': 'outcomes@example.com',
                'enrollment': 500,
                'estimated_completion': '2027-06-30'
            }
        ]
        
        return mock_trials
    
    @staticmethod
    def analyze_trial_eligibility(trial: Dict[str, Any], patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patient eligibility for a specific trial."""
        eligibility_factors = {
            'age_match': 18 <= patient_data.get('age', 0) <= 65,
            'organ_match': patient_data.get('transplant_type') in trial.get('title', ''),
            'time_post_transplant': patient_data.get('months_post', 0) >= 6,
            'rejection_history': patient_data.get('rejection_episodes', 0) <= 2
        }
        
        eligibility_score = sum(eligibility_factors.values()) / len(eligibility_factors)
        
        return {
            'eligible': eligibility_score >= 0.75,
            'eligibility_score': round(eligibility_score, 2),
            'matching_factors': [k for k, v in eligibility_factors.items() if v],
            'missing_factors': [k for k, v in eligibility_factors.items() if not v]
        }

class SkillEngine:
    """Main skill engine for transplant and reconstructive surgery expertise."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.calculator = TransplantCalculator()
        self.vca_planner = VCAPlanner()
        self.reconstructive = ReconstructivePlanner()
        self.trial_tracker = ClinicalTrialTracker()
        
    def run(self, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch to appropriate capability handler."""
        handlers = {
            'organ_allocation_analysis': self._handle_organ_allocation,
            'donor_recipient_matching': self._handle_matching,
            'immunosuppression_protocols': self._handle_is_protocols,
            'rejection_monitoring': self._handle_rejection_monitoring,
            'vca_surgical_planning': self._handle_vca_planning,
            'microsurgical_planning': self._handle_microsurgery,
            'outcome_prediction': self._handle_outcome_prediction,
            'clinical_trial_tracker': self._handle_trial_search,
            'rehabilitation_planning': self._handle_rehabilitation,
            'ethical_framework_analysis': self._handle_ethics
        }
        
        if capability not in handlers:
            raise ValueError(f"Unknown capability: {capability}")
        
        try:
            return handlers[capability](params)
        except Exception as e:
            return {'error': str(e), 'capability': capability}
    
    def _handle_organ_allocation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle organ allocation analysis."""
        organ_type = params.get('organ_type', 'kidney')
        meld_score = params.get('meld_score', 15)
        blood_type = params.get('blood_type', 'O')
        
        # Simplified allocation model
        wait_time_months = {
            'kidney': max(6, 36 - meld_score),
            'liver': max(1, 24 - meld_score),
            'heart': max(1, 18 - meld_score),
            'lung': max(1, 12 - meld_score)
        }
        
        return {
            'organ_type': organ_type,
            'meld_score': meld_score,
            'estimated_wait_months': wait_time_months.get(organ_type, 24),
            'allocation_probability': min(100, 100 - (meld_score * 2)),
            'optimization_strategies': ['increase listing centers', 'accept ECD organs', 'consider living donor']
        }
    
    def _handle_matching(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle donor-recipient matching."""
        patient = Patient(**params.get('patient', {}))
        donor = Donor(**params.get('donor', {}))
        
        hla_result = self.calculator.calculate_hla_compatibility(patient.hla, donor.hla)
        pra_result = self.calculator.calculate_pra_risk(patient.pra, donor.hla, params.get('unacceptable_antigens', []))
        
        # Crossmatch calculation
        crossmatch_compatible = patient.blood_type in ['O', donor.blood_type] or donor.blood_type == 'O'
        
        return {
            'hla_compatibility': hla_result,
            'pra_risk': pra_result,
            'crossmatch_compatible': crossmatch_compatible,
            'overall_match_grade': 'Acceptable' if crossmatch_compatible and hla_result['compatibility_score'] > 50 else 'Unsuitable'
        }
    
    def _handle_is_protocols(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle immunosuppression protocols."""
        transplant_type = params.get('transplant_type', 'kidney')
        risk_level = params.get('risk_level', 'standard')
        
        protocols = {
            'induction': {
                'standard': 'Basiliximab 20mg day 0,4',
                'high_risk': 'rATG 1.5mg/kg x 5 days',
                'vca': 'rATG 2.0mg/kg x 7 days + rituximab'
            },
            'maintenance': {
                'standard': 'Tacrolimus + MMF + prednisone',
                'high_risk': 'Tacrolimus + MMF + prednisone + belatacept',
                'vca': 'Tacrolimus + MMF + prednisone + belatacept'
            }
        }
        
        return {
            'induction_protocol': protocols['induction'][risk_level],
            'maintenance_protocol': protocols['maintenance'][risk_level],
            'target_levels': {
                'tacrolimus_ng_ml': 8-12 if transplant_type == 'kidney' else 10-15,
                'mmf_ng_ml': 1.5-3.0
            }
        }
    
    def _handle_rejection_monitoring(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle rejection monitoring."""
        time_post = params.get('time_post_transplant_days', 0)
        dsa_levels = params.get('dsa_levels', [])
        biopsy_grade = params.get('biopsy_grade', 'none')
        
        # Rejection risk calculation
        risk_factors = []
        if time_post < 90:
            risk_factors.append('Early post-transplant')
        if any(dsa > 1000 for dsa in dsa_levels):
            risk_factors.append('Elevated DSA')
        if biopsy_grade != 'none':
            risk_factors.append(f'Biopsy: {biopsy_grade}')
        
        monitoring_schedule = {
            'protocol_biopsy': '3, 12, 24 months' if risk_factors else '12, 24 months',
            'lab_frequency': 'weekly' if risk_factors else 'monthly',
            'dsa_monitoring': 'monthly' if dsa_levels else 'quarterly'
        }
        
        return {
            'rejection_risk': 'High' if len(risk_factors) > 2 else 'Moderate' if risk_factors else 'Low',
            'risk_factors': risk_factors,
            'monitoring_schedule': monitoring_schedule
        }
    
    def _handle_vca_planning(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle VCA surgical planning."""
        vca_type = params.get('vca_type', 'face')
        
        if vca_type == 'face':
            return self.vca_planner.plan_face_transplant(
                params.get('defect_map', {}),
                params.get('donor_data', {})
            )
        else:
            return self.vca_planner.plan_hand_transplant(
                params.get('level', 'wrist'),
                params.get('laterality', 'right'),
                params.get('donor_data', {})
            )
    
    def _handle_microsurgery(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle microsurgical planning."""
        defect_size = params.get('defect_size', (10, 5, 3))
        location = params.get('location', 'head_neck')
        
        return self.reconstructive.select_free_flap(
            defect_size,
            location,
            params.get('patient_factors', {})
        )
    
    def _handle_outcome_prediction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle outcome prediction."""
        patient_age = params.get('patient_age', 50)
        donor_age = params.get('donor_age', 30)
        hla_mismatch = params.get('hla_mismatch', 3)
        
        # Simplified survival model
        base_survival = 0.9
        age_penalty = (patient_age - 50) * 0.002
        donor_penalty = (donor_age - 30) * 0.001
        hla_penalty = hla_mismatch * 0.02
        
        adjusted_survival = max(0.5, base_survival - age_penalty - donor_penalty - hla_penalty)
        
        return {
            '1_year_survival': round(adjusted_survival, 3),
            '5_year_survival': round(adjusted_survival * 0.85, 3),
            'confidence_interval': [adjusted_survival - 0.1, adjusted_survival + 0.1]
        }
    
    def _handle_trial_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle clinical trial search."""
        condition = params.get('condition', 'kidney transplant')
        trials = self.trial_tracker.search_trials(condition)
        
        # Filter by eligibility
        eligible_trials = []
        for trial in trials:
            eligibility = self.trial_tracker.analyze_trial_eligibility(trial, params)
            if eligibility['eligible']:
                trial.update({'eligibility': eligibility})
                eligible_trials.append(trial)
        
        return {
            'total_trials': len(trials),
            'eligible_trials': eligible_trials,
            'search_criteria': condition
        }
    
    def _handle_rehabilitation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle rehabilitation planning."""
        procedure_type = params.get('procedure_type', 'kidney_transplant')
        postop_day = params.get('postop_day', 1)
        
        phases = {
            'acute': {'days': range(0, 7), 'focus': 'pain_control, mobility'},
            'early': {'days': range(7, 30), 'focus': 'strength, function'},
            'intermediate': {'days': range(30, 90), 'focus': 'independence, endurance'},
            'late': {'days': range(90, 365), 'focus': 'optimization, return_to_work'}
        }
        
        current_phase = next(phase for phase, data in phases.items() if postop_day in data['days'])
        
        return {
            'current_phase': current_phase,
            'rehabilitation_focus': phases[current_phase]['focus'],
            'milestones': {
                '2_weeks': 'Independent ambulation',
                '6_weeks': 'Wound healing complete',
                '3_months': 'Return to light activities',
                '6_months': 'Full recovery expected'
            }
        }
    
    def _handle_ethics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ethical framework analysis."""
        procedure_type = params.get('procedure_type', 'vca')
        capacity = params.get('capacity_assessment', 'adequate')
        risk_benefit = params.get('risk_benefit_ratio', 1.0)
        
        ethical_concerns = []
        if procedure_type == 'vca' and risk_benefit < 2.0:
            ethical_concerns.append('Risk-benefit ratio may be insufficient for VCA')
        if capacity != 'adequate':
            ethical_concerns.append('Decision-making capacity requires evaluation')
        
        return {
            'ethical_framework': 'Beneficence, non-maleficence, autonomy, justice',
            'primary_concerns': ethical_concerns,
            'recommendation': 'Proceed with enhanced consent process' if not ethical_concerns else 'Ethics consultation recommended'
        }

class TestTransplantSurgerySkill(unittest.TestCase):
    """Comprehensive test suite for transplant surgery skill."""
    
    def setUp(self):
        self.engine = SkillEngine()
    
    def test_metadata(self):
        """Test skill metadata."""
        self.assertEqual(SKILL_METADATA['name'], "Transplant Surgery & Reconstructive Expert")
        self.assertIn('organ_allocation_analysis', SKILL_METADATA['capabilities'])
    
    def test_meld_calculation(self):
        """Test MELD score calculation."""
        meld = TransplantCalculator.calculate_meld_score(2.0, 1.5, 1.2)
        self.assertIsInstance(meld, int)
        self.assertGreater(meld, 6)
        
        with self.assertRaises(ValueError):
            TransplantCalculator.calculate_meld_score(-1, 1.5, 1.2)
    
    def test_hla_compatibility(self):
        """Test HLA compatibility calculation."""
        patient_hla = ['A1', 'A2', 'B7', 'B8', 'DR3', 'DR4']
        donor_hla = ['A1', 'A3', 'B7', 'B44', 'DR3', 'DR11']
        
        result = TransplantCalculator.calculate_hla_compatibility(patient_hla, donor_hla)
        self.assertIn('compatibility_score', result)
        self.assertIn('hla_mismatches', result)
        self.assertGreater(result['hla_mismatches'], 0)
    
    def test_pra_risk(self):
        """Test PRA risk calculation."""
        result = TransplantCalculator.calculate_pra_risk(75, ['A1', 'B7'], ['A2'])
        self.assertEqual(result['risk_level'], 'High')
        self.assertTrue(result['desensitization_needed'])
    
    def test_vca_face_planning(self):
        """Test VCA face transplant planning."""
        defect_map = {'volume_cc': 600, 'vascular_pedicles': ['facial_artery', 'superficial_temporal']}
        donor_data = {'height_cm': 175, 'gender': 'male'}
        
        plan = self.engine.run('vca_surgical_planning', {
            'vca_type': 'face',
            'defect_map': defect_map,
            'donor_data': donor_data
        })
        
        self.assertEqual(plan['approach'], 'Full face')
        self.assertIn('anastomosis_plan', plan)
    
    def test_free_flap_selection(self):
        """Test free flap selection."""
        result = ReconstructivePlanner.select_free_flap((15, 8, 4), 'head_neck', {})
        self.assertEqual(result['selected_flap'], 'ALT')
        self.assertIn('vascular_pedicle', result)
    
    def test_tissue_expansion(self):
        """Test tissue expansion calculation."""
        result = ReconstructivePlanner.calculate_tissue_expansion(100)
        self.assertEqual(result['expander_volume_cc'], 125.0)
        self.assertGreater(result['total_treatment_weeks'], 10)
        
        with self.assertRaises(ValueError):
            ReconstructivePlanner.calculate_tissue_expansion(-10)
    
    def test_trial_search(self):
        """Test clinical trial search."""
        result = self.engine.run('clinical_trial_tracker', {
            'condition': 'kidney transplant',
            'patient_age': 45
        })
        
        self.assertIn('eligible_trials', result)
        self.assertIsInstance(result['eligible_trials'], list)
    
    def test_outcome_prediction(self):
        """Test outcome prediction."""
        result = self.engine.run('outcome_prediction', {
            'patient_age': 45,
            'donor_age': 25,
            'hla_mismatch': 2
        })
        
        self.assertIn('1_year_survival', result)
        self.assertIn('5_year_survival', result)
        self.assertGreater(result['1_year_survival'], 0.8)
    
    def test_error_handling(self):
        """Test error handling."""
        result = self.engine.run('unknown_capability', {})
        self.assertIn('error', result)
        
        with self.assertRaises(ValueError):
            TransplantCalculator.calculate_meld_score(-1, 1, 1)

if __name__ == '__main__':
    unittest.main()