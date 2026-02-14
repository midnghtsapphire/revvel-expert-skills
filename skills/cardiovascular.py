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
            "ldl