import json
import os
import re
import datetime
import hashlib
import statistics
import math
import unittest
import logging
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, namedtuple
import requests

SKILL_METADATA = {
    "name": "Glaucoma & Ophthalmology",
    "id": "glaucoma_ophthalmology",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Comprehensive glaucoma and ophthalmology analysis module for intraocular pressure management, optic nerve assessment, visual field interpretation, treatment protocols, and emerging therapies",
    "capabilities": [
        "intraocular_pressure_analysis",
        "optic_nerve_damage_assessment",
        "visual_field_interpretation",
        "treatment_protocol_recommendation",
        "neuroprotective_therapy_evaluation",
        "emerging_therapy_analysis",
        "clinical_trial_matching",
        "patient_monitoring_alerts",
        "risk_stratification",
        "progression_tracking"
    ],
    "domain": "ophthalmology"
}

EXPERT_PROMPTS = {
    "iop_analysis": """Analyze the following intraocular pressure readings for glaucoma risk assessment:
Patient Age: {patient_age}
IOP Readings (mmHg): {iop_readings}
Corneal Thickness (μm): {cct}
Family History: {family_history}
Current Medications: {medications}
Provide risk stratification and treatment recommendations based on latest EGS guidelines.""",
    
    "optic_nerve_evaluation": """Evaluate this optic nerve analysis for glaucomatous damage:
CDR: {cdr}
Rim Area (mm²): {rim_area}
RNFL Thickness (μm): {rnfl_thickness}
Visual Field MD (dB): {vf_md}
Pattern SD: {vf_psd}
Determine glaucoma stage and progression risk.""",
    
    "visual_field_progression": """Interpret this visual field test series for progression:
Baseline MD: {baseline_md}
Current MD: {current_md}
Test Dates: {test_dates}
Pattern Deviation: {pattern_deviation}
Provide progression analysis and confidence level.""",
    
    "treatment_protocol": """Recommend treatment protocol for:
Glaucoma Type: {glaucoma_type}
Current IOP: {current_iop}
Target IOP: {target_iop}
Previous Surgeries: {surgeries}
Comorbidities: {comorbidities}
Consider ROCK inhibitors, prostaglandin analogs, and surgical options.""",
    
    "clinical_trial_matching": """Find relevant clinical trials for:
Patient Demographics: {demographics}
Glaucoma Stage: {stage}
Previous Treatments: {treatments}
Location: {location}
Include gene therapy and neuroprotection trials.""",
    
    "neuroprotective_assessment": """Evaluate neuroprotective treatment options for:
Current Therapy: {current_therapy}
Disease Progression: {progression}
Optic Nerve Status: {optic_nerve_status}
Patient Compliance: {compliance}
Consider memantine, brimonidine, and emerging agents.""",
    
    "post_surgical_monitoring": """Monitor post-trabeculectomy patient:
Surgery Date: {surgery_date}
Current IOP: {current_iop}
Bleb Appearance: {bleb_status}
Complications: {complications}
Assess for cystic bleb formation and intervention needs.""",
    
    "pediatric_glaucoma": """Manage pediatric glaucoma case:
Age: {age}
IOP: {iop}
Corneal Diameter: {corneal_diameter}
Haab's Striae: {haab_striae}
Family History: {family_history}
Provide age-appropriate treatment algorithm."""
}

INTEGRATION_POINTS = {
    "egs_guidelines_api": {
        "type": "api",
        "endpoint": "https://api.egs.org/guidelines/v6",
        "description": "European Glaucoma Society guidelines database",
        "auth_method": "api_key",
        "documentation_url": "https://egs.org/api/docs"
    },
    "clinical_trials_gov": {
        "type": "api",
        "endpoint": "https://clinicaltrials.gov/api/query",
        "description": "Clinical trials database for glaucoma studies",
        "auth_method": "none",
        "documentation_url": "https://clinicaltrials.gov/api/"
    },
    "ophthalmology_emr": {
        "type": "database",
        "endpoint": "postgresql://emr-db:5432/ophthalmology",
        "description": "Ophthalmology electronic medical records",
        "auth_method": "oauth2",
        "documentation_url": "https://emr-docs.revvel.ai"
    },
    "imaging_analysis_tool": {
        "type": "tool",
        "endpoint": "http://oct-analysis.revvel.ai:8080",
        "description": "OCT and fundus image analysis service",
        "auth_method": "jwt",
        "documentation_url": "https://imaging.revvel.ai/docs"
    }
}

def validate_iop_readings(iop_readings: List[float]) -> Tuple[bool, str]:
    """Validate intraocular pressure readings for physiological range."""
    if not iop_readings:
        return False, "No IOP readings provided"
    
    for iop in iop_readings:
        if not isinstance(iop, (int, float)):
            return False, f"Invalid IOP value: {iop}"
        if iop < 0 or iop > 60:
            return False, f"IOP value {iop} mmHg outside physiological range (0-60)"
    
    return True, "Valid IOP readings"

def calculate_mean_iop(iop_readings: List[float]) -> float:
    """Calculate mean intraocular pressure with outlier detection."""
    if len(iop_readings) < 2:
        return statistics.mean(iop_readings) if iop_readings else 0.0
    
    # Remove outliers beyond 2 standard deviations
    mean_iop = statistics.mean(iop_readings)
    stdev = statistics.stdev(iop_readings)
    
    filtered = [iop for iop in iop_readings if abs(iop - mean_iop) <= 2 * stdev]
    return statistics.mean(filtered) if filtered else mean_iop

def assess_glaucoma_risk(iop: float, cct: float, age: int, family_history: bool) -> Dict[str, Any]:
    """Assess glaucoma risk based on multiple factors."""
    risk_score = 0
    risk_factors = []
    
    # IOP-based risk
    if iop > 21:
        risk_score += 2
        risk_factors.append("Elevated IOP")
    elif iop > 18:
        risk_score += 1
        risk_factors.append("Borderline IOP")
    
    # CCT-based risk (thinner corneas = higher risk)
    if cct < 500:
        risk_score += 2
        risk_factors.append("Thin cornea")
    elif cct < 550:
        risk_score += 1
        risk_factors.append("Borderline corneal thickness")
    
    # Age-based risk
    if age > 60:
        risk_score += 2
        risk_factors.append("Advanced age")
    elif age > 40:
        risk_score += 1
        risk_factors.append("Middle age")
    
    # Family history
    if family_history:
        risk_score += 2
        risk_factors.append("Family history of glaucoma")
    
    # Risk stratification
    if risk_score >= 6:
        risk_level = "High"
    elif risk_score >= 3:
        risk_level = "Moderate"
    else:
        risk_level = "Low"
    
    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "recommended_follow_up": "3-6 months" if risk_level in ["High", "Moderate"] else "12 months"
    }

def interpret_visual_field(md: float, psd: float, vfi: float) -> Dict[str, Any]:
    """Interpret visual field test results."""
    interpretation = {}
    
    # Mean Deviation analysis
    if md >= -2:
        interpretation["md_status"] = "Normal"
        interpretation["md_severity"] = "None"
    elif md >= -6:
        interpretation["md_status"] = "Borderline"
        interpretation["md_severity"] = "Early"
    elif md >= -12:
        interpretation["md_status"] = "Abnormal"
        interpretation["md_severity"] = "Moderate"
    else:
        interpretation["md_status"] = "Severely abnormal"
        interpretation["md_severity"] = "Advanced"
    
    # Pattern Standard Deviation
    if psd < 2:
        interpretation["psd_status"] = "Normal"
    elif psd < 5:
        interpretation["psd_status"] = "Borderline"
    else:
        interpretation["psd_status"] = "Abnormal"
    
    # Visual Field Index
    interpretation["vfi_percentage"] = vfi
    if vfi >= 90:
        interpretation["vfi_status"] = "Excellent"
    elif vfi >= 70:
        interpretation["vfi_status"] = "Good"
    elif vfi >= 50:
        interpretation["vfi_status"] = "Fair"
    else:
        interpretation["vfi_status"] = "Poor"
    
    # Overall assessment
    if interpretation["md_severity"] == "None" and interpretation["psd_status"] == "Normal":
        interpretation["overall_status"] = "Normal visual field"
    elif interpretation["md_severity"] in ["Early", "Moderate"]:
        interpretation["overall_status"] = f"Glaucomatous defect - {interpretation['md_severity']}"
    else:
        interpretation["overall_status"] = f"Severe glaucomatous defect - {interpretation['md_severity']}"
    
    return interpretation

def calculate_target_iop(baseline_iop: float, md: float, age: int) -> float:
    """Calculate target IOP based on disease severity and risk factors."""
    # Base target reduction
    if md >= -6:  # Early damage
        target_reduction = 0.20
    elif md >= -12:  # Moderate damage
        target_reduction = 0.30
    else:  # Advanced damage
        target_reduction = 0.40
    
    # Age adjustment
    if age < 50:
        target_reduction += 0.05  # More aggressive for younger patients
    
    target_iop = baseline_iop * (1 - target_reduction)
    
    # Ensure target is within safe range
    return max(target_iop, 6.0)  # Minimum safe IOP

def evaluate_optic_nerve_damage(cdr: float, rim_area: float, rnfl_thickness: float) -> Dict[str, Any]:
    """Evaluate optic nerve damage from clinical parameters."""
    damage_score = 0
    findings = []
    
    # Cup-to-disc ratio
    if cdr > 0.7:
        damage_score += 3
        findings.append("Advanced cupping")
    elif cdr > 0.5:
        damage_score += 2
        findings.append("Moderate cupping")
    elif cdr > 0.3:
        damage_score += 1
        findings.append("Mild cupping")
    
    # Rim area (normal >1.2 mm²)
    if rim_area < 0.5:
        damage_score += 3
        findings.append("Severe rim loss")
    elif rim_area < 0.8:
        damage_score += 2
        findings.append("Moderate rim loss")
    elif rim_area < 1.0:
        damage_score += 1
        findings.append("Mild rim loss")
    
    # RNFL thickness (normal ~100 μm)
    if rnfl_thickness < 60:
        damage_score += 3
        findings.append("Severe RNFL thinning")
    elif rnfl_thickness < 80:
        damage_score += 2
        findings.append("Moderate RNFL thinning")
    elif rnfl_thickness < 90:
        damage_score += 1
        findings.append("Mild RNFL thinning")
    
    # Stage determination
    if damage_score >= 7:
        stage = "Advanced"
    elif damage_score >= 4:
        stage = "Moderate"
    elif damage_score >= 2:
        stage = "Early"
    else:
        stage = "Normal"
    
    return {
        "damage_score": damage_score,
        "stage": stage,
        "findings": findings,
        "progression_risk": "High" if damage_score >= 5 else "Moderate" if damage_score >= 3 else "Low"
    }

def generate_monitoring_schedule(risk_level: str, stage: str, age: int) -> List[Dict[str, str]]:
    """Generate patient monitoring schedule based on risk and disease stage."""
    schedule = []
    
    # Base intervals
    if risk_level == "High" or stage == "Advanced":
        iop_interval = "1-2 months"
        vf_interval = "6 months"
        oct_interval = "6 months"
    elif risk_level == "Moderate" or stage == "Moderate":
        iop_interval = "3-6 months"
        vf_interval = "12 months"
        oct_interval = "12 months"
    else:
        iop_interval = "6-12 months"
        vf_interval = "24 months"
        oct_interval = "24 months"
    
    # Age adjustment
    if age > 70:
        iop_interval = iop_interval.replace("months", "months (consider more frequent)")
    
    schedule = [
        {"test": "Intraocular Pressure", "frequency": iop_interval},
        {"test": "Visual Field", "frequency": vf_interval},
        {"test": "OCT/RNFL Analysis", "frequency": oct_interval},
        {"test": "Optic Disc Examination", "frequency": vf_interval}
    ]
    
    return schedule

def check_drug_interactions(current_meds: List[str], proposed_med: str) -> Dict[str, Any]:
    """Check for potential drug interactions with glaucoma medications."""
    interactions = {
        "timolol": ["calcium_channel_blockers", "beta_blockers", "digoxin"],
        "brimonidine": ["monoamine_oxidase_inhibitors", "tricyclic_antidepressants"],
        "acetazolamide": ["aspirin", "lithium", "phenytoin"],
        "latanoprost": ["thimerosal"]
    }
    
    relevant_interactions = []
    severity = "None"
    
    proposed_lower = proposed_med.lower()
    if proposed_lower in interactions:
        for med in current_meds:
            med_lower = med.lower()
            if any(interaction in med_lower for interaction in interactions[proposed_lower]):
                relevant_interactions.append(f"{proposed_med} + {med}")
                severity = "Moderate"  # Simplified severity assessment
    
    return {
        "has_interactions": len(relevant_interactions) > 0,
        "interactions": relevant_interactions,
        "severity": severity,
        "recommendation": "Consider alternative therapy" if relevant_interactions else "Safe to proceed"
    }

def analyze_progression_rate(test_dates: List[str], md_values: List[float]) -> Dict[str, Any]:
    """Analyze visual field progression rate over time."""
    if len(test_dates) < 3 or len(md_values) < 3:
        return {"error": "Insufficient data for progression analysis"}
    
    # Convert dates to years from first test
    dates = [datetime.datetime.strptime(d, "%Y-%m-%d") for d in test_dates]
    base_date = dates[0]
    years = [(d - base_date).days / 365.25 for d in dates]
    
    # Linear regression for progression rate
    n = len(years)
    sum_x = sum(years)
    sum_y = sum(md_values)
    sum_xy = sum(x * y for x, y in zip(years, md_values))
    sum_x2 = sum(x * x for x in years)
    
    if n * sum_x2 - sum_x * sum_x == 0:
        return {"error": "Cannot calculate progression rate"}
    
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
    intercept = (sum_y - slope * sum_x) / n
    
    # Significance test (simplified)
    progression_significant = abs(slope) > 0.5  # dB/year threshold
    
    return {
        "progression_rate_db_per_year": round(slope, 2),
        "significant": progression_significant,
        "predicted_5_year_md": round(intercept + slope * (years[-1] + 5), 2),
        "trend": "Worsening" if slope < -0.5 else "Stable" if slope < 0.5 else "Improving"
    }

class SkillEngine:
    """Main skill engine for glaucoma and ophthalmology analysis."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the skill engine with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.capabilities = SKILL_METADATA["capabilities"]
        
        # Set up logging
        log_level = config.get("log_level", "INFO")
        self.logger.setLevel(getattr(logging, log_level))
        
    def run(self, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run the specified capability with given parameters."""
        if capability not in self.capabilities:
            raise ValueError(f"Unknown capability: {capability}")
        
        try:
            if capability == "intraocular_pressure_analysis":
                return self.analyze_iop(params)
            elif capability == "optic_nerve_damage_assessment":
                return self.assess_optic_nerve(params)
            elif capability == "visual_field_interpretation":
                return self.interpret_vf(params)
            elif capability == "treatment_protocol_recommendation":
                return self.recommend_treatment(params)
            elif capability == "neuroprotective_therapy_evaluation":
                return self.evaluate_neuroprotection(params)
            elif capability == "emerging_therapy_analysis":
                return self.analyze_emerging_therapies(params)
            elif capability == "clinical_trial_matching":
                return self.match_clinical_trials(params)
            elif capability == "patient_monitoring_alerts":
                return self.generate_alerts(params)
            elif capability == "risk_stratification":
                return self.stratify_risk(params)
            elif capability == "progression_tracking":
                return self.track_progression(params)
            else:
                raise ValueError(f"Capability not implemented: {capability}")
        except Exception as e:
            self.logger.error(f"Error in capability {capability}: {str(e)}")
            return {"error": str(e)}
    
    def analyze_iop(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze intraocular pressure readings."""
        iop_readings = params.get("iop_readings", [])
        cct = params.get("cct", 545)
        age = params.get("age", 50)
        family_history = params.get("family_history", False)
        
        # Validate inputs
        valid, message = validate_iop_readings(iop_readings)
        if not valid:
            return {"error": message}
        
        # Calculate metrics
        mean_iop = calculate_mean_iop(iop_readings)
        risk_assessment = assess_glaucoma_risk(mean_iop, cct, age, family_history)
        
        return {
            "mean_iop": round(mean_iop, 1),
            "risk_assessment": risk_assessment,
            "target_iop": calculate_target_iop(mean_iop, -2.0, age),
            "monitoring_schedule": generate_monitoring_schedule(
                risk_assessment["risk_level"], "Normal", age
            )
        }
    
    def assess_optic_nerve(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Assess optic nerve damage."""
        cdr = params.get("cdr", 0.3)
        rim_area = params.get("rim_area", 1.2)
        rnfl_thickness = params.get("rnfl_thickness", 100)
        
        damage_assessment = evaluate_optic_nerve_damage(cdr, rim_area, rnfl_thickness)
        
        return {
            "damage_assessment": damage_assessment,
            "recommended_tests": ["OCT", "Visual Field", "Fundus Photography"],
            "follow_up_interval": "3 months" if damage_assessment["stage"] == "Advanced" else "6 months"
        }
    
    def interpret_vf(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Interpret visual field test results."""
        md = params.get("md", -2.0)
        psd = params.get("psd", 2.0)
        vfi = params.get("vfi", 95.0)
        
        interpretation = interpret_visual_field(md, psd, vfi)
        
        return {
            "interpretation": interpretation,
            "reliability_check": "Pass" if psd < 5 else "Review",
            "clinical_significance": "Monitor" if interpretation["md_status"] == "Normal" else "Investigate"
        }
    
    def recommend_treatment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend treatment protocol."""
        glaucoma_type = params.get("glaucoma_type", "POAG")
        current_iop = params.get("current_iop", 22)
        target_iop = params.get("target_iop", 16)
        current_meds = params.get("current_meds", [])
        
        # Simple treatment algorithm
        if current_iop > target_iop + 5:
            recommendation = "Initiate dual therapy (PGA + beta-blocker)"
            urgency = "High"
        elif current_iop > target_iop:
            recommendation = "Add second agent or increase current medication"
            urgency = "Moderate"
        else:
            recommendation = "Continue current therapy"
            urgency = "Low"
        
        # Check interactions for proposed therapy
        interaction_check = check_drug_interactions(current_meds, "latanoprost")
        
        return {
            "recommendation": recommendation,
            "urgency": urgency,
            "proposed_medications": ["Latanoprost", "Timolol"],
            "drug_interaction_check": interaction_check,
            "follow_up": "4-6 weeks"
        }
    
    def evaluate_neuroprotection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate neuroprotective therapy options."""
        current_therapy = params.get("current_therapy", [])
        progression = params.get("progression", "stable")
        
        recommendations = []
        if progression == "worsening":
            recommendations.extend([
                "Consider brimonidine (neuroprotective properties)",
                "Evaluate memantine adjunct therapy",
                "Assess compliance with current therapy"
            ])
        else:
            recommendations.append("Continue current monitoring protocol")
        
        return {
            "neuroprotective_options": recommendations,
            "evidence_level": "Moderate",
            "clinical_trial_eligibility": progression == "worsening"
        }
    
    def analyze_emerging_therapies(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze emerging therapy options."""
        stage = params.get("stage", "moderate")
        previous_surgeries = params.get("previous_surgeries", [])
        
        emerging_options = []
        if stage in ["moderate", "advanced"]:
            emerging_options.extend([
                "ROCK inhibitors (Netarsudil)",
                "Gene therapy trials (MYOC, OPTN genes)",
                "Stem cell therapy (experimental)",
                "Neurotrophic factor therapy"
            ])
        
        return {
            "emerging_therapies": emerging_options,
            "clinical_trial_availability": len(emerging_options) > 0,
            "insurance_coverage": "Limited",
            "regulatory_status": "Investigational"
        }
    
    def match_clinical_trials(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Match patients to relevant clinical trials."""
        age = params.get("age", 60)
        stage = params.get("stage", "moderate")
        location = params.get("location", "US")
        
        # Mock trial matching
        trials = [
            {
                "nct_id": "NCT12345678",
                "title": "ROCK Inhibitor vs PGA in Primary Open-Angle Glaucoma",
                "phase": "III",
                "eligibility": age >= 18 and stage in ["moderate", "advanced"]
            },
            {
                "nct_id": "NCT87654321",
                "title": "Gene Therapy for Myocilin Glaucoma",
                "phase": "I/II",
                "eligibility": age >= 21 and "MYOC" in str(params.get("genetics", ""))
            }
        ]
        
        eligible_trials = [t for t in trials if t["eligibility"]]
        
        return {
            "eligible_trials": eligible_trials,
            "total_trials_found": len(trials),
            "recommendation": "Contact site for" if eligible_trials else "No current matches"
        }
    
    def generate_alerts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate patient monitoring alerts."""
        current_iop = params.get("current_iop", 15)
        baseline_iop = params.get("baseline_iop", 15)
        surgery_date = params.get("surgery_date")
        
        alerts = []
        
        # IOP alert
        if current_iop > baseline_iop + 5:
            alerts.append({
                "type": "IOP_ELEVATION",
                "severity": "High",
                "message": f"IOP increased by {current_iop - baseline_iop} mmHg from baseline"
            })
        
        # Post-surgical alert
        if surgery_date:
            surgery_dt = datetime.datetime.strptime(surgery_date, "%Y-%m-%d")
            days_post_op = (datetime.datetime.now() - surgery_dt).days
            if days_post_op < 30 and current_iop > 21:
                alerts.append({
                    "type": "POST_SURGICAL_SPIKE",
                    "severity": "High",
                    "message": "Elevated IOP in post-operative period"
                })
        
        return {
            "alerts": alerts,
            "alert_count": len(alerts),
            "requires_attention": len(alerts) > 0
        }
    
    def stratify_risk(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stratify patient risk."""
        return self.analyze_iop(params)  # Reuse IOP analysis for risk stratification
    
    def track_progression(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Track disease progression."""
        test_dates = params.get("test_dates", [])
        md_values = params.get("md_values", [])
        
        progression_analysis = analyze_progression_rate(test_dates, md_values)
        
        return {
            "progression_analysis": progression_analysis,
            "treatment_adjustment_needed": progression_analysis.get("significant", False),
            "next_test_recommended": "6 months" if progression_analysis.get("significant") else "12 months"
        }

class TestGlaucomaOphthalmologySkill(unittest.TestCase):
    """Test cases for glaucoma and ophthalmology skill."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {"log_level": "DEBUG"}
        self.engine =SkillEngine(self.config)
    
    def test_metadata_validation(self):
        """Test skill metadata structure."""
        self.assertEqual(SKILL_METADATA["name"], "Glaucoma & Ophthalmology")
        self.assertIn("intraocular_pressure_analysis", SKILL_METADATA["capabilities"])
        self.assertEqual(len(SKILL_METADATA["capabilities"]), 10)
    
    def test_iop_validation(self):
        """Test IOP reading validation."""
        # Valid readings
        valid, msg = validate_iop_readings([15, 16, 14])
        self.assertTrue(valid)
        self.assertEqual(msg, "Valid IOP readings")
        
        # Invalid readings
        valid, msg = validate_iop_readings([15, 80, 14])
        self.assertFalse(valid)
        self.assertIn("outside physiological range", msg)
    
    def test_mean_iop_calculation(self):
        """Test mean IOP calculation with outlier removal."""
        readings = [15, 16, 15, 30, 14]  # 30 is outlier
        mean_iop = calculate_mean_iop(readings)
        self.assertLess(mean_iop, 20)  # Should exclude outlier
    
    def test_glaucoma_risk_assessment(self):
        risk = assess_glaucoma_risk(25, 480, 65, True)
        self.assertEqual(risk["risk_level"], "High")
        self.assertIn("Elevated IOP", risk["risk_factors"])
        self.assertIn("Family history of glaucoma", risk["risk_factors"])
    
    def test_visual_field_interpretation(self):
        """Test visual field interpretation."""
        interpretation = interpret_visual_field(-8.5, 4.2, 75)
        self.assertEqual(interpretation["md_severity"], "Moderate")
        self.assertEqual(interpretation["overall_status"], "Glaucomatous defect - Moderate")
    
    def test_optic_nerve_damage_evaluation(self):
        """Test optic nerve damage assessment."""
        damage = evaluate_optic_nerve_damage(0.8, 0.4, 65)
        self.assertEqual(damage["stage"], "Advanced")
        self.assertIn("Advanced cupping", damage["findings"])
    
    def test_target_iop_calculation(self):
        """Test target IOP calculation."""
        target = calculate_target_iop(25, -15, 45)
        self.assertLess(target, 20)  # Should be reduced from baseline
        self.assertGreaterEqual(target, 6)  # Minimum safe IOP
    
    def test_drug_interaction_check(self):
        """Test drug interaction checking."""
        interactions = check_drug_interactions(["atenolol", "digoxin"], "timolol")
        self.assertTrue(interactions["has_interactions"])
        self.assertIn("Consider alternative therapy", interactions["recommendation"])
    
    def test_progression_rate_analysis(self):
        """Test visual field progression analysis."""
        dates = ["2020-01-01", "2021-01-01", "2022-01-01", "2023-01-01"]
        md_values = [-2.0, -3.0, -4.5, -6.0]
        progression = analyze_progression_rate(dates, md_values)
        self.assertLess(progression["progression_rate_db_per_year"], 0)
        self.assertTrue(progression["significant"])
    
    def test_skill_engine_iop_analysis(self):
        """Test skill engine IOP analysis capability."""
        params = {
            "iop_readings": [18, 19, 17, 20],
            "cct": 520,
            "age": 55,
            "family_history": False
        }
        result = self.engine.run("intraocular_pressure_analysis", params)
        self.assertIn("mean_iop", result)
        self.assertIn("risk_assessment", result)
        self.assertEqual(result["risk_assessment"]["risk_level"], "Moderate")
    
    def test_skill_engine_vf_interpretation(self):
        """Test skill engine visual field interpretation."""
        params = {"md": -10.5, "psd": 6.8, "vfi": 65}
        result = self.engine.run("visual_field_interpretation", params)
        self.assertEqual(result["interpretation"]["md_severity"], "Moderate")
        self.assertEqual(result["clinical_significance"], "Investigate")
    
    def test_skill_engine_treatment_recommendation(self):
        """Test skill engine treatment recommendation."""
        params = {
            "glaucoma_type": "POAG",
            "current_iop": 28,
            "target_iop": 16,
            "current_meds": ["latanoprost"]
        }
        result = self.engine.run("treatment_protocol_recommendation", params)
        self.assertIn("recommendation", result)
        self.assertEqual(result["urgency"], "High")
    
    def test_skill_engine_error_handling(self):
        """Test skill engine error handling."""
        # Invalid capability
        with self.assertRaises(ValueError):
            self.engine.run("invalid_capability", {})
        
        # Invalid IOP readings
        result = self.engine.run("intraocular_pressure_analysis", {"iop_readings": [100]})
        self.assertIn("error", result)

if __name__ == "__main__":
    unittest.main()