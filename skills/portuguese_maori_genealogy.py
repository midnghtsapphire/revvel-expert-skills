import re
import json
import os
import hashlib
import statistics
import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, namedtuple
import unittest
import requests
from urllib.parse import urlencode

SKILL_METADATA = {
    "name": "Portuguese & Maori/New Zealand Genealogy Expert",
    "id": "portuguese_maori_genealogy",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Expert system for Portuguese and Maori/New Zealand genealogical research, covering civil records, whakapapa traditions, DNA markers, and migration patterns",
    "capabilities": [
        "parse_portuguese_civil_records",
        "analyze_maori_whakapapa",
        "trace_portuguese_emigration",
        "validate_maori_land_court_records",
        "generate_dna_haplogroup_report",
        "build_family_tree",
        "search_historical_archives",
        "validate_genealogical_data",
        "generate_research_report",
        "cross_reference_migration_records"
    ],
    "domain": "genealogy"
}

EXPERT_PROMPTS = {
    "portuguese_civil_record_analysis": """
Analyze the following Portuguese civil registration record:
{record_text}

Extract and structure the following information:
- Event type (birth/marriage/death)
- Full names of principal individuals
- Dates and locations
- Parents' names and origins
- Witnesses/godparents
- Any marginal notes or annotations

Return as JSON with keys: event_type, primary_person, date, location, parents, witnesses, notes
""",
    
    "maori_whakapapa_reconstruction": """
Given the following Maori genealogical information:
{whakapapa_data}

Reconstruct the whakapapa following traditional formats:
- Identify iwi, hapū, and whānau connections
- Map generational relationships
- Note any significant ancestors (tīpuna)
- Include tribal affiliations and locations
- Mark any gaps or disputed connections

Format as hierarchical JSON with keys: iwi, hapu, whanau, generations, significant_ancestors, locations, notes
""",
    
    "portuguese_emigration_trace": """
Trace Portuguese emigration for:
{individual_name}
Born: {birth_date} in {birth_location}
Emigration period: {emigration_range}

Search for:
- Passport records from Torre do Tombo
- Ship passenger lists (especially to Hawaii/California)
- Azorean whaling records
- Naturalization documents
- Census records in destination country

Return timeline of migration events with sources
""",
    
    "dna_haplogroup_analysis": """
Analyze the following DNA test results:
{dna_data}

Determine:
- Y-DNA haplogroup (Portuguese/Maori markers)
- mtDNA haplogroup
- Autosomal DNA matches
- Migration patterns based on genetic markers
- Percentage breakdown by region
- Notable genetic matches in genealogical databases

Format as detailed genetic ancestry report
""",
    
    "maori_land_court_search": """
Search Maori Land Court records for:
{block_name} or {owner_name}

Retrieve:
- Minute book references
- Ownership succession
- Block histories
- Any whakapapa recorded
- Treaty claims associated
- Current status

Return structured data with citations
""",
    
    "sephardic_lineage_validation": """
Investigate potential Sephardic Jewish ancestry for:
{family_name} from {location}

Research:
- Surname origins and variants
- Crypto-Jewish practices in family
- Inquisition records
- Jewish community archives
- DNA matches with known Sephardic families
- Migration patterns consistent with Jewish diaspora

Provide evidence assessment and confidence level
""",
    
    "cross_polynesian_connections": """
Establish connections between Maori whakapapa and other Polynesian genealogies:
{maori_lineage}

Compare with:
- Hawaiian moʻokūʻauhau
- Tahitian genealogies
- Samoan faʻalupega
- Tongan langi

Identify:
- Common ancestors
- Migration timing
- Cultural parallels
- DNA evidence supporting connections
""",
    
    "research_report_generation": """
Generate comprehensive genealogical research report for:
{subject_name}

Include:
- Executive summary
- Documented lineage
- Source citations
- DNA evidence
- Migration timeline
- Cultural context
- Recommendations for further research
- Confidence levels for each claim

Format as professional report with sections and subsections
"""
}

INTEGRATION_POINTS = {
    "torre_do_tombo_api": {
        "type": "api",
        "endpoint": "https://digitarq.arquivos.pt",
        "description": "Portuguese National Archives digital repository",
        "auth_method": "api_key",
        "documentation_url": "https://digitarq.arquivos.pt/docs"
    },
    "bdm_nz_api": {
        "type": "api",
        "endpoint": "https://www.bdmhistoricalrecords.dia.govt.nz",
        "description": "New Zealand Births, Deaths and Marriages historical records",
        "auth_method": "oauth2",
        "documentation_url": "https://www.bdmhistoricalrecords.dia.govt.nz/api/docs"
    },
    "archives_nz_api": {
        "type": "api",
        "endpoint": "https://collections.archives.govt.nz",
        "description": "Archives New Zealand collections search",
        "auth_method": "api_key",
        "documentation_url": "https://archives.govt.nz/api"
    },
    "maori_land_court_db": {
        "type": "database",
        "endpoint": "maori_land_court.research.govt.nz:5432/mlc_records",
        "description": "Maori Land Court minute books and records",
        "auth_method": "certificate",
        "documentation_url": "https://maorilandcourt.govt.nz/research"
    },
    "familysearch_api": {
        "type": "api",
        "endpoint": "https://api.familysearch.org",
        "description": "FamilySearch genealogical records",
        "auth_method": "oauth2",
        "documentation_url": "https://www.familysearch.org/developers"
    },
    "azorean_emigration_db": {
        "type": "database",
        "endpoint": "emigration.azores.gov.pt:3306/passenger_records",
        "description": "Azorean emigration and passenger records",
        "auth_method": "basic_auth",
        "documentation_url": "https://emigration.azores.gov.pt/api"
    }
}

# Utility functions
def parse_portuguese_date(date_str: str) -> Optional[datetime]:
    """Parse Portuguese date formats including variations like '15 de Março de 1875'."""
    months = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6,
        'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
    }
    
    date_str = date_str.lower().strip()
    pattern = r'(\d{1,2})\s+de\s+([a-zç]+)\s+de\s+(\d{4})'
    match = re.search(pattern, date_str)
    
    if match:
        day = int(match.group(1))
        month = months.get(match.group(2), 1)
        year = int(match.group(3))
        return datetime(year, month, day)
    
    return None

def validate_maori_name(name: str) -> bool:
    """Validate Maori names according to traditional naming conventions."""
    if not name or len(name) < 2:
        return False
    
    # Check for macrons and valid Maori characters
    maori_pattern = r'^[A-Za-zĀāĒēĪīŌōŪū]+$'
    if not re.match(maori_pattern, name):
        return False
    
    # Check for common Maori name patterns
    valid_prefixes = ['Te', 'Ngā', 'Ngāi', 'Ngāti', 'Tū', 'Whā', 'Rā']
    name_parts = name.split()
    
    if len(name_parts) > 1 and name_parts[0] in valid_prefixes:
        return True
    
    # Single names should be at least 3 characters
    return len(name) >= 3

def extract_portuguese_names(full_name: str) -> Dict[str, str]:
    """Parse Portuguese full names into components."""
    parts = full_name.strip().split()
    
    # Handle common Portuguese name patterns
    given_names = []
    surnames = []
    
    # Find surname indicators
    surname_indicators = ['de', 'da', 'dos', 'das', 'do', 'e']
    
    surname_start = len(parts)
    for i, part in enumerate(parts):
        if part.lower() in surname_indicators and i > 0:
            surname_start = i
            break
    
    given_names = parts[:surname_start]
    surnames = parts[surname_start:]
    
    return {
        'first_name': ' '.join(given_names),
        'surname': ' '.join(surnames),
        'full_name': full_name
    }

def calculate_genetic_distance(dna1: Dict[str, float], dna2: Dict[str, float]) -> float:
    """Calculate genetic distance between two DNA profiles."""
    if not dna1 or not dna2:
        return float('inf')
    
    common_markers = set(dna1.keys()) & set(dna2.keys())
    if not common_markers:
        return float('inf')
    
    distances = []
    for marker in common_markers:
        dist = abs(dna1[marker] - dna2[marker])
        distances.append(dist)
    
    return statistics.mean(distances) if distances else float('inf')

def build_gedcom_lineage(individuals: List[Dict]) -> str:
    """Generate GEDCOM format lineage from individual records."""
    gedcom = []
    gedcom.append("0 HEAD")
    gedcom.append("1 SOUR Revvel Genealogy Expert")
    gedcom.append("1 DATE {}".format(datetime.now().strftime("%d %b %Y")))
    
    for idx, person in enumerate(individuals):
        person_id = f"@{person.get('id', f'I{idx+1}')}@"
        gedcom.append(f"0 {person_id} INDI")
        gedcom.append(f"1 NAME {person.get('name', 'Unknown')}")
        
        if person.get('birth'):
            gedcom.append(f"1 BIRT")
            gedcom.append(f"2 DATE {person['birth'].get('date', '')}")
            gedcom.append(f"2 PLAC {person['birth'].get('place', '')}")
        
        if person.get('parents'):
            if person['parents'].get('father'):
                gedcom.append(f"1 FAMC @F{person['parents']['father']['id']}@")
    
    gedcom.append("0 TRLR")
    return '\n'.join(gedcom)

def search_maori_land_blocks(query: str) -> List[Dict]:
    """Search Maori Land Court records for land blocks."""
    # Mock implementation - in production would query actual database
    blocks = [
        {
            "block_name": "Te Whaiti-nui-a-Toi",
            "area": 5000,
            "owners": ["Ngāti Whare", "Ngāti Manawa"],
            "court_reference": "MLC 1915/123",
            "location": "Bay of Plenty"
        },
        {
            "block_name": "Rangitaiki",
            "area": 12000,
            "owners": ["Ngāti Awa", "Ngāti Tuwharetoa"],
            "court_reference": "MLC 1920/45",
            "location": "Bay of Plenty"
        }
    ]
    
    return [b for b in blocks if query.lower() in b['block_name'].lower()]

def validate_portuguese_civil_record(record: Dict) -> Dict[str, Any]:
    """Validate Portuguese civil registration record structure."""
    required_fields = ['event_type', 'date', 'location', 'person_name']
    validation = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    for field in required_fields:
        if field not in record or not record[field]:
            validation['valid'] = False
            validation['errors'].append(f"Missing required field: {field}")
    
    if record.get('event_type') not in ['birth', 'marriage', 'death']:
        validation['valid'] = False
        validation['errors'].append("Invalid event type")
    
    if record.get('date'):
        parsed_date = parse_portuguese_date(record['date'])
        if not parsed_date:
            validation['warnings'].append("Could not parse date format")
    
    return validation

def generate_migration_timeline(events: List[Dict]) -> List[Dict]:
    """Generate chronological migration timeline from events."""
    timeline = []
    
    for event in events:
        timeline.append({
            'date': event.get('date'),
            'event': event.get('type'),
            'location': event.get('location'),
            'source': event.get('source'),
            'notes': event.get('notes', '')
        })
    
    return sorted(timeline, key=lambda x: x['date'] or '')

def analyze_naming_patterns(names: List[str]) -> Dict[str, Any]:
    """Analyze naming patterns in a family lineage."""
    patterns = {
        'patronymic_frequency': 0,
        'matronymic_frequency': 0,
        'surname_variants': defaultdict(int),
        'given_name_repeats': defaultdict(int),
        'generational_patterns': []
    }
    
    for name in names:
        name_parts = extract_portuguese_names(name)
        surname = name_parts['surname']
        patterns['surname_variants'][surname] += 1
        
        first_name = name_parts['first_name'].split()[0]
        patterns['given_name_repeats'][first_name] += 1
    
    # Calculate frequencies
    total_names = len(names)
    if total_names > 0:
        patterns['patronymic_frequency'] = sum(1 for n in names if 'son' in n.lower()) / total_names
        patterns['matronymic_frequency'] = sum(1 for n in names if 'daughter' in n.lower()) / total_names
    
    return dict(patterns)

class SkillEngine:
    """Main skill engine for Portuguese & Maori genealogy research."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        """Setup basic logging for the skill."""
        import logging
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
    
    def parse_portuguese_civil_records(self, record_text: str) -> Dict[str, Any]:
        """Parse Portuguese civil registration records."""
        self.logger.info("Parsing Portuguese civil record")
        
        # Extract basic information using regex patterns
        event_type = None
        if 'nascimento' in record_text.lower():
            event_type = 'birth'
        elif 'casamento' in record_text.lower():
            event_type = 'marriage'
        elif 'óbito' in record_text.lower():
            event_type = 'death'
        
        # Extract names
        name_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+de\s+[A-Z][a-z]+)*)'
        names = re.findall(name_pattern, record_text)
        
        # Extract dates
        date_pattern = r'(\d{1,2}\s+de\s+[a-zç]+\s+de\s+\d{4})'
        dates = re.findall(date_pattern, record_text.lower())
        
        # Extract locations
        location_pattern = r'(?:em|na|no)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        locations = re.findall(location_pattern, record_text)
        
        return {
            'event_type': event_type,
            'person_name': names[0] if names else None,
            'date': parse_portuguese_date(dates[0]) if dates else None,
            'location': locations[0] if locations else None,
            'raw_text': record_text
        }
    
    def analyze_maori_whakapapa(self, whakapapa_data: Dict) -> Dict[str, Any]:
        """Analyze Maori whakapapa structure."""
        self.logger.info("Analyzing Maori whakapapa")
        
        analysis = {
            'iwi': whakapapa_data.get('iwi', []),
            'hapu': whakapapa_data.get('hapu', []),
            'whanau': whakapapa_data.get('whanau', []),
            'generations': [],
            'significant_ancestors': [],
            'locations': [],
            'confidence': 0.0
        }
        
        # Validate names
        for name in whakapapa_data.get('names', []):
            if validate_maori_name(name):
                analysis['significant_ancestors'].append(name)
        
        # Calculate confidence based on data completeness
        total_fields = len([v for v in whakapapa_data.values() if v])
        max_fields = len(whakapapa_data)
        analysis['confidence'] = total_fields / max_fields if max_fields > 0 else 0
        
        return analysis
    
    def trace_portuguese_emigration(self, params: Dict[str, str]) -> List[Dict]:
        """Trace Portuguese emigration patterns."""
        self.logger.info("Tracing Portuguese emigration")
        
        # Mock implementation - would query actual databases
        individual_name = params.get('individual_name', '')
        birth_location = params.get('birth_location', '')
        
        timeline = []
        
        # Azores to Hawaii route
        if 'azores' in birth_location.lower():
            timeline.append({
                'date': '1882-03-15',
                'event': 'departure',
                'location': 'Horta, Azores',
                'ship': 'SS Hansa',
                'destination': 'Honolulu, Hawaii'
            })
            timeline.append({
                'date': '1882-05-20',
                'event': 'arrival',
                'location': 'Honolulu, Hawaii',
                'ship': 'SS Hansa',
                'source': 'Hawaii State Archives passenger lists'
            })
        
        return timeline
    
    def validate_maori_land_court_records(self, block_name: str) -> Dict[str, Any]:
        """Validate Maori Land Court records."""
        self.logger.info("Validating Maori Land Court records")
        
        blocks = search_maori_land_blocks(block_name)
        
        if not blocks:
            return {'valid': False, 'error': 'No matching land blocks found'}
        
        return {
            'valid': True,
            'blocks': blocks,
            'total_blocks': len(blocks),
            'court_references': [b['court_reference'] for b in blocks]
        }
    
    def generate_dna_haplogroup_report(self, dna_data: Dict) -> Dict[str, Any]:
        """Generate DNA haplogroup analysis report."""
        self.logger.info("Generating DNA haplogroup report")
        
        report = {
            'y_dna_haplogroup': dna_data.get('y_dna', 'Unknown'),
            'mt_dna_haplogroup': dna_data.get('mt_dna', 'Unknown'),
            'autosomal_breakdown': {},
            'migration_patterns': [],
            'confidence': 0.0
        }
        
        # Portuguese markers
        if dna_data.get('y_dna', '').startswith('R1b'):
            report['migration_patterns'].append({
                'route': 'Iberian Peninsula',
                'timeframe': '4000-2000 BCE',
                'confidence': 'high'
            })
        
        # Maori/Polynesian markers
        if dna_data.get('mt_dna', '').startswith('B4'):
            report['migration_patterns'].append({
                'route': 'Polynesian Triangle',
                'timeframe': '800-1200 CE',
                'confidence': 'high'
            })
        
        return report
    
    def build_family_tree(self, individuals: List[Dict]) -> Dict[str, Any]:
        """Build comprehensive family tree."""
        self.logger.info("Building family tree")
        
        tree = {
            'individuals': individuals,
            'relationships': [],
            'generations': defaultdict(list),
            'gedcom': build_gedcom_lineage(individuals)
        }
        
        # Organize by generation
        for person in individuals:
            generation = person.get('generation', 0)
            tree['generations'][generation].append(person)
        
        return tree
    
    def search_historical_archives(self, query: Dict[str, str]) -> List[Dict]:
        """Search historical archives."""
        self.logger.info("Searching historical archives")
        
        # Mock search results
        results = []
        
        if query.get('type') == 'birth' and 'portugal' in query.get('location', '').lower():
            results.append({
                'record_type': 'birth',
                'name': query.get('name'),
                'date': '1875-03-15',
                'location': 'Lisbon, Portugal',
                'archive': 'Torre do Tombo',
                'reference': 'Registo Civil 1875/12345'
            })
        
        return results
    
    def validate_genealogical_data(self, data: Dict) -> Dict[str, Any]:
        """Validate genealogical data integrity."""
        self.logger.info("Validating genealogical data")
        
        validation = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'confidence': 0.0
        }
        
        # Check for circular references
        individuals = data.get('individuals', [])
        ids = [i.get('id') for i in individuals if i.get('id')]
        
        if len(set(ids)) != len(ids):
            validation['errors'].append("Duplicate individual IDs found")
            validation['valid'] = False
        
        # Validate dates
        for person in individuals:
            if person.get('birth', {}).get('date'):
                try:
                    datetime.strptime(person['birth']['date'], '%Y-%m-%d')
                except ValueError:
                    validation['warnings'].append(f"Invalid birth date format for {person.get('name')}")
        
        # Calculate confidence
        total_checks = 3
        passed_checks = total_checks - len(validation['errors'])
        validation['confidence'] = passed_checks / total_checks
        
        return validation
    
    def generate_research_report(self, data: Dict) -> str:
        """Generate comprehensive research report."""
        self.logger.info("Generating research report")
        
        report = []
        report.append("GENEALOGICAL RESEARCH REPORT")
        report.append("=" * 40)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Executive summary
        report.append("EXECUTIVE SUMMARY")
        report.append("-" * 20)
        report.append(f"Subject: {data.get('subject_name', 'Unknown')}")
        report.append(f"Research Period: {data.get('period', 'Not specified')}")
        report.append("")
        
        # Documented lineage
        if data.get('lineage'):
            report.append("DOCUMENTED LINEAGE")
            report.append("-" * 20)
            for gen, people in data['lineage'].items():
                report.append(f"Generation {gen}:")
                for person in people:
                    report.append(f"  - {person.get('name', 'Unknown')} ({person.get('birth', '')})")
        
        return '\n'.join(report)
    
    def cross_reference_migration_records(self, params: Dict) -> List[Dict]:
        """Cross-reference migration records across sources."""
        self.logger.info("Cross-referencing migration records")
        
        references = []
        
        # Portuguese emigration
        portuguese_timeline = self.trace_portuguese_emigration(params)
        references.extend(portuguese_timeline)
        
        # NZ immigration
        nz_records = self.search_historical_archives({
            'type': 'immigration',
            'name': params.get('individual_name'),
            'location': 'new zealand'
        })
        references.extend(nz_records)
        
        return references
    
    def run(self, capability: str, params: Dict[str, Any]) -> Any:
        """Main entry point for skill execution."""
        self.logger.info(f"Running capability: {capability}")
        
        capability_map = {
            'parse_portuguese_civil_records': self.parse_portuguese_civil_records,
            'analyze_maori_whakapapa': self.analyze_maori_whakapapa,
            'trace_portuguese_emigration': self.trace_portuguese_emigration,
            'validate_maori_land_court_records': self.validate_maori_land_court_records,
            'generate_dna_haplogroup_report': self.generate_dna_haplogroup_report,
            'build_family_tree': self.build_family_tree,
            'search_historical_archives': self.search_historical_archives,
            'validate_genealogical_data': self.validate_genealogical_data,
            'generate_research_report': self.generate_research_report,
            'cross_reference_migration_records': self.cross_reference_migration_records
        }
        
        if capability not in capability_map:
            raise ValueError(f"Unknown capability: {capability}")
        
        try:
            return capability_map[capability](params)
        except Exception as e:
            self.logger.error(f"Error in capability {capability}: {str(e)}")
            raise

class TestPortugueseMaoriGenealogy(unittest.TestCase):
    """Comprehensive test suite for the genealogy skill."""
    
    def setUp(self):
        self.engine = SkillEngine()
    
    def test_skill_metadata(self):
        """Test skill metadata structure."""
        self.assertEqual(SKILL_METADATA['name'], "Portuguese & Maori/New Zealand Genealogy Expert")
        self.assertIn('parse_portuguese_civil_records', SKILL_METADATA['capabilities'])
        self.assertEqual(SKILL_METADATA['domain'], 'genealogy')
    
    def test_parse_portuguese_date(self):
        """Test Portuguese date parsing."""
        date = parse_portuguese_date("15 de Março de 1875")
        self.assertEqual(date.year, 1875)
        self.assertEqual(date.month, 3)
        self.assertEqual(date.day, 15)
        
        invalid = parse_portuguese_date("invalid date")
        self.assertIsNone(invalid)
    
    def test_validate_maori_name(self):
        """Test Maori name validation."""
        self.assertTrue(validate_maori_name("Te Rangitāwhia"))
        self.assertTrue(validate_maori_name("Ngāti Porou"))
        self.assertFalse(validate_maori_name("A"))
        self.assertFalse(validate_maori_name("123"))
    
    def test_extract_portuguese_names(self):
        """Test Portuguese name extraction."""
        result = extract_portuguese_names("João Silva de Oliveira")
        self.assertEqual(result['first_name'], "João Silva")
        self.assertEqual(result['surname'], "de Oliveira")
    
    def test_calculate_genetic_distance(self):
        """Test genetic distance calculation."""
        dna1 = {'marker1': 0.5, 'marker2': 0.3}
        dna2 = {'marker1': 0.6, 'marker2': 0.2}
        distance = calculate_genetic_distance(dna1, dna2)
        self.assertAlmostEqual(distance, 0.1, places=2)
    
    def test_build_gedcom_lineage(self):
        """Test GEDCOM generation."""
        individuals = [
            {'id': 'I1', 'name': 'John Doe', 'birth': {'date': '1900-01-01', 'place': 'Lisbon'}}
        ]
        gedcom = build_gedcom_lineage(individuals)
        self.assertIn("0 @I1@ INDI", gedcom)
        self.assertIn("1 NAME John Doe", gedcom)
    
    def test_search_maori_land_blocks(self):
        """Test Maori land block search."""
        results = search_maori_land_blocks("Te Whaiti")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['block_name'], "Te Whaiti-nui-a-Toi")
    
    def test_validate_portuguese_civil_record(self):
        """Test Portuguese civil record validation."""
        record = {
            'event_type': 'birth',
            'date': '15 de Março de 1875',
            'location': 'Lisbon',
            'person_name': 'Maria Silva'
        }
        validation = validate_portuguese_civil_record(record)
        self.assertTrue(validation['valid'])
    
    def test_skill_engine_capabilities(self):
        """Test skill engine main capabilities."""
        # Test parse_portuguese_civil_records
        result = self.engine.run('parse_portuguese_civil_records', {
            'record_text': 'Registo de nascimento de João Silva, 15 de Março de 1875, Lisboa'
        })
        self.assertEqual(result['event_type'], 'birth')
        
        # Test analyze_maori_whakapapa
        whakapapa = {
            'iwi': ['Ngāti Porou'],
            'hapu': ['Te Whānau-ā-Apanui'],
            'names': ['Te Rangitāwhia']
        }
        analysis = self.engine.run('analyze_maori_whakapapa', whakapapa)
        self.assertIn('Ngāti Porou', analysis['iwi'])
        
        # Test build_family_tree
        tree = self.engine.run('build_family_tree', {
            'individuals': [
                {'id': 'I1', 'name': 'John', 'generation': 1},
                {'id': 'I2', 'name': 'Mary', 'generation': 1}
            ]
        })
        self.assertEqual(len(tree['individuals']), 2)
    
    def test_error_handling(self):
        """Test error handling in skill engine."""
        with self.assertRaises(ValueError):
            self.engine.run('invalid_capability', {})
    
    def test_migration_timeline(self):
        """Test migration timeline generation."""
        events = [
            {'date': '1882-03-15', 'type': 'departure', 'location': 'Horta'},
            {'date': '1882-05-20', 'type': 'arrival', 'location': 'Honolulu'}
        ]
        timeline = generate_migration_timeline(events)
        self.assertEqual(len(timeline), 2)
        self.assertEqual(timeline[0]['date'], '1882-03-15')

if __name__ == '__main__':
    unittest.main()