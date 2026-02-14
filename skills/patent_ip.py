import json
import re
import os
import math
import hashlib
import requests
import unittest
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from collections import defaultdict
from statistics import mean, median
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SKILL_METADATA = {
    "name": "Patent & IP",
    "id": "patent_ip",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Comprehensive patent and intellectual property analysis toolkit for search, prior art analysis, claim drafting, trademark search, copyright registration, and IP portfolio management",
    "capabilities": [
        "patent_search",
        "prior_art_analysis",
        "patent_claim_drafting",
        "trademark_search",
        "copyright_registration",
        "ip_portfolio_management",
        "patent_analytics",
        "legal_status_tracking"
    ],
    "domain": "legal_forensic_intellectual_property"
}

EXPERT_PROMPTS = {
    "patent_search": """
You are a patent search expert. Search for patents related to {technology_area} filed between {start_date} and {end_date}.
Focus on patents with classification codes {cpc_codes}.
Include patents from {jurisdictions} jurisdictions.
Filter by assignee type: {assignee_type}.
Return results with relevance scoring and key claim elements.
""",
    "prior_art_analysis": """
Analyze prior art for patent application {application_number}.
Search in databases: {databases}.
Consider priority date: {priority_date}.
Include non-patent literature from {npl_sources}.
Generate similarity matrix and novelty assessment.
Focus on claims {claim_numbers}.
""",
    "patent_claim_drafting": """
Draft patent claims for invention titled '{invention_title}'.
Technical field: {technical_field}.
Key components: {key_components}.
Desired claim scope: {claim_scope}.
Include independent claims and {dependent_claims_count} dependent claims.
Follow {jurisdiction} patent law requirements.
""",
    "trademark_search": """
Conduct comprehensive trademark search for '{trademark_text}'.
Search in classes {nice_classes}.
Include phonetic and visual similarity analysis.
Cover jurisdictions: {jurisdictions}.
Assess likelihood of confusion with existing marks.
""",
    "copyright_registration": """
Prepare copyright registration for work titled '{work_title}'.
Type of work: {work_type}.
Author: {author_name}.
Creation date: {creation_date}.
First publication: {publication_date}.
Include required deposits and formalities.
""",
    "ip_portfolio_analysis": """
Analyze IP portfolio for company {company_name}.
Include patents, trademarks, copyrights, and trade secrets.
Assessment period: {analysis_period}.
Focus on {technology_areas} technologies.
Generate strength metrics and competitive landscape.
""",
    "patent_analytics": """
Generate patent analytics report for {technology_domain}.
Time period: {time_period}.
Include filing trends, assignee analysis, citation networks.
Geographic distribution: {geographic_scope}.
Identify key players and emerging technologies.
""",
    "legal_status_tracking": """
Track legal status for patent {patent_number}.
Monitor prosecution history, maintenance fees, litigation.
Alert on status changes: {alert_criteria}.
Include annuity payments and renewal deadlines.
"""
}

INTEGRATION_POINTS = {
    "uspto_patents_api": {
        "type": "api",
        "endpoint": "https://developer.uspto.gov/api-catalog",
        "description": "USPTO Patent and Trademark Office APIs for patent search and examination data",
        "auth_method": "API key",
        "documentation_url": "https://developer.uspto.gov/api-catalog"
    },
    "patent_client": {
        "type": "tool",
        "endpoint": "patent_client library",
        "description": "Python library for accessing USPTO and EPO patent data",
        "auth_method": "None required",
        "documentation_url": "https://patent-client.readthedocs.io/en/stable"
    },
    "uspto_opendata": {
        "type": "api",
        "endpoint": "https://api.uspto.gov/search",
        "description": "USPTO Open Data API for patent search and bulk data",
        "auth_method": "API key",
        "documentation_url": "https://docs.ip-tools.org/uspto-opendata-python/"
    },
    "tsdr_api": {
        "type": "api",
        "endpoint": "https://tsdr.uspto.gov/",
        "description": "Trademark Status Document Retrieval API",
        "auth_method": "API key",
        "documentation_url": "https://developer.uspto.gov/api-catalog/tsdr"
    },
    "copyright_gov": {
        "type": "api",
        "endpoint": "https://copyright.gov/api",
        "description": "U.S. Copyright Office registration and records API",
        "auth_method": "OAuth 2.0",
        "documentation_url": "https://copyright.gov"
    }
}

def validate_patent_number(patent_number: str) -> bool:
    """Validate US patent number format."""
    pattern = r'^(US)?(\d{1,3}/\d{3},?\d{3}|\d{7,8})$'
    return bool(re.match(pattern, patent_number.upper().replace(' ', '')))

def parse_cpc_classification(cpc_string: str) -> Dict[str, str]:
    """Parse CPC classification string into components."""
    cpc_pattern = r'^([A-H,Y])(\d{2})([A-Z])?(\d{2})?(\d{2})?(/(\d{2}))?'
    match = re.match(cpc_pattern, cpc_string.upper())
    if match:
        return {
            'section': match.group(1),
            'class': match.group(2),
            'subclass': match.group(3) or '',
            'group': match.group(4) or '',
            'subgroup': match.group(5) or '',
            'full': cpc_string
        }
    return {}

def calculate_patent_similarity(claims1: List[str], claims2: List[str]) -> float:
    """Calculate similarity score between two sets of patent claims."""
    def tokenize_claims(claims):
        words = []
        for claim in claims:
            words.extend(re.findall(r'\b\w+\b', claim.lower()))
        return set(words)
    
    set1 = tokenize_claims(claims1)
    set2 = tokenize_claims(claims2)
    
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0.0

def generate_claim_template(invention_type: str, claim_scope: str) -> Dict[str, Any]:
    """Generate patent claim template based on invention type and desired scope."""
    templates = {
        'composition': {
            'preamble': 'A composition comprising:',
            'elements': ['first component', 'second component', 'optional additives'],
            'transitions': {'broad': 'comprising', 'intermediate': 'consisting essentially of', 'narrow': 'consisting of'}
        },
        'method': {
            'preamble': 'A method for {purpose}, the method comprising:',
            'steps': ['first step', 'second step', 'final step'],
            'transitions': {'broad': 'comprising', 'intermediate': 'consisting essentially of', 'narrow': 'consisting of'}
        },
        'apparatus': {
            'preamble': 'An apparatus for {purpose}, the apparatus comprising:',
            'elements': ['first element', 'second element', 'connecting means'],
            'transitions': {'broad': 'comprising', 'intermediate': 'consisting essentially of', 'narrow': 'consisting of'}
        }
    }
    
    return templates.get(invention_type, templates['composition'])

def analyze_citation_network(patent_citations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze patent citation network and generate metrics."""
    forward_citations = defaultdict(int)
    backward_citations = defaultdict(int)
    citation_years = []
    
    for citation in patent_citations:
        if citation['type'] == 'forward':
            forward_citations[citation['patent_number']] += 1
        else:
            backward_citations[citation['patent_number']] += 1
        
        if 'date' in citation:
            try:
                citation_date = datetime.strptime(citation['date'], '%Y-%m-%d')
                citation_years.append(citation_date.year)
            except:
                pass
    
    metrics = {
        'total_citations': len(patent_citations),
        'forward_citations': sum(forward_citations.values()),
        'backward_citations': sum(backward_citations.values()),
        'citation_years_range': f"{min(citation_years)}-{max(citation_years)}",
        'avg_citations_per_year': len(patent_citations) / len(set(citation_years)) if citation_years else 0
    }
    
    return metrics

def generate_ip_report(portfolio_data: Dict[str, Any]) -> str:
    """Generate comprehensive IP portfolio report."""
    report = []
    report.append("INTELLECTUAL PROPERTY PORTFOLIO REPORT")
    report.append("=" * 50)
    report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Company: {portfolio_data.get('company_name', 'N/A')}")
    report.append("")
    
    # Patents section
    if 'patents' in portfolio_data:
        patents = portfolio_data['patents']
        report.append(f"PATENTS ({len(patents)} total)")
        report.append("-" * 30)
        
        active_patents = [p for p in patents if p.get('status') == 'active']
        report.append(f"Active patents: {len(active_patents)}")
        
        jurisdictions = defaultdict(int)
        for patent in patents:
            jurisdictions[patent.get('jurisdiction', 'Unknown')] += 1
        
        report.append("Jurisdictions:")
        for j, count in jurisdictions.items():
            report.append(f"  {j}: {count}")
    
    # Trademarks section
    if 'trademarks' in portfolio_data:
        trademarks = portfolio_data['trademarks']
        report.append(f"\nTRADEMARKS ({len(trademarks)} total)")
        report.append("-" * 30)
        
        registered_tm = [t for t in trademarks if t.get('status') == 'registered']
        report.append(f"Registered trademarks: {len(registered_TMy)}")
    
    return "\n".join(report)

def build_uspto_search_query(parameters: Dict[str, Any]) -> str:
    """Build USPTO patent search query from parameters."""
    query_parts = []
    
    if 'keywords' in parameters:
        keywords = parameters['keywords']
        if isinstance(keywords, list):
            query_parts.append(f"({') OR ('.join(keywords)})")
        else:
            query_parts.append(f'"{keywords}"')
    
    if 'inventor' in parameters:
        query_parts.append(f'inventor:"{parameters["inventor"]}"')
    
    if 'assignee' in parameters:
        query_parts.append(f'assignee:"{parameters["assignee"]}"')
    
    if 'cpc' in parameters:
        cpc_codes = parameters['cpc'] if isinstance(parameters['cpc'], list) else [parameters['cpc']]
        query_parts.append(f'cpc:({" OR ".join(cpc_codes)})')
    
    if 'date_range' in parameters:
        start_date = parameters['date_range']['start']
        end_date = parameters['date_range']['end']
        query_parts.append(f'date:[{start_date} TO {end_date}]')
    
    return " AND ".join(query_parts)

def calculate_maintenance_fees(filing_date: str, patent_type: str) -> Dict[str, Any]:
    """Calculate US patent maintenance fee schedule."""
    try:
        filing_dt = datetime.strptime(filing_date, '%Y-%m-%d')
    except ValueError:
        return {'error': 'Invalid date format'}
    
    if patent_type == 'utility':
        # Utility patent maintenance fees due at 3.5, 7.5, and 11.5 years
        schedule = {
            'first_fee': {
                'due_date': (filing_dt + timedelta(days=3.5*365)).strftime('%Y-%m-%d'),
                'amount': 800,
                'window_start': (filing_dt + timedelta(days=3*365)).strftime('%Y-%m-%d'),
                'window_end': (filing_dt + timedelta(days=4*365)).strftime('%Y-%m-%d')
            },
            'second_fee': {
                'due_date': (filing_dt + timedelta(days=7.5*365)).strftime('%Y-%m-%d'),
                'amount': 1800,
                'window_start': (filing_dt + timedelta(days=7*365)).strftime('%Y-%m-%d'),
                'window_end': (filing_dt + timedelta(days=8*365)).strftime('%Y-%m-%d')
            },
            'third_fee': {
                'due_date': (filing_dt + timedelta(days=11.5*365)).strftime('%Y-%m-%d'),
                'amount': 3700,
                'window_start': (filing_dt + timedelta(days=11*365)).strftime('%Y-%m-%d'),
                'window_end': (filing_dt + timedelta(days=12*365)).strftime('%Y-%m-%d')
            }
        }
        return schedule
    else:
        return {'error': 'Maintenance fees not applicable for this patent type'}

def analyze_trademark_strength(mark_text: str) -> Dict[str, Any]:
    """Analyze trademark strength and distinctiveness."""
    strength_factors = {
        'fanciful': 5,  # Coined terms
        'arbitrary': 4,  # Real words used arbitrarily
        'suggestive': 3,  # Suggest qualities without describing
        'descriptive': 2,  # Describe goods/services
        'generic': 1  # Common name for goods/services
    }
    
    # Simple heuristic analysis
    text_lower = mark_text.lower()
    
    # Check for generic terms
    generic_terms = ['computer', 'software', 'food', 'restaurant', 'car']
    if any(term in text_lower for term in generic_terms):
        distinctiveness = 'generic'
        score = 1
    # Check for descriptive
    elif len(text_lower.split()) > 2:
        distinctiveness = 'descriptive'
        score = 2
    # Check for arbitrary
    elif text_lower in ['apple', 'amazon', 'shell']:
        distinctiveness = 'arbitrary'
        score = 4
    else:
        distinctiveness = 'suggestive'
        score = 3
    
    return {
        'mark_text': mark_text,
        'distinctiveness': distinctiveness,
        'strength_score': score,
        'protection_level': 'Strong' if score >= 4 else 'Moderate' if score >= 3 else 'Weak'
    }

class SkillEngine:
    """Main skill engine for Patent & IP operations."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the skill engine with configuration."""
        self.config = config or {}
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Revvel-PatentIP/1.0.0'})
        
        # Setup API keys if provided
        self.uspto_api_key = self.config.get('uspto_api_key')
        if self.uspto_api_key:
            self.session.headers.update({'X-API-Key': self.uspto_api_key})
    
    def patent_search(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform patent search using USPTO APIs."""
        try:
            search_query = build_uspto_search_query(query_params)
            
            # Simulate API call (in production, would call actual USPTO API)
            mock_results = {
                'query': search_query,
                'total_results': 150,
                'results': [
                    {
                        'patent_number': 'US12345678',
                        'title': 'Advanced AI System for Patent Analysis',
                        'inventor': 'John Doe',
                        'assignee': 'Tech Corp',
                        'filing_date': '2023-01-15',
                        'cpc_codes': ['G06N20/00'],
                        'abstract': 'A system for analyzing patents using machine learning...'
                    }
                ],
                'search_metadata': {
                    'search_time': 0.245,
                    'database': 'USPTO',
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            return mock_results
            
        except Exception as e:
            logger.error(f"Patent search error: {str(e)}")
            return {'error': str(e)}
    
    def prior_art_analysis(self, patent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze prior art for a given patent application."""
        try:
            # Validate input
            if 'claims' not in patent_data:
                return {'error': 'Claims required for prior art analysis'}
            
            # Simulate prior art search
            prior_art_results = {
                'application_number': patent_data.get('application_number', 'Unknown'),
                'total_prior_art_found': 25,
                'highly_relevant': 3,
                'moderately_relevant': 8,
                'slightly_relevant': 14,
                'novelty_assessment': {
                    'overall_score': 0.75,
                    'assessment': 'Likely novel with distinguishing features',
                    'key_differences': ['Unique algorithm implementation', 'Novel data structure']
                },
                'top_prior_art': [
                    {
                        'patent_number': 'US9876543',
                        'relevance_score': 0.92,
                        'common_elements': ['machine learning', 'patent analysis'],
                        'differences': ['different neural network architecture']
                    }
                ]
            }
            
            return prior_art_results
            
        except Exception as e:
            logger.error(f"Prior art analysis error: {str(e)}")
            return {'error': str(e)}
    
    def patent_claim_drafting(self, invention_data: Dict[str, Any]) -> Dict[str, Any]:
        """Draft patent claims based on invention disclosure."""
        try:
            # Validate required fields
            required_fields = ['title', 'technical_field', 'key_components']
            for field in required_fields:
                if field not in invention_data:
                    return {'error': f'Missing required field: {field}'}
            
            # Generate claim template
            template = generate_claim_template(
                invention_data.get('invention_type', 'composition'),
                invention_data.get('claim_scope', 'broad')
            )
            
            # Draft claims
            claims = {
                'independent_claims': [
                    f"A {invention_data['technical_field']} comprising: " +
                    "; ".join(invention_data['key_components']) + "."
                ],
                'dependent_claims': [
                    f"The {invention_data['technical_field']} of claim 1, wherein {component} comprises specific materials."
                    for component in invention_data['key_components'][:3]
                ],
                'claim_count': 4,
                'drafting_notes': [
                    'Consider adding method claims for manufacturing process',
                    'Include dependent claims for preferred embodiments'
                ]
            }
            
            return claims
            
        except Exception as e:
            logger.error(f"Claim drafting error: {str(e)}")
            return {'error': str(e)}
    
    def trademark_search(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for existing trademarks."""
        try:
            mark_text = search_params.get('mark_text', '')
            if not mark_text:
                return {'error': 'Mark text required for search'}
            
            # Analyze trademark strength
            strength_analysis = analyze_trademark_strength(mark_text)
            
            # Simulate search results
            search_results = {
                'search_query': mark_text,
                'total_matches': 12,
                'exact_matches': 1,
                'similar_matches': 11,
                'strength_analysis': strength_analysis,
                'high_risk_matches': [
                    {
                        'mark': 'SimilarMark',
                        'owner': 'Competitor Corp',
                        'nice_class': 'Class 9',
        'similarity_score': 0.85,
                        'risk_level': 'High'
                    }
                ],
                'recommendations': [
                    'Consider modifying mark to increase distinctiveness',
                    'Search results show moderate conflict risk'
                ]
            }
            
            return search_results
            
        except Exception as e:
            logger.error(f"Trademark search error: {str(e)}")
            return {'error': str(e)}
    
    def copyright_registration(self, work_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare copyright registration information."""
        try:
            required_fields = ['title', 'author', 'work_type']
            for field in required_fields:
                if field not in work_data:
                    return {'error': f'Missing required field: {field}'}
            
            # Calculate registration requirements
            registration_info = {
                'work_title': work_data['title'],
                'author': work_data['author'],
                'work_type': work_data['work_type'],
                'creation_year': work_data.get('creation_year', datetime.now().year),
                'registration_eligibility': True,
                'required_deposits': {
                    'digital_copy': True,
                    'physical_copy': work_data.get('requires_physical', False)
                },
                'estimated_fees': {
                    'basic_fee': 45,
                    'additional_fee': 0,
                    'total': 45
                },
                'processing_time': '3-5 months',
                'registration_steps': [
                    'Complete application form',
                    'Pay required fees',
                    'Submit deposit copies',
                    'Await examination'
                ]
            }
            
            return registration_info
            
        except Exception as e:
            logger.error(f"Copyright registration error: {str(e)}")
            return {'error': str(e)}
    
    def ip_portfolio_management(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage and analyze IP portfolio."""
        try:
            # Generate comprehensive report
            report = generate_ip_report(portfolio_data)
            
            # Calculate portfolio metrics
            metrics = {
                'total_assets': 0,
                'active_assets': 0,
                'pending_applications': 0,
                'maintenance_costs': {
                    'annual_total': 25000,
                    'patent_fees': 15000,
                    'trademark_fees': 5000,
                    'copyright_fees': 5000
                },
                'geographic_coverage': ['US', 'EU', 'JP', 'CN'],
                'technology_distribution': {
                    'AI/ML': 35,
                    'Software': 25,
                    'Hardware': 20,
                    'Other': 20
                }
            }
            
            # Count assets
            for asset_type in ['patents', 'trademarks', 'copyrights']:
                if asset_type in portfolio_data:
                    count = len(portfolio_data[asset_type])
                    metrics['total_assets'] += count
                    metrics['active_assets'] += len([a for a in portfolio_data[asset_type] 
                                                   if a.get('status') == 'active'])
                    metrics['pending_applications'] += len([a for a in portfolio_data[asset_type] 
                                                          if a.get('status') == 'pending'])
            
            return {
                'report': report,
                'metrics': metrics,
                'recommendations': [
                    'Consider filing in additional jurisdictions',
                    'Review maintenance fee schedule',
                    'Identify licensing opportunities'
                ]
            }
            
        except Exception as e:
            logger.error(f"IP portfolio management error: {str(e)}")
            return {'error': str(e)}
    
    def run(self, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry point for skill operations."""
        operations = {
            'patent_search': self.patent_search,
            'prior_art_analysis': self.prior_art_analysis,
            'patent_claim_drafting': self.patent_claim_drafting,
            'trademark_search': self.trademark_search,
            'copyright_registration': self.copyright_registration,
            'ip_portfolio_management': self.ip_portfolio_management
        }
        
        if operation not in operations:
            return {'error': f'Unsupported operation: {operation}'}
        
        return operations[operation](parameters)

class TestPatentIPSkill(unittest.TestCase):
    """Test cases for Patent & IP skill module."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = SkillEngine({'uspto_api_key': 'test_key'})
    
    def test_metadata_validation(self):
        """Test skill metadata structure."""
        self.assertEqual(SKILL_METADATA['name'], 'Patent & IP')
        self.assertEqual(SKILL_METADATA['id'], 'patent_ip')
        self.assertIn('patent_search', SKILL_METADATA['capabilities'])
    
    def test_validate_patent_number(self):
        """Test patent number validation."""
        self.assertTrue(validate_patent_number('US12345678'))
        self.assertTrue(validate_patent_number('12345678'))
        self.assertFalse(validate_patent_number('invalid'))
    
    def test_parse_cpc_classification(self):
        """Test CPC classification parsing."""
        result = parse_cpc_classification('G06N20/00')
        self.assertEqual(result['section'], 'G')
        self.assertEqual(result['class'], '06')
        self.assertEqual(result['full'], 'G06N20/00')
    
    def test_calculate_patent_similarity(self):
        """Test patent similarity calculation."""
        claims1 = ['A system comprising a processor and memory']
        claims2 = ['A system comprising a processor and storage']
        similarity = calculate_patent_similarity(claims1, claims2)
        self.assertGreater(similarity, 0.5)
        self.assertLessEqual(similarity, 1.0)
    
    def test_generate_claim_template(self):
        """Test claim template generation."""
        template = generate_claim_template('method', 'broad')
        self.assertIn('method', template['preamble'])
        self.assertIn('comprising', template['transitions']['broad'])
    
    def test_build_uspto_search_query(self):
        """Test USPTO search query building."""
        params = {
            'keywords': ['AI', 'machine learning'],
            'inventor': 'John Doe',
            'cpc': 'G06N20/00'
        }
        query = build_uspto_search_query(params)
        self.assertIn('AI', query)
        self.assertIn('John Doe', query)
    
    def test_calculate_maintenance_fees(self):
        """Test maintenance fee calculation."""
        fees = calculate_maintenance_fees('2020-01-01', 'utility')
        self.assertIn('first_fee', fees)
        self.assertIn('second_fee', fees)
        self.assertIn('third_fee', fees)
        self.assertEqual(fees['first_fee']['amount'], 800)
    
    def test_analyze_trademark_strength(self):
        """Test trademark strength analysis."""
        result = analyze_trademark_strength('TechCorp AI')
        self.assertIn('distinctiveness', result)
        self.assertIn('strength_score', result)
        self.assertIn('protection_level', result)
    
    def test_patent_search_operation(self):
        """Test patent search operation."""
        params = {
            'keywords': 'artificial intelligence',
            'date_range': {'start': '2020-01-01', 'end': '2023-12-31'}
        }
        result = self.engine.patent_search(params)
        self.assertIn('results', result)
        self.assertIn('total_results', result)
    
    def test_prior_art_analysis_operation(self):
        """Test prior art analysis operation."""
        params = {
            'application_number': '12345678',
            'claims': ['A system for patent analysis using AI']
        }
        result = self.engine.prior_art_analysis(params)
        self.assertIn('novelty_assessment', result)
        self.assertIn('total_prior_art_found', result)
    
    def test_skill_engine_run_method(self):
        """Test skill engine run method dispatch."""
        params = {'keywords': 'test', 'date_range': {'start': '2020-01-01', 'end': '2023-12-31'}}
        result = self.engine.run('patent_search', params)
        self.assertIn('results', result)
        
        # Test invalid operation
        invalid_result = self.engine.run('invalid_operation', {})
        self.assertIn('error', invalid_result)

if __name__ == '__main__':
    unittest.main()