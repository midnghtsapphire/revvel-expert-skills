import json
import os
import re
import math
import hashlib
import requests
import unittest
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from collections import defaultdict, namedtuple
from statistics import mean, median, stdev

SKILL_METADATA = {
    "name": "Cardiovascular Disease Research",
    "id": "cardiovascular",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Comprehensive cardiovascular disease research module for risk modeling, lipid analysis, biomarker evaluation, therapy recommendations, and lifestyle interventions.",
    "capabilities": [
        "heart_disease_risk_modeling",
        "lipid_panel_analysis",
        "cardiac_biomarker_evaluation",
        "statin_alternatives_recommendation",
        "emerging_therapies_analysis",
        "lifestyle_intervention_protocols",
        "cardiac_imaging_analysis",
        "arrhythmia_detection",
        "blood_pressure_optimization"
    ],
    "domain": "cardiovascular_medicine"
}

EXPERT_PROMPTS = {
    "risk_assessment": """You are a cardiovascular specialist. Assess the 10-year ASCVD risk for a {age}-year-old {gender} with the following profile:
- Total cholesterol: {total_chol} mg/dL
- HDL cholesterol: {hdl} mg/dL
- Systolic BP: {systolic_bp} mmHg
- On BP medication: {bp_meds}
- Diabetes status: {diabetes}
- Smoking status: {smoker}
- Family history of premature CAD: {family_history}

Provide risk score, risk category, and evidence-based recommendations for primary prevention.""",
    
    "lipid_analysis": """Analyze this lipid panel for {patient_name}:
- Total cholesterol: {total_chol} mg/dL
- LDL cholesterol: {ldl} mg/dL  
- HDL cholesterol: {hdl} mg/dL
- Triglycerides: {tg} mg/dL
- Non-HDL cholesterol: {non_hdl} mg/dL
- Patient age: {age}
- Existing conditions: {conditions}

Interpret results, calculate ratios, assess cardiovascular risk, and recommend treatment targets based on {risk_level} risk profile.""",
    
    "biomarker_evaluation": """Evaluate these cardiac biomarkers for {patient_name}:
- High-sensitivity CRP: {hs_crp} mg/L
- NT-proBNP: {nt_probnp} pg/mL
- Troponin I: {troponin} ng/mL
- Lipoprotein(a): {lpa} mg/dL
- Apolipoprotein B: {apob} mg/dL

Interpret values, assess prognostic significance, and recommend clinical actions based on {clinical_context}.""",
    
    "statin_intolerance": """Patient {patient_name} reports {symptoms} on {statin_type} at {dose}mg daily for {duration} weeks.
Current lipid profile: LDL {ldl} mg/dL, Total {total} mg/dL, HDL {hdl} mg/dL, TG {tg} mg/dL.
CK level: {ck_level} U/L (normal <{ck_normal} U/L)

Recommend statin alternatives or non-statin therapies to achieve LDL target of <{target_ldl} mg/dL.""",
    
    "emerging_therapies": """For a {age}-year-old {gender} with {condition} and baseline LDL {baseline_ldl} mg/dL:
- Failed to achieve target on maximally tolerated statin + ezetimibe
- Has {comorbidities}
- Insurance status: {insurance}

Evaluate suitability for PCSK9 inhibitors, inclisiran, bempedoic acid, or other emerging therapies. Include efficacy data, administration, monitoring, and cost considerations.""",
    
    "lifestyle_intervention": """Design a comprehensive lifestyle intervention for {patient_name}, a {age}-year-old {gender} with:
- BMI: {bmi} kg/m²
- Waist circumference: {waist} cm
- Blood pressure: {bp} mmHg
- Current diet: {diet}
- Physical activity: {activity_level}
- Smoking: {smoking}
- Alcohol: {alcohol}

Include specific dietary modifications, exercise prescription, weight loss targets, and behavioral strategies.""",
    
    "imaging_analysis": """Analyze the following cardiac imaging findings for {patient_name}:
- Coronary calcium score: {cac_score}
- Carotid IMT: {cimt} mm
- Echo EF: {ef}%
- Wall motion: {wall_motion}
- Valvular disease: {valves}

Assess cardiovascular risk, recommend follow-up intervals, and suggest additional testing if needed.""",
    
    "arrhythmia_evaluation": """Evaluate this ECG for arrhythmia:
- Rhythm: {rhythm}
- Heart rate: {hr} bpm
- PR interval: {pr} ms
- QRS duration: {qrs} ms
- QTc: {qtc} ms
- P wave morphology: {p_wave}
- QRS morphology: {qrs_morphology}
- Symptoms: {symptoms}

Identify arrhythmia type, assess clinical significance, and recommend management strategy."""
}

INTEGRATION_POINTS = {
    "pubmed_api": {
        "type": "api",
        "endpoint": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
        "description": "PubMed API for accessing cardiovascular research literature",
        "auth_method": "api_key",
        "documentation_url": "https://www.ncbi.nlm.nih.gov/books/NBK25501/"
    },
    "clinical_trials_gov": {
        "type": "api", 
        "endpoint": "https://clinicaltrials.gov/api/",
        "description": "Clinical trials database for cardiovascular studies",
        "auth_method": "none",
        "documentation_url": "https://clinicaltrials.gov/api/"
    },
    "fda_drugs_api": {
        "type": "api",
        "endpoint": "https://api.fda.gov/drug/",
        "description": "FDA drug information and approvals",
        "auth_method": "none", 
        "documentation_url": "https://open.fda.gov/apis/drug/"
    },
    "lipid_research_database": {
        "type": "database",
        "endpoint": "postgresql://lipid-db.research.org:5432/lipidomics",
        "description": "Comprehensive lipid metabolism research database",
        "auth_method": "oauth2",
        "documentation_url": "https://lipid-db.research.org/docs"
    },
    "cardiac_imaging_ai": {
        "type": "tool",
        "endpoint": "https://cardiac-ai.research.org/api/v1/analyze",
        "description": "AI-powered cardiac imaging analysis platform",
        "auth_method": "bearer_token",
        "documentation_url": "https://cardiac-ai.research.org/docs"
    }
}

def calculate_ascvd_risk(age: int, gender: str, total_chol: float, hdl: float, systolic_bp: float, 
                        bp_meds: bool, diabetes: bool, smoker: bool) -> Dict[str, Any]:
    """Calculate 10-year ASCVD risk using pooled cohort equations."""
    if not (40 <= age <= 79):
        raise ValueError("Age must be between 40-79 years for ASCVD calculation")
    
    # Convert to risk factors
    age_rf = math.log(age)
    tot_chol_rf = math.log(total_chol)
    hdl_rf = math.log(hdl)
    systolic_rf = systolic_bp
    
    # Coefficients for white male (simplified version)
    if gender.lower() == 'male':
        baseline_survival = 0.9144
        coefficients = {
            'age': 12.344, 'age_sq': 0, 'tot_chol': 11.853, 'age_tot_chol': -2.664,
            'hdl': -7.990, 'age_hdl': 1.769, 'treated_systolic': 1.797,
            'untreated_systolic': 1.764, 'diabetes': 0.657, 'smoker': 7.837, 'age_smoker': -1.795
        }
    else:
        baseline_survival = 0.9665
        coefficients = {
            'age': -29.799, 'age_sq': 4.884, 'tot_chol': 13.540, 'age_tot_chol': -3.114,
            'hdl': -13.578, 'age_hdl': 3.149, 'treated_systolic': 2.019,
            'untreated_systolic': 1.957, 'diabetes': 0.661, 'smoker': 7.574, 'age_smoker': -1.665
        }
    
    # Calculate linear predictor
    lp = (coefficients['age'] * age_rf +
          coefficients['tot_chol'] * tot_chol_rf +
          coefficients['hdl'] * hdl_rf)
    
    if bp_meds:
        lp += coefficients['treated_systolic'] * math.log(systolic_rf)
    else:
        lp += coefficients['untreated_systolic'] * math.log(systolic_rf)
    
    if diabetes:
        lp += coefficients['diabetes']
    if smoker:
        lp += coefficients['smoker'] + coefficients['age_smoker'] * age_rf
    
    # Calculate 10-year risk
    risk = 1 - math.pow(baseline_survival, math.exp(lp - (coefficients['age'] * math.log(55) if gender.lower() == 'male' else coefficients['age'] * math.log(55))))
    
    risk = max(0, min(1, risk))  # Bound between 0-1
    
    risk_category = "Low" if risk < 0.075 else "Intermediate" if risk < 0.2 else "High"
    
    return {
        "risk_score": round(risk * 100, 2),
        "risk_category": risk_category,
        "recommendations": get_risk_recommendations(risk_category)
    }

def get_risk_recommendations(risk_category: str) -> List[str]:
    """Get evidence-based recommendations based on risk category."""
    recommendations = {
        "Low": [
            "Continue lifestyle modifications",
            "Reassess risk in 4-6 years",
            "Consider aspirin if benefit outweighs bleeding risk"
        ],
        "Intermediate": [
            "Intensify lifestyle modifications",
            "Consider moderate-intensity statin therapy",
            "Consider coronary calcium scoring for further risk stratification"
        ],
        "High": [
            "Initiate high-intensity statin therapy",
            "Target LDL-C reduction ≥50%",
            "Consider aspirin 81mg daily",
            "Optimize blood pressure control"
        ]
    }
    return recommendations.get(risk_category, [])

def analyze_lipid_panel(total_chol: float, ldl: float, hdl: float, tg: float, 
                       age: int = None, fasting: bool = True) -> Dict[str, Any]:
    """Comprehensive lipid panel analysis with ratios and risk assessment."""
    if total_chol < 50 or total_chol > 500:
        raise ValueError("Total cholesterol must be between 50-500 mg/dL")
    if ldl < 10 or ldl > 300:
        raise ValueError("LDL must be between 10-300 mg/dL")
    if hdl < 10 or hdl > 150:
        raise ValueError("HDL must be between 10-150 mg/dL")
    if tg < 10 or tg > 2000:
        raise ValueError("Triglycerides must be between 10-2000 mg/dL")
    
    non_hdl = total_chol - hdl
    chol_hdl_ratio = total_chol / hdl if hdl > 0 else float('inf')
    ldl_hdl_ratio = ldl / hdl if hdl > 0 else float('inf')
    tg_hdl_ratio = tg / hdl if hdl > 0 else float('inf')
    
    # ATP III classifications
    ldl_category = "Optimal" if ldl < 100 else "Near optimal" if ldl < 130 else "Borderline high" if ldl < 160 else "High" if ldl < 190 else "Very high"
    hdl_category = "Low" if hdl < 40 else "Normal" if hdl < 60 else "High"
    tg_category = "Normal" if tg < 150 else "Borderline high" if tg < 200 else "High" if tg < 500 else "Very high"
    
    # Calculate remnant cholesterol
    remnant_chol = total_chol - hdl - ldl
    
    return {
        "lipid_values": {
            "total_cholesterol": total_chol,
            "ldl": ldl,
            "hdl": hdl,
            "triglycerides": tg,
            "non_hdl": round(non_hdl, 1),
            "remnant_cholesterol": round(remnant_chol, 1)
        },
        "ratios": {
            "total_chol_hdl": round(chol_hdl_ratio, 2),
            "ldl_hdl": round(ldl_hdl_ratio, 2),
            "tg_hdl": round(tg_hdl_ratio, 2)
        },
        "classifications": {
            "ldl": ldl_category,
            "hdl": hdl_category,
            "triglycerides": tg_category
        },
        "fasting": fasting
    }


def calculate_framingham_risk(age: int, sex: str, total_chol: float, hdl: float,
                              systolic_bp: float, bp_treated: bool = False,
                              smoker: bool = False, diabetic: bool = False) -> Dict[str, Any]:
    """Calculate 10-year cardiovascular risk using Framingham Risk Score."""
    if sex.lower() not in ('male', 'female'):
        raise ValueError("Sex must be 'male' or 'female'")
    
    points = 0
    
    # Age points
    if sex.lower() == 'male':
        if age < 35: points += -9
        elif age < 40: points += -4
        elif age < 45: points += 0
        elif age < 50: points += 3
        elif age < 55: points += 6
        elif age < 60: points += 8
        elif age < 65: points += 10
        elif age < 70: points += 11
        else: points += 12
    else:
        if age < 35: points += -7
        elif age < 40: points += -3
        elif age < 45: points += 0
        elif age < 50: points += 3
        elif age < 55: points += 6
        elif age < 60: points += 8
        elif age < 65: points += 10
        elif age < 70: points += 12
        else: points += 14
    
    # Cholesterol points
    if total_chol < 160: points += 0
    elif total_chol < 200: points += 1
    elif total_chol < 240: points += 2
    elif total_chol < 280: points += 3
    else: points += 4
    
    # HDL points
    if hdl >= 60: points += -1
    elif hdl >= 50: points += 0
    elif hdl >= 40: points += 1
    else: points += 2
    
    # Blood pressure
    if systolic_bp < 120: points += 0
    elif systolic_bp < 130: points += 1 if not bp_treated else 2
    elif systolic_bp < 140: points += 1 if not bp_treated else 2
    elif systolic_bp < 160: points += 2 if not bp_treated else 3
    else: points += 3 if not bp_treated else 4
    
    if smoker: points += 2
    if diabetic: points += 2
    
    # Approximate risk percentage
    risk_table = {-3: 1, -2: 1, -1: 2, 0: 3, 1: 4, 2: 5, 3: 6, 4: 8,
                  5: 10, 6: 12, 7: 14, 8: 16, 9: 20, 10: 25, 11: 30}
    risk_pct = risk_table.get(min(max(points, -3), 11), 30)
    
    risk_category = 'low' if risk_pct < 10 else 'moderate' if risk_pct < 20 else 'high'
    
    return {
        'total_points': points,
        'ten_year_risk_percent': risk_pct,
        'risk_category': risk_category,
        'factors': {
            'age': age, 'sex': sex, 'total_cholesterol': total_chol,
            'hdl': hdl, 'systolic_bp': systolic_bp, 'bp_treated': bp_treated,
            'smoker': smoker, 'diabetic': diabetic
        }
    }


def recommend_statin_alternatives(ldl: float, risk_category: str,
                                   statin_intolerant: bool = False) -> List[Dict[str, Any]]:
    """Recommend statin alternatives based on patient profile."""
    alternatives = []
    
    if statin_intolerant or risk_category == 'high':
        alternatives.append({
            'drug_class': 'PCSK9 Inhibitors',
            'examples': ['Evolocumab (Repatha)', 'Alirocumab (Praluent)'],
            'ldl_reduction': '50-60%',
            'mechanism': 'Monoclonal antibodies that increase LDL receptor recycling'
        })
    
    alternatives.append({
        'drug_class': 'Ezetimibe',
        'examples': ['Zetia'],
        'ldl_reduction': '15-20%',
        'mechanism': 'Blocks cholesterol absorption in small intestine'
    })
    
    alternatives.append({
        'drug_class': 'Bempedoic Acid',
        'examples': ['Nexletol'],
        'ldl_reduction': '15-25%',
        'mechanism': 'ACL inhibitor upstream of HMG-CoA reductase'
    })
    
    if ldl > 190:
        alternatives.append({
            'drug_class': 'Inclisiran (RNA Therapeutics)',
            'examples': ['Leqvio'],
            'ldl_reduction': '50%',
            'mechanism': 'siRNA targeting PCSK9 mRNA — twice yearly injection'
        })
    
    return alternatives


class SkillEngine:
    """Cardiovascular Disease Research skill engine."""
    
    def __init__(self):
        self.name = SKILL_METADATA['name']
        self.version = SKILL_METADATA['version']
    
    def run(self, action: str, **kwargs) -> Dict[str, Any]:
        actions = {
            'lipid_panel': lambda: analyze_lipid_panel(**kwargs),
            'framingham_risk': lambda: calculate_framingham_risk(**kwargs),
            'statin_alternatives': lambda: recommend_statin_alternatives(**kwargs),
        }
        if action in actions:
            return actions[action]()
        return {'error': f'Unknown action: {action}'}


class TestCardiovascular(unittest.TestCase):
    """Unit tests for Cardiovascular Disease Research skill."""
    
    def test_metadata(self):
        self.assertEqual(SKILL_METADATA['id'], 'cardiovascular')
    
    def test_lipid_panel(self):
        result = analyze_lipid_panel(total_chol=200, ldl=120, hdl=55, tg=150)
        self.assertIn('lipid_values', result)
        self.assertIn('ratios', result)
        self.assertIn('classifications', result)
    
    def test_lipid_panel_invalid(self):
        with self.assertRaises(ValueError):
            analyze_lipid_panel(total_chol=10, ldl=120, hdl=55, tg=150)
    
    def test_framingham_risk(self):
        result = calculate_framingham_risk(
            age=55, sex='male', total_chol=220, hdl=45,
            systolic_bp=140, smoker=True
        )
        self.assertIn('ten_year_risk_percent', result)
        self.assertIn('risk_category', result)
    
    def test_statin_alternatives(self):
        result = recommend_statin_alternatives(ldl=200, risk_category='high', statin_intolerant=True)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
    
    def test_skill_engine(self):
        engine = SkillEngine()
        self.assertEqual(engine.name, 'Cardiovascular Disease Research')
    
    def test_prompts_exist(self):
        self.assertGreater(len(EXPERT_PROMPTS), 0)


if __name__ == '__main__':
    unittest.main()