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
        description = event.get('description