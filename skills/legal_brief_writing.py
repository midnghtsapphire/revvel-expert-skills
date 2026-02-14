import json
import re
import os
import hashlib
import datetime
import statistics
import math
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
import unittest
import logging

SKILL_METADATA = {
    "name": "Legal Brief Writing",
    "id": "legal_brief_writing",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Advanced legal brief writing skill for drafting motions, appellate briefs, memoranda, and legal arguments with Bluebook citation formatting and persuasive writing techniques",
    "capabilities": [
        "motion_drafting",
        "appellate_brief_construction",
        "memorandum_of_law_drafting",
        "legal_argument_construction",
        "citation_formatting_bluebook",
        "persuasive_writing_enhancement",
        "statement_of_facts_drafting",
        "issue_spotting_and_framing",
        "legal_research_integration",
        "brief_structure_optimization"
    ],
    "domain": "legal_writing_and_advocacy"
}

EXPERT_PROMPTS = {
    "motion_drafting": """
You are a senior litigation attorney drafting a {motion_type} motion for {court_name}.
Case: {case_name}
Procedural posture: {procedural_posture}
Key facts: {key_facts}
Legal issues: {legal_issues}
Desired outcome: {desired_outcome}

Draft a compelling motion that includes:
1. Caption and title
2. Introduction with clear statement of relief sought
3. Statement of facts (persuasive but accurate)
4. Legal argument with supporting authorities
5. Conclusion with specific prayer for relief

Tone: {tone} (persuasive/professional/forceful)
Target length: {target_length} pages
""",
    
    "appellate_brief": """
Draft an appellate brief as {appellant_respondent} in {court_name}.
Lower court: {lower_court_name}
Judgment appealed: {judgment_appealed}
Standard of review: {standard_of_review}

Case facts: {case_facts}
Errors assigned: {assigned_errors}
Precedent cases: {precedent_cases}

Structure requirements:
- Questions presented (clear, concise, favorable)
- Statement of the case (procedural history)
- Statement of facts (with record citations)
- Summary of argument
- Argument (with headings and subheadings)
- Conclusion

Word limit: {word_limit}
""",
    
    "legal_memorandum": """
Prepare a legal memorandum analyzing: {legal_question}
Client: {client_name}
Jurisdiction: {jurisdiction}
Applicable law: {applicable_law}

Known facts: {known_facts}
Research findings: {research_findings}

Format:
1. Heading (TO, FROM, DATE, RE)
2. Question presented
3. Brief answer
4. Statement of facts
5. Discussion (IRAC format)
6. Conclusion

Objective analysis required - present both sides.
""",
    
    "citation_formatting": """
Format the following citations according to Bluebook 21st edition:
Raw citations: {raw_citations}
Document type: {document_type}
Court: {court_name}
Year: {year}

Ensure proper:
- Case name formatting
- Reporter abbreviations
- Pinpoint citations
- Parenthetical information
- Signals and order
""",
    
    "statement_of_facts": """
Draft a statement of facts for {document_type} in {case_name}.
Raw facts from client: {raw_facts}
Key legal issues: {legal_issues}
Procedural posture: {procedural_posture}

Guidelines:
- Tell a coherent story
- Emphasize favorable facts
- Include unfavorable facts strategically
- Use active voice
- Include dates and specifics
- Cite to record when possible
Tone: {tone}
""",
    
    "issue_spotting": """
Analyze the following fact pattern and identify all legal issues:
Fact pattern: {fact_pattern}
Jurisdiction: {jurisdiction}
Area of law: {area_of_law}

For each issue identified:
1. State the issue as a question
2. Identify governing law
3. Note key facts bearing on issue
4. Suggest additional facts needed
5. Assess strength of potential claims/defenses
""",
    
    "persuasive_argument": """
Construct a persuasive legal argument for {position} on:
Legal issue: {legal_issue}
Applicable law: {applicable_law}
Key facts: {key_facts}
Precedent: {precedent_cases}

Argument structure:
1. Strong opening (theme)
2. Rule statement and explanation
3. Application to facts
4. Policy arguments
5. Distinguish adverse authority
6. Compelling conclusion

Target audience: {audience}
Argument length: {length}
""",
    
    "brief_optimization": """
Review and optimize this legal brief:
Draft brief: {draft_brief}
Document type: {document_type}
Target court: {target_court}
Judge preferences: {judge_preferences}

Improve:
1. Clarity and concision
2. Logical flow
3. Persuasive impact
4. Citation accuracy
5. Formatting compliance
6. Strength of arguments

Provide specific revision suggestions and rewritten sections.
"""
}

INTEGRATION_POINTS = {
    "court_listener_api": {
        "type": "api",
        "endpoint": "https://www.courtlistener.com/api/rest/v3/",
        "description": "Access to federal and state court opinions for citation and research",
        "auth_method": "token",
        "documentation_url": "https://www.courtlistener.com/api/"
    },
    "bluebook_citation_db": {
        "type": "database",
        "endpoint": "internal://citations/bluebook",
        "description": "Internal database of Bluebook citation rules and examples",
        "auth_method": "internal",
        "documentation_url": "internal://docs/citations"
    },
    "legal_templates_db": {
        "type": "database",
        "endpoint": "internal://templates/legal",
        "description": "Repository of legal document templates and forms",
        "auth_method": "internal",
        "documentation_url": "internal://docs/templates"
    },
    "case_law_retriever": {
        "type": "tool",
        "endpoint": "internal://tools/case_retrieval",
        "description": "Tool for retrieving relevant case law based on legal issues",
        "auth_method": "internal",
        "documentation_url": "internal://docs/case_retrieval"
    },
    "citation_validator": {
        "type": "tool",
        "endpoint": "internal://tools/citation_validator",
        "description": "Validates and corrects legal citations per Bluebook rules",
        "auth_method": "internal",
        "documentation_url": "internal://docs/citation_validator"
    }
}

def parse_case_citation(citation: str) -> Dict[str, Any]:
    """Parse a case citation into component parts.
    
    Args:
        citation: Raw case citation string
        
    Returns:
        Dict with case_name, volume, reporter, page, year, court
    """
    patterns = [
        r'(.+?)\s*,?\s*(\d+)\s+([A-Z]\.\s?[A-Z]?\.?[A-Z]?\.?)\s+(\d+)\s*(?:\(([^)]+)\))?',
        r'(.+?)\s*,?\s*(\d+)\s+([A-Z]\.\s?[A-Z]?\.?[A-Z]?\.?)\s+(\d+)\s*\((\d{4})\)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, citation)
        if match:
            return {
                'case_name': match.group(1).strip(),
                'volume': match.group(2),
                'reporter': match.group(3),
                'page': match.group(4),
                'year': match.group(5) if len(match.groups()) > 4 else None,
                'court': None
            }
    
    return {'case_name': citation, 'volume': None, 'reporter': None, 'page': None, 'year': None, 'court': None}

def format_bluebook_citation(case_info: Dict[str, Any]) -> str:
    """Format case citation according to Bluebook rules.
    
    Args:
        case_info: Dict with case_name, volume, reporter, page, year, court
        
    Returns:
        Properly formatted Bluebook citation
    """
    case_name = case_info.get('case_name', '').strip()
    volume = case_info.get('volume', '')
    reporter = case_info.get('reporter', '')
    page = case_info.get('page', '')
    year = case_info.get('year', '')
    court = case_info.get('court', '')
    
    if not all([case_name, volume, reporter, page]):
        return case_name
    
    citation = f"{case_name}, {volume} {reporter} {page}"
    
    if year:
        if court:
            citation += f" ({court} {year})"
        else:
            citation += f" ({year})"
    
    return citation

def extract_legal_issues(text: str) -> List[Dict[str, Any]]:
    """Extract potential legal issues from text.
    
    Args:
        text: Input text to analyze
        
    Returns:
        List of dicts with issue descriptions and confidence scores
    """
    issue_patterns = {
        'negligence': r'\b(negligence|negligent|duty of care|breach of duty)\b',
        'contract': r'\b(contract|breach of contract|agreement|consideration)\b',
        'constitutional': r'\b(constitutional|first amendment|due process|equal protection)\b',
        'employment': r'\b(employment|wrongful termination|discrimination|harassment)\b',
        'property': r'\b(property|real estate|landlord|tenant|easement)\b',
        'criminal': r'\b(crime|criminal|felony|misdemeanor|arrest|conviction)\b',
        'tort': r'\b(tort|personal injury|damages|liability)\b',
        'procedure': r'\b(motion|discovery|summary judgment|dismissal)\b'
    }
    
    issues = []
    text_lower = text.lower()
    
    for issue_type, pattern in issue_patterns.items():
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            confidence = min(len(matches) / 3, 1.0)
            issues.append({
                'issue_type': issue_type,
                'mentions': len(matches),
                'confidence': confidence,
                'context': matches[:2]
            })
    
    return sorted(issues, key=lambda x: x['confidence'], reverse=True)

def calculate_brief_score(brief_text: str) -> Dict[str, float]:
    """Calculate quality metrics for a legal brief.
    
    Args:
        brief_text: The brief text to evaluate
        
    Returns:
        Dict with various quality scores
    """
    scores = {}
    
    word_count = len(brief_text.split())
    scores['word_count'] = word_count
    
    sentence_count = len(re.findall(r'[.!?]+', brief_text))
    scores['avg_sentence_length'] = word_count / max(sentence_count, 1)
    
    paragraph_count = len([p for p in brief_text.split('\n\n') if p.strip()])
    scores['avg_paragraph_length'] = word_count / max(paragraph_count, 1)
    
    citation_count = len(re.findall(r'\d+\s+[A-Z]\.\s?[A-Z]?\.?[A-Z]?\.?\s+\d+', brief_text))
    scores['citation_density'] = citation_count / max(word_count, 1) * 1000
    
    passive_voice = len(re.findall(r'\b(was|were|been|being|is|are)\s+\w+ed\b', brief_text, re.IGNORECASE))
    scores['passive_voice_ratio'] = passive_voice / max(word_count, 1)
    
    transition_words = ['however', 'furthermore', 'moreover', 'therefore', 'thus', 'consequently', 'nevertheless']
    transition_count = sum(1 for word in transition_words if word in brief_text.lower())
    scores['transition_usage'] = transition_count / max(paragraph_count, 1)
    
    return scores

def generate_issue_statement(facts: str, legal_area: str) -> str:
    """Generate a well-framed legal issue statement.
    
    Args:
        facts: Case facts
        legal_area: Area of law (e.g., 'contract', 'tort', 'constitutional')
        
    Returns:
        Properly framed issue statement
    """
    templates = {
        'contract': "Whether {party} breached the contract by {action} when {facts}?",
        'tort': "Whether {party} is liable for {tort_type} based on {facts}?",
        'constitutional': "Whether {law_action} violates the {amendment} Amendment's {clause} clause?",
        'criminal': "Whether the evidence is sufficient to support a conviction for {crime}?",
        'procedure': "Whether the trial court erred by {ruling}?"
    }
    
    template = templates.get(legal_area, "Whether {party} {action} based on {facts}?")
    
    party_match = re.search(r'\b(\w+)\s+(?:defendant|plaintiff|appellant|respondent)\b', facts, re.IGNORECASE)
    party = party_match.group(1) if party_match else "the defendant"
    
    action_match = re.search(r'\b(\w+ed|\w+ing)\b', facts)
    action = action_match.group(1) if action_match else "acting"
    
    facts_summary = ' '.join(facts.split()[:20]) + '...' if len(facts.split()) > 20 else facts
    
    return template.format(party=party, action=action, facts=facts_summary, 
                          tort_type="negligence", amendment="First", clause="Due Process",
                          crime="the charged offense", ruling="granting summary judgment")

def validate_citations(text: str) -> List[Dict[str, Any]]:
    """Validate legal citations in text.
    
    Args:
        text: Text containing citations
        
    Returns:
        List of validation results for each citation
    """
    citation_pattern = r'\d+\s+[A-Z]\.\s?[A-Z]?\.?[A-Z]?\.?\s+\d+(?:\s*\([^)]*\))?'
    citations = re.findall(citation_pattern, text)
    
    results = []
    for citation in citations:
        parsed = parse_case_citation(citation)
        is_valid = all([parsed['volume'], parsed['reporter'], parsed['page']])
        
        results.append({
            'original': citation,
            'parsed': parsed,
            'is_valid': is_valid,
            'formatted': format_bluebook_citation(parsed) if is_valid else citation
        })
    
    return results

def create_brief_outline(issues: List[str], court_rules: Dict[str, Any]) -> Dict[str, Any]:
    """Create a structured outline for a legal brief.
    
    Args:
        issues: List of legal issues to address
        court_rules: Court-specific formatting rules
        
    Returns:
        Structured brief outline
    """
    outline = {
        'caption': {
            'court': court_rules.get('court_name', 'Court'),
            'title': 'Brief Outline',
            'case_number': '[Case Number]'
        },
        'sections': []
    }
    
    required_sections = court_rules.get('required_sections', [
        'Questions Presented',
        'Statement of the Case',
        'Statement of Facts',
        'Summary of Argument',
        'Argument',
        'Conclusion'
    ])
    
    for section in required_sections:
        section_outline = {
            'name': section,
            'subsections': []
        }
        
        if section == 'Argument':
            for i, issue in enumerate(issues, 1):
                section_outline['subsections'].append({
                    'heading': f"{i}. {issue}",
                    'content': f"[Argument regarding {issue}]"
                })
        
        outline['sections'].append(section_outline)
    
    return outline

def optimize_persuasive_language(text: str, audience: str = 'court') -> str:
    """Optimize text for persuasive impact.
    
    Args:
        text: Original text
        audience: Target audience ('court', 'client', 'opposing_counsel')
        
    Returns:
        Enhanced persuasive text
    """
    weak_phrases = {
        'it seems that': 'it is clear that',
        'it appears': 'the evidence demonstrates',
        'might be': 'is',
        'could possibly': 'does',
        'perhaps': 'certainly',
        'somewhat': '',
        'rather': '',
        'quite': ''
    }
    
    enhanced = text
    for weak, strong in weak_phrases.items():
        enhanced = re.sub(rf'\b{weak}\b', strong, enhanced, flags=re.IGNORECASE)
    
    if audience == 'court':
        enhanced = re.sub(r'\bwe believe\b', 'the evidence shows', enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r'\bwe think\b', 'this Court should find', enhanced, flags=re.IGNORECASE)
    elif audience == 'opposing_counsel':
        enhanced = re.sub(r'\bwe believe\b', 'the law requires', enhanced, flags=re.IGNORECASE)
    
    return enhanced

def calculate_readability_score(text: str) -> Dict[str, float]:
    """Calculate readability metrics for legal writing.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dict with readability scores
    """
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    words = text.split()
    syllables = 0
    
    for word in words:
        word = word.lower().strip('.,!?";')
        syllable_count = max(1, len(re.findall(r'[aeiouy]+', word)))
        syllables += syllable_count
    
    avg_sentence_length = len(words) / max(len(sentences), 1)
    avg_syllables_per_word = syllables / max(len(words), 1)
    
    flesch_reading_ease = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
    flesch_kincaid_grade = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
    
    return {
        'flesch_reading_ease': flesch_reading_ease,
        'flesch_kincaid_grade': flesch_kincaid_grade,
        'avg_sentence_length': avg_sentence_length,
        'avg_syllables_per_word': avg_syllables_per_word
    }

class SkillEngine:
    """Main engine for legal brief writing skill."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the skill engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.court_rules = config.get('court_rules', {})
        self.default_tone = config.get('default_tone', 'professional')
        
    def draft_motion(self, motion_type: str, case_info: Dict[str, Any], **kwargs) -> str:
        """Draft a legal motion.
        
        Args:
            motion_type: Type of motion to draft
            case_info: Case information dictionary
            **kwargs: Additional parameters
            
        Returns:
            Drafted motion text
        """
        prompt = EXPERT_PROMPTS['motion_drafting'].format(
            motion_type=motion_type,
            court_name=case_info.get('court', 'Court'),
            case_name=case_info.get('case_name', 'Case'),
            procedural_posture=case_info.get('procedural_posture', ''),
            key_facts=case_info.get('key_facts', ''),
            legal_issues=case_info.get('legal_issues', ''),
            desired_outcome=case_info.get('desired_outcome', ''),
            tone=kwargs.get('tone', self.default_tone),
            target_length=kwargs.get('target_length', '5-10')
        )
        
        return f"DRAFT MOTION:\n{prompt}\n\n[This would be replaced with actual LLM output]"
    
    def draft_appellate_brief(self, brief_info: Dict[str, Any], **kwargs) -> str:
        """Draft an appellate brief.
        
        Args:
            brief_info: Brief information dictionary
            **kwargs: Additional parameters
            
        Returns:
            Drafted appellate brief text
        """
        prompt = EXPERT_PROMPTS['appellate_brief'].format(
            appellant_respondent=brief_info.get('party_role', 'Appellant'),
            court_name=brief_info.get('court', 'Court of Appeals'),
            lower_court_name=brief_info.get('lower_court', 'Trial Court'),
            judgment_appealed=brief_info.get('judgment', 'Judgment'),
            standard_of_review=brief_info.get('standard_of_review', 'De novo'),
            case_facts=brief_info.get('facts', ''),
            assigned_errors=brief_info.get('errors', ''),
            precedent_cases=brief_info.get('precedent', ''),
            word_limit=kwargs.get('word_limit', '14000')
        )
        
        return f"DRAFT APPELLATE BRIEF:\n{prompt}\n\n[This would be replaced with actual LLM output]"
    
    def format_citations(self, text: str, citation_style: str = 'bluebook') -> str:
        """Format citations in text according to specified style.
        
        Args:
            text: Text containing citations
            citation_style: Citation style to use
            
        Returns:
            Text with properly formatted citations
        """
        if citation_style != 'bluebook':
            return text
            
        validation_results = validate_citations(text)
        
        formatted_text = text
        for result in validation_results:
            if result['is_valid'] and result['original'] != result['formatted']:
                formatted_text = formatted_text.replace(result['original'], result['formatted'])
        
        return formatted_text
    
    def analyze_legal_issues(self, fact_pattern: str, jurisdiction: str = 'federal') -> List[Dict[str, Any]]:
        """Analyze fact pattern and identify legal issues.
        
        Args:
            fact_pattern: Facts to analyze
            jurisdiction: Jurisdiction for analysis
            
        Returns:
            List of identified legal issues
        """
        return extract_legal_issues(fact_pattern)
    
    def optimize_brief_quality(self, brief_text: str, **kwargs) -> Dict[str, Any]:
        """Analyze and optimize brief quality.
        
        Args:
            brief_text: Brief text to analyze
            **kwargs: Additional parameters
            
        Returns:
            Quality analysis and recommendations
        """
        scores = calculate_brief_score(brief_text)
        readability = calculate_readability_score(brief_text)
        
        recommendations = []
        
        if scores['avg_sentence_length'] > 25:
            recommendations.append("Consider shorter sentences for clarity")
        
        if scores['passive_voice_ratio'] > 0.05:
            recommendations.append("Reduce passive voice usage")
        
        if readability['flesch_reading_ease'] < 30:
            recommendations.append("Simplify language for better readability")
        
        if scores['citation_density'] < 2:
            recommendations.append("Add more supporting citations")
        
        return {
            'scores': scores,
            'readability': readability,
            'recommendations': recommendations,
            'quality_grade': self._calculate_quality_grade(scores, readability)
        }
    
    def generate_legal_argument(self, issue: str, position: str, supporting_authorities: List[str]) -> str:
        """Generate a persuasive legal argument.
        
        Args:
            issue: Legal issue to address
            position: Position to argue
            supporting_authorities: List of supporting cases/statutes
            
        Returns:
            Generated legal argument
        """
        prompt = EXPERT_PROMPTS['persuasive_argument'].format(
            position=position,
            legal_issue=issue,
            applicable_law='[Applicable law would be inserted]',
            key_facts='[Key facts would be inserted]',
            precedent_cases=', '.join(supporting_authorities[:3]),
            audience='court',
            length='medium'
        )
        
        return f"LEGAL ARGUMENT:\n{prompt}\n\n[This would be replaced with actual LLM output]"
    
    def create_brief_template(self, document_type: str, court: str, issues: List[str]) -> Dict[str, Any]:
        """Create a template for a specific type of brief.
        
        Args:
            document_type: Type of brief
            court: Target court
            issues: Legal issues to address
            
        Returns:
            Brief template structure
        """
        court_rules = self.court_rules.get(court, {})
        return create_brief_outline(issues, court_rules)
    
    def enhance_persuasive_writing(self, text: str, audience: str = 'court') -> str:
        """Enhance text for persuasive impact.
        
        Args:
            text: Text to enhance
            audience: Target audience
            
        Returns:
            Enhanced persuasive text
        """
        return optimize_persuasive_language(text, audience)
    
    def run(self, capability: str, **kwargs) -> Any:
        """Run the specified capability.
        
        Args:
            capability: Capability to execute
            **kwargs: Parameters for the capability
            
        Returns:
            Result of the capability execution
        """
        try:
            if capability == 'motion_drafting':
                return self.draft_motion(kwargs['motion_type'], kwargs['case_info'], **kwargs)
            elif capability == 'appellate_brief_construction':
                return self.draft_appellate_brief(kwargs['brief_info'], **kwargs)
            elif capability == 'citation_formatting_bluebook':
                return self.format_citations(kwargs['text'], kwargs.get('style', 'bluebook'))
            elif capability == 'issue_spotting_and_framing':
                return self.analyze_legal_issues(kwargs['fact_pattern'], kwargs.get('jurisdiction', 'federal'))
            elif capability == 'brief_structure_optimization':
                return self.optimize_brief_quality(kwargs['brief_text'], **kwargs)
            elif capability == 'legal_argument_construction':
                return self.generate_legal_argument(kwargs['issue'], kwargs['position'], kwargs['authorities'])
            elif capability == 'brief_template_creation':
                return self.create_brief_template(kwargs['document_type'], kwargs['court'], kwargs['issues'])
            elif capability == 'persuasive_writing_enhancement':
                return self.enhance_persuasive_writing(kwargs['text'], kwargs.get('audience', 'court'))
            else:
                raise ValueError(f"Unknown capability: {capability}")
                
        except Exception as e:
            self.logger.error(f"Error running capability {capability}: {str(e)}")
            raise
    
    def _calculate_quality_grade(self, scores: Dict[str, float], readability: Dict[str, float]) -> str:
        """Calculate overall quality grade.
        
        Args:
            scores: Brief quality scores
            readability: Readability metrics
            
        Returns:
            Letter grade
        """
        grade_score = 100
        
        grade_score -= max(0, (scores['avg_sentence_length'] - 20) * 2)
        grade_score -= max(0, scores['passive_voice_ratio'] * 500)
        grade_score -= max(0, (30 - readability['flesch_reading_ease']) * 0.5)
        
        if grade_score >= 90:
            return 'A'
        elif grade_score >= 80:
            return 'B'
        elif grade_score >= 70:
            return 'C'
        elif grade_score >= 60:
            return 'D'
        else:
            return 'F'

class TestLegalBriefWritingSkill(unittest.TestCase):
    """Test cases for Legal Brief Writing skill."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'court_rules': {
                'Supreme Court': {
                    'required_sections': ['Questions Presented', 'Argument', 'Conclusion']
                }
            },
            'default_tone': 'professional'
        }
        self.engine = SkillEngine(self.config)
    
    def test_skill_metadata(self):
        """Test skill metadata validation."""
        self.assertEqual(SKILL_METADATA['name'], 'Legal Brief Writing')
        self.assertEqual(SKILL_METADATA['id'], 'legal_brief_writing')
        self.assertIn('motion_drafting', SKILL_METADATA['capabilities'])
        self.assertGreater(len(SKILL_METADATA['capabilities']), 5)
    
    def test_parse_case_citation(self):
        """Test case citation parsing."""
        citation = "Smith v. Jones, 123 F.3d 456 (2019)"
        parsed = parse_case_citation(citation)
        self.assertEqual(parsed['case_name'], "Smith v. Jones")
        self.assertEqual(parsed['volume'], "123")
        self.assertEqual(parsed['reporter'], "F.3d")
        self.assertEqual(parsed['page'], "456")
        self.assertEqual(parsed['year'], "2019")
    
    def test_format_bluebook_citation(self):
        """Test Bluebook citation formatting."""
        case_info = {
            'case_name': 'Smith v. Jones',
            'volume': '123',
            'reporter': 'F.3d',
            'page': '456',
            'year': '2019'
        }
        formatted = format_bluebook_citation(case_info)
        self.assertEqual(formatted, 'Smith v. Jones, 123 F.3d 456 (2019)')
    
    def test_extract_legal_issues(self):
        """Test legal issue extraction."""
        text = "The defendant was negligent in operating the vehicle and breached the contract."
        issues = extract_legal_issues(text)
        self.assertGreater(len(issues), 0)
        issue_types = [issue['issue_type'] for issue in issues]
        self.assertIn('negligence', issue_types)
        self.assertIn('contract', issue_types)
    
    def test_calculate_brief_score(self):
        """Test brief quality scoring."""
        text = "This is a test brief. It contains some legal arguments and citations."
        scores = calculate_brief_score(text)
        self.assertIn('word_count', scores)
        self.assertIn('avg_sentence_length', scores)
        self.assertIn('citation_density', scores)
        self.assertGreaterEqual(scores['word_count'], 0)
    
    def test_generate_issue_statement(self):
        """Test issue statement generation."""
        facts = "The defendant breached the contract by failing to deliver goods."
        statement = generate_issue_statement(facts, 'contract')
        self.assertIn('Whether', statement)
        self.assertIn('breached', statement)
    
    def test_validate_citations(self):
        """Test citation validation."""
        text = "See Smith v. Jones, 123 F.3d 456 (2019)."
        results = validate_citations(text)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]['is_valid'])
    
    def test_create_brief_outline(self):
        """Test brief outline creation."""
        issues = ['negligence', 'breach of contract']
        rules = {'required_sections': ['Facts', 'Argument', 'Conclusion']}
        outline = create_brief_outline(issues, rules)
        self.assertIn('sections', outline)
        self.assertGreater(len(outline['sections']), 0)
    
    def test_optimize_persuasive_language(self):
        """Test persuasive language optimization."""
        text = "It seems that the defendant was somewhat negligent."
        optimized = optimize_persuasive_language(text)
        self.assertNotIn('It seems that', optimized)
        self.assertNotIn('somewhat', optimized)
    
    def test_calculate_readability_score(self):
        """Test readability calculation."""
        text = "This is a simple sentence. It is easy to read."
        scores = calculate_readability_score(text)
        self.assertIn('flesch_reading_ease', scores)
        self.assertIn('flesch_kincaid_grade', scores)
    
    def test_skill_engine_initialization(self):
        """Test SkillEngine initialization."""
        self.assertIsInstance(self.engine, SkillEngine)
        self.assertEqual(self.engine.default_tone, 'professional')
    
    def test_skill_engine_motion_drafting(self):
        """Test motion drafting capability."""
        case_info = {
            'court': 'District Court',
            'case_name': 'Test v. Case',
            'key_facts': 'Facts here',
            'legal_issues': 'Issues here'
        }
        result = self.engine.run('motion_drafting', motion_type='summary_judgment', case_info=case_info)
        self.assertIn('DRAFT MOTION', result)
    
    def test_skill_engine_citation_formatting(self):
        """Test citation formatting capability."""
        text = "Smith v. Jones, 123 F.3d 456"
        result = self.engine.run('citation_formatting_bluebook', text=text)
        self.assertIn('Smith v. Jones', result)
    
    def test_skill_engine_issue_analysis(self):
        """Test issue analysis capability."""
        fact_pattern = "The defendant was negligent in driving."
        result = self.engine.run('issue_spotting_and_framing', fact_pattern=fact_pattern)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
    
    def test_skill_engine_brief_optimization(self):
        """Test brief optimization capability."""
        brief_text = "This is a test brief with some legal content."
        result = self.engine.run('brief_structure_optimization', brief_text=brief_text)
        self.assertIn('scores', result)
        self.assertIn('recommendations', result)
        self.assertIn('quality_grade', result)
    
    def test_skill_engine_error_handling(self):
        """Test error handling for unknown capability."""
        with self.assertRaises(ValueError):
            self.engine.run('unknown_capability')
    
    def test_integration_points(self):
        """Test integration points structure."""
        self.assertIn('court_listener_api', INTEGRATION_POINTS)
        self.assertIn('bluebook_citation_db', INTEGRATION_POINTS)
        
        for integration, config in INTEGRATION_POINTS.items():
            self.assertIn('type', config)
            self.assertIn('endpoint', config)
            self.assertIn('description', config)
            self.assertIn('auth_method', config)

if __name__ == '__main__':
    unittest.main()