import json
import re
import os
import hashlib
import statistics
import math
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import unittest
import logging

SKILL_METADATA = {
    "name": "Expert Witness",
    "id": "expert_witness",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Comprehensive expert witness preparation and analysis system for legal proceedings, covering Daubert compliance, report generation, deposition prep, and cross-examination strategies",
    "capabilities": [
        "daubert_compliance_check",
        "expert_report_generation",
        "deposition_preparation",
        "cross_examination_strategy",
        "expert_qualification_analysis",
        "testimony_admissibility_assessment",
        "expert_discovery_compliance",
        "rebuttal_report_creation"
    ],
    "domain": "Legal/Forensic Expert Testimony"
}

EXPERT_PROMPTS = {
    "daubert_analysis": """
Analyze the following expert testimony for Daubert standard compliance:
Expert Field: {expert_field}
Proposed Testimony: {proposed_testimony}
Methodology Used: {methodology}
Peer Review Status: {peer_review}
Error Rate: {error_rate}
Acceptance in Scientific Community: {community_acceptance}

Provide a detailed assessment covering:
1. Whether the testimony is based on sufficient facts or data
2. Whether it is the product of reliable principles and methods
3. Whether the expert has reliably applied the principles and methods to the facts of the case
4. Specific recommendations for strengthening admissibility
""",
    
    "expert_report_draft": """
Draft a comprehensive expert witness report based on:
Case Type: {case_type}
Expert Specialty: {expert_specialty}
Key Findings: {key_findings}
Methodology Employed: {methodology}
Data Sources: {data_sources}
Opinions Formed: {opinions}
Exhibits: {exhibits}

Structure the report with:
1. Executive Summary
2. Expert Qualifications
3. Materials Reviewed
4. Methodology and Approach
5. Factual Findings
6. Expert Opinions
7. Supporting Exhibits
8. Expert Declaration
""",
    
    "deposition_prep": """
Prepare deposition preparation materials for expert witness:
Expert Name: {expert_name}
Specialty: {specialty}
Case Issues: {case_issues}
Opposing Counsel Style: {opposing_style}
Key Vulnerabilities: {vulnerabilities}

Include:
1. Likely deposition questions with model answers
2. Document production checklist
3. Credentials to emphasize
4. Weaknesses to address proactively
5. Demeanor and presentation tips
""",
    
    "cross_examination_prep": """
Develop cross-examination strategy for opposing expert:
Expert Name: {opposing_expert}
Field: {expert_field}
Testimony Focus: {testimony_focus}
Known Methodology: {methodology}
Previous Cases: {previous_cases}

Provide:
1. Potential impeachment angles
2. Daubert challenge opportunities
3. Credentials to question
4. Methodology attacks
5. Prior inconsistent statements to explore
6. Demonstrative exhibits for contradiction
""",
    
    "expert_qualification": """
Evaluate expert witness qualifications:
Education: {education}
Experience: {experience}
Certifications: {certifications}
Publications: {publications}
Prior Testimony: {prior_testimony}
Professional Membershiphips: {memberships}

Assess:
1. Qualification under FRE 702
2. Specialized knowledge demonstration
3. Relevance to case issues
4. Potential disqualification issues
5. Comparison to opposing expert qualifications
""",
    
    "rebuttal_report": """
Draft rebuttal expert report responding to:
Original Expert Report: {original_report}
Points of Disagreement: {disagreements}
Supporting Evidence: {supporting_evidence}
Alternative Methodology: {alternative_methodology}

Structure:
1. Introduction and Qualifications
2. Materials Reviewed
3. Points of Agreement
4. Points of Disagreement with Analysis
5. Alternative Explanations
6. Conclusions and Opinions
7. Supporting Documentation
""",
    
    "discovery_compliance": """
Review expert discovery materials for compliance:
Expert Materials: {expert_materials}
Discovery Requests: {discovery_requests}
Production Timeline: {timeline}
Privilege Claims: {privilege_claims}

Analyze:
1. Completeness of production
2. Timeliness issues
3. Privilege assertions validity
4. Supplemental disclosure needs
5. Sanction risks
""",
    
    "testimony_admissibility": """
Assess admissibility of proposed expert testimony:
Jurisdiction: {jurisdiction}
Type of Evidence: {evidence_type}
Expert Reliability: {expert_reliability}
Fit to Facts: {fit_to_facts}
Prejudicial Effect: {prejudicial_effect}

Evaluate under:
1. FRE 702/703 standards
2. Daubert factors if applicable
3. State law equivalents
4. Specific case law precedents
5. Likely evidentiary challenges
"""
}

INTEGRATION_POINTS = {
    "pacer_api": {
        "type": "api",
        "endpoint": "https://pacer.uscourts.gov/api/",
        "description": "Access federal court records for expert witness history and case precedents",
        "auth_method": "API key with certificate",
        "documentation_url": "https://pacer.uscourts.gov/api-docs"
    },
    "westlaw_edge": {
        "type": "api",
        "endpoint": "https://api.westlaw.com/edge/",
        "description": "Legal research database for expert witness precedents and Daubert challenges",
        "auth_method": "OAuth 2.0",
        "documentation_url": "https://developer.westlaw.com/docs"
    },
    "expert_directory": {
        "type": "database",
        "endpoint": "postgresql://expert-db.revvel.ai:5432/experts",
        "description": "Internal database of expert witness profiles and testimony history",
        "auth_method": "JWT token",
        "documentation_url": "https://docs.revvel.ai/integrations/expert-directory"
    },
    "forensic_tools": {
        "type": "tool",
        "endpoint": "local",
        "description": "Suite of forensic analysis tools for evidence processing",
        "auth_method": "Local authentication",
        "documentation_url": "https://docs.revvel.ai/integrations/forensic-suite"
    }
}

def parse_expert_credentials(credentials_text: str) -> Dict[str, Any]:
    """Parse and structure expert witness credentials from free-form text."""
    sections = re.split(r'\n\s*\n', credentials_text.strip())
    parsed = {
        'education': [],
        'experience': [],
        'certifications': [],
        'publications': [],
        'testimony_history': []
    }
    
    current_section = None
    for section in sections:
        section_lower = section.lower()
        if 'education' in section_lower:
            current_section = 'education'
        elif 'experience' in section_lower or 'employment' in section_lower:
            current_section = 'experience'
        elif 'certification' in section_lower or 'license' in section_lower:
            current_section = 'certifications'
        elif 'publication' in section_lower or 'article' in section_lower:
            current_section = 'publications'
        elif 'testimony' in section_lower or 'court' in section_lower:
            current_section = 'testimony_history'
        
        if current_section:
            lines = [line.strip('- •').strip() for line in section.split('\n') if line.strip()]
            parsed[current_section].extend([line for line in lines if len(line) > 10])
    
    return parsed

def calculate_daubert_score(methodology: str, peer_reviewed: bool, error_rate: float, 
                           general_acceptance: bool, publications: int) -> float:
    """Calculate Daubert standard compliance score (0-100)."""
    score = 50.0  # Base score
    
    # Peer review factor
    if peer_reviewed:
        score += 15
    
    # Error rate factor (lower is better)
    if error_rate <= 0.01:
        score += 15
    elif error_rate <= 0.05:
        score += 10
    elif error_rate <= 0.10:
        score += 5
    
    # General acceptance factor
    if general_acceptance:
        score += 10
    
    # Publications factor
    if publications >= 10:
        score += 10
    elif publications >= 5:
        score += 7
    elif publications >= 2:
        score += 5
    
    return min(score, 100.0)

def generate_expert_timeline(events: List[Dict[str, Any]]) -> str:
    """Generate formatted timeline of expert witness activities."""
    sorted_events = sorted(events, key=lambda x: x.get('date', ''))
    
    timeline = "EXPERT WITNESS ACTIVITY TIMELINE\n"
    timeline += "=" * 50 + "\n\n"
    
    for event in sorted_events:
        date = event.get('date', 'Unknown')
        activity = event.get('activity', '')
        description = event.get('description', '')
        timeline += f"[{date}] {activity}\n"
        if description:
            timeline += f"  Details: {description}\n"
        timeline += "\n"
    
    return timeline


def prepare_cross_examination(expert_profile: Dict[str, Any], opposing_claims: List[str]) -> Dict[str, Any]:
    """Prepare cross-examination strategy for opposing expert."""
    strategies = []
    
    # Check for bias indicators
    if expert_profile.get('percentage_plaintiff', 0) > 80:
        strategies.append({
            'type': 'bias',
            'question': 'Isn\'t it true that over 80% of your work is for plaintiff attorneys?',
            'goal': 'Establish potential bias'
        })
    
    if expert_profile.get('percentage_defendant', 0) > 80:
        strategies.append({
            'type': 'bias',
            'question': 'Isn\'t it true that over 80% of your work is for defense attorneys?',
            'goal': 'Establish potential bias'
        })
    
    # Check methodology weaknesses
    if not expert_profile.get('peer_reviewed', False):
        strategies.append({
            'type': 'methodology',
            'question': 'Your methodology has not been peer-reviewed, correct?',
            'goal': 'Challenge reliability under Daubert'
        })
    
    # Check for contradictions with opposing claims
    for claim in opposing_claims:
        strategies.append({
            'type': 'contradiction',
            'question': f'How do you reconcile your opinion with the finding that {claim}?',
            'goal': 'Highlight inconsistencies'
        })
    
    return {
        'total_strategies': len(strategies),
        'strategies': strategies,
        'recommended_order': ['bias', 'methodology', 'contradiction']
    }


def generate_deposition_outline(case_type: str, expert_field: str, key_issues: List[str]) -> Dict[str, Any]:
    """Generate a deposition outline for expert witness examination."""
    outline = {
        'case_type': case_type,
        'expert_field': expert_field,
        'sections': []
    }
    
    # Standard sections
    outline['sections'].append({
        'title': 'Qualifications and Background',
        'questions': [
            'State your full name and professional address.',
            'Describe your educational background.',
            'List your professional certifications.',
            f'How long have you practiced in {expert_field}?',
            'How many times have you testified as an expert?'
        ]
    })
    
    outline['sections'].append({
        'title': 'Engagement and Compensation',
        'questions': [
            'Who retained you in this matter?',
            'What is your hourly rate for this engagement?',
            'What is your total compensation to date?',
            'What materials did you review?'
        ]
    })
    
    # Issue-specific sections
    for issue in key_issues:
        outline['sections'].append({
            'title': f'Analysis of {issue}',
            'questions': [
                f'What is your opinion regarding {issue}?',
                f'What methodology did you use to analyze {issue}?',
                f'What facts support your conclusion about {issue}?',
                f'Are there alternative explanations for {issue}?'
            ]
        })
    
    return outline


class SkillEngine:
    """Expert Witness skill engine."""
    
    def __init__(self):
        self.name = SKILL_METADATA['name']
        self.version = SKILL_METADATA['version']
    
    def run(self, action: str, **kwargs) -> Dict[str, Any]:
        actions = {
            'daubert_check': lambda: assess_daubert_compliance(**kwargs),
            'generate_report': lambda: generate_expert_report(**kwargs),
            'cross_exam': lambda: prepare_cross_examination(**kwargs),
            'deposition': lambda: generate_deposition_outline(**kwargs),
            'timeline': lambda: generate_expert_timeline(**kwargs),
            'credibility': lambda: calculate_expert_credibility(**kwargs),
        }
        if action in actions:
            return actions[action]()
        return {'error': f'Unknown action: {action}'}


class TestExpertWitness(unittest.TestCase):
    """Unit tests for Expert Witness skill."""
    
    def test_metadata(self):
        self.assertEqual(SKILL_METADATA['id'], 'expert_witness')
        self.assertIn('daubert_compliance_check', SKILL_METADATA['capabilities'])
    
    def test_daubert_compliance(self):
        result = assess_daubert_compliance(
            methodology='Peer-reviewed statistical analysis',
            peer_reviewed=True,
            error_rate=0.03,
            testable=True,
            general_acceptance=True
        )
        self.assertIn('overall_score', result)
        self.assertGreater(result['overall_score'], 0)
    
    def test_expert_report(self):
        result = generate_expert_report(
            expert_name='Dr. Smith',
            case_number='2024-CV-001',
            expert_field='Forensic Accounting',
            opinions=['Defendant committed fraud'],
            methodology='Statistical analysis of financial records',
            facts_relied_upon=['Bank statements', 'Tax returns']
        )
        self.assertIn('report_text', result)
        self.assertIn('Dr. Smith', result['report_text'])
    
    def test_credibility_score(self):
        score = calculate_expert_credibility(
            years_experience=20,
            publications=15,
            prior_testimony_count=30,
            daubert_challenges_survived=8,
            daubert_challenges_total=10,
            peer_reviewed=True,
            error_rate=0.02,
            general_acceptance=True
        )
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_cross_examination(self):
        result = prepare_cross_examination(
            expert_profile={'percentage_plaintiff': 90, 'peer_reviewed': False},
            opposing_claims=['The data was incomplete']
        )
        self.assertIn('strategies', result)
        self.assertGreater(result['total_strategies'], 0)
    
    def test_deposition_outline(self):
        result = generate_deposition_outline(
            case_type='Medical Malpractice',
            expert_field='Cardiology',
            key_issues=['Standard of care', 'Causation']
        )
        self.assertIn('sections', result)
        self.assertGreater(len(result['sections']), 2)
    
    def test_timeline(self):
        events = [
            {'date': '2024-01-15', 'activity': 'Retained', 'description': 'Initial engagement'},
            {'date': '2024-02-20', 'activity': 'Report Filed', 'description': 'Expert report submitted'}
        ]
        result = generate_expert_timeline(events)
        self.assertIn('2024-01-15', result)
        self.assertIn('Retained', result)
    
    def test_empty_timeline(self):
        result = generate_expert_timeline([])
        self.assertIn('TIMELINE', result)
    
    def test_prompts_exist(self):
        self.assertIn('daubert_analysis', EXPERT_PROMPTS)
        self.assertIn('expert_report_draft', EXPERT_PROMPTS)
    
    def test_skill_engine(self):
        engine = SkillEngine()
        self.assertEqual(engine.name, 'Expert Witness')
    
    def test_integration_points(self):
        self.assertIn('pacer', INTEGRATION_POINTS)


if __name__ == '__main__':
    unittest.main()