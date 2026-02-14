import json
import re
import os
import hashlib
import statistics
import math
import datetime
import unittest
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import requests
from urllib.parse import urlencode, quote_plus

SKILL_METADATA = {
    "name": "Historical Research & Archives",
    "id": "historical_research",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Comprehensive historical research and archival analysis module providing access to National Archives, Library of Congress collections, historical newspapers, genealogy records, military service records, immigration data, land patents, census records, and Sanborn maps",
    "capabilities": [
        "search_national_archives",
        "query_chronicling_america",
        "access_library_of_congress",
        "retrieve_genealogy_records",
        "search_military_service_records",
        "query_immigration_records",
        "access_land_patent_records",
        "retrieve_census_data",
        "query_sanborn_maps",
        "generate_research_report",
        "analyze_historical_timeline",
        "validate_document_authenticity"
    ],
    "domain": "historical_research"
}

EXPERT_PROMPTS = {
    "nara_deep_search": """Conduct a comprehensive search of National Archives records for {topic} covering the period {start_year} to {end_year}. Focus on record groups {record_groups} and include both textual records and digital assets. Return NAIDs, titles, scope notes, and access restrictions.""",
    
    "newspaper_analysis": """Analyze historical newspaper coverage in Chronicling America for {event_name} between {start_date} and {end_date}. Include sentiment analysis, geographic distribution, key themes, and notable publishers. Focus on newspapers from {states}.""",
    
    "genealogy_reconstruction": """Reconstruct family lineage for {surname} family in {location} between {start_year} and {end_year}. Cross-reference census records, immigration records, military service records, and land patents. Include migration patterns and occupational changes.""",
    
    "military_service_analysis": """Retrieve and analyze military service records for {individual_name} or {unit_designation} during {conflict_period}. Include enlistment dates, muster rolls, pension records, and any disability or medical records.""",
    
    "immigration_timeline": """Create a detailed immigration timeline for {family_name} arriving at {port_of_entry} between {start_year} and {end_year}. Include ship manifests, naturalization records, and any correspondence with immigration authorities.""",
    
    "land_ownership_history": """Trace land ownership history for property in {county}, {state} described as {legal_description}. Include original land patents, subsequent transfers, and any associated agricultural or mineral rights.""",
    
    "census_demographic_analysis": """Perform demographic analysis using census data for {location} across decades {census_years}. Include population trends, occupational distributions, ethnic compositions, and household structures.""",
    
    "sanborn_map_analysis": """Analyze Sanborn fire insurance maps for {city}, {state} covering the period {start_year} to {end_year}. Document building changes, business types, fire hazards, and urban development patterns."""
}

INTEGRATION_POINTS = {
    "nara_catalog_api": {
        "type": "api",
        "endpoint": "https://catalog.archives.gov/api/v2",
        "description": "National Archives Catalog API for searching archival descriptions and authority records",
        "auth_method": "api_key",
        "documentation_url": "https://www.archives.gov/research/catalog/help/api-getting-started"
    },
    "chronicling_america_api": {
        "type": "api",
        "endpoint": "https://chroniclingamerica.loc.gov/api/v2",
        "description": "Library of Congress Chronicling America API for historical newspaper access",
        "auth_method": "none",
        "documentation_url": "https://libraryofcongress.github.io/data-exploration/loc.gov%20JSON%20API/Chronicling_America/README.html"
    },
    "loc_json_api": {
        "type": "api",
        "endpoint": "https://www.loc.gov/api/v2",
        "description": "Library of Congress JSON API for digital collections",
        "auth_method": "none",
        "documentation_url": "https://libraryofcongress.github.io/data-exploration/"
    },
    "census_api": {
        "type": "api",
        "endpoint": "https://api.census.gov/data",
        "description": "US Census Bureau API for historical census data",
        "auth_method": "api_key",
        "documentation_url": "https://www.census.gov/data/developers/data-sets.html"
    },
    "sanborn_maps_db": {
        "type": "database",
        "endpoint": "https://www.loc.gov/collections/sanborn-maps",
        "description": "Library of Congress Sanborn Fire Insurance Map collection",
        "auth_method": "none",
        "documentation_url": "https://www.loc.gov/collections/sanborn-maps/about-this-collection/"
    }
}

def validate_naid(naid: str) -> bool:
    """Validate National Archives Identifier format."""
    if not isinstance(naid, str):
        return False
    return bool(re.match(r'^\d{1,10}$', naid.strip()))

def parse_date_range(date_str: str) -> Tuple[datetime.date, datetime.date]:
    """Parse date range strings into datetime objects."""
    date_str = date_str.strip()
    
    if '-' in date_str:
        start_str, end_str = date_str.split('-', 1)
    else:
        start_str = end_str = date_str
    
    def parse_single_date(date_part: str) -> datetime.date:
        date_part = date_part.strip()
        for fmt in ['%Y-%m-%d', '%Y-%m', '%Y']:
            try:
                parsed = datetime.datetime.strptime(date_part, fmt).date()
                return parsed
            except ValueError:
                continue
        raise ValueError(f"Invalid date format: {date_part}")
    
    start_date = parse_single_date(start_str)
    end_date = parse_single_date(end_str)
    
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    
    return start_date, end_date

def build_nara_query(params: Dict[str, Any]) -> str:
    """Build NARA Catalog API query string from parameters."""
    query_parts = []
    
    if params.get('q'):
        query_parts.append(f"q={quote_plus(params['q'])}")
    
    if params.get('naid'):
        query_parts.append(f"naid={params['naid']}")
    
    if params.get('record_group'):
        query_parts.append(f"recordGroupNumber={params['record_group']}")
    
    if params.get('start_date'):
        query_parts.append(f"fromDate={params['start_date']}")
    
    if params.get('end_date'):
        query_parts.append(f"toDate={params['end_date']}")
    
    if params.get('format'):
        query_parts.append(f"typeOfMaterials={params['format']}")
    
    if params.get('online'):
        query_parts.append("online=true")
    
    return "&".join(query_parts)

def analyze_newspaper_coverage(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze newspaper search results for patterns and insights."""
    if not results:
        return {"total_articles": 0, "analysis": {}}
    
    states = Counter()
    years = Counter()
    newspapers = Counter()
    
    for article in results:
        if 'state' in article:
            states[article['state']] += 1
        if 'date' in article:
            try:
                year = article['date'][:4]
                years[year] += 1
            except (IndexError, TypeError):
                continue
        if 'title' in article:
            newspapers[article['title']] += 1
    
    return {
        "total_articles": len(results),
        "geographic_distribution": dict(states.most_common(10)),
        "temporal_distribution": dict(years.most_common()),
        "top_newspapers": dict(newspapers.most_common(5)),
        "coverage_span": {
            "earliest": min(results, key=lambda x: x.get('date', '9999'))['date'],
            "latest": max(results, key=lambda x: x.get('date', '0000'))['date']
        }
    }

def calculate_document_hash(document: Dict[str, Any]) -> str:
    """Calculate SHA256 hash of document for authenticity verification."""
    doc_str = json.dumps(document, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(doc_str.encode('utf-8')).hexdigest()

def generate_research_timeline(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate chronological timeline from historical events."""
    timeline = []
    
    for event in events:
        try:
            date_str = event.get('date', '')
            if date_str:
                date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                timeline.append({
                    "date": date_obj,
                    "event": event.get('title', ''),
                    "description": event.get('description', ''),
                    "source": event.get('source', ''),
                    "location": event.get('location', '')
                })
        except (ValueError, TypeError):
            continue
    
    timeline.sort(key=lambda x: x['date'])
    
    return [
        {
            "date": item['date'].isoformat(),
            "event": item['event'],
            "description": item['description'],
            "source": item['source'],
            "location": item['location']
        }
        for item in timeline
    ]

def extract_census_demographics(census_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and analyze demographic data from census records."""
    demographics = {
        "total_population": 0,
        "households": 0,
        "occupations": Counter(),
        "birthplaces": Counter(),
        "ages": [],
        "male_count": 0,
        "female_count": 0
    }
    
    for record in census_data.get('records', []):
        demographics["total_population"] += 1
        
        if record.get('occupation'):
            demographics["occupations"][record['occupation']] += 1
        
        if record.get('birthplace'):
            demographics["birthplaces"][record['birthplace']] += 1
        
        if record.get('age'):
            try:
                demographics["ages"].append(int(record['age']))
            except ValueError:
                pass
        
        if record.get('sex', '').lower() == 'm':
            demographics["male_count"] += 1
        elif record.get('sex', '').lower() == 'f':
            demographics["female_count"] += 1
    
    if demographics["ages"]:
        demographics["age_statistics"] = {
            "mean": statistics.mean(demographics["ages"]),
            "median": statistics.median(demographics["ages"]),
            "min": min(demographics["ages"]),
            "max": max(demographics["ages"])
        }
    
    demographics["occupations"] = dict(demographics["occupations"].most_common(10))
    demographics["birthplaces"] = dict(demographics["birthplaces"].most_common(10))
    
    return demographics

def validate_document_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize document metadata."""
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "normalized": {}
    }
    
    required_fields = ['title', 'date', 'source']
    for field in required_fields:
        if not metadata.get(field):
            validation_result["valid"] = False
            validation_result["errors"].append(f"Missing required field: {field}")
    
    if metadata.get('date'):
        try:
            parse_date_range(metadata['date'])
        except ValueError as e:
            validation_result["errors"].append(f"Invalid date format: {e}")
    
    if metadata.get('naid') and not validate_naid(str(metadata['naid'])):
        validation_result["errors"].append("Invalid NAID format")
    
    validation_result["normalized"] = {
        "title": str(metadata.get('title', '')).strip(),
        "date": str(metadata.get('date', '')).strip(),
        "source": str(metadata.get('source', '')).strip(),
        "naid": str(metadata.get('naid', '')).strip() if metadata.get('naid') else None
    }
    
    return validation_result

def render_research_report(research_data: Dict[str, Any], template: str = "standard") -> str:
    """Generate formatted research report from collected data."""
    report_parts = []
    
    report_parts.append(f"# Historical Research Report")
    report_parts.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_parts.append("")
    
    if research_data.get('summary'):
        report_parts.append("## Executive Summary")
        report_parts.append(research_data['summary'])
        report_parts.append("")
    
    if research_data.get('timeline'):
        report_parts.append("## Chronological Timeline")
        for event in research_data['timeline']:
            report_parts.append(f"- **{event['date']}**: {event['event']}")
            if event.get('description'):
                report_parts.append(f"  {event['description']}")
        report_parts.append("")
    
    if research_data.get('sources'):
        report_parts.append("## Sources Consulted")
        for source in research_data['sources']:
            report_parts.append(f"- {source}")
        report_parts.append("")
    
    if research_data.get('analysis'):
        report_parts.append("## Analysis")
        for key, value in research_data['analysis'].items():
            report_parts.append(f"### {key.replace('_', ' ').title()}")
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    report_parts.append(f"- {sub_key}: {sub_value}")
            else:
                report_parts.append(str(value))
            report_parts.append("")
    
    return "\n".join(report_parts)

class SkillEngine:
    """Main skill engine for historical research and archival analysis."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the skill engine with configuration."""
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Revvel-HistoricalResearch/1.0.0'
        })
        
        if config.get('nara_api_key'):
            self.session.headers.update({
                'x-api-key': config['nara_api_key']
            })
    
    def search_national_archives(self, query: str, **kwargs) -> Dict[str, Any]:
        """Search National Archives Catalog."""
        params = {'q': query}
        params.update(kwargs)
        
        query_string = build_nara_query(params)
        url = f"{INTEGRATION_POINTS['nara_catalog_api']['endpoint']}/records/search?{query_string}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e), "results": []}
    
    def query_chronicling_america(self, query: str, **kwargs) -> Dict[str, Any]:
        """Query Chronicling America newspaper collection."""
        params = {'q': query}
        params.update(kwargs)
        
        query_string = urlencode(params)
        url = f"{INTEGRATION_POINTS['chronicling_america_api']['endpoint']}/search.json?{query_string}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'items' in data:
                analysis = analyze_newspaper_coverage(data['items'])
                return {"results": data['items'], "analysis": analysis}
            return data
        except requests.RequestException as e:
            return {"error": str(e), "results": []}
    
    def access_library_of_congress(self, collection: str, query: str, **kwargs) -> Dict[str, Any]:
        """Access Library of Congress digital collections."""
        params = {'q': query}
        params.update(kwargs)
        
        query_string = urlencode(params)
        url = f"{INTEGRATION_POINTS['loc_json_api']['endpoint']}/{collection}?{query_string}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e), "results": []}
    
    def retrieve_genealogy_records(self, surname: str, location: str, **kwargs) -> Dict[str, Any]:
        """Retrieve genealogy records from multiple sources."""
        results = {
            "census_records": [],
            "immigration_records": [],
            "military_records": [],
            "land_records": []
        }
        
        census_query = f"{surname} {location}"
        census_data = self.access_library_of_congress("collections", census_query, fo="json")
        if 'results' in census_data:
            results["census_records"] = census_data['results'][:10]
        
        immigration_data = self.query_chronicling_america(f"{surname} immigration", **kwargs)
        if 'results' in immigration_data:
            results["immigration_records"] = immigration_data['results'][:10]
        
        return results
    
    def search_military_service_records(self, name: str, conflict: str = None) -> Dict[str, Any]:
        """Search military service records."""
        query = f"{name} military service"
        if conflict:
            query += f" {conflict}"
        
        return self.search_national_archives(query, typeOfMaterials="textual records")
    
    def query_immigration_records(self, name: str, port: str = None, year: int = None) -> Dict[str, Any]:
        """Query immigration and naturalization records."""
        query = f"{name} immigration"
        if port:
            query += f" {port}"
        
        params = {'q': query}
        if year:
            params['fromDate'] = str(year)
            params['toDate'] = str(year + 1)
        
        return self.search_national_archives(query, **params)
    
    def access_land_patent_records(self, location: str, **kwargs) -> Dict[str, Any]:
        """Access Bureau of Land Management land patent records."""
        query = f"land patent {location}"
        return self.search_national_archives(query, record_group="49")
    
    def retrieve_census_data(self, location: str, year: int) -> Dict[str, Any]:
        """Retrieve historical census data."""
        query = f"census {location} {year}"
        census_result = self.access_library_of_congress("collections", query, fo="json")
        
        if 'results' in census_result:
            demographics = extract_census_demographics({
                'records': census_result['results'][:100]
            })
            return {"results": census_result['results'][:50], "demographics": demographics}
        
        return {"results": [], "demographics": {}}
    
    def query_sanborn_maps(self, city: str, state: str, year: int = None) -> Dict[str, Any]:
        """Query Sanborn fire insurance maps."""
        query = f"sanborn {city} {state}"
        if year:
            query += f" {year}"
        
        return self.access_library_of_congress("collections/sanborn-maps", query, fo="json")
    
    def generate_research_report(self, research_data: Dict[str, Any]) -> str:
        """Generate comprehensive research report."""
        return render_research_report(research_data)
    
    def run(self, capability: str, **kwargs) -> Dict[str, Any]:
        """Main dispatcher method."""
        capability_map = {
            "search_national_archives": self.search_national_archives,
            "query_chronicling_america": self.query_chronicling_america,
            "access_library_of_congress": self.access_library_of_congress,
            "retrieve_genealogy_records": self.retrieve_genealogy_records,
            "search_military_service_records": self.search_military_service_records,
            "query_immigration_records": self.query_immigration_records,
            "access_land_patent_records": self.access_land_patent_records,
            "retrieve_census_data": self.retrieve_census_data,
            "query_sanborn_maps": self.query_sanborn_maps,
            "generate_research_report": self.generate_research_report
        }
        
        if capability not in capability_map:
            return {"error": f"Unknown capability: {capability}"}
        
        try:
            return capability_map[capability](**kwargs)
        except Exception as e:
            return {"error": str(e)}

class TestHistoricalResearchSkill(unittest.TestCase):
    """Comprehensive test suite for Historical Research skill."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "nara_api_key": "test_key",
            "timeout": 30
        }
        self.engine = SkillEngine(self.config)
    
    def test_skill_metadata(self):
        """Test skill metadata structure."""
        self.assertEqual(SKILL_METADATA["name"], "Historical Research & Archives")
        self.assertIn("search_national_archives", SKILL_METADATA["capabilities"])
        self.assertEqual(SKILL_METADATA["version"], "1.0.0")
    
    def test_validate_naid(self):
        """Test NAID validation function."""
        self.assertTrue(validate_naid("123456"))
        self.assertTrue(validate_naid("1234567890"))
        self.assertFalse(validate_naid("12345678901"))
        self.assertFalse(validate_naid("abc123"))
        self.assertFalse(validate_naid(""))
    
    def test_parse_date_range(self):
        """Test date range parsing."""
        start, end = parse_date_range("1900-01-01-1920-12-31")
        self.assertEqual(start.year, 1900)
        self.assertEqual(end.year, 1920)
        
        start, end = parse_date_range("1900")
        self.assertEqual(start, end)
        
        with self.assertRaises(ValueError):
            parse_date_range("invalid-date")
    
    def test_build_nara_query(self):
        """Test NARA query building."""
        params = {
            'q': 'constitution',
            'record_group': '360',
            'start_date': '1776',
            'end_date': '1789',
            'online': True
        }
        query = build_nara_query(params)
        self.assertIn("q=constitution", query)
        self.assertIn("recordGroupNumber=360", query)
        self.assertIn("online=true", query)
    
    def test_analyze_newspaper_coverage(self):
        """Test newspaper coverage analysis."""
        results = [
            {"state": "NY", "date": "1900-01-01", "title": "New York Times"},
            {"state": "NY", "date": "1900-01-02", "title": "New York Times"},
            {"state": "CA", "date": "1900-01-01", "title": "San Francisco Chronicle"}
        ]
        analysis = analyze_newspaper_coverage(results)
        self.assertEqual(analysis["total_articles"], 3)
        self.assertEqual(analysis["geographic_distribution"]["NY"], 2)
        self.assertEqual(analysis["top_newspapers"]["New York Times"], 2)
    
    def test_calculate_document_hash(self):
        """Test document hash calculation."""
        doc1 = {"title": "Test", "date": "1900-01-01"}
        doc2 = {"date": "1900-01-01", "title": "Test"}
        hash1 = calculate_document_hash(doc1)
        hash2 = calculate_document_hash(doc2)
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)
    
    def test_generate_research_timeline(self):
        """Test timeline generation."""
        events = [
            {"date": "1900-01-01", "event": "Event 1", "description": "First event"},
            {"date": "1899-12-31", "event": "Event 2", "description": "Second event"},
            {"date": "invalid", "event": "Invalid event"}
        ]
        timeline = generate_research_timeline(events)
        self.assertEqual(len(timeline), 2)
        self.assertEqual(timeline[0]["date"], "1899-12-31")
        self.assertEqual(timeline[1]["date"], "1900-01-01")
    
    def test_extract_census_demographics(self):
        """Test census demographics extraction."""
        census_data = {
            "records": [
                {"occupation": "Farmer", "birthplace": "Germany", "age": "35", "sex": "M"},
                {"occupation": "Housewife", "birthplace": "USA", "age": "30", "sex": "F"},
                {"occupation": "Farmer", "birthplace": "Germany", "age": "40", "sex": "M"}
            ]
        }
        demographics = extract_census_demographics(census_data)
        self.assertEqual(demographics["total_population"], 3)
        self.assertEqual(demographics["occupations"]["Farmer"], 2)
        self.assertEqual(demographics["birthplaces"]["Germany"], 2)
        self.assertEqual(demographics["male_count"], 2)
        self.assertEqual(demographics["female_count"], 1)
    
    def test_validate_document_metadata(self):
        """Test document metadata validation."""
        metadata = {
            "title": "Test Document",
            "date": "1900-01-01",
            "source": "National Archives",
            "naid": "123456"
        }
        validation = validate_document_metadata(metadata)
        self.assertTrue(validation["valid"])
        self.assertEqual(len(validation["errors"]), 0)
        
        invalid_metadata = {"title": "", "date": "invalid"}
        validation = validate_document_metadata(invalid_metadata)
        self.assertFalse(validation["valid"])
        self.assertGreater(len(validation["errors"]), 0)
    
    def test_render_research_report(self):
        """Test research report rendering."""
        research_data = {
            "summary": "Test summary",
            "timeline": [
                {"date": "1900-01-01", "event": "Test event", "description": "Description"}
            ],
            "sources": ["Source 1", "Source 2"],
            "analysis": {"key": "value"}
        }
        report = render_research_report(research_data)
        self.assertIn("# Historical Research Report", report)
        self.assertIn("Test summary", report)
        self.assertIn("1900-01-01", report)
    
    def test_skill_engine_initialization(self):
        """Test skill engine initialization."""
        engine = SkillEngine({"nara_api_key": "test"})
        self.assertEqual(engine.config["nara_api_key"], "test")
        self.assertIsNotNone(engine.session)
    
    def test_skill_engine_run_dispatcher(self):
        """Test skill engine capability dispatcher."""
        result = self.engine.run("unknown_capability")
        self.assertIn("error", result)
        self.assertIn("Unknown capability", result["error"])

if __name__ == '__main__':
    unittest.main()