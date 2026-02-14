import json
import re
import os
import math
import hashlib
import statistics
import requests
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple
import unittest
import logging

SKILL_METADATA = {
    "name": "Stealth Lead Generator — Insurance & Life Events",
    "id": "stealth_lead_gen",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Advanced stealth scraping and lead generation for insurance life events including death, marriage, birth, property, business, retirement, and health-related triggers with full campaign management and compliance tracking",
    "capabilities": [
        "death_registry_scraping",
        "marriage_registry_scraping", 
        "birth_registry_scraping",
        "property_transfer_scraping",
        "business_filing_scraping",
        "obituary_aggregation",
        "court_record_scraping",
        "campaign_automation",
        "lead_scoring",
        "data_enrichment",
        "compliance_tracking",
        "roi_analysis"
    ],
    "domain": "insurance_lead_generation"
}

EXPERT_PROMPTS = {
    "death_lead_generation": """
Generate a targeted lead list for final expense insurance based on recent deaths in {county}, {state} 
for the past {time_period} days. Focus on surviving spouses aged 50-85 with estimated household 
income above {min_income}. Include family relationship mapping and contact information discovery.
Target demographics: {target_demographics}
Exclusion criteria: {exclusion_criteria}
""",
    "marriage_insurance_opportunity": """
Identify newly married couples in {location} within the last {timeframe} months for life insurance 
and homeowners insurance lead generation. Prioritize couples with age range {age_range}, 
property purchases over ${property_value}, and combined income estimates above ${income_threshold}.
Include wedding registry data analysis and social media profile matching.
""",
    "new_parent_insurance_leads": """
Scrape birth registry records for {state} covering the last {months} months to identify new parents 
needing life insurance coverage. Target parents aged {parent_age_range} with home ownership indicators,
income estimates ${income_min}+, and existing insurance gap analysis. Include pediatrician office
proximity mapping for local agent targeting.
""",
    "property_insurance_triggers": """
Extract recent property transfers and new mortgages in {county} county from assessor records.
Filter for purchase prices between ${min_price} and ${max_price}, owner ages {age_demographics},
and properties with loan-to-value ratios above {ltv_threshold}. Cross-reference with existing
insurance policy databases to identify coverage gaps.
""",
    "business_commercial_leads": """
Scrape new business filings with the {state} Secretary of State for the last {days} days.
Filter by business type: {business_types}, employee count {employee_range}, and registered
capital ${capital_min}+. Identify commercial insurance needs including general liability,
workers comp, and professional liability coverage requirements.
""",
    "retirement_final_expense": """
Mine pension and retirement system records for {state} to identify individuals aged {age_range}
approaching retirement. Focus on those with pension amounts below ${pension_threshold} and
no existing final expense coverage. Include Medicare enrollment status and health facility
proximity for burial insurance targeting.
""",
    "health_event_insurance_trigger": """
Analyze hospital discharge records and health facility data for {region} to identify
insurance-triggering health events. Target patients aged {target_age} with diagnoses
indicating potential life expectancy concerns. Cross-reference with existing life insurance
databases and include family contact discovery for outreach.
""",
    "divorce_policy_update_leads": """
Scrape divorce filings and decrees from {county} county courts for the past {time_period}.
Identify individuals needing beneficiary updates, policy splits, and new insurance coverage.
Target age range {age_range} with dependent children and asset division indicating
insurance protection needs.
""",
    "obituary_family_outreach": """
Aggregate all obituaries from {geographic_area} published in the last {days} days.
Identify surviving family members, their relationships, ages, and locations. Focus on
spouses aged 50-85 and adult children with families. Include funeral service information
and condolence guestbook analysis for respectful final expense insurance outreach.
""",
    "campaign_performance_optimization": """
Analyze lead conversion data for insurance campaigns targeting {life_event} triggers.
Calculate cost per acquisition by channel, conversion rates by demographic segment,
and lifetime value estimates. Optimize campaign parameters including timing, messaging,
channel mix, and geographic targeting for maximum ROI on insurance lead generation spend.
"""
}

INTEGRATION_POINTS = {
    "legacy_com_obituaries": {
        "type": "api",
        "endpoint": "https://www.legacy.com/api/obituaries/search",
        "description": "Legacy.com obituary search and aggregation API",
        "auth_method": "api_key",
        "documentation_url": "https://github.com/littlehoushontheprairie/check-obituaries-alert"
    },
    "apify_company_registry": {
        "type": "tool",
        "endpoint": "https://api.apify.com/v2/acts/tropical_quince~us-company-registry-scraper",
        "description": "US company registry scraping via Apify platform",
        "auth_method": "token",
        "documentation_url": "https://apify.com/tropical_quince/us-company-registry-scraper/api/openapi"
    },
    "county_clerk_api": {
        "type": "database",
        "endpoint": "https://county-clerk-api.gov/vital-records",
        "description": "County clerk vital records database",
        "auth_method": "oauth2",
        "documentation_url": "https://county-clerk-docs.gov"
    },
    "state_corporation_commission": {
        "type": "database",
        "endpoint": "https://scc.state.gov/business-filings",
        "description": "State business filing records",
        "auth_method": "certificate",
        "documentation_url": "https://scc.state.gov/api-docs"
    },
    "medicare_enrollment_db": {
        "type": "database",
        "endpoint": "https://medicare.gov/enrollment-data",
        "description": "Medicare enrollment and demographic data",
        "auth_method": "oauth2",
        "documentation_url": "https://medicare.gov/api"
    },
    "property_assessor_api": {
        "type": "api",
        "endpoint": "https://assessor.county.gov/property-records",
        "description": "County property assessment and transfer records",
        "auth_method": "api_key",
        "documentation_url": "https://assessor.county.gov/api-docs"
    },
    "court_records_system": {
        "type": "database",
        "endpoint": "https://court-system.state.gov/records",
        "description": "State court case management system",
        "auth_method": "certificate",
        "documentation_url": "https://court-system.state.gov/api"
    },
    "social_media_contact_scraper": {
        "type": "tool",
        "endpoint": "https://api.apify.com/v2/acts/easyapi~social-media-contact-scraper",
        "description": "Social media profile and contact discovery",
        "auth_method": "token",
        "documentation_url": "https://apify.com/easyapi/social-media-contact-scraper/api"
    }
}

def parse_vital_record(record_text: str) -> Dict[str, Any]:
    """Parse vital record text into structured data"""
    patterns = {
        'name': r'Name[:\s]+([A-Za-z\s,.-]+?)(?=\s*(?:Age|Date|Location)|$)',
        'age': r'Age[:\s]+(\d+)',
        'date': r'Date[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
        'location': r'(?:Location|County)[:\s]+([A-Za-z\s,.]+?)(?=\s*(?:Age|Date|Name)|$)',
        'spouse': r'(?:Spouse|Husband|Wife)[:\s]+([A-Za-z\s,.]+?)(?=\s*(?:Age|Date|Location)|$)'
    }
    
    result = {}
    for field, pattern in patterns.items():
        match = re.search(pattern, record_text, re.IGNORECASE)
        if match:
            result[field] = match.group(1).strip()
    
    if 'age' in result:
        try:
            result['age'] = int(result['age'])
        except ValueError:
            pass
            
    if 'date' in result:
        try:
            result['parsed_date'] = datetime.strptime(result['date'], '%B %d, %Y')
        except:
            pass
            
    return result

def calculate_lead_score(life_event: str, age: int, income_estimate: float, 
                        family_size: int, location_score: float = 1.0) -> float:
    """Calculate lead quality score based on multiple factors"""
    base_scores = {
        'death': 85,
        'marriage': 75,
        'birth': 70,
        'divorce': 65,
        'property_purchase': 80,
        'business_start': 60,
        'retirement': 90,
        'health_event': 95
    }
    
    base_score = base_scores.get(life_event, 50)
    
    age_modifier = 1.0
    if 50 <= age <= 85:
        age_modifier = 1.2
    elif age < 30 or age > 90:
        age_modifier = 0.7
        
    income_modifier = min(income_estimate / 50000, 2.0)
    
    family_modifier = 1 + (family_size - 2) * 0.1
    
    final_score = base_score * age_modifier * income_modifier * family_modifier * location_score
    
    return min(100, max(0, final_score))

def generate_campaign_message(life_event: str, demographic_profile: Dict[str, Any]) -> str:
    """Generate personalized insurance outreach message"""
    templates = {
        'death': "Dear {name}, We understand this may be a difficult time. Our final expense insurance can help protect your loved ones from unexpected costs. Coverage starts at just ${monthly_cost}/month.",
        'marriage': "Congratulations {name}! As you begin this new chapter, consider protecting your future together with life insurance designed for newlyweds. Get a free quote today.",
        'birth': "Welcome baby {baby_name}! As new parents, it's time to think about protecting your growing family. We specialize in affordable life insurance for young families.",
        'divorce': "Hi {name}, going through changes? Update your beneficiaries and explore new insurance options tailored to your current situation. Free consultation available.",
        'property_purchase': "Congratulations on your new home {name}! Protect your investment with homeowners and life insurance packages. Local agents ready to help.",
        'business_start': "Exciting times {name}! Starting a business means new insurance needs. We offer comprehensive commercial coverage including liability and workers comp.",
        'retirement': "Planning retirement {name}? Consider final expense insurance to protect your family from unexpected costs. No medical exam required for qualified applicants.",
        'health_event': "Hi {name}, your health is important. We specialize in life insurance for individuals with health considerations. Guaranteed acceptance policies available."
    }
    
    template = templates.get(life_event, "Hello {name}, we have insurance options that may interest you.")
    
    name = demographic_profile.get('preferred_name', 'there')
    monthly_cost = demographic_profile.get('estimated_monthly_cost', 25)
    baby_name = demographic_profile.get('baby_name', 'baby')
    
    message = template.format(
        name=name,
        monthly_cost=monthly_cost,
        baby_name=baby_name
    )
    
    return message

def build_county_query(county: str, state: str, record_type: str, 
                      date_range: Tuple[str, str]) -> Dict[str, Any]:
    """Build optimized query for county records"""
    query = {
        "county": county.upper(),
        "state": state.upper(),
        "record_type": record_type,
        "start_date": date_range[0],
        "end_date": date_range[1],
        "fields": ["name", "age", "date", "location", "related_parties"],
        "limit": 1000,
        "offset": 0
    }
    
    if record_type == 'death':
        query["age_range"] = {"min": 18, "max": 100}
        query["include_obituaries"] = True
    elif record_type == 'marriage':
        query["include_divorces"] = False
        query["age_range"] = {"min": 18, "max": 85}
    elif record_type == 'birth':
        query["parent_info"] = True
        query["birth_weight"] = True
        
    return query

def estimate_household_income(property_value: float, location_zip: str, 
                            census_data: Dict[str, float]) -> float:
    """Estimate household income based on property and location data"""
    base_multiplier = {
        'urban': 0.28,
        'suburban': 0.25,
        'rural': 0.20
    }
    
    zip_prefix = location_zip[:3]
    location_type = 'suburban'
    
    if zip_prefix in ['100', '606', '900', '021']:
        location_type = 'urban'
    elif zip_prefix in ['590', '677', '822', '835']:
        location_type = 'rural'
        
    multiplier = base_multiplier[location_type]
    estimated_income = (property_value * multiplier) / 0.28
    
    census_modifier = census_data.get(zip_prefix, 1.0)
    estimated_income *= census_modifier
    
    return max(25000, min(estimated_income, 250000))

def validate_phone_number(phone: str) -> Optional[str]:
    """Validate and format phone number"""
    digits_only = re.subsub('[^0-9]', '', phone)
    
    if len(digits_only) == 10:
        return f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
    elif len(digits_only) == 11 and digits_only[0] == '1':
        return f"({digits_only[:4]}) {digits_only[4:7]}-{digits_only[7:]}"
        
    return None

def generate_compliance_report(campaign_data: Dict[str, Any], 
                             jurisdiction: str) -> Dict[str, Any]:
    """Generate compliance report for insurance marketing regulations"""
    report = {
        "jurisdiction": jurisdiction,
        "campaign_id": campaign_data.get('id'),
        "date_generated": datetime.now().isoformat(),
        "total_contacts": len(campaign_data.get('contacts', [])),
        "opt_outs": campaign_data.get('opt_outs', 0),
        "complaints": campaign_data.get('complaints', 0),
        "compliance_score": 100
    }
    
    if report['opt_outs'] > report['total_contacts'] * 0.02:
        report['compliance_score'] -= 20
        
    if report['complaints'] > report['total_contacts'] * 0.005:
        report['compliance_score'] -= 30
        
    can_spam_violations = []
    tcpa_violations = []
    
    for contact in campaign_data.get('contacts', []):
        if not contact.get('consent_timestamp'):
            tcpa_violations.append(contact.get('phone'))
        if not contact.get('unsubscribe_link'):
            can_spam_violations.append(contact.get('email'))
            
    report['can_spam_violations'] = len(can_spam_violations)
    report['tcpa_violations'] = len(tcpa_violations)
    
    if report['can_spam_violations'] > 0:
        report['compliance_score'] -= 15
    if report['tcpa_violations'] > 0:
        report['compliance_score'] -= 25
        
    return report

def create_lead_database(leads: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Organize leads by category and score"""
    database = defaultdict(list)
    
    for lead in leads:
        category = lead.get('life_event', 'unknown')
        score = lead.get('lead_score', 0)
        
        if score >= 80:
            tier = 'hot'
        elif score >= 60:
            tier = 'warm'
        elif score >= 40:
            tier = 'cold'
        else:
            tier = 'archive'
            
        lead['tier'] = tier
        lead['assigned_date'] = datetime.now().isoformat()
        
        database[category].append(lead)
        
    for category in database:
        database[category].sort(key=lambda x: x['lead_score'], reverse=True)
        
    return dict(database)

def analyze_roi(campaign_id: str, spend: float, revenue: float, 
               leads_generated: int, policies_sold: int) -> Dict[str, float]:
    """Calculate return on investment metrics"""
    metrics = {
        'campaign_id': campaign_id,
        'total_spend': spend,
        'total_revenue': revenue,
        'gross_profit': revenue - spend,
        'roi_percentage': ((revenue - spend) / spend * 100) if spend > 0 else 0,
        'cost_per_lead': spend / leads_generated if leads_generated > 0 else 0,
        'cost_per_policy': spend / policies_sold if policies_sold > 0 else 0,
        'lead_conversion_rate': (policies_sold / leads_generated * 100) if leads_generated > 0 else 0,
        'revenue_per_lead': revenue / leads_generated if leads_generated > 0 else 0
    }
    
    return metrics

class SkillEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def scrape_death_records(self, county: str, state: str,
                           date_range: Tuple[str, str]) -> List[Dict[str, Any]]:
        """Scrape death registry records for insurance leads"""
        query = build_county_query(county, state, 'death', date_range)
        
        # Simulate API call
        mock_data = [
            {
                "name": "John Smith",
                "age": 67,
                "date": "2024-01-15",
                "location": "Springfield County",
                "spouse": "Mary Smith",
                "address": "123 Main St",
                "zip_code": "62701"
            }
        ]
        
        leads = []
        for record in mock_data:
            income_estimate = estimate_household_income(150000, record['zip_code'], {})
            lead_score = calculate_lead_score('death', record['age'], income_estimate, 2)
            
            lead = {
                "life_event": "death",
                "deceased_name": record['name'],
                "surviving_spouse": record.get('spouse'),
                "lead_score": lead_score,
                "estimated_income": income_estimate,
                "location": record['location'],
                "date": record['date'],
                "data_source": "county_death_records"
            }
            leads.append(lead)
            
        return leads
    
    def scrape_marriage_records(self, county: str, state: str,
                              date_range: Tuple[str, str]) -> List[Dict[str, Any]]:
        """Scrape marriage registry for newlywed insurance leads"""
        query = build_county_query(county, state, 'marriage', date_range)
        
        mock_data = [
            {
                "bride_name": "Sarah Johnson",
                "groom_name": "Michael Davis",
                "bride_age": 28,
                "groom_age": 30,
                "marriage_date": "2024-01-20",
                "county": "Cook County",
                "zip_code": "60601"
            }
        ]
        
        leads = []
        for record in mock_data:
            avg_age = (record['bride_age'] + record['groom_age']) / 2
            income_estimate = estimate_household_income(300000, record['zip_code'], {})
            lead_score = calculate_lead_score('marriage', avg_age, income_estimate, 2)
            
            lead = {
                "life_event": "marriage",
                "couple_names": f"{record['bride_name']} & {record['groom_name']}",
                "average_age": avg_age,
                "lead_score": lead_score,
                "estimated_income": income_estimate,
                "marriage_date": record['marriage_date'],
                "location": record['county'],
                "data_source": "county_marriage_records"
            }
            leads.append(lead)
            
        return leads
    
    def aggregate_obituaries(self, geographic_area: str,
                           days_back: int) -> List[Dict[str, Any]]:
        """Aggregate obituaries for final expense insurance leads"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        mock_obituaries = [
            {
                "deceased_name": "Robert Johnson",
                "age": 72,
                "death_date": "2024-01-10",
                "survivors": ["wife Linda", "son Robert Jr.", "daughter Susan"],
                "service_location": "Springfield Funeral Home",
                "zip_code": "62702"
            }
        ]
        
        leads = []
        for obit in mock_obituaries:
            for survivor in obit['survivors']:
                relationship = survivor.split()[0]
                if relationship in ['wife', 'husband', 'spouse']:
                    income_estimate = estimate_household_income(180000, obit['zip_code'], {})
                    lead_score = calculate_lead_score('death', 65, income_estimate, 2)
                    
                    lead = {
                        "life_event": "death",
                        "deceased_name": obit['deceased_name'],
                        "survivor_name": survivor,
                        "relationship": relationship,
                        "lead_score": lead_score,
                        "estimated_income": income_estimate,
                        "death_date": obit['death_date'],
                        "service_location": obit['service_location'],
                        "data_source": "obituary_aggregation"
                    }
                    leads.append(lead)
                    
        return leads
    
    def generate_campaign(self, leads: List[Dict[str, Any]], 
                         campaign_type: str) -> Dict[str, Any]:
        """Generate targeted insurance campaign"""
        campaign = {
            "id": hashlib.md5(f"{campaign_type}_{datetime.now()}".encode()).hexdigest(),
            "type": campaign_type,
            "created_date": datetime.now().isoformat(),
            "total_leads": len(leads),
            "contacts": []
        }
        
        for lead in leads:
            demographic_profile = {
                "preferred_name": lead.get('surviving_spouse', 'there'),
                "estimated_monthly_cost": 35 if lead['lead_score'] > 80 else 50
            }
            
            message = generate_campaign_message(lead['life_event'], demographic_profile)
            
            contact = {
                "lead_id": hashlib.md5(str(lead).encode()).hexdigest(),
                "message": message,
                "life_event": lead['life_event'],
                "lead_score": lead['lead_score'],
                "channel": "direct_mail" if lead['lead_score'] > 70 else "email",
                "estimated_conversion_probability": min(lead['lead_score'] / 100 * 0.3, 0.25)
            }
            
            campaign['contacts'].append(contact)
            
        return campaign
    
    def run(self, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution method"""
        self.logger.info(f"Executing capability: {capability}")
        
        try:
            if capability == 'death_registry_scraping':
                return {
                    "leads": self.scrape_death_records(
                        params['county'], params['state'], 
                        (params['start_date'], params['end_date'])
                    ),
                    "capability": capability
                }
                
            elif capability == 'marriage_registry_scraping':
                return {
                    "leads": self.scrape_marriage_records(
                        params['county'], params['state'],
                        (params['start_date'], params['end_date'])
                    ),
                    "capability": capability
                }
                
            elif capability == 'obituary_aggregation':
                return {
                    "leads": self.aggregate_obituaries(
                        params['geographic_area'], params['days_back']
                    ),
                    "capability": capability
                }
                
            elif capability == 'campaign_automation':
                return self.generate_campaign(params['leads'], params['campaign_type'])
                
            elif capability == 'lead_scoring':
                return {
                    "scores": [
                        calculate_lead_score(
                            params['life_event'], lead['age'], 
                            lead['income_estimate'], lead['family_size']
                        ) for lead in params['leads']
                    ]
                }
                
            elif capability == 'compliance_tracking':
                return generate_compliance_report(
                    params['campaign_data'], params['jurisdiction']
                )
                
            elif capability == 'roi_analysis':
                return analyze_roi(
                    params['campaign_id'], params['spend'], 
                    params['revenue'], params['leads_generated'],
                    params['policies_sold']
                )
                
            else:
                raise ValueError(f"Unknown capability: {capability}")
                
asian exception as e:
            self.logger.error(f"Error in {capability}: {str(e)}")
            return {"error": str(e), "capability": capability}

class TestStealthLeadGenerator(unittest.TestCase):
    
    def test_metadata_validation(self):
        self.assertEqual(SKILL_METADATA['id'], 'stealth_lead_gen')
        self.assertIn('death_registry_scraping', SKILL_METADATA['capabilities'])
        self.assertGreater(len(SKILL_METADATA['capabilities']), 10)
        
    def test_parse_vital_record(self):
        record_text = "Name: John Smith, Age: 67, Date: January 15, 2024, Location: Springfield County"
        parsed = parse_vital_record(record_text)
        self.assertEqual(parsed['name'], 'John Smith')
        self.assertEqual(parsed['age'], 67)
        self.assertIn('parsed_date', parsed)
        
    def test_calculate_lead_score(self):
        score = calculate_lead_score('death', 65, 75000, 3)
        self.assertGreater(score, 80)
        self.assertLessEqual(score, 100)
        
        young_score = calculate_lead_score('marriage', 25, 50000, 2)
        self.assertLess(young_score, 80)
        
    def test_generate_campaign_message(self):
        profile = {"preferred_name": "Mary", "estimated_monthly_cost": 35}
        message = generate_campaign_message('death', profile)
        self.assertIn('Mary', message)
        self.assertIn('35', message)
        
    def test_build_county_query(self):
        query = build_county_query('Cook', 'IL', 'death', ('2024-01-01', '2024-01-31'))
        self.assertEqual(query['county'], 'COOK')
        self.assertEqual(query['state'], 'IL')
        self.assertIn('age_range', query)
        
    def test_estimate_household_income(self):
        income = estimate_household_income(200000, '60601', {})
        self.assertGreater(income, 50000)
        self.assertLess(income, 200000)
        
    def test_validate_phone_number(self):
        valid_phone = validate_phone_number('(555) 123-4567')
        self.assertIsNotNone(valid_phone)
        
        invalid_phone = validate_phone_number('123')
        self.assertIsNone(invalid_phone)
        
    def test_generate_compliance_report(self):
        campaign_data = {
            'id': 'test123',
            'contacts': [
                {'email': 'test@test.com', 'consent_timestamp': '2024-01-01'},
                {'phone': '5551234567', 'consent_timestamp': None}
            ],
            'opt_outs': 1,
            'complaints': 0
        }
        report = generate_compliance_report(campaign_data, 'IL')
        self.assertEqual(report['jurisdiction'], 'IL')
        self.assertIn('compliance_score', report)
        
    def test_create_lead_database(self):
        leads = [
            {'life_event': 'death', 'lead_score': 85, 'name': 'Lead 1'},
            {'life_event': 'marriage', 'lead_score': 65, 'name': 'Lead 2'},
            {'life_event': 'death', 'lead_score': 45, 'name': 'Lead 3'}
        ]
        database = create_lead_database(leads)
        self.assertIn('death', database)
        self.assertIn('marriage', database)
        self.assertEqual(database['death'][0]['tier'], 'hot')
        
    def test_analyze_roi(self):
        metrics = analyze_roi('campaign123', 10000, 25000, 200, 15)
        self.assertEqual(metrics['roi_percentage'], 150)
        self.assertEqual(metrics['cost_per_lead'], 50)
        self.assertEqual(metrics['lead_conversion_rate'], 7.5)
        
    def test_skill_engine_initialization(self):
        engine = SkillEngine({'api_key': 'test123'})
        self.assertIsNotNone(engine.config)
        self.assertIsNotNone(engine.session)
        
    def test_skill_engine_death_scraping(self):
        engine = SkillEngine({})
        result = engine.run('death_registry_scraping', {
            'county': 'Cook',
            'state': 'IL',
            'start_date': '2024-01-01',
            'end_date': '2024-01-31'
        })
        self.assertIn('leads', result)
        self.assertGreater(len(result['leads']), 0)
        
    def test_skill_engine_campaign_generation(self):
        engine = SkillEngine({})
        leads = [{'life_event': 'death', 'lead_score': 85}]
        campaign = engine.run('campaign_automation', {
            'leads': leads,
            'campaign_type': 'final_expense'
        })
        self.assertIn('contacts', campaign)
        self.assertGreater(campaign['total_leads'], 0)

if __name__ == '__main__':
    unittest.main()