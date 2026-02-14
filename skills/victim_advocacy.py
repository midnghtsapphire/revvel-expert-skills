import json
import re
import os
import hashlib
import datetime
import statistics
import math
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, namedtuple
import unittest
import logging

SKILL_METADATA = {
    "name": "Victim Advocacy",
    "id": "victim_advocacy",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Comprehensive victim advocacy support for legal professionals handling crime victim cases, including VAWA compliance, trafficking victim resources, compensation claims, protective orders, and victim timeline reconstruction.",
    "capabilities": [
        "victim_impact_statement_generation",
        "vawa_compliance_check",
        "trafficking_resource_lookup",
        "crime_victim_compensation_calculation",
        "protective_order_assistance",
        "victim_timeline_reconstruction",
        "victim_rights_notification",
        "restitution_calculation"
    ],
    "domain": "legal/forensic/victim_advocacy"
}

EXPERT_PROMPTS = {
    "victim_impact_statement": """Generate a comprehensive victim impact statement for {victim_name} who experienced {crime_type} on {incident_date}. 
Key details:
- Physical injuries: {physical_injuries}
- Emotional impact: {emotional_impact}
- Financial losses: {financial_losses}
- Ongoing effects: {ongoing_effects}
- Restitution requested: {restitution_amount}
- Safety concerns: {safety_concerns}
Use trauma-informed language and include all elements required by {jurisdiction} law.""",

    "vawa_compliance_audit": """Conduct a VAWA compliance audit for {agency_name} regarding their handling of {case_type} cases. 
Evaluate:
- Victim notification procedures: {notification_procedures}
- Confidentiality protections: {confidentiality_measures}
- Access to services: {service_access}
- Language access compliance: {language_access}
- Disability accommodations: {disability_accommodations}
Provide specific recommendations for compliance gaps identified.""",

    "trafficking_victim_screening": """Screen {victim_name} for human trafficking indicators based on:
- Recruitment circumstances: {recruitment_details}
- Working conditions: {work_conditions}
- Control mechanisms: {control_methods}
- Documentation status: {documentation}
- Living situation: {living_arrangements}
- Physical signs: {physical_indicators}
- Behavioral indicators: {behavioral_indicators}
Generate a trafficking assessment report with resource referrals.""",

    "compensation_claim_builder": """Build a VOCA compensation claim for {victim_name} with:
- Crime details: {crime_details}
- Medical expenses: {medical_expenses}
- Mental health counseling: {counseling_costs}
- Lost wages: {lost_wages}
- Funeral expenses: {funeral_costs}
- Property damage: {property_damage}
- Insurance coverage: {insurance_info}
Include all required documentation and state-specific requirements for {state}.""",

    "protective_order_analysis": """Analyze the protective order needs for {victim_name} considering:
- Relationship to perpetrator: {relationship}
- History of violence: {violence_history}
- Current threats: {current_threats}
- Children involved: {children_involved}
- Firearms access: {firearms_info}
- Stalking behaviors: {stalking_details}
Recommend appropriate order type and provisions for {jurisdiction}.""",

    "victim_timeline_reconstruction": """Reconstruct the victim timeline for {case_name} from {start_date} to {end_date} using:
- Police reports: {police_reports}
- Medical records: {medical_records}
- Witness statements: {witness_statements}
- Digital evidence: {digital_evidence}
- Financial records: {financial_records}
- Communication logs: {communication_logs}
Create a comprehensive chronological narrative with evidence mapping.""",

    "restitution_calculation": """Calculate restitution owed to {victim_name} in {case_type} case including:
- Medical expenses: {medical_costs}
- Therapy costs: {therapy_costs}
- Lost wages: {lost_wages}
- Property damage: {property_damage}
- Legal fees: {legal_fees}
- Other losses: {other_losses}
Apply {jurisdiction} guidelines and provide itemized calculation.""",

    "victim_rights_notification": """Draft victim rights notification for {victim_name} in {case_type} case under {jurisdiction} law. Include:
- Right to be present: {presence_rights}
- Right to be heard: {hearing_rights}
- Right to restitution: {restitution_rights}
- Right to protection: {protection_rights}
- Right to information: {information_rights}
- Contact information for victim services: {service_contacts}"""
}

INTEGRATION_POINTS = {
    "voca_compensation_api": {
        "type": "api",
        "endpoint": "https://api.ovc.gov/voca/claims",
        "description": "Victims of Crime Act compensation claims processing",
        "auth_method": "oauth2",
        "documentation_url": "https://ovc.gov/library/publications/voca-compensation-manual"
    },
    "vawa_compliance_db": {
        "type": "database",
        "endpoint": "postgresql://victims-db.doj.gov:5432/vawa_compliance",
        "description": "VAWA compliance tracking and audit records",
        "auth_method": "certificate",
        "documentation_url": "https://justice.gov/ovw/compliance"
    },
    "trafficking_resource_directory": {
        "type": "api",
        "endpoint": "https://api.ovcttac.gov/trafficking/resources",
        "description": "National human trafficking victim service directory",
        "auth_method": "api_key",
        "documentation_url": "https://ovcttac.gov/taskforceguide"
    },
    "protective_order_registry": {
        "type": "api",
        "endpoint": "https://api.ncjrs.gov/protective-orders",
        "description": "National protective order registry and validation",
        "auth_method": "oauth2",
        "documentation_url": "https://ncjrs.gov/privacy"
    },
    "victim_notification_system": {
        "type": "tool",
        "endpoint": "https://notify.vinelink.com/api/v2",
        "description": "Automated victim notification system",
        "auth_method": "api_key",
        "documentation_url": "https://vinelink.com/developers"
    }
}

VictimImpactData = namedtuple('VictimImpactData', [
    'victim_name', 'crime_type', 'incident_date', 'physical_injuries',
    'emotional_impact', 'financial_losses', 'ongoing_effects',
    'restitution_amount', 'safety_concerns', 'jurisdiction'
])

CompensationClaim = namedtuple('CompensationClaim', [
    'victim_name', 'crime_details', 'medical_expenses', 'counseling_costs',
    'lost_wages', 'funeral_costs', 'property_damage', 'insurance_info', 'state'
])

TimelineEvent = namedtuple('TimelineEvent', [
    'timestamp', 'event_type', 'description', 'evidence_source', 'significance'
])

def validate_victim_id(victim_id: str) -> bool:
    """Validate victim ID format according to standard conventions."""
    if not victim_id or not isinstance(victim_id, str):
        return False
    pattern = r'^[A-Z]{2}\d{4}-\d{2}-\d{4}$'
    return bool(re.match(pattern, victim_id))

def parse_financial_losses(loss_string: str) -> Dict[str, float]:
    """Parse financial loss string into categorized dictionary."""
    losses = {}
    if not loss_string:
        return losses
    
    pattern = r'(\w+):\s*\$?([\d,]+(?:\.\d{2})?)'
    matches = re.findall(pattern, loss_string)
    
    for category, amount in matches:
        losses[category.lower().replace(' ', '_')] = float(amount.replace(',', ''))
    
    return losses

def calculate_compensation_eligibility(
    state: str, 
    crime_date: datetime.date, 
    reporting_delay_days: int,
    victim_cooperation: bool,
    criminal_history: bool
) -> Dict[str, Any]:
    """Calculate VOCA compensation eligibility based on state rules."""
    eligibility = {
        'eligible': False,
        'reasons': [],
        'max_benefits': 0,
        'deadline_days': 0
    }
    
    state_rules = {
        'CA': {'max_benefit': 70000, 'deadline_days': 365, 'cooperation_required': True},
        'NY': {'max_benefit': 60000, 'deadline_days': 730, 'cooperation_required': True},
        'TX': {'max_benefit': 50000, 'deadline_days': 365, 'cooperation_required': False},
        'FL': {'max_benefit': 25000, 'deadline_days': 365, 'cooperation_required': True}
    }
    
    if state not in state_rules:
        eligibility['reasons'].append(f"State {state} rules not configured")
        return eligibility
    
    rules = state_rules[state]
    
    if reporting_delay_days > rules['deadline_days']:
        eligibility['reasons'].append(f"Reported {reporting_delay_days} days after deadline")
    
    if rules['cooperation_required'] and not victim_cooperation:
        eligibility['reasons'].append("Victim cooperation required but not provided")
    
    if criminal_history:
        eligibility['reasons'].append("Criminal history may affect eligibility")
    
    if not eligibility['reasons']:
        eligibility['eligible'] = True
        eligibility['max_benefits'] = rules['max_benefit']
        eligibility['deadline_days'] = rules['deadline_days']
    
    return eligibility

def generate_victim_impact_statement(data: VictimImpactData) -> str:
    """Generate a comprehensive victim impact statement."""
    statement = f"""
VICTIM IMPACT STATEMENT
    
Victim: {data.victim_name}
Crime Type: {data.crime_type}
Incident Date: {data.incident_date}
Jurisdiction: {data.jurisdiction}

PHYSICAL INJURIES:
{data.physical_injuries}

EMOTIONAL IMPACT:
{data.emotional_impact}

FINANCIAL LOSSES:
{data.financial_losses}

ONGOING EFFECTS:
{data.ongoing_effects}

SAFETY CONCERNS:
{data.safety_concerns}

REQUESTED RESTITUTION: ${data.restitution_amount:,.2f}

I affirm that the above statement is true and accurate to the best of my knowledge.

Date: {datetime.date.today().strftime('%B %d, %Y')}
    """
    return statement.strip()

def build_victim_timeline(events: List[TimelineEvent]) -> List[Dict[str, Any]]:
    """Build chronological victim timeline from events."""
    sorted_events = sorted(events, key=lambda x: x.timestamp)
    
    timeline = []
    for event in sorted_events:
        timeline.append({
            'date': event.timestamp.isoformat(),
            'type': event.event_type,
            'description': event.description,
            'evidence': event.evidence_source,
            'significance': event.significance
        })
    
    return timeline

def calculate_restitution_amount(losses: Dict[str, float]) -> Dict[str, Any]:
    """Calculate total restitution amount with breakdown."""
    total = sum(losses.values())
    
    breakdown = {
        'total_restitution': total,
        'itemized_losses': losses,
        'calculation_date': datetime.date.today().isoformat()
    }
    
    return breakdown

def validate_protective_order_requirements(
    relationship: str,
    violence_history: List[str],
    current_threats: List[str],
    jurisdiction: str
) -> Dict[str, Any]:
    """Validate protective order requirements for jurisdiction."""
    requirements = {
        'eligible': False,
        'order_type': None,
        'requirements_met': [],
        'requirements_missing': []
    }
    
    relationship_eligible = relationship.lower() in [
        'spouse', 'former spouse', 'dating', 'family', 'household'
    ]
    
    if relationship_eligible:
        requirements['requirements_met'].append('Qualifying relationship')
    else:
        requirements['requirements_missing'].append('Qualifying relationship required')
    
    if violence_history:
        requirements['requirements_met'].append('History of violence documented')
    else:
        requirements['requirements_missing'].append('Evidence of violence required')
    
    if current_threats:
        requirements['requirements_met'].append('Current threat established')
    else:
        requirements['requirements_missing'].append('Imminent threat required')
    
    if len(requirements['requirements_met']) == 3:
        requirements['eligible'] = True
        requirements['order_type'] = 'Domestic Violence Protective Order'
    
    return requirements

def generate_vawa_compliance_checklist(agency_type: str) -> List[Dict[str, Any]]:
    """Generate VAWA compliance checklist for agency type."""
    base_checklist = [
        {'item': 'Victim notification within 24 hours', 'required': True, 'category': 'notification'},
        {'item': 'Confidentiality protections in place', 'required': True, 'category': 'privacy'},
        {'item': 'Language access services available', 'required': True, 'category': 'access'},
        {'item': 'Disability accommodations provided', 'required': True, 'category': 'access'},
        {'item': 'Trauma-informed training completed', 'required': True, 'category': 'training'},
        {'item': 'Victim services referrals documented', 'required': True, 'category': 'services'}
    ]
    
    if agency_type == 'law_enforcement':
        base_checklist.extend([
            {'item': 'Mandatory arrest policies reviewed', 'required': True, 'category': 'policy'},
            {'item': 'Evidence collection training current', 'required': True, 'category': 'training'}
        ])
    
    return base_checklist

def search_trafficking_resources(state: str, service_type: str) -> List[Dict[str, str]]:
    """Search trafficking victim resources by state and service type."""
    resources = []
    
    mock_resources = {
        'CA': {
            'legal': [{'name': 'California Victim Legal Services', 'phone': '800-834-5000'}],
            'medical': [{'name': 'CA Human Trafficking Health Network', 'phone': '888-373-7888'}],
            'housing': [{'name': 'CA Trafficking Shelters', 'phone': '877-389-7378'}]
        },
        'NY': {
            'legal': [{'name': 'NY Anti-Trafficking Legal Services', 'phone': '800-621-4673'}],
            'medical': [{'name': 'NY Trafficking Health Initiative', 'phone': '212-349-6009'}],
            'housing': [{'name': 'NYC Trafficking Safe Houses', 'phone': '212-349-6009'}]
        }
    }
    
    if state in mock_resources and service_type in mock_resources[state]:
        resources = mock_resources[state][service_type]
    
    return resources

class SkillEngine:
    """Main skill engine for victim advocacy capabilities."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('victim_advocacy')
        self.logger.setLevel(logging.INFO)
        
    def generate_victim_impact_statement(self, data: Dict[str, Any]) -> str:
        """Generate victim impact statement from provided data."""
        try:
            victim_data = VictimImpactData(**data)
            return generate_victim_impact_statement(victim_data)
        except Exception as e:
            self.logger.error(f"Error generating impact statement: {str(e)}")
            raise
    
    def check_vawa_compliance(self, agency_type: str) -> List[Dict[str, Any]]:
        """Check VAWA compliance for agency type."""
        return generate_vawa_compliance_checklist(agency_type)
    
    def get_trafficking_resources(self, state: str, service_type: str) -> List[Dict[str, str]]:
        """Get trafficking victim resources for state and service type."""
        return search_trafficking_resources(state, service_type)
    
    def calculate_compensation(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate crime victim compensation eligibility and amount."""
        try:
            claim = CompensationClaim(**claim_data)
            return calculate_compensation_eligibility(
                claim.state,
                datetime.datetime.strptime(claim.crime_details['date'], '%Y-%m-%d').date(),
                claim.crime_details.get('reporting_delay_days', 0),
                claim.crime_details.get('victim_cooperation', True),
                claim.crime_details.get('criminal_history', False)
            )
        except Exception as e:
            self.logger.error(f"Error calculating compensation: {str(e)}")
            raise
    
    def analyze_protective_order(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze protective order requirements and eligibility."""
        return validate_protective_order_requirements(
            case_data.get('relationship', ''),
            case_data.get('violence_history', []),
            case_data.get('current_threats', []),
            case_data.get('jurisdiction', '')
        )
    
    def reconstruct_timeline(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Reconstruct victim timeline from event data."""
        timeline_events = []
        for event in events:
            timeline_events.append(TimelineEvent(
                timestamp=datetime.datetime.fromisoformat(event['timestamp']),
                event_type=event['type'],
                description=event['description'],
                evidence_source=event['evidence'],
                significance=event['significance']
            ))
        
        return build_victim_timeline(timeline_events)
    
    def calculate_restitution(self, losses: Dict[str, float]) -> Dict[str, Any]:
        """Calculate restitution amount from losses."""
        return calculate_restitution_amount(losses)
    
    def run(self, capability: str, **kwargs) -> Any:
        """Dispatch to appropriate capability method."""
        capabilities = {
            'victim_impact_statement': self.generate_victim_impact_statement,
            'vawa_compliance_check': self.check_vawa_compliance,
            'trafficking_resource_lookup': self.get_trafficking_resources,
            'crime_victim_compensation_calculation': self.calculate_compensation,
            'protective_order_assistance': self.analyze_protective_order,
            'victim_timeline_reconstruction': self.reconstruct_timeline,
            'restitution_calculation': self.calculate_restitution
        }
        
        if capability not in capabilities:
            raise ValueError(f"Unknown capability: {capability}")
        
        return capabilities[capability](**kwargs)

class TestVictimAdvocacy(unittest.TestCase):
    """Test cases for victim advocacy skill."""
    
    def test_metadata_validation(self):
        """Test skill metadata structure."""
        self.assertEqual(SKILL_METADATA['name'], 'Victim Advocacy')
        self.assertEqual(SKILL_METADATA['id'], 'victim_advocacy')
        self.assertIn('victim_impact_statement_generation', SKILL_METADATA['capabilities'])
    
    def test_validate_victim_id(self):
        """Test victim ID validation."""
        self.assertTrue(validate_victim_id('CA2024-01-1234'))
        self.assertFalse(validate_victim_id('invalid-id'))
        self.assertFalse(validate_victim_id(''))
    
    def test_parse_financial_losses(self):
        """Test financial loss parsing."""
        losses = "Medical: $5,000, Lost Wages: $2,500.50"
        parsed = parse_financial_losses(losses)
        self.assertEqual(parsed['medical'], 5000.0)
        self.assertEqual(parsed['lost_wages'], 2500.50)
    
    def test_calculate_compensation_eligibility(self):
        """Test compensation eligibility calculation."""
        result = calculate_compensation_eligibility('CA', datetime.date(2024, 1, 1), 30, True, False)
        self.assertTrue(result['eligible'])
        self.assertEqual(result['max_benefits'], 70000)
        
        result = calculate_compensation_eligibility('CA', datetime.date(2024, 1, 1), 400, True, False)
        self.assertFalse(result['eligible'])
    
    def test_generate_victim_impact_statement(self):
        """Test impact statement generation."""
        data = VictimImpactData(
            victim_name='Jane Doe',
            crime_type='Assault',
            incident_date='2024-01-15',
            physical_injuries='Broken arm, concussion',
            emotional_impact='PTSD, anxiety',
            financial_losses='Medical bills $5000',
            ongoing_effects='Cannot work for 3 months',
            restitution_amount=7500.00,
            safety_concerns='Fear of retaliation',
            jurisdiction='California'
        )
        statement = generate_victim_impact_statement(data)
        self.assertIn('Jane Doe', statement)
        self.assertIn('$7,500.00', statement)
    
    def test_build_victim_timeline(self):
        """Test timeline reconstruction."""
        events = [
            TimelineEvent(
                timestamp=datetime.datetime(2024, 1, 1, 10, 0),
                event_type='incident',
                description='Assault occurred',
                evidence_source='Police report #12345',
                significance='Primary incident'
            ),
            TimelineEvent(
                timestamp=datetime.datetime(2024, 1, 2, 9, 0),
                event_type='medical',
                description='Hospital treatment',
                evidence_source='Medical records',
                significance='Injury documentation'
            )
        ]
        timeline = build_victim_timeline(events)
        self.assertEqual(len(timeline), 2)
        self.assertEqual(timeline[0]['type'], 'incident')
    
    def test_calculate_restitution_amount(self):
        """Test restitution calculation."""
        losses = {'medical': 5000.0, 'lost_wages': 3000.0, 'property': 1500.0}
        result = calculate_restitution_amount(losses)
        self.assertEqual(result['total_restitution'], 9500.0)
        self.assertEqual(len(result['itemized_losses']), 3)
    
    def test_validate_protective_order_requirements(self):
        """Test protective order validation."""
        result = validate_protective_order_requirements(
            'spouse',
            ['physical abuse', 'threats'],
            ['continued harassment'],
            'California'
        )
        self.assertTrue(result['eligible'])
        self.assertEqual(result['order_type'], 'Domestic Violence Protective Order')
    
    def test_generate_vawa_compliance_checklist(self):
        """Test VAWA compliance checklist generation."""
        checklist = generate_vawa_compliance_checklist('law_enforcement')
        self.assertEqual(len(checklist), 8)
        self.assertTrue(any(item['item'] == 'Mandatory arrest policies reviewed' for item in checklist))
    
    def test_skill_engine_initialization(self):
        """Test skill engine initialization."""
        engine = SkillEngine({'test': 'config'})
        self.assertIsNotNone(engine)
    
    def test_skill_engine_victim_impact_statement(self):
        """Test skill engine impact statement generation."""
        engine = SkillEngine({})
        data = {
            'victim_name': 'John Smith',
            'crime_type': 'Robbery',
            'incident_date': '2024-02-01',
            'physical_injuries': 'Minor injuries',
            'emotional_impact': 'Anxiety',
            'financial_losses': '$1000 cash stolen',
            'ongoing_effects': 'None',
            'restitution_amount': 1000.00,
            'safety_concerns': 'None',
            'jurisdiction': 'Texas'
        }
        result = engine.run('victim_impact_statement', **data)
        self.assertIn('John Smith', result)
    
    def test_skill_engine_timeline_reconstruction(self):
        """Test skill engine timeline reconstruction."""
        engine = SkillEngine({})
        events = [{
            'timestamp': '2024-01-01T10:00:00',
            'type': 'incident',
            'description': 'Test incident',
            'evidence': 'Test evidence',
            'significance': 'Test significance'
        }]
        result = engine.run('victim_timeline_reconstruction', events=events)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'incident')

if __name__ == '__main__':
    unittest.main()