import json
import re
import os
import hashlib
import statistics
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import unittest
import logging

SKILL_METADATA = {
    "name": "Cold Case Analysis",
    "id": "cold_case_analysis",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Advanced forensic analysis toolkit for cold case investigations, integrating evidence re-examination, witness re-interview strategies, DNA genealogy matching, digital forensics, timeline reconstruction, and cross-case pattern analysis",
    "capabilities": [
        "evidence_reexamination",
        "witness_reinterview_strategy",
        "dna_genealogy_matching",
        "digital_forensics_historical",
        "timeline_reconstruction",
        "cross_case_pattern_analysis",
        "case_priority_scoring",
        "lead_generation",
        "forensic_report_generation",
        "investigative_workflow_optimization"
    ],
    "domain": "forensic_investigation"
}

EXPERT_PROMPTS = {
    "evidence_reexamination": """You are a senior forensic analyst reviewing cold case evidence from {case_name}.
    
Key evidence items to re-examine:
- Physical evidence: {physical_evidence_list}
- Digital evidence: {digital_evidence_list}
- Forensic reports: {forensic_reports}
- Chain of custody gaps: {custody_gaps}

Apply modern forensic techniques to identify:
1. New testing opportunities (DNA, trace, chemical)
2. Previously overlooked evidence
3. Contamination or degradation issues
4. Advanced analysis possibilities (isotope, pollen, etc.)

Return a structured analysis with actionable recommendations.""",

    "witness_reinterview_strategy": """Design a re-interview strategy for witnesses in cold case {case_id}.
    
Witness details:
- Original statements: {original_statements}
- Time elapsed: {years_elapsed} years
- Memory factors: {memory_factors}
- Current contact status: {contact_status}

Develop:
1. Cognitive interview techniques appropriate for time elapsed
2. Memory refresh protocols
3. Trauma-informed approaches
4. Documentation strategies
5. Follow-up verification methods

Consider memory decay, suggestibility, and potential contamination.""",

    "dna_genealogy_matching": """Perform genealogical DNA analysis for cold case {case_name}.
    
DNA profile details:
- CODIS markers: {codis_markers}
- SNP data: {snp_data}
- Partial profiles: {partial_profiles}
- Degradation level: {degradation_level}

Genealogy database access:
- GEDmatch: {gedmatch_access}
- FamilyTreeDNA: {ftdna_access}
- Ancestry: {ancestry_access}

Generate:
1. Potential relative matches
2. Family tree reconstruction
3. Common ancestor identification
4. Investigative leads prioritization
5. Privacy and legal considerations""",

    "digital_forensics_historical": """Analyze historical digital evidence from {evidence_source}.
    
Evidence types:
- Hard drives: {drive_list}
- Mobile devices: {device_list}
- Cloud data: {cloud_sources}
- Internet activity: {internet_records}
- Metadata: {metadata_info}

Apply:
1. Data carving for deleted files
2. Timeline reconstruction from logs
3. Cross-reference with historical IP/domain data
4. Social media archive analysis
5. Email header analysis
6. Cryptocurrency transaction tracing

Account for technology changes and data format evolution.""",

    "timeline_reconstruction": """Reconstruct the complete timeline for cold case {case_id}.
    
Available data:
- Incident date: {incident_date}
- Witness statements: {statements}
- Phone records: {phone_records}
- Financial transactions: {financial_data}
- Travel records: {travel_logs}
- Digital timestamps: {digital_evidence}

Create:
1. Minute-by-minute timeline where possible
2. Gap identification
3. Alibi verification points
4. Opportunity windows
5. Contradiction highlights
6. Visual timeline representation""",

    "cross_case_pattern_analysis": """Analyze patterns across {case_count} cold cases in {jurisdiction}.
    
Case characteristics:
- Victim demographics: {victim_data}
- Crime scene similarities: {scene_patterns}
- M.O. elements: {modus_operandi}
- Geographic clusters: {locations}
- Time patterns: {temporal_patterns}
- Evidence types: {evidence_types}

Identify:
1. Potential serial connections
2. Geographic profiling opportunities
3. Victimology patterns
4. Signature behaviors
5. Linkage analysis
6. Task force recommendations""",

    "case_priority_scoring": """Calculate priority scores for cold case {case_id}.
    
Scoring factors:
- Solvability factors: {solvability_factors}
- Family advocacy: {family_pressure}
- Public interest: {media_attention}
- Resource requirements: {resource_estimate}
- DNA evidence potential: {dna_potential}
- Witness availability: {witness_status}

Weight and calculate:
1. Overall priority score (0-100)
2. Resource allocation recommendation
3. Timeline for next review
4. Success probability estimate""",

    "lead_generation": """Generate investigative leads for cold case {case_name}.
    
Current status:
- Active leads: {current_leads}
- Dead ends: {investigated_leads}
- New evidence: {recent_discoveries}
- Technology advances: {new_techniques}

Create:
1. Fresh lead list with priority ranking
2. Investigative steps for each lead
3. Resource requirements
4. Timeline estimates
5. Success metrics
6. Contingency plans"""
}

INTEGRATION_POINTS = {
    "ncic_database": {
        "type": "database",
        "endpoint": "https://api.ncic.gov/v2/query",
        "description": "National Crime Information Center database access for criminal history and missing persons",
        "auth_method": "certificate",
        "documentation_url": "https://ncic.gov/api-docs"
    },
    "codis_api": {
        "type": "api",
        "endpoint": "https://codis.fbi.gov/api/v1/profiles",
        "description": "Combined DNA Index System for DNA profile matching",
        "auth_method": "oauth2",
        "documentation_url": "https://fbi.gov/codis-api"
    },
    "gedmatch_pro": {
        "type": "api",
        "endpoint": "https://api.gedmatch.com/v1",
        "description": "GEDmatch Pro API for genealogical DNA matching",
        "auth_method": "api_key",
        "documentation_url": "https://gedmatch.com/api-docs"
    },
    "wayback_machine": {
        "type": "api",
        "endpoint": "https://archive.org/wayback/available",
        "description": "Internet Archive Wayback Machine for historical web data",
        "auth_method": "none",
        "documentation_url": "https://archive.org/help/wayback_api.php"
    },
    "revvel_evidence_db": {
        "type": "database",
        "endpoint": "postgresql://revvel-db:5432/evidence",
        "description": "Internal evidence management database",
        "auth_method": "service_account",
        "documentation_url": "internal://docs.evidence-db"
    },
    "forensic_lab_api": {
        "type": "api",
        "endpoint": "https://lab-api.forensics.gov/v2",
        "description": "National forensic laboratory services API",
        "auth_method": "jwt",
        "documentation_url": "https://forensics.gov/api"
    }
}

def validate_case_id(case_id: str) -> bool:
    """Validate cold case ID format."""
    pattern = r'^CC-\d{4}-\d{6}$'
    return bool(re.match(pattern, case_id))

def parse_date_flexible(date_str: str) -> Optional[datetime]:
    """Parse various date formats commonly found in case files."""
    formats = [
        '%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y%m%d',
        '%B %d, %Y', '%d %B %Y', '%Y-%m-%d %H:%M:%S'
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None

def calculate_evidence_degradation_score(evidence_date: datetime, evidence_type: str) -> float:
    """Calculate degradation score (0-1) for evidence based on type and age."""
    age_days = (datetime.now() - evidence_date).days
    
    degradation_rates = {
        'dna_blood': 0.0001,
        'dna_other': 0.0002,
        'fingerprints': 0.00005,
        'fibers': 0.0003,
        'bullets': 0.00001,
        'digital': 0.000001,
        'documents': 0.00002
    }
    
    rate = degradation_rates.get(evidence_type.lower(), 0.0001)
    degradation = 1 - (age_days * rate)
    return max(0, min(1, degradation))

def extract_phone_numbers(text: str) -> List[str]:
    """Extract phone numbers from text using multiple patterns."""
    patterns = [
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\d{3}-\d{3}-\d{4}',
        r'\(\d{3}\)\s?\d{3}-\d{4}',
        r'\d{10}'
    ]
    
    phones = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        phones.extend(matches)
    
    return list(set(phones))

def generate_timeline_from_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate chronological timeline from event data."""
    timeline = []
    
    for event in events:
        event_date = parse_date_flexible(event.get('date', ''))
        if event_date:
            timeline.append({
                'timestamp': event_date,
                'event_type': event.get('type', 'unknown'),
                'description': event.get('description', ''),
                'source': event.get('source', ''),
                'confidence': event.get('confidence', 1.0)
            })
    
    return sorted(timeline, key=lambda x: x['timestamp'])

def calculate_geographic_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two geographic coordinates in miles."""
    R = 3959  # Earth's radius in miles
    
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def analyze_victimology_patterns(victims: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze patterns in victim demographics and characteristics."""
    if not victims:
        return {}
    
    patterns = {
        'age_distribution': [],
        'gender_distribution': Counter(),
        'occupation_patterns': Counter(),
        'location_clusters': [],
        'time_patterns': Counter()
    }
    
    for victim in victims:
        patterns['age_distribution'].append(victim.get('age', 0))
        patterns['gender_distribution'][victim.get('gender', 'unknown')] += 1
        patterns['occupation_patterns'][victim.get('occupation', 'unknown')] += 1
        
        if 'location' in victim:
            patterns['location_clusters'].append(victim['location'])
        
        incident_date = parse_date_flexible(victim.get('incident_date', ''))
        if incident_date:
            patterns['time_patterns'][incident_date.strftime('%Y-%m')] += 1
    
    patterns['age_stats'] = {
        'mean': statistics.mean(patterns['age_distribution']) if patterns['age_distribution'] else 0,
        'median': statistics.median(patterns['age_distribution']) if patterns['age_distribution'] else 0,
        'std': statistics.stdev(patterns['age_distribution']) if len(patterns['age_distribution']) > 1 else 0
    }
    
    return patterns

def build_investigative_query(filters: Dict[str, Any]) -> str:
    """Build SQL query for cold case database search."""
    base_query = "SELECT * FROM cold_cases WHERE 1=1"
    params = []
    
    if filters.get('case_id'):
        base_query += " AND case_id = %s"
        params.append(filters['case_id'])
    
    if filters.get('date_from'):
        base_query += " AND incident_date >= %s"
        params.append(filters['date_from'])
    
    if filters.get('date_to'):
        base_query += " AND incident_date <= %s"
        params.append(filters['date_to'])
    
    if filters.get('location'):
        base_query += " AND location ILIKE %s"
        params.append(f"%{filters['location']}%")
    
    if filters.get('evidence_type'):
        base_query += " AND evidence_types @> ARRAY[%s]"
        params.append(filters['evidence_type'])
    
    if filters.get('unsolved_only', True):
        base_query += " AND status = 'unsolved'"
    
    return base_query, params

def generate_forensic_report(case_data: Dict[str, Any]) -> str:
    """Generate comprehensive forensic analysis report."""
    report = []
    report.append("=" * 60)
    report.append(f"COLD CASE FORENSIC ANALYSIS REPORT")
    report.append(f"Case ID: {case_data.get('case_id', 'UNKNOWN')}")
    report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 60)
    
    if 'evidence_summary' in case_data:
        report.append("\nEVIDENCE SUMMARY:")
        for evidence in case_data['evidence_summary']:
            report.append(f"- {evidence['type']}: {evidence['status']}")
    
    if 'dna_analysis' in case_data:
        report.append("\nDNA ANALYSIS:")
        report.append(f"- Profile completeness: {case_data['dna_analysis'].get('completeness', 'N/A')}")
        report.append(f"- Degradation score: {case_data['dna_analysis'].get('degradation', 'N/A')}")
    
    if 'timeline' in case_data:
        report.append("\nTIMELINE RECONSTRUCTION:")
        for event in case_data['timeline'][:5]:  # Top 5 events
            report.append(f"- {event['timestamp']}: {event['description']}")
    
    if 'leads' in case_data:
        report.append("\nINVESTIGATIVE LEADS:")
        for lead in case_data['leads']:
            report.append(f"- Priority {lead.get('priority', 'N/A')}: {lead.get('description', '')}")
    
    return "\n".join(report)

def hash_evidence_file(file_path: str) -> str:
    """Generate SHA-256 hash for evidence file integrity."""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

class SkillEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(config.get('log_level', 'INFO'))
        
    def evidence_reexamination(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Re-examine evidence with modern techniques."""
        results = {
            'case_id': case_data.get('case_id'),
            'evidence_items': [],
            'new_techniques': [],
            'recommendations': []
        }
        
        for evidence in case_data.get('evidence', []):
            degradation_score = calculate_evidence_degradation_score(
                parse_date_flexible(evidence.get('date_collected', '')),
                evidence.get('type', 'unknown')
            )
            
            results['evidence_items'].append({
                'id': evidence.get('id'),
                'type': evidence.get('type'),
                'degradation_score': degradation_score,
                'testable': degradation_score > 0.3
            })
            
            if degradation_score > 0.7:
                results['new_techniques'].append({
                    'evidence_id': evidence.get('id'),
                    'techniques': ['touch_dna', 'mps_sequencing', 'isotope_analysis']
                })
        
        return results
    
    def witness_reinterview_strategy(self, witness_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate re-interview strategy for witnesses."""
        years_elapsed = (datetime.now() - parse_date_flexible(witness_data.get('original_date', ''))).days / 365.25
        
        strategy = {
            'witness_id': witness_data.get('witness_id'),
            'years_elapsed': round(years_elapsed, 1),
            'memory_risk_factors': [],
            'interview_techniques': [],
            'documentation_requirements': []
        }
        
        if years_elapsed > 10:
            strategy['memory_risk_factors'].extend(['high_decay', 'suggestibility', 'confabulation'])
            strategy['interview_techniques'].extend(['cognitive_interview', 'timeline_method', 'context_reinstatement'])
        
        if witness_data.get('trauma_indicated', False):
            strategy['interview_techniques'].append('trauma_informed_approach')
        
        strategy['documentation_requirements'] = [
            'video_recording',
            'transcription',
            'memory_confidence_ratings',
            'third_party_verification'
        ]
        
        return strategy
    
    def dna_genealogy_matching(self, dna_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform DNA genealogy analysis."""
        results = {
            'profile_id': dna_data.get('profile_id'),
            'matches': [],
            'confidence_scores': [],
            'investigative_leads': []
        }
        
        # Simulate genealogy matching
        if dna_data.get('snps_count', 0) > 100000:
            results['matches'] = [
                {'relative': '3rd_cousin', 'shared_cm': 87, 'confidence': 0.95},
                {'relative': '4th_cousin', 'shared_cm': 45, 'confidence': 0.78}
            ]
        
        for match in results['matches']:
            if match['confidence'] > 0.8:
                results['investigative_leads'].append({
                    'type': 'genealogy_match',
                    'priority': 'high',
                    'description': f"High-confidence {match['relative']} match"
                })
        
        return results
    
    def timeline_reconstruction(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Reconstruct detailed timeline from case data."""
        events = case_data.get('events', [])
        timeline = generate_timeline_from_events(events)
        
        gaps = []
        for i in range(1, len(timeline)):
            gap_hours = (timeline[i]['timestamp'] - timeline[i-1]['timestamp']).total_seconds() / 3600
            if gap_hours > 24:
                gaps.append({
                    'start': timeline[i-1]['timestamp'],
                    'end': timeline[i]['timestamp'],
                    'duration_hours': gap_hours
                })
        
        return {
            'timeline': timeline,
            'gaps': gaps,
            'confidence_score': statistics.mean([e['confidence'] for e in timeline]) if timeline else 0
        }
    
    def cross_case_pattern_analysis(self, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns across multiple cold cases."""
        patterns = {
            'geographic_clusters': [],
            'temporal_patterns': [],
            'victimology_patterns': analyze_victimology_patterns(
                [c.get('victim', {}) for c in cases]
            ),
            'potential_links': []
        }
        
        # Geographic clustering
        locations = [(c.get('lat'), c.get('lon')) for c in cases if c.get('lat') and c.get('lon')]
        for i, (lat1, lon1) in enumerate(locations):
            for j, (lat2, lon2) in enumerate(locations[i+1:], i+1):
                distance = calculate_geographic_distance(lat1, lon1, lat2, lon2)
                if distance < 5:  # 5 miles
                    patterns['geographic_clusters'].append({
                        'case1': cases[i]['case_id'],
                        'case2': cases[j]['case_id'],
                        'distance_miles': round(distance, 2)
                    })
        
        return patterns
    
    def case_priority_scoring(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate priority score for cold case."""
        score = 0
        
        # DNA evidence potential (0-30 points)
        dna_potential = case_data.get('dna_potential', 0)
        score += min(dna_potential * 30, 30)
        
        # Witness availability (0-25 points)
        witness_count = len(case_data.get('available_witnesses', []))
        score += min(witness_count * 5, 25)
        
        # Evidence quality (0-20 points)
        evidence_score = case_data.get('evidence_quality', 0)
        score += evidence_score * 20
        
        # Family advocacy (0-15 points)
        family_pressure = case_data.get('family_advocacy', 0)
        score += family_pressure * 15
        
        # Public interest (0-10 points)
        media_attention = case_data.get('media_attention', 0)
        score += media_attention * 10
        
        return {
            'case_id': case_data.get('case_id'),
            'priority_score': round(score, 1),
            'tier': 'high' if score > 75 else 'medium' if score > 50 else 'low',
            'next_review_days': max(30, int(365 - score * 3))
        }
    
    def run(self, capability: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch to appropriate capability handler."""
        handlers = {
            'evidence_reexamination': self.evidence_reexamination,
            'witness_reinterview_strategy': self.witness_reinterview_strategy,
            'dna_genealogy_matching': self.dna_genealogy_matching,
            'timeline_reconstruction': self.timeline_reconstruction,
            'cross_case_pattern_analysis': self.cross_case_pattern_analysis,
            'case_priority_scoring': self.case_priority_scoring
        }
        
        if capability not in handlers:
            raise ValueError(f"Unknown capability: {capability}")
        
        try:
            return handlers[capability](data)
        except Exception as e:
            self.logger.error(f"Error in {capability}: {str(e)}")
            raise

class TestColdCaseAnalysis(unittest.TestCase):
    def setUp(self):
        self.engine = SkillEngine({'log_level': 'DEBUG'})
    
    def test_skill_metadata(self):
        self.assertEqual(SKILL_METADATA['name'], 'Cold Case Analysis')
        self.assertIn('evidence_reexamination', SKILL_METADATA['capabilities'])
        self.assertEqual(SKILL_METADATA['version'], '1.0.0')
    
    def test_validate_case_id(self):
        self.assertTrue(validate_case_id('CC-2024-000001'))
        self.assertFalse(validate_case_id('INVALID-ID'))
        self.assertFalse(validate_case_id('CC-24-1'))
    
    def test_parse_date_flexible(self):
        self.assertEqual(parse_date_flexible('2024-01-15').year, 2024)
        self.assertEqual(parse_date_flexible('01/15/2024').month, 1)
        self.assertIsNone(parse_date_flexible('invalid-date'))
    
    def test_calculate_evidence_degradation_score(self):
        old_date = datetime.now() - timedelta(days=365*10)
        score = calculate_evidence_degradation_score(old_date, 'dna_blood')
        self.assertTrue(0 < score < 1)
        
        recent_date = datetime.now() - timedelta(days=30)
        score = calculate_evidence_degradation_score(recent_date, 'digital')
        self.assertAlmostEqual(score, 1.0, places=2)
    
    def test_extract_phone_numbers(self):
        text = "Call 555-123-4567 or (555) 987-6543"
        phones = extract_phone_numbers(text)
        self.assertEqual(len(phones), 2)
        self.assertIn('555-123-4567', phones)
    
    def test_geographic_distance(self):
        distance = calculate_geographic_distance(40.7128, -74.0060, 34.0522, -118.2437)
        self.assertAlmostEqual(distance, 2445, delta=50)
    
    def test_timeline_reconstruction(self):
        events = [
            {'date': '2024-01-01', 'type': 'incident', 'description': 'Crime occurred'},
            {'date': '2024-01-02', 'type': 'discovery', 'description': 'Body found'}
        ]
        timeline = generate_timeline_from_events(events)
        self.assertEqual(len(timeline), 2)
        self.assertEqual(timeline[0]['event_type'], 'incident')
    
    def test_evidence_reexamination(self):
        case_data = {
            'case_id': 'CC-2024-000001',
            'evidence': [
                {'id': 'E001', 'type': 'dna_blood', 'date_collected': '2014-01-01'},
                {'id': 'E002', 'type': 'digital', 'date_collected': '2024-01-01'}
            ]
        }
        result = self.engine.evidence_reexamination(case_data)
        self.assertEqual(len(result['evidence_items']), 2)
        self.assertTrue(result['evidence_items'][0]['degradation_score'] < result['evidence_items'][1]['degradation_score'])
    
    def test_case_priority_scoring(self):
        case_data = {
            'case_id': 'CC-2024-000001',
            'dna_potential': 0.8,
            'available_witnesses': ['W1', 'W2', 'W3'],
            'evidence_quality': 0.9,
            'family_advocacy': 1,
            'media_attention': 0.5
        }
        result = self.engine.case_priority_scoring(case_data)
        self.assertEqual(result['case_id'], 'CC-2024-000001')
        self.assertTrue(result['priority_score'] > 50)
        self.assertIn('tier', result)
    
    def test_cross_case_pattern_analysis(self):
        cases = [
            {'case_id': 'CC-001', 'victim': {'age': 25, 'gender': 'F'}, 'lat': 40.7, 'lon': -74.0},
            {'case_id': 'CC-002', 'victim': {'age': 30, 'gender': 'F'}, 'lat': 40.8, 'lon': -74.1}
        ]
        result = self.engine.cross_case_pattern_analysis(cases)
        self.assertIn('geographic_clusters', result)
        self.assertIn('victimology_patterns', result)
        self.assertEqual(len(result['geographic_clusters']), 1)

if __name__ == '__main__':
    unittest.main()