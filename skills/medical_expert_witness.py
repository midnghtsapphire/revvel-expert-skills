import json
import re
import os
import math
import hashlib
import datetime
import statistics
import unittest
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, namedtuple
import requests

SKILL_METADATA = {
    "name": "Medical Expert Witness",
    "id": "medical_expert_witness",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Comprehensive medical expert witness analysis and report generation for legal proceedings, covering Daubert/Frye compliance, malpractice evaluation, causation analysis, and expert testimony preparation.",
    "capabilities": [
        "daubert_frye_compliance_check",
        "standard_of_care_analysis",
        "malpractice_case_evaluation",
        "causation_analysis",
        "damages_assessment",
        "life_care_plan_creation",
        "ime_report_generation",
        "deposition_preparation",
        "medical_chronology_builder",
        "medical_literature_review",
        "rebuttal_report_writer",
        "jury_friendly_explanation",
        "case_merit_screening",
        "statute_limitations_analysis",
        "informed_consent_analysis",
        "medical_board_standards"
    ],
    "domain": "legal_medical_expertise"
}

EXPERT_PROMPTS = {
    "daubert_analysis": """Analyze the following medical expert testimony for Daubert/Frye standard compliance:

Testimony: {testimony}
Jurisdiction: {jurisdiction}
Scientific Method: {scientific_method}
Peer Review Status: {peer_review}
Error Rate: {error_rate}
General Acceptance: {general_acceptance}

Provide a detailed compliance assessment including:
1. Reliability factors under Daubert
2. Frye general acceptance test
3. Potential challenges
4. Recommendations for strengthening admissibility""",

    "standard_of_care": """Evaluate the standard of care in this medical scenario:

Medical Specialty: {specialty}
Patient Presentation: {patient_presentation}
Provider Actions: {provider_actions}
Geographic Location: {location}
Time Period: {time_period}

Determine:
1. Applicable standard of care
2. Whether actions met/fell below standard
3. Supporting medical literature
4. Expert consensus guidelines""",

    "causation_analysis": """Perform causation analysis for this medical malpractice case:

Patient Injury: {injury}
Alleged Negligence: {negligence}
Timeline: {timeline}
Pre-existing Conditions: {pre_existing}
Alternative Causes: {alternative_causes}

Apply both:
1. But-for causation test
2. Substantial factor analysis
3. Proximate cause evaluation
4. Damages apportionment""",

    "damages_calculation": """Calculate damages for this medical injury:

Economic Damages:
- Medical expenses: {medical_expenses}
- Lost wages: {lost_wages}
- Future care costs: {future_care}
- Diminished earning capacity: {diminished_earning}

Non-economic:
- Pain and suffering multiplier: {multiplier}
- Jurisdiction caps: {caps}
- Life expectancy: {life_expectancy}

Provide:
1. Present value calculations
2. Per diem arguments
3. Comparable verdicts
4. Total damage range""",

    "life_care_plan": """Create a life care plan for:

Patient Age: {age}
Injury Type: {injury_type}
Severity: {severity}
Life Expectancy: {life_expectancy}
Current Function: {current_function}

Include:
1. Medical needs (present and future)
2. Therapeutic interventions
3. Assistive devices
4. Home modifications
5. Vocational rehabilitation
6. Cost projections with inflation""",

    "ime_report": """Generate an Independent Medical Examination report:

Patient: {patient_name}
Date of Exam: {exam_date}
Referral Source: {referral_source}
History Provided: {history}
Examination Findings: {findings}
Diagnostic Tests: {tests}

Structure:
1. Introduction and methodology
2. History review
3. Physical examination
4. Diagnostic impressions
5. Causation analysis
6. Prognosis
7. Recommendations""",

    "deposition_prep": """Prepare deposition questions for medical expert:

Expert Specialty: {specialty}
Case Issues: {case_issues}
Weaknesses: {weaknesses}
Key Facts: {key_facts}
Damages: {damages}

Provide:
1. Qualification challenges
2. Standard of care questions
3. Causation challenges
4. Damages limitations
5. Bias exposure questions
6. Prior testimony impeachment""",

    "medical_chronology": """Build medical chronology from records:

Patient: {patient}
Date Range: {date_range}
Records: {medical_records}

Create:
1. Timeline of events
2. Provider encounters
3. Treatment progression
4. Symptom evolution
5. Key medical decisions
6. Potential negligence markers""",

    "literature_review": """Review medical literature for litigation support:

Medical Issue: {medical_issue}
Key Terms: {search_terms}
Date Range: {date_range}
Journals: {journals}

Provide:
1. Relevant studies summary
2. Methodology critique
3. Statistical significance
4. Clinical applicability
5. Expert consensus
6. Citation for court use""",

    "jury_explanation": """Explain complex medical concept to jury:

Medical Concept: {concept}
Patient Impact: {impact}
Technical Details: {technical_details}
Jury Education Level: {education_level}

Create:
1. Simple analogy
2. Visual description
3. Key takeaway points
4. Impact on daily life
5. Why it matters for case
6. Memorable phrasing"""
}

INTEGRATION_POINTS = {
    "pubmed_api": {
        "type": "api",
        "endpoint": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
        "description": "PubMed medical literature database",
        "auth_method": "api_key",
        "documentation_url": "https://www.ncbi.nlm.nih.gov/books/NBK25501/"
    },
    "westlaw_edge": {
        "type": "api",
        "endpoint": "https://api.westlaw.com/edge",
        "description": "Legal research and case law database",
        "auth_method": "oauth2",
        "documentation_url": "https://developer.thomsonreuters.com/westlaw-edge"
    },
    "medical_board_db": {
        "type": "database",
        "endpoint": "postgresql://medical_boards:5432/standards",
        "description": "State medical board standards and disciplinary records",
        "auth_method": "service_account",
        "documentation_url": "https://medical-boards.docs.revvel.com"
    },
    "damages_calculator": {
        "type": "tool",
        "endpoint": "internal://damages_calculator/v2",
        "description": "Economic damages calculation engine",
        "auth_method": "service_token",
        "documentation_url": "https://tools.revvel.com/damages"
    },
    "statute_api": {
        "type": "api",
        "endpoint": "https://statutes.revvel.com/api/v1",
        "description": "State-by-state statute of limitations database",
        "auth_method": "api_key",
        "documentation_url": "https://docs.revvel.com/statutes"
    }
}

MedicalRecord = namedtuple('MedicalRecord', ['date', 'provider', 'type', 'notes', 'significance'])
DamagesBreakdown = namedtuple('DamagesBreakdown', ['economic', 'non_economic', 'total', 'present_value'])
CausationFactors = namedtuple('CausationFactors', ['but_for', 'substantial_factor', 'proximate_cause', 'pre_existing'])

def parse_medical_record(text: str) -> List[MedicalRecord]:
    """Parse raw medical record text into structured MedicalRecord objects."""
    records = []
    entries = re.split(r'\n\s*\n', text.strip())
    
    for entry in entries:
        lines = entry.split('\n')
        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', entry)
        date = datetime.datetime.strptime(date_match.group(1), '%m/%d/%Y') if date_match else None
        
        provider = None
        record_type = None
        notes = []
        
        for line in lines:
            if line.startswith('Provider:'):
                provider = line.split(':', 1)[1].strip()
            elif line.startswith('Type:'):
                record_type = line.split(':', 1)[1].strip()
            elif line.startswith('Notes:'):
                notes.append(line.split(':', 1)[1].strip())
        
        significance = calculate_record_significance(' '.join(notes))
        records.append(MedicalRecord(date, provider, record_type, ' '.join(notes), significance))
    
    return sorted(records, key=lambda x: x.date or datetime.datetime.min)

def calculate_record_significance(notes: str) -> int:
    """Calculate significance score (1-10) for medical record notes."""
    keywords = {
        'diagnosis': 8, 'surgery': 9, 'emergency': 10, 'complication': 9,
        'error': 10, 'malpractice': 10, 'negligence': 9, 'standard': 7,
        'breach': 8, 'injury': 7, 'damages': 6, 'treatment': 5
    }
    
    score = 1
    notes_lower = notes.lower()
    for keyword, weight in keywords.items():
        if keyword in notes_lower:
            score = max(score, weight)
    
    return min(score, 10)

def check_daubert_compliance(methodology: Dict[str, Any]) -> Dict[str, Any]:
    """Check Daubert standard compliance for expert methodology."""
    compliance = {
        'testable': False,
        'peer_reviewed': False,
        'error_rate_known': False,
        'standards': False,
        'general_acceptance': False,
        'overall_score': 0
    }
    
    if methodology.get('testable', False):
        compliance['testable'] = True
    if methodology.get('peer_reviewed', False):
        compliance['peer_reviewed'] = True
    if methodology.get('error_rate') is not None:
        compliance['error_rate_known'] = True
    if methodology.get('standards', False):
        compliance['standards'] = True
    if methodology.get('general_acceptance', 0) > 0.7:
        compliance['general_acceptance'] = True
    
    compliance['overall_score'] = sum(compliance.values()) - compliance['overall_score']
    compliance['admissible'] = compliance['overall_score'] >= 4
    
    return compliance

def calculate_standard_of_care_deviation(
    specialty: str, 
    actions: List[str], 
    guidelines: List[str]
) -> Dict[str, Any]:
    """Calculate deviation from standard of care."""
    deviation = {
        'specialty': specialty,
        'deviations': [],
        'severity': 0,
        'breach_probability': 0.0
    }
    
    guideline_set = set(guidelines)
    action_set = set(actions)
    
    missing_actions = guideline_set - action_set
    extra_actions = action_set - guideline_set
    
    for action in missing_actions:
        deviation['deviations'].append({
            'type': 'omission',
            'action': action,
            'severity': 8
        })
    
    for action in extra_actions:
        deviation['deviations'].append({
            'type': 'commission',
            'action': action,
            'severity': 5
        })
    
    if deviation['deviations']:
        deviation['severity'] = max(d['severity'] for d in deviation['deviations'])
        deviation['breach_probability'] = min(0.95, len(deviation['deviations']) * 0.3)
    
    return deviation

def analyze_causation(
    negligence: str,
    injury: str,
    timeline: List[Dict[str, Any]],
    pre_existing: List[str]
) -> CausationFactors:
    """Analyze causation factors in medical malpractice."""
    but_for = True
    substantial_factor = True
    proximate_cause = True
    
    # Simple but-for test
    if not timeline or timeline[0]['event'] != negligence:
        but_for = False
    
    # Substantial factor analysis
    if pre_existing and any(cond in injury.lower() for cond in pre_existing):
        substantial_factor = False
    
    # Proximate cause (foreseeability)
    foreseeable_injuries = ['infection', 'bleeding', 'nerve_damage', 'organ_failure']
    if not any(inj in injury.lower() for inj in foreseeable_injuries):
        proximate_cause = False
    
    return CausationFactors(but_for, substantial_factor, proximate_cause, pre_existing)

def calculate_damages(
    medical_expenses: float,
    lost_wages: float,
    future_care: float,
    multiplier: float,
    years: int,
    discount_rate: float = 0.03
) -> DamagesBreakdown:
    """Calculate economic and non-economic damages."""
    economic = medical_expenses + lost_wages + future_care
    
    # Present value calculation
    pv_factor = (1 - (1 + discount_rate) ** -years) / discount_rate
    economic_pv = economic * pv_factor
    
    non_economic = economic * multiplier
    non_economic_pv = non_economic * pv_factor
    
    total = economic_pv + non_economic_pv
    
    return DamagesBreakdown(economic_pv, non_economic_pv, total, total)

def build_life_care_plan(
    age: int,
    injury_type: str,
    severity: int,
    life_expectancy: int
) -> Dict[str, Any]:
    """Build comprehensive life care plan."""
    plan = {
        'patient_age': age,
        'injury_type': injury_type,
        'severity': severity,
        'life_expectancy': life_expectancy,
        'annual_costs': {},
        'total_cost': 0
    }
    
    base_costs = {
        'medical_care': 50000 * severity,
        'therapy': 25000 * severity,
        'medications': 15000 * severity,
        'assistive_devices': 10000 * severity,
        'home_modifications': 75000 if severity > 7 else 25000
    }
    
    years_remaining = life_expectancy - age
    for category, annual_cost in base_costs.items():
        plan['annual_costs'][category] = annual_cost
        plan['total_cost'] += annual_cost * years_remaining
    
    # Add 3% annual inflation
    plan['total_cost'] *= 1.5
    
    return plan

def generate_ime_report(
    patient_info: Dict[str, Any],
    findings: Dict[str, Any]
) -> str:
    """Generate Independent Medical Examination report."""
    report = f"""
INDEPENDENT MEDICAL EXAMINATION REPORT

Patient: {patient_info['name']}
Date of Birth: {patient_info['dob']}
Date of Examination: {findings['exam_date']}
Referral Source: {findings['referral']}

MEDICAL HISTORY:
{patient_info['history']}

PHYSICAL EXAMINATION:
{findings['physical_exam']}

DIAGNOSTIC FINDINGS:
{findings['diagnostics']}

IMPRESSION:
Based on the examination and review of medical records, the patient has sustained {findings['diagnosis']} as a result of {findings['causation']}.

PROGNOSIS:
{findings['prognosis']}

RECOMMENDATIONS:
{findings['recommendations']}

Respectfully submitted,
Medical Expert
{findings['exam_date']}
"""
    return report.strip()

def statute_of_limitations(
    jurisdiction: str,
    injury_date: str,
    discovery_date: Optional[str] = None
) -> Dict[str, Any]:
    """Calculate statute of limitations for medical malpractice."""
    statutes = {
        'CA': 3,
        'NY': 2.5,
        'TX': 2,
        'FL': 2,
        'IL': 2,
        'PA': 2,
        'OH': 1,
        'MI': 2,
        'GA': 2,
        'NC': 3
    }
    
    injury_dt = datetime.datetime.strptime(injury_date, '%Y-%m-%d')
    discovery_dt = datetime.datetime.strptime(discovery_date, '%Y-%m-%d') if discovery_date else injury_dt
    
    years = statutes.get(jurisdiction.upper(), 2)
    deadline = discovery_dt + datetime.timedelta(days=years * 365)
    
    remaining = (deadline - datetime.datetime.now()).days
    
    return {
        'jurisdiction': jurisdiction,
        'limit_years': years,
        'deadline': deadline.strftime('%Y-%m-%d'),
        'days_remaining': max(0, remaining),
        'expired': remaining < 0
    }

def create_medical_chronology(records: List[MedicalRecord]) -> str:
    """Create chronological medical history from records."""
    chronology = "MEDICAL CHRONOLOGY\n" + "="*50 + "\n\n"
    
    for record in records:
        date_str = record.date.strftime('%m/%d/%Y') if record.date else 'Unknown'
        chronology += f"{date_str} - {record.provider}\n"
        chronology += f"Type: {record.type}\n"
        chronology += f"Notes: {record.notes}\n"
        chronology += f"Significance: {record.significance}/10\n"
        chronology += "-"*30 + "\n"
    
    return chronology

class SkillEngine:
    """Main skill engine for Medical Expert Witness capabilities."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """Setup basic logging."""
        class Logger:
            def info(self, msg): print(f"INFO: {msg}")
            def error(self, msg): print(f"ERROR: {msg}")
            def warning(self, msg): print(f"WARNING: {msg}")
        return Logger()
    
    def run(self, capability: str, **kwargs) -> Any:
        """Dispatch to appropriate capability method."""
        method_map = {
            'daubert_frye_compliance_check': self.check_daubert_compliance,
            'standard_of_care_analysis': self.analyze_standard_of_care,
            'malpractice_case_evaluation': self.evaluate_malpractice,
            'causation_analysis': self.analyze_causation,
            'damages_assessment': self.assess_damages,
            'life_care_plan_creation': self.create_life_care_plan,
            'ime_report_generation': self.generate_ime_report,
            'deposition_preparation': self.prepare_deposition,
            'medical_chronology_builder': self.build_chronology,
            'medical_literature_review': self.review_literature,
            'rebuttal_report_writer': self.write_rebuttal,
            'jury_friendly_explanation': self.explain_to_jury,
            'case_merit_screening': self.screen_case_merit,
            'statute_limitations_analysis': self.analyze_statute,
            'informed_consent_analysis': self.analyze_consent,
            'medical_board_standards': self.get_board_standards
        }
        
        if capability not in method_map:
            raise ValueError(f"Unknown capability: {capability}")
        
        return method_map[capability](**kwargs)
    
    def check_daubert_compliance(self, methodology: Dict[str, Any]) -> Dict[str, Any]:
        """Check Daubert standard compliance."""
        return check_daubert_compliance(methodology)
    
    def analyze_standard_of_care(self, specialty: str, actions: List[str], guidelines: List[str]) -> Dict[str, Any]:
        """Analyze standard of care deviation."""
        return calculate_standard_of_care_deviation(specialty, actions, guidelines)
    
    def evaluate_malpractice(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate medical malpractice case."""
        evaluation = {
            'standard_of_care': self.analyze_standard_of_care(
                case_data['specialty'],
                case_data['actions'],
                case_data['guidelines']
            ),
            'causation': self.analyze_causation(
                case_data['negligence'],
                case_data['injury'],
                case_data['timeline'],
                case_data.get('pre_existing', [])
            ),
            'damages': self.assess_damages(**case_data['damages']),
            'merit_score': 0
        }
        
        # Calculate merit score
        if evaluation['standard_of_care']['breach_probability'] > 0.7:
            evaluation['merit_score'] += 40
        if all([evaluation['causation'].but_for, evaluation['causation'].substantial_factor]):
            evaluation['merit_score'] += 40
        if evaluation['damages'].total > 100000:
            evaluation['merit_score'] += 20
            
        return evaluation
    
    def analyze_causation(self, negligence: str, injury: str, timeline: List[Dict], pre_existing: List[str]) -> CausationFactors:
        """Analyze causation factors."""
        return analyze_causation(negligence, injury, timeline, pre_existing)
    
    def assess_damages(self, **kwargs) -> DamagesBreakdown:
        """Assess damages in case."""
        return calculate_damages(**kwargs)
    
    def create_life_care_plan(self, age: int, injury_type: str, severity: int, life_expectancy: int) -> Dict[str, Any]:
        """Create life care plan."""
        return build_life_care_plan(age, injury_type, severity, life_expectancy)
    
    def generate_ime_report(self, patient_info: Dict, findings: Dict) -> str:
        """Generate IME report."""
        return generate_ime_report(patient_info, findings)
    
    def prepare_deposition(self, expert_info: Dict) -> List[str]:
        """Prepare deposition questions."""
        questions = [
            f"Please state your qualifications in {expert_info['specialty']}",
            "Have you ever been disciplined by any medical board?",
            "What methodology did you use to determine the standard of care?",
            "Are you familiar with the guidelines published by {expert_info['guideline_source']}?",
            "What is your error rate in similar cases?",
            "How much are you being paid for your testimony?",
            "Have you testified for the same attorney before?"
        ]
        return questions
    
    def build_chronology(self, medical_records: str) -> str:
        """Build medical chronology."""
        records = parse_medical_record(medical_records)
        return create_medical_chronology(records)
    
    def review_literature(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Review medical literature."""
        # Mock implementation - would integrate with PubMed
        return [
            {
                'title': f"Study on {query}",
                'authors': ['Smith, J', 'Johnson, K'],
                'journal': 'Medical Journal',
                'year': 2023,
                'relevance': 0.85,
                'summary': f"Key findings related to {query}"
            }
        ]
    
    def write_rebuttal(self, original_report: str, criticisms: List[str]) -> str:
        """Write rebuttal report."""
        rebuttal = "REBUTTAL REPORT\n" + "="*50 + "\n\n"
        rebuttal += "This report addresses the following criticisms:\n\n"
        
        for criticism in criticisms:
            rebuttal += f"CRITICISM: {criticism}\n"
            rebuttal += "RESPONSE: [Detailed response would be provided]\n\n"
        
        return rebuttal
    
    def explain_to_jury(self, concept: str, complexity_level: str = "basic") -> str:
        """Explain medical concept to jury."""
        explanations = {
            "standard_of_care": "The standard of care is what a reasonably careful doctor would do in the same situation",
            "causation": "We must prove the doctor's mistake actually caused the injury",
            "damages": "Damages include medical bills, lost wages, and pain and suffering"
        }
        
        return explanations.get(concept, f"Simple explanation of {concept}")
    
    def screen_case_merit(self, case_data: Dict) -> Dict[str, Any]:
        """Screen case for merit."""
        evaluation = self.evaluate_malpractice(case_data)
        
        return {
            'merit_score': evaluation['merit_score'],
            'recommendation': 'Pursue' if evaluation['merit_score'] >= 70 else 'Decline',
            'key_issues': [
                f"Standard of care breach: {evaluation['standard_of_care']['breach_probability']:.0%}",
                f"Causation strength: {'Strong' if all([evaluation['causation'].but_for, evaluation['causation'].substantial_factor]) else 'Weak'}",
                f"Damages: ${evaluation['damages'].total:,.0f}"
            ]
        }
    
    def analyze_statute(self, jurisdiction: str, injury_date: str, discovery_date: str = None) -> Dict[str, Any]:
        """Analyze statute of limitations."""
        return statute_of_limitations(jurisdiction, injury_date, discovery_date)
    
    def analyze_consent(self, consent_form: str, procedure: str) -> Dict[str, Any]:
        """Analyze informed consent."""
        required_elements = ['risks', 'benefits', 'alternatives', 'complications']
        present_elements = [elem for elem in required_elements if elem in consent_form.lower()]
        
        return {
            'complete': len(present_elements) == len(required_elements),
            'missing_elements': [elem for elem in required_elements if elem not in present_elements],
            'adequacy_score': len(present_elements) / len(required_elements)
        }
    
    def get_board_standards(self, state: str, specialty: str) -> Dict[str, Any]:
        """Get medical board standards."""
        return {
            'state': state,
            'specialty': specialty,
            'licensing_requirements': ['Medical degree', 'Residency', 'Board certification'],
            'continuing_education': 40,  # hours per year
            'disciplinary_actions': 'Check state medical board website'
        }

class TestMedicalExpertWitness(unittest.TestCase):
    """Test cases for Medical Expert Witness skill."""
    
    def test_metadata(self):
        """Test skill metadata."""
        self.assertEqual(SKILL_METADATA['name'], "Medical Expert Witness")
        self.assertIn('daubert_frye_compliance_check', SKILL_METADATA['capabilities'])
    
    def test_parse_medical_record(self):
        """Test medical record parsing."""
        text = """
Provider: Dr. Smith
Type: Consultation
Date: 01/15/2023
Notes: Patient presents with chest pain, rule out MI
"""
        records = parse_medical_record(text)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].provider, "Dr. Smith")
    
    def test_daubert_compliance(self):
        """Test Daubert compliance check."""
        methodology = {
            'testable': True,
            'peer_reviewed': True,
            'error_rate': 0.05,
            'standards': True,
            'general_acceptance': 0.8
        }
        result = check_daubert_compliance(methodology)
        self.assertTrue(result['admissible'])
    
    def test_standard_of_care(self):
        """Test standard of care analysis."""
        result = calculate_standard_of_care_deviation(
            'cardiology',
            ['ECG', 'troponin', 'cath'],
            ['ECG', 'troponin', 'cath', 'echo']
        )
        self.assertEqual(len(result['deviations']), 1)
    
    def test_causation_analysis(self):
        """Test causation analysis."""
        factors = analyze_causation(
            'delayed diagnosis',
            'heart damage',
            [{'event': 'delayed diagnosis', 'date': '2023-01-01'}],
            ['hypertension']
        )
        self.assertIsInstance(factors, CausationFactors)
    
    def test_damages_calculation(self):
        """Test damages calculation."""
        damages = calculate_damages(
            medical_expenses=100000,
            lost_wages=50000,
            future_care=200000,
            multiplier=2.5,
            years=20
        )
        self.assertGreater(damages.total, 0)
    
    def test_life_care_plan(self):
        """Test life care plan creation."""
        plan = build_life_care_plan(35, 'spinal cord injury', 8, 75)
        self.assertIn('annual_costs', plan)
        self.assertGreater(plan['total_cost'], 0)
    
    def test_ime_report(self):
        """Test IME report generation."""
        report = generate_ime_report(
            {'name': 'John Doe', 'dob': '1980-01-01', 'history': 'Back pain'},
            {'exam_date': '2023-06-01', 'referral': 'Attorney Smith', 'diagnosis': 'Herniated disc'}
        )
        self.assertIn('INDEPENDENT MEDICAL EXAMINATION REPORT', report)
    
    def test_statute_limitations(self):
        """Test statute of limitations."""
        result = statute_of_limitations('CA', '2023-01-01')
        self.assertEqual(result['limit_years'], 3)
        self.assertIn('deadline', result)
    
    def test_skill_engine(self):
        """Test SkillEngine class."""
        engine = SkillEngine()
        result = engine.run('daubert_frye_compliance_check', methodology={'testable': True})
        self.assertIsInstance(result, dict)
    
    def test_case_merit_screening(self):
        """Test case merit screening."""
        engine = SkillEngine()
        case_data = {
            'specialty': 'surgery',
            'actions': ['surgery'],
            'guidelines': ['surgery', 'follow_up'],
            'negligence': 'wrong site surgery',
            'injury': 'nerve damage',
            'timeline': [{'event': 'wrong site surgery', 'date': '2023-01-01'}],
            'damages': {
                'medical_expenses': 100000,
                'lost_wages': 50000,
                'future_care': 200000,
                'multiplier': 2.5,
                'years': 20
            }
        }
        result = engine.screen_case_merit(case_data)
        self.assertIn('merit_score', result)

if __name__ == '__main__':
    unittest.main()