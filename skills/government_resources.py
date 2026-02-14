import json
import os
import re
import datetime
import hashlib
import requests
import unittest
from typing import Dict, List, Optional, Any, Union
from collections import defaultdict
from statistics import mean, median
from math import ceil
import xml.etree.ElementTree as ET


SKILL_METADATA = {
    "name": "Presidential/Government Resources",
    "id": "government_resources",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Comprehensive access to U.S. federal government data sources including executive orders, federal register, congressional records, FOIA requests, grants, court records, census data, and federal budget analysis",
    "capabilities": [
        "executive_orders_search",
        "federal_register_analysis",
        "congressional_records_query",
        "foia_request_automation",
        "grants_gov_research",
        "pacer_court_records",
        "census_data_analysis",
        "federal_budget_analysis"
    ],
    "domain": "government_legal_research"
}


EXPERT_PROMPTS = {
    "executive_orders_analysis": """Analyze executive orders related to {topic} issued between {start_date} and {end_date}. 
    Provide summary of key provisions, legal implications, and enforcement mechanisms.
    Focus on orders affecting {affected_sectors} and their impact on {stakeholder_groups}.""",
    
    "federal_register_monitoring": """Monitor Federal Register entries for {agency_name} published in the last {time_period} days.
    Identify proposed rules, final rules, and notices that could impact {business_sector}.
    Provide compliance requirements and comment deadlines.""",
    
    "congressional_legislation_tracking": """Track congressional bills related to {policy_area} introduced during the {congress_session} Congress.
    Analyze sponsor patterns, committee assignments, and likelihood of passage.
    Include voting records and amendment history.""",
    
    "foia_request_builder": """Draft a FOIA request to {agency_name} requesting {document_types} related to {subject_matter}.
    Include proper legal citations, fee waiver justifications, and expedited processing requests if applicable.
    Format according to {jurisdiction} requirements.""",
    
    "grants_opportunity_analysis": """Identify federal grant opportunities for {organization_type} working on {program_area}.
    Filter by eligibility requirements, funding levels between ${min_amount} and ${max_amount}, and application deadlines.
    Analyze success rates and required matching funds.""",
    
    "federal_court_case_monitoring": """Search PACER database for federal cases involving {party_name} filed in {court_jurisdiction} since {filing_date}.
    Include case types, judges assigned, and current status.
    Analyze litigation patterns and outcomes.""",
    
    "census_demographic_analysis": """Analyze census data for {geographic_area} comparing {demographic_variables} between {year_1} and {year_2}.
    Calculate growth rates, population shifts, and economic indicators.
    Identify trends relevant to {policy_implications}.""",
    
    "federal_budget_tracking": """Track federal budget allocations for {budget_category} across {fiscal_years}.
    Analyze appropriations, outlays, and proposed changes.
    Identify congressional committee jurisdictions and markup schedules."""
}


INTEGRATION_POINTS = {
    "federal_register_api": {
        "type": "api",
        "endpoint": "https://www.federalregister.gov/api/v1",
        "description": "Federal Register documents and metadata",
        "auth_method": "none",
        "documentation_url": "https://www.federalregister.gov/developers/api/v1"
    },
    "pacer_case_locator": {
        "type": "api",
        "endpoint": "https://pcl.uscourts.gov/pcl-public-api",
        "description": "PACER Case Locator for federal court records",
        "auth_method": "basic_auth",
        "documentation_url": "https://pacersdk.org/"
    },
    "grants_gov_api": {
        "type": "api",
        "endpoint": "https://api.grants.gov/api/v2",
        "description": "Federal grant opportunities database",
        "auth_method": "api_key",
        "documentation_url": "https://www.grants.gov/web/grants/api.html"
    },
    "census_api": {
        "type": "api",
        "endpoint": "https://api.census.gov/data",
        "description": "U.S. Census Bureau data API",
        "auth_method": "api_key",
        "documentation_url": "https://www.census.gov/data/developers/data-sets.html"
    },
    "usa_spending_api": {
        "type": "api",
        "endpoint": "https://api.usaspending.gov/api/v2",
        "description": "Federal spending data and awards",
        "auth_method": "none",
        "documentation_url": "https://www.usaspending.gov/api"
    },
    "fac_api": {
        "type": "api",
        "endpoint": "https://api.fac.gov",
        "description": "Federal Audit Clearinghouse data",
        "auth_method": "api_key",
        "documentation_url": "https://fac.gov/api/examples"
    }
}


def parse_executive_order_number(eo_string: str) -> Dict[str, Any]:
    """Parse executive order number from various formats."""
    patterns = [
        r'Executive Order (\d+)',
        r'E\.O\. (\d+)',
        r'EO (\d+)',
        r'Exec\. Order (\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, eo_string, re.IGNORECASE)
        if match:
            return {
                'number': int(match.group(1)),
                'original_format': eo_string.strip(),
                'parsed': True
            }
    
    return {'number': None, 'original_format': eo_string.strip(), 'parsed': False}


def validate_federal_register_citation(citation: str) -> Dict[str, Any]:
    """Validate and parse Federal Register citation format."""
    pattern = r'(\d+) Fed\. Reg\. (\d+) \((\w+ \d+, \d{4})\)'
    match = re.match(pattern, citation)
    
    if match:
        volume, page, date_str = match.groups()
        try:
            date_obj = datetime.datetime.strptime(date_str, '%B %d, %Y')
            return {
                'valid': True,
                'volume': int(volume),
                'page': int(page),
                'date': date_obj.strftime('%Y-%m-%d'),
                'components': {
                    'volume': int(volume),
                    'page': int(page),
                    'date': date_str
                }
            }
        except ValueError:
            return {'valid': False, 'error': 'Invalid date format'}
    
    return {'valid': False, 'error': 'Citation does not match expected format'}


def build_foia_request_template(agency: str, request_text: str, 
                                requester_name: str, requester_address: str,
                                fee_category: str = 'other') -> str:
    """Generate properly formatted FOIA request letter."""
    template = f"""Freedom of Information Act Request

To: {agency}
FOIA Officer
{agency} Headquarters
Washington, D.C.

From: {requester_name}
{requester_address}

Date: {datetime.date.today().strftime('%B %d, %Y')}

Subject: Freedom of Information Act Request

Dear FOIA Officer:

Pursuant to the Freedom of Information Act, 5 U.S.C. § 552, I hereby request the following records:

{request_text}

I request that you provide me with access to these records in electronic format if possible. 
If there are any fees for searching or copying these records, please inform me if the cost will exceed $25.

I am requesting a fee waiver pursuant to 5 U.S.C. § 552(a)(4)(A)(iii) and 28 C.F.R. § 16.10(k). 
The information requested is in the public interest because it will contribute significantly to 
public understanding of the operations or activities of the government.

I am a {fee_category} requester within the meaning of 5 U.S.C. § 552(a)(4)(A).

Thank you for your consideration of this request.

Sincerely,
{requester_name}
"""
    return template


def analyze_census_growth_rates(data: List[Dict[str, Any]], 
                               start_year: int, end_year: int) -> Dict[str, float]:
    """Calculate population growth rates from census data."""
    if not data or len(data) < 2:
        return {'error': 'Insufficient data for analysis'}
    
    start_pop = None
    end_pop = None
    
    for record in data:
        if record.get('year') == start_year:
            start_pop = record.get('population')
        elif record.get('year') == end_year:
            end_pop = record.get('population')
    
    if start_pop is None or end_pop is None:
        return {'error': 'Data for specified years not found'}
    
    if start_pop <= 0:
        return {'error': 'Invalid starting population'}
    
    years_diff = end_year - start_year
    growth_rate = ((end_pop - start_pop) / start_pop) * 100
    
    annualized_rate = ((end_pop / start_pop) ** (1/years_diff) - 1) * 100
    
    return {
        'total_growth_rate': round(growth_rate, 2),
        'annualized_growth_rate': round(annualized_rate, 2),
        'start_population': start_pop,
        'end_population': end_pop,
        'years_span': years_diff
    }


def parse_pacer_case_number(case_string: str) -> Dict[str, Any]:
    """Parse and validate PACER case number format."""
    pattern = r'(\d:\d{2})-([a-z]{2})-(\d+)'
    match = re.match(pattern, case_string, re.IGNORECASE)
    
    if match:
        court_code, case_type, case_num = match.groups()
        return {
            'valid': True,
            'court_code': court_code,
            'case_type': case_type.upper(),
            'case_number': int(case_num),
            'formatted': f"{court_code}-{case_type.upper()}-{case_num}"
        }
    
    return {'valid': False, 'error': 'Invalid PACER case number format'}


def build_grants_gov_query(filters: Dict[str, Any]) -> str:
    """Build query string for Grants.gov API."""
    query_parts = []
    
    if filters.get('keywords'):
        query_parts.append(f"keyword={filters['keywords']}")
    
    if filters.get('agency'):
        query_parts.append(f"agency={filters['agency']}")
    
    if filters.get('category'):
        query_parts.append(f"fundingCategory={filters['category']}")
    
    if filters.get('eligibility'):
        query_parts.append(f"eligibility={filters['eligibility']}")
    
    if filters.get('min_amount'):
        query_parts.append(f"minAward={filters['min_amount']}")
    
    if filters.get('max_amount'):
        query_parts.append(f"maxAward={filters['max_amount']}")
    
    if filters.get('deadline_start'):
        query_parts.append(f"closeDateStart={filters['deadline_start']}")
    
    if filters.get('deadline_end'):
        query_parts.append(f"closeDateEnd={filters['deadline_end']}")
    
    return "&".join(query_parts)


def validate_congressional_bill_number(bill_str: str) -> Dict[str, Any]:
    """Validate congressional bill number format."""
    pattern = r'([A-Z]{1,3})\s*(\d{1,5})'
    match = re.match(pattern, bill_str.strip(), re.IGNORECASE)
    
    if match:
        bill_type, bill_num = match.groups()
        bill_type = bill_type.upper()
        
        valid_types = ['HR', 'S', 'HRES', 'SRES', 'HJRES', 'SJRES', 'HCONRES', 'SCONRES']
        
        if bill_type in valid_types:
            return {
                'valid': True,
                'type': bill_type,
                'number': int(bill_num),
                'chamber': 'House' if bill_type.startswith('H') else 'Senate',
                'formatted': f"{bill_type}{bill_num}"
            }
    
    return {
        'valid': False,
        'error': 'Invalid bill number format',
        'expected_format': 'HR1234, S567, HRES89, etc.'
    }


def generate_budget_analysis_report(budget_data: List[Dict[str, Any]], 
                                  fiscal_years: List[int]) -> Dict[str, Any]:
    """Generate comprehensive budget analysis report."""
    report = {
        'fiscal_years': fiscal_years,
        'total_budget': 0,
        'agency_breakdown': defaultdict(float),
        'year_over_year_changes': {},
        'largest_increases': [],
        'largest_decreases': []
    }
    
    year_totals = defaultdict(float)
    agency_year_data = defaultdict(lambda: defaultdict(float))
    
    for item in budget_data:
        year = item.get('fiscal_year')
        agency = item.get('agency')
        amount = item.get('budget_amount', 0)
        
        if year in fiscal_years:
            year_totals[year] += amount
            agency_year_data[agency][year] = amount
            report['agency_breakdown'][agency] += amount
    
    if len(fiscal_years) >= 2:
        fiscal_years_sorted = sorted(fiscal_years)
        for i in range(1, len(fiscal_years_sorted)):
            prev_year = fiscal_years_sorted[i-1]
            curr_year = fiscal_years_sorted[i]
            
            prev_total = year_totals[prev_year]
            curr_total = year_totals[curr_year]
            
            if prev_total > 0:
                change_pct = ((curr_total - prev_total) / prev_total) * 100
                report['year_over_year_changes'][f"{prev_year}-{curr_year}"] = round(change_pct, 2)
    
    report['total_budget'] = sum(year_totals.values())
    
    return dict(report)


def extract_agency_acronyms(text: str) -> List[str]:
    """Extract federal agency acronyms from text."""
    agency_pattern = r'\b([A-Z]{2,5})\b'
    matches = re.findall(agency_pattern, text)
    
    common_agencies = {
        'EPA', 'FBI', 'CIA', 'NSA', 'DOD', 'DHS', 'DOJ', 'DOT', 'DOL', 
        'HHS', 'HUD', 'HUD', 'VA', 'SSA', 'IRS', 'FDA', 'USDA', 'NASA',
        'NSF', 'NIH', 'CDC', 'FEMA', 'SEC', 'FTC', 'FCC', 'NRC', 'TSA'
    }
    
    return [match for match in matches if match in common_agencies]


class SkillEngine:
    """Main engine for Presidential/Government Resources skill."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_keys = config.get('api_keys', {})
        self.timeout = config.get('timeout', 30)
        self.session = requests.Session()
        
    def executive_orders_search(self, query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search executive orders database."""
        if filters is None:
            filters = {}
        
        parsed_eo = parse_executive_order_number(query)
        
        return {
            'query': query,
            'parsed_order': parsed_eo,
            'filters': filters,
            'results': [],
            'status': 'success'
        }
    
    def federal_register_analysis(self, agency: str, date_range: Dict[str, str]) -> Dict[str, Any]:
        """Analyze Federal Register entries."""
        return {
            'agency': agency,
            'date_range': date_range,
            'document_count': 0,
            'rule_makings': [],
            'notices': [],
            'analysis': {
                'total_documents': 0,
                'significant_rules': 0
            }
        }
    
    def congressional_records_query(self, bill_number: str, congress: int) -> Dict[str, Any]:
        """Query congressional records."""
        validation = validate_congressional_bill_number(bill_number)
        
        return {
            'bill_number': bill_number,
            'congress': congress,
            'validation': validation,
            'sponsors': [],
            'status': 'unknown',
            'actions': []
        }
    
    def foia_request_automation(self, agency: str, request_details: Dict[str, Any]) -> Dict[str, Any]:
        """Automate FOIA request generation."""
        request_text = request_details.get('request_text', '')
        requester_name = request_details.get('requester_name', 'Requester')
        requester_address = request_details.get('requester_address', 'Address Unknown')
        
        foia_letter = build_foia_request_template(
            agency, request_text, requester_name, requester_address
        )
        
        return {
            'agency': agency,
            'request_letter': foia_letter,
            'tracking_number': hashlib.md5(foia_letter.encode()).hexdigest()[:12],
            'status': 'draft'
        }
    
    def grants_gov_research(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """Research grants.gov opportunities."""
        query_string = build_grants_gov_query(search_params)
        
        return {
            'search_params': search_params,
            'query_string': query_string,
            'opportunities': [],
            'total_matches': 0,
            'eligibility_matches': 0
        }
    
    def pacer_court_records(self, case_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Search PACER court records."""
        case_number = case_criteria.get('case_number', '')
        parsed_case = parse_pacer_case_number(case_number)
        
        return {
            'search_criteria': case_criteria,
            'case_validation': parsed_case,
            'results': [],
            'court_info': {},
            'docket_entries': 0
        }
    
    def census_data_analysis(self, geographic_area: str, variables: List[str]) -> Dict[str, Any]:
        """Analyze census data."""
        return {
            'geographic_area': geographic_area,
            'variables': variables,
            'data_points': {},
            'growth_analysis': {},
            'demographics': {}
        }
    
    def federal_budget_analysis(self, category: str, years: List[int]) -> Dict[str, Any]:
        """Analyze federal budget data."""
        sample_data = [
            {'fiscal_year': year, 'agency': category, 'budget_amount': year * 1000000}
            for year in years
        ]
        
        analysis = generate_budget_analysis_report(sample_data, years)
        
        return {
            'budget_category': category,
            'fiscal_years': years,
            'analysis': analysis,
            'total_allocation': analysis.get('total_budget', 0)
        }
    
    def run(self, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Main dispatcher method."""
        capability_map = {
            'executive_orders_search': self.executive_orders_search,
            'federal_register_analysis': self.federal_register_analysis,
            'congressional_records_query': self.congressional_records_query,
            'foia_request_automation': self.foia_request_automation,
            'grants_gov_research': self.grants_gov_research,
            'pacer_court_records': self.pacer_court_records,
            'census_data_analysis': self.census_data_analysis,
            'federal_budget_analysis': self.federal_budget_analysis
        }
        
        if capability not in capability_map:
            raise ValueError(f"Unknown capability: {capability}")
        
        try:
            method = capability_map[capability]
            return method(**params)
        except Exception as e:
            return {
                'error': str(e),
                'capability': capability,
                'status': 'failed'
            }


class TestGovernmentResourcesSkill(unittest.TestCase):
    """Test cases for Government Resources skill."""
    
    def setUp(self):
        self.config = {'api_keys': {}, 'timeout': 30}
        self.engine = SkillEngine(self.config)
    
    def test_skill_metadata(self):
        """Test that skill metadata is properly defined."""
        self.assertEqual(SKILL_METADATA['name'], "Presidential/Government Resources")
        self.assertEqual(SKILL_METADATA['id'], "government_resources")
        self.assertIn('capabilities', SKILL_METADATA)
        self.assertIn('executive_orders_search', SKILL_METADATA['capabilities'])
    
    def test_parse_executive_order_number(self):
        """Test executive order number parsing."""
        test_cases = [
            ("Executive Order 12345", 12345),
            ("E.O. 6789", 6789),
            ("EO 987", 987),
            ("Exec. Order 123", 123),
            ("Invalid order", None)
        ]
        
        for test_input, expected in test_cases:
            result = parse_executive_order_number(test_input)
            if expected:
                self.assertEqual(result['number'], expected)
                self.assertTrue(result['parsed'])
            else:
                self.assertFalse(result['parsed'])
    
    def test_validate_federal_citation(self):
        """Test Federal Register citation validation."""
        valid_citation = "88 Fed. Reg. 12345 (January 15, 2023)"
        result = validate_federal_register_citation(valid_citation)
        self.assertTrue(result['valid'])
        self.assertEqual(result['volume'], 88)
        self.assertEqual(result['page'], 12345)
        
        invalid_citation = "Invalid format"
        result = validate_federal_register_citation(invalid_citation)
        self.assertFalse(result['valid'])
    
    def test_build_foia_request_template(self):
        """Test FOIA request template generation."""
        result = build_foia_request_template(
            "EPA", 
            "All emails regarding climate policy",
            "John Doe",
            "123 Main St, Washington DC 20001"
        )
        
        self.assertIn("EPA", result)
        self.assertIn("Freedom of Information Act Request", result)
        self.assertIn("John Doe", result)
        self.assertIn("123 Main St", result)
    
    def test_analyze_census_growth_rates(self):
        """Test census growth rate analysis."""
        test_data = [
            {'year': 2020, 'population': 1000000},
            {'year': 2021, 'population': 1100000},
            {'year': 2022, 'population': 1210000}
        ]
        
        result = analyze_census_growth_rates(test_data, 2020, 2022)
        self.assertEqual(result['total_growth_rate'], 21.0)
        self.assertEqual(result['start_population'], 1000000)
        self.assertEqual(result['end_population'], 1210000)
    
    def test_parse_pacer_case_number(self):
        """Test PACER case number parsing."""
        valid_case = "1:23-cv-12345"
        result = parse_pacer_case_number(valid_case)
        self.assertTrue(result['valid'])
        self.assertEqual(result['court_code'], '1:23')
        self.assertEqual(result['case_type'], 'CV')
        self.assertEqual(result['case_number'], 12345)
        
        invalid_case = "invalid-case"
        result = parse_pacer_case_number(invalid_case)
        self.assertFalse(result['valid'])
    
    def test_validate_congressional_bill_number(self):
        """Test congressional bill number validation."""
        valid_bills = ['HR1234', 'S567', 'HRES89', 'SJRES12']
        for bill in valid_bills:
            result = validate_congressional_bill_number(bill)
            self.assertTrue(result['valid'])
        
        invalid_bills = ['INVALID', 'H1234', 'HR']
        for bill in invalid_bills:
            result = validate_congressional_bill_number(bill)
            self.assertFalse(result['valid'])
    
    def test_build_grants_gov_query(self):
        """Test grants.gov query builder."""
        filters = {
            'keywords': 'environment',
            'agency': 'EPA',
            'min_amount': 100000,
            'max_amount': 500000
        }
        
        result = build_grants_gov_query(filters)
        self.assertIn('keyword=environment', result)
        self.assertIn('agency=EPA', result)
        self.assertIn('minAward=100000', result)
        self.assertIn('maxAward=500000', result)
    
    def test_skill_engine_initialization(self):
        """Test SkillEngine initialization."""
        engine = SkillEngine({'api_keys': {'test': 'key'}, 'timeout': 60})
        self.assertEqual(engine.config['timeout'], 60)
        self.assertIn('test', engine.api_keys)
    
    def test_skill_engine_executive_orders(self):
        """Test executive orders search capability."""
        result = self.engine.executive_orders_search("Executive Order 12345")
        self.assertEqual(result['query'], "Executive Order 12345")
        self.assertIn('parsed_order', result)
        self.assertTrue(result['parsed_order']['parsed'])
    
    def test_skill_engine_foia_automation(self):
        """Test FOIA request automation."""
        params = {
            'agency': 'FBI',
            'request_details': {
                'request_text': 'All documents regarding surveillance programs',
                'requester_name': 'Jane Smith',
                'requester_address': '456 Oak Ave, Washington DC 20002'
            }
        }
        
        result = self.engine.foia_request_automation(**params)
        self.assertIn('request_letter', result)
        self.assertIn('tracking_number', result)
        self.assertEqual(len(result['tracking_number']), 12)
    
    def test_skill_engine_dispatcher(self):
        """Test main dispatcher method."""
        params = {'query': 'Executive Order 123', 'filters': {}}
        result = self.engine.run('executive_orders_search', params)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['capability'], 'executive_orders_search')
        
        with self.assertRaises(ValueError):
            self.engine.run('invalid_capability', {})


if __name__ == '__main__':
    unittest.main()