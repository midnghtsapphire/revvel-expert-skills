import requests
import json
import os
import re
import datetime
import hashlib
import collections
import statistics
import math
import sqlite3
import csv
import io
import zipfile
import tempfile
import logging
import unittest
from typing import Dict, List, Optional, Any, Tuple, Set
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
from collections import defaultdict, Counter
import xml.etree.ElementTree as ET
import subprocess
import shutil
import time
import random

SKILL_METADATA = {
    "name": "Epstein Files Intelligence Analysis & Data Scraper",
    "id": "epstein_files_intel",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Comprehensive investigative tool for Jeffrey Epstein case files with document analysis, relationship mapping, social media intelligence, and fact verification capabilities",
    "capabilities": [
        "Court document scraping and OCR",
        "Redacted text recovery via metadata analysis",
        "Flight log analysis and passenger mapping",
        "Black book contact database extraction",
        "Deposition transcript entity extraction",
        "Financial records analysis",
        "PACER court record scraping",
        "Social network graph building",
        "Timeline construction and visualization",
        "Geographic mapping of properties and locations",
        "Corporate structure mapping",
        "Social media intelligence gathering",
        "Fact verification and credibility scoring",
        "Evidence chain building",
        "Automated report generation"
    ],
    "domain": "legal_forensic_investigation"
}

EXPERT_PROMPTS = {
    "flight_analysis": """Analyze Jeffrey Epstein's flight logs to identify:
- All passengers who flew on the Lolita Express more than 3 times
- Flight patterns to Little St. James island
- Co-travelers with high-profile individuals
- Unusual flight destinations or timing
- Correlation between flights and known events/dates

Focus on flights between {start_date} and {end_date}. 
Cross-reference passenger names with black book contacts.
Flag any flights containing {target_names}.""",
    
    "network_mapping": """Build a comprehensive social network graph showing:
- All connections between {target_individual} and Epstein associates
- Connection strength based on frequency of contact
- Types of relationships (financial, social, legal, familial)
- Geographic clustering of connections
- Temporal evolution of the network

Include data from flight logs, black book, depositions, and property records.
Highlight any connections to {organizations_of_interest}.""",
    
    "financial_forensics": """Analyze financial records to uncover:
- Shell companies controlled by {target_name}
- Wire transfers to/from Epstein entities
- Property transactions and ownership chains
- Trust structures and beneficiaries
- Banking relationships with JPMorgan/Deutsche Bank

Focus on transactions between {start_year} and {end_year}.
Cross-reference with corporate filings and court documents.
Flag any transactions over ${amount_threshold}.""",
    
    "victim_pattern_analysis": """Identify patterns in victim testimonies:
- Recruitment locations and methods
- Age ranges and demographics
- Common locations of abuse
- Time periods of highest activity
- Methods of coercion and control

Cross-reference victim statements with:
- Flight logs showing presence at locations
- Property records for access to venues
- Staff schedules and employment records
- Security camera footage timestamps""",
    
    "redaction_recovery": """Attempt to recover redacted text from:
- Court documents released by SDNY and SDFL
- FBI vault releases
- FOIA responses
- Maxwell trial exhibits

Use techniques:
- Metadata layer extraction
- OCR artifact analysis
- Copy-paste vulnerabilities
- Font spacing analysis
- Cross-reference with unredacted versions

Focus on documents related to {case_name} from {date_range}.""",
    
    "timeline_reconstruction": """Build a comprehensive timeline of events:
- All known meetings between Epstein and {target_individual}
- Property acquisitions and sales
- Corporate formations and dissolutions
- Legal proceedings and settlements
- Victim incidents by date
- Media coverage and public statements

Include supporting evidence for each event.
Flag any gaps or inconsistencies in the timeline.""",
    
    "social_media_intelligence": """Gather and analyze social media content:
- Posts mentioning Epstein and associates
- Deleted content recovered via Wayback Machine
- Reddit discussions in relevant subreddits
- Twitter/X conversations and threads
- Instagram photos with location tags

Focus on content from {platforms} between {start_date} and {end_date}.
Identify key influencers and information spread patterns.
Flag any posts containing {keywords}.""",
    
    "fact_verification": """Verify claims about {subject} by:
- Cross-referencing with court documents
- Checking against official records
- Analyzing source credibility
- Identifying supporting/contradicting evidence
- Tracking legal adjudication status

Categorize claims as: PROVEN, ALLEGED, CLAIMED, UNVERIFIED
Provide confidence scores and evidence chains.
Flag any disputed or contradictory information."""
}

INTEGRATION_POINTS = {
    "pacer_api": {
        "type": "api",
        "endpoint": "https://pacer.uscourts.gov",
        "description": "Public Access to Court Electronic Records for federal case documents",
        "auth_method": "username/password with 2FA",
        "documentation_url": "https://pacer.uscourts.gov/pacer-cmecf-automation"
    },
    "documentcloud": {
        "type": "api",
        "endpoint": "https://api.documentcloud.org",
        "description": "Document analysis and OCR platform for investigative documents",
        "auth_method": "API key",
        "documentation_url": "https://www.documentcloud.org/help/api"
    },
    "courtlistener": {
        "type": "api",
        "endpoint": "https://www.courtlistener.com/api/rest/v3/",
        "description": "Free legal database with opinions, oral arguments, and judges",
        "auth_method": "API key",
        "documentation_url": "https://www.courtlistener.com/api/"
    },
    "wayback_machine": {
        "type": "api",
        "endpoint": "http://archive.org/wayback/available",
        "description": "Internet Archive for historical webpage snapshots",
        "auth_method": "None required",
        "documentation_url": "https://archive.org/help/wayback_api.php"
    },
    "twitter_api": {
        "type": "api",
        "endpoint": "https://api.twitter.com/2",
        "description": "Twitter/X API for social media intelligence",
        "auth_method": "Bearer token",
        "documentation_url": "https://developer.twitter.com/en/docs/twitter-api"
    },
    "reddit_api": {
        "type": "api",
        "endpoint": "https://oauth.reddit.com",
        "description": "Reddit API for forum discussion analysis",
        "auth_method": "OAuth2",
        "documentation_url": "https://www.reddit.com/dev/api/"
    },
    "epstein_sqlite_db": {
        "type": "database",
        "endpoint": "local/epstein_files.db",
        "description": "Local SQLite database for storing scraped and analyzed data",
        "auth_method": "File-based",
        "documentation_url": "https://www.sqlite.org/docs.html"
    },
    "tesseract_ocr": {
        "type": "tool",
        "endpoint": "local/tesseract",
        "description": "Open-source OCR engine for text extraction from images and PDFs",
        "auth_method": "Local installation",
        "documentation_url": "https://github.com/tesseract-ocr/tesseract"
    }
}

@dataclass
class FlightRecord:
    date: str
    aircraft: str
    departure: str
    arrival: str
    passengers: List[str]
    pilot: str
    notes: str

@dataclass
class ContactRecord:
    name: str
    phone: str
    email: str
    address: str
    category: str
    source: str

@dataclass
class FinancialTransaction:
    date: str
    amount: float
    sender: str
    receiver: str
    method: str
    purpose: str
    source_doc: str

@dataclass
class NetworkNode:
    entity_id: str
    name: str
    entity_type: str
    connections: List[str]
    metadata: Dict[str, Any]

class EpsteinDataParser:
    @staticmethod
    def parse_flight_log(text: str) -> List[FlightRecord]:
        """Parse Epstein flight log text into structured records"""
        flights = []
        lines = text.strip().split('\n')
        
        for line in lines:
            parts = re.split(r'\s{2,}|\t|,', line.strip())
            if len(parts) >= 6:
                try:
                    flight = FlightRecord(
                        date=parts[0].strip(),
                        aircraft=parts[1].strip(),
                        departure=parts[2].strip(),
                        arrival=parts[3].strip(),
                        passengers=[p.strip() for p in parts[4].split(';') if p.strip()],
                        pilot=parts[5].strip(),
                        notes=' '.join(parts[6:]) if len(parts) > 6 else ''
                    )
                    flights.append(flight)
                except Exception as e:
                    logging.warning(f"Failed to parse flight line: {line[:100]}... Error: {e}")
        
        return flights
    
    @staticmethod
    def parse_black_book(text: str) -> List[ContactRecord]:
        """Parse Epstein's black book contact list"""
        contacts = []
        lines = text.strip().split('\n')
        
        for line in lines:
            parts = re.split(r'\s{2,}|\t', line.strip())
            if len(parts) >= 2:
                contact = ContactRecord(
                    name=parts[0].strip(),
                    phone=parts[1].strip() if len(parts) > 1 else '',
                    email=parts[2].strip() if len(parts) > 2 else '',
                    address=parts[3].strip() if len(parts) > 3 else '',
                    category=parts[4].strip() if len(parts) > 4 else 'unknown',
                    source='black_book'
                )
                contacts.append(contact)
        
        return contacts
    
    @staticmethod
    def extract_entities(text: str) -> Dict[str, List[str]]:
        """Extract people, organizations, and locations from text"""
        entities = {
            'people': [],
            'organizations': [],
            'locations': [],
            'dates': []
        }
        
        # Simple name extraction (can be enhanced with NER)
        name_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
        names = re.findall(name_pattern, text)
        entities['people'] = list(set(names))
        
        # Organization extraction
        org_pattern = r'\b[A-Z][A-Z\s]+(?:Inc|LLC|Corp|Foundation|Trust|Company)\b'
        orgs = re.findall(org_pattern, text)
        entities['organizations'] = list(set(orgs))
        
        # Location extraction
        location_pattern = r'\b(?:Palm Beach|Little St James|Great St James|Manhattan|Paris|New Mexico|USVI|New York)\b'
        locations = re.findall(location_pattern, text, re.IGNORECASE)
        entities['locations'] = list(set(locations))
        
        # Date extraction
        date_pattern = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        dates = re.findall(date_pattern, text)
        entities['dates'] = list(set(dates))
        
        return entities
    
    @staticmethod
    def recover_redacted_text(pdf_path: str) -> Dict[str, Any]:
        """Attempt to recover redacted text from PDF using multiple techniques"""
        recovered = {
            'method_used': '',
            'text': '',
            'confidence': 0.0,
            'metadata': {}
        }
        
        try:
            # Try copy-paste vulnerability first
            result = subprocess.run(['pdftotext', pdf_path, '-'], 
                                  capture_output=True, text=True, timeout=30)
            if result.stdout:
                recovered['text'] = result.stdout
                recovered['method_used'] = 'pdftotext'
                recovered['confidence'] = 0.7
            
            # Try OCR if pdftotext fails
            if not recovered['text']:
                result = subprocess.run(['tesseract', pdf_path, 'stdout', '--psm', '6'],
                                      capture_output=True, text=True, timeout=60)
                if result.stdout:
                    recovered['text'] = result.stdout
                    recovered['method_used'] = 'tesseract_ocr'
                    recovered['confidence'] = 0.5
            
            # Extract metadata
            result = subprocess.run(['pdfinfo', pdf_path], 
                                  capture_output=True, text=True, timeout=10)
            if result.stdout:
                recovered['metadata'] = dict(line.split(':', 1) for line in result.stdout.split('\n') if ':' in line)
                
        except Exception as e:
            logging.error(f"Failed to recover redacted text from {pdf_path}: {e}")
        
        return recovered

class NetworkAnalyzer:
    @staticmethod
    def build_connection_graph(entities: List[NetworkNode]) -> Dict[str, Any]:
        """Build a social network graph from entity connections"""
        graph = {
            'nodes': [],
            'edges': [],
            'metrics': {}
        }
        
        entity_map = {e.entity_id: e for e in entities}
        
        # Build nodes
        for entity in entities:
            graph['nodes'].append({
                'id': entity.entity_id,
                'name': entity.name,
                'type': entity.entity_type,
                'metadata': entity.metadata
            })
        
        # Build edges
        edge_counts = defaultdict(int)
        for entity in entities:
            for connection in entity.connections:
                if connection in entity_map:
                    edge_counts[(entity.entity_id, connection)] += 1
        
        for (source, target), count in edge_counts.items():
            graph['edges'].append({
                'source': source,
                'target': target,
                'weight': count,
                'type': 'connection'
            })
        
        # Calculate network metrics
        graph['metrics'] = NetworkAnalyzer.calculate_network_metrics(graph)
        
        return graph
    
    @staticmethod
    def calculate_network_metrics(graph: Dict[str, Any]) -> Dict[str, float]:
        """Calculate network centrality and connectivity metrics"""
        metrics = {}
        
        # Node count
        metrics['node_count'] = len(graph['nodes'])
        metrics['edge_count'] = len(graph['edges'])
        
        # Average degree
        if graph['nodes']:
            degrees = [0] * len(graph['nodes'])
            node_index = {node['id']: i for i, node in enumerate(graph['nodes'])}
            
            for edge in graph['edges']:
                if edge['source'] in node_index:
                    degrees[node_index[edge['source']]] += edge['weight']
                if edge['target'] in node_index:
                    degrees[node_index[edge['target']]] += edge['weight']
            
            metrics['avg_degree'] = statistics.mean(degrees) if degrees else 0
            metrics['max_degree'] = max(degrees) if degrees else 0
        
        # Network density
        n = metrics['node_count']
        if n > 1:
            max_edges = n * (n - 1) / 2
            metrics['density'] = metrics['edge_count'] / max_edges
        else:
            metrics['density'] = 0
        
        return metrics
    
    @staticmethod
    def find_key_players(graph: Dict[str, Any], min_connections: int = 5) -> List[Dict[str, Any]]:
        """Identify key players in the network based on connectivity"""
        key_players = []
        
        # Build adjacency list
        adjacency = defaultdict(list)
        for edge in graph['edges']:
            adjacency[edge['source']].append((edge['target'], edge['weight']))
            adjacency[edge['target']].append((edge['source'], edge['weight']))
        
        # Calculate centrality for each node
        for node in graph['nodes']:
            node_id = node['id']
            connections = adjacency[node_id]
            total_weight = sum(weight for _, weight in connections)
            
            if len(connections) >= min_connections:
                key_players.append({
                    'node': node,
                    'connection_count': len(connections),
                    'total_weight': total_weight,
                    'centrality_score': total_weight / len(connections) if connections else 0
                })
        
        # Sort by centrality score
        key_players.sort(key=lambda x: x['centrality_score'], reverse=True)
        
        return key_players

class FactVerifier:
    @staticmethod
    def categorize_claim(claim: str, evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Categorize a claim based on available evidence"""
        result = {
            'claim': claim,
            'category': 'UNVERIFIED',
            'confidence': 0.0,
            'evidence': [],
            'contradictions': []
        }
        
        # Analyze each piece of evidence
        court_evidence = []
        media_evidence = []
        other_evidence = []
        
        for ev in evidence:
            if ev.get('type') == 'court_document':
                court_evidence.append(ev)
            elif ev.get('type') == 'media_report':
                media_evidence.append(ev)
            else:
                other_evidence.append(ev)
        
        # Prioritize court evidence
        if court_evidence:
            # Check for proven claims
            proven = any(ev.get('status') == 'proven' for ev in court_evidence)
            if proven:
                result['category'] = 'PROVEN'
                result['confidence'] = 0.95
            else:
                result['category'] = 'ALLEGED'
                result['confidence'] = 0.7
            
            result['evidence'].extend(court_evidence)
        
        # Check media evidence
        elif media_evidence:
            credible_sources = ['nytimes.com', 'washingtonpost.com', 'wsj.com', 'reuters.com', 'ap.org']
            credible_count = sum(1 for ev in media_evidence 
                               if any(source in ev.get('source', '') for source in credible_sources))
            
            if credible_count >= 2:
                result['category'] = 'CLAIMED'
                result['confidence'] = 0.6
            else:
                result['category'] = 'UNVERIFIED'
                result['confidence'] = 0.3
            
            result['evidence'].extend(media_evidence)
        
        # Add other evidence
        result['evidence'].extend(other_evidence)
        
        return result
    
    @staticmethod
    def calculate_source_credibility(source: str, history: List[Dict[str, Any]]) -> float:
        """Calculate credibility score for a source based on historical accuracy"""
        if not history:
            return 0.5  # Neutral for unknown sources
        
        total_claims = len(history)
        accurate_claims = sum(1 for h in history if h.get('accuracy') == 'accurate')
        
        base_score = accurate_claims / total_claims if total_claims > 0 else 0.5
        
        # Adjust for source type
        if 'court' in source.lower() or '.gov' in source:
            base_score = min(0.95, base_score + 0.2)
        elif any(domain in source for domain in ['nytimes.com', 'washingtonpost.com', 'wsj.com']):
            base_score = min(0.9, base_score + 0.1)
        elif any(domain in source for domain in ['twitter.com', 'facebook.com', 'reddit.com']):
            base_score = max(0.1, base_score - 0.3)
        
        return max(0.0, min(1.0, base_score))

class ReportGenerator:
    @staticmethod
    def generate_network_report(graph: Dict[str, Any], key_players: List[Dict[str, Any]]) -> str:
        """Generate a comprehensive network analysis report"""
        report = []
        report.append("EPSTEIN NETWORK ANALYSIS REPORT")
        report.append("=" * 40)
        report.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Network overview
        metrics = graph['metrics']
        report.append("NETWORK OVERVIEW:")
        report.append(f"- Total Entities: {metrics['node_count']}")
        report.append(f"- Total Connections: {metrics['edge_count']}")
        report.append(f"- Network Density: {metrics['density']:.3f}")
        report.append(f"- Average Connections: {metrics['avg_degree']:.1f}")
        report.append("")
        
        # Key players
        report.append("KEY PLAYERS (Top 10):")
        for i, player in enumerate(key_players[:10], 1):
            node = player['node']
            report.append(f"{i}. {node['name']} ({node['type']})")
            report.append(f"   - Connections: {player['connection_count']}")
            report.append(f"   - Centrality Score: {player['centrality_score']:.2f}")
            report.append("")
        
        # Connection types
        edge_types = defaultdict(int)
        for edge in graph['edges']:
            edge_types[edge['type']] += 1
        
        report.append("CONNECTION TYPES:")
        for edge_type, count in sorted(edge_types.items(), key=lambda x: x[1], reverse=True):
            report.append(f"- {edge_type}: {count}")
        
        return "\n".join(report)
    
    @staticmethod
    def generate_timeline_report(events: List[Dict[str, Any]]) -> str:
        """Generate a chronological timeline report"""
        report = []
        report.append("EPSTEIN CASE TIMELINE")
        report.append("=" * 25)
        report.append("")
        
        # Sort events by date
        sorted_events = sorted(events, key=lambda x: x.get('date', ''))
        
        current_year = None
        for event in sorted_events:
            date = event.get('date', '')
            if not date:
                continue
                
            year = date[:4] if len(date) >= 4 else 'Unknown'
            
            if year != current_year:
                report.append(f"\n{year}:")
                current_year = year
            
            report.append(f"  {date}: {event.get('description', 'No description')}")
            if event.get('sources'):
                report.append(f"    Sources: {', '.join(event['sources'][:3])}")
        
        return "\n".join(report)
    
    @staticmethod
    def export_to_csv(data: List[Dict[str, Any]], filename: str) -> bool:
        """Export data to CSV format"""
        if not data:
            return False
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            return True
        except Exception as e:
            logging.error(f"Export failed: {e}")
            return False

class EpsteinFilesIntel:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = config.get('db_path', 'epstein_files.db')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.setup_database()
        self.setup_logging()
    
    def setup_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT,
                target_id TEXT,
                type TEXT,
                weight REAL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES entities (id),
                FOREIGN KEY (target_id) REFERENCES entities (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT,
                source TEXT,
                url TEXT,
                content TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                aircraft TEXT,
                departure TEXT,
                arrival TEXT,
                passengers TEXT,
                pilot TEXT,
                notes TEXT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                category TEXT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def setup_logging(self):
        """Configure logging for the module"""
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('epstein_intel.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def scrape_court_documents(self, court: str, case_number: str) -> List[Dict[str, Any]]:
        """Scrape court documents from PACER or CourtListener"""
        documents = []
        
        # Try CourtListener first (free)
        try:
            url = f"https://www.courtlistener.com/api/rest/v3/?type=document&q=epstein&court={court}"
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                for doc in data.get('results', []):
                    documents.append({
                        'id': doc.get('id'),
                        'title': doc.get('case_name', ''),
                        'source': 'courtlistener',
                        'url': doc.get('absolute_url', ''),
                        'content': doc.get('plain_text', ''),
                        'metadata': json.dumps({
                            'date_filed': doc.get('date_filed'),
                            'court': doc.get('court', ''),
                            'docket_number': doc.get('docket_number', '')
                        })
                    })
        except Exception as e:
            self.logger.error(f"CourtListener scrape failed: {e}")
        
        return documents
    
    def analyze_flight_logs(self, log_data: str) -> Dict[str, Any]:
        """Analyze flight logs for patterns and key passengers"""
        parser = EpsteinDataParser()
        flights = parser.parse_flight_log(log_data)
        
        analysis = {
            'total_flights': len(flights),
            'unique_passengers': set(),
            'destination_frequency': Counter(),
            'passenger_frequency': Counter(),
            'high_frequency_passengers': []
        }
        
        for flight in flights:
            # Count destinations
            analysis['destination_frequency'][flight.arrival] += 1
            
            # Count passengers
            for passenger in flight.passengers:
                clean_name = passenger.strip().lower()
                if clean_name and len(clean_name) > 2:
                    analysis['passenger_frequency'][clean_name] += 1
                    analysis['unique_passengers'].add(clean_name)
        
        # Identify high-frequency passengers
        for passenger, count in analysis['passenger_frequency'].most_common(20):
            if count >= 3:  # Minimum 3 flights
                analysis['high_frequency_passengers'].append({
                    'name': passenger,
                    'flight_count': count
                })
        
        analysis['unique_passengers'] = len(analysis['unique_passengers'])
        
        return analysis
    
    def extract_black_book_contacts(self, book_data: str) -> List[Dict[str, Any]]:
        """Extract and categorize contacts from Epstein's black book"""
        parser = EpsteinDataParser()
        contacts = parser.parse_black_book(book_data)
        
        categorized = []
        for contact in contacts:
            categorized.append({
                'name': contact.name,
                'phone': contact.phone,
                'email': contact.email,
                'address': contact.address,
                'category': contact.category,
                'source': 'black_book',
                'extracted_at': datetime.datetime.now().isoformat()
            })
        
        return categorized
    
    def build_social_network(self, data_sources: List[str]) -> Dict[str, Any]:
        """Build comprehensive social network from multiple data sources"""
        entities = []
        connections = []
        
        # Process each data source
        for source in data_sources:
            try:
                if source.endswith('.json'):
                    with open(source, 'r') as f:
                        data = json.load(f)
                elif source.endswith('.csv'):
                    data = self._load_csv_data(source)
                else:
                    continue
                
                # Extract entities and connections
                for item in data:
                    if 'name' in item:
                        entity = NetworkNode(
                            entity_id=hashlib.md5(item['name'].encode()).hexdigest(),
                            name=item['name'],
                            entity_type=item.get('type', 'person'),
                            connections=[],
                            metadata=item
                        )
                        entities.append(entity)
                        
                        # Add connections
                        if 'connections' in item:
                            for conn in item['connections']:
                                connections.append({
                                    'source': entity.entity_id,
                                    'target': conn,
                                    'type': 'known_association'
                                })
                                
            except Exception as e:
                self.logger.error(f"Failed to process data source {source}: {e}")
        
        # Build network graph
        analyzer = NetworkAnalyzer()
        graph = analyzer.build_connection_graph(entities)
        key_players = analyzer.find_key_players(graph)
        
        return {
            'graph': graph,
            'key_players': key_players,
            'entity_count': len(entities),
            'connection_count': len(connections)
        }
    
    def verify_facts(self, claims: List[str], evidence_sources: List[str]) -> List[Dict[str, Any]]:
        """Verify claims against available evidence"""
        verifier = FactVerifier()
        verified_claims = []
        
        for claim in claims:
            # Gather evidence for this claim
            evidence = []
            for source in evidence_sources:
                try:
                    if source.endswith('.json'):
                        with open(source, 'r') as f:
                            source_data = json.load(f)
                            evidence.extend(source_data)
                except Exception as e:
                    self.logger.warning(f"Failed to load evidence source {source}: {e}")
            
            # Verify claim
            result = verifier.categorize_claim(claim, evidence)
            verified_claims.append(result)
        
        return verified_claims
    
    def generate_investigation_report(self, investigation_type: str, parameters: Dict[str, Any]) -> str:
        """Generate comprehensive investigation report"""
        if investigation_type == 'network_analysis':
            network_data = self.build_social_network(parameters.get('data_sources', []))
            report = ReportGenerator.generate_network_report(
                network_data['graph'], 
                network_data['key_players']
            )
            
        elif investigation_type == 'timeline':
            events = parameters.get('events', [])
            report = ReportGenerator.generate_timeline_report(events)
            
        elif investigation_type == 'flight_analysis':
            log_data = parameters.get('flight_logs', '')
            analysis = self.analyze_flight_logs(log_data)
            report = self._generate_flight_report(analysis)
            
        else:
            report = f"Unknown investigation type: {investigation_type}"
        
        return report
    
    def export_data(self, data_type: str, format: str, output_path: str) -> bool:
        """Export analyzed data to specified format"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if data_type == 'entities':
                cursor.execute("SELECT * FROM entities")
                rows = cursor.fetchall()
                data = []
                for row in rows:
                    data.append({
                        'id': row[0],
                        'name': row[1],
                        'type': row[2],
                        'metadata': row[3],
                        'created_at': row[4]
                    })
            
            elif data_type == 'connections':
                cursor.execute("SELECT * FROM connections")
                rows = cursor.fetchall()
                data = []
                for row in rows:
                    data.append({
                        'id': row[0],
                        'source_id': row[1],
                        'target_id': row[2],
                        'type': row[3],
                        'weight': row[4],
                        'metadata': row[5],
                        'created_at': row[6]
                    })
            
            else:
                self.logger.error(f"Unknown data type: {data_type}")
                return False
            
            conn.close()
            
            if format == 'csv':
                return ReportGenerator.export_to_csv(data, output_path)
            elif format == 'json':
                with open(output_path, 'w') as f:
                    json.dump(data, f, indent=2)
                return True
            else:
                self.logger.error(f"Unsupported format: {format}")
                return False
                
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            return False
    
    def _load_csv_data(self, filepath: str) -> List[Dict[str, Any]]:
        """Load data from CSV file"""
        data = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = list(reader)
        except Exception as e:
            self.logger.error(f"Failed to load CSV {filepath}: {e}")
        return data
    
    def _generate_flight_report(self, analysis: Dict[str, Any]) -> str:
        """Generate flight analysis report"""
        report = []
        report.append("EPSTEIN FLIGHT LOG ANALYSIS")
        report.append("=" * 30)
        report.append(f"Total Flights Analyzed: {analysis['total_flights']}")
        report.append(f"Unique Passengers: {analysis['unique_passengers']}")
        report.append("")
        
        report.append("TOP DESTINATIONS:")
        for dest, count in analysis['destination_frequency'].most_common(10):
            report.append(f"- {dest}: {count} flights")
        
        report.append("\nHIGH-FREQUENCY PASSENGERS:")
        for passenger in analysis['high_frequency_passengers'][:15]:
            report.append(f"- {passenger['name']}: {passenger['flight_count']} flights")
        
        return "\n".join(report)

class SkillEngine:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.intel = EpsteinFilesIntel(self.config)
        self.logger = logging.getLogger(__name__)
    
    def run(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry point for skill execution"""
        try:
            if action == 'scrape_court_documents':
                return {
                    'success': True,
                    'data': self.intel.scrape_court_documents(
                        parameters.get('court', ''),
                        parameters.get('case_number', '')
                    )
                }
            
            elif action == 'analyze_flight_logs':
                return {
                    'success': True,
                    'data': self.intel.analyze_flight_logs(
                        parameters.get('log_data', '')
                    )
                }
            
            elif action == 'extract_black_book':
                return {
                    'success': True,
                    'data': self.intel.extract_black_book_contacts(
                        parameters.get('book_data', '')
                    )
                }
            
            elif action == 'build_network':
                return {
                    'success': True,
                    'data': self.intel.build_social_network(
                        parameters.get('data_sources', [])
                    )
                }
            
            elif action == 'verify_facts':
                return {
                    'success': True,
                    'data': self.intel.verify_facts(
                        parameters.get('claims', []),
                        parameters.get('evidence_sources', [])
                    )
                }
            
            elif action == 'generate_report':
                return {
                    'success': True,
                    'data': self.intel.generate_investigation_report(
                        parameters.get('investigation_type', ''),
                        parameters
                    )
                }
            
            elif action == 'export_data':
                return {
                    'success': self.intel.export_data(
                        parameters.get('data_type', ''),
                        parameters.get('format', 'csv'),
                        parameters.get('output_path', 'output.csv')
                    )
                }
            
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}'
                }
                
        except Exception as e:
            self.logger.error(f"Skill execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

class TestEpsteinFilesIntel(unittest.TestCase):
    
    def setUp(self):
        self.config = {
            'db_path': ':memory:',
            'log_level': 'DEBUG'
        }
        self.skill = SkillEngine(self.config)
        self.intel = EpsteinFilesIntel(self.config)
    
    def test_metadata_validation(self):
        """Test that skill metadata is properly formatted"""
        self.assertEqual(SKILL_METADATA['name'], "Epstein Files Intelligence Analysis & Data Scraper")
        self.assertEqual(SKILL_METADATA['id'], "epstein_files_intel")
        self.assertIn('capabilities', SKILL_METADATA)
        self.assertIsInstance(SKILL_METADATA['capabilities'], list)
        self.assertGreater(len(SKILL_METADATA['capabilities']), 0)
    
    def test_flight_log_parsing(self):
        """Test flight log parsing functionality"""
        sample_log = """2024-01-15    Boeing 727    Teterboro    St. Thomas    Epstein; Maxwell; Clinton    Pilot1    Notes
2024-01-20    Gulfstream    Palm Beach    Paris    Epstein; Prince Andrew    Pilot2    Refuel"""
        
        parser = EpsteinDataParser()
        flights = parser.parse_flight_log(sample_log)
        
        self.assertEqual(len(flights), 2)
        self.assertEqual(flights[0].aircraft, "Boeing 727")
        self.assertIn("Epstein", flights[0].passengers)
        self.assertEqual(flights[1].arrival, "Paris")
    
    def test_black_book_parsing(self):
        """Test black book contact extraction"""
        sample_book = """John Doe    555-1234    john@email.com    123 Main St    Business
Jane Smith    555-5678    jane@email.com    456 Oak Ave    Personal"""
        
        parser = EpsteinDataParser()
        contacts = parser.parse_black_book(sample_book)
        
        self.assertEqual(len(contacts), 2)
        self.assertEqual(contacts[0].name, "John Doe")
        self.assertEqual(contacts[1].phone, "555-5678")
    
 def test_entity_extraction(self):
        """Test entity extraction from text"""
        sample_text = "Jeffrey Epstein and Ghislaine Maxwell met with Bill Clinton on Little St James in January 2024."
        
        parser = EpsteinDataParser()
        entities = parser.extract_entities(sample_text)
        
        self.assertIn('people', entities)
        self.assertIn('locations', entities)
        self.assertIn('dates', entities)
        self.assertGreater(len(entities['people']), 0)
    
    def test_network_analysis(self):
        """Test network graph building and analysis"""
        entities = [
            NetworkNode("1", "Epstein", "person", ["2", "3"], {}),
            NetworkNode("2", "Maxwell", "person", ["1", "3"], {}),
            NetworkNode("3", "Clinton", "person", ["1", "2"], {})
        ]
        
        analyzer = NetworkAnalyzer()
        graph = analyzer.build_connection_graph(entities)
        
        self.assertEqual(graph['metrics']['node_count'], 3)
        self.assertEqual(graph['metrics']['edge_count'], 6)  # Bidirectional edges
        self.assertIn('density', graph['metrics'])
        
        key_players = analyzer.find_key_players(graph, min_connections=1)
        self.assertEqual(len(key_players), 3)
    
    def test_fact_verification(self):
        """Test fact verification functionality"""
        verifier = FactVerifier()
        
        claim = "Epstein flew to his island with Clinton"
        evidence = [
            {'type': 'court_document', 'status': 'proven', 'source': 'court.gov'},
            {'type': 'media_report', 'source': 'nytimes.com'}
        ]
        
        result = verifier.categorize_claim(claim, evidence)
        
        self.assertEqual(result['claim'], claim)
        self.assertEqual(result['category'], 'PROVEN')
        self.assertGreater(result['confidence'], 0.9)
    
    def test_report_generation(self):
        """Test report generation capabilities"""
        graph = {
            'nodes': [
                {'id': '1', 'name': 'Epstein', 'type': 'person', 'metadata': {}},
                {'id': '2', 'name': 'Maxwell', 'type': 'person', 'metadata': {}}
            ],
            'edges': [
                {'source': '1', 'target': '2', 'weight': 5, 'type': 'connection'}
            ],
            'metrics': {
                'node_count': 2,
                'edge_count': 1,
                'density': 0.5,
                'avg_degree': 1.0,
                'max_degree': 1
            }
        }
        
        key_players = [
            {
                'node': {'id': '1', 'name': 'Epstein', 'type': 'person'},
                'connection_count': 1,
                'centrality_score': 1.0
            }
        ]
        
        report = ReportGenerator.generate_network_report(graph, key_players)
        
        self.assertIn("EPSTEIN NETWORK ANALYSIS REPORT", report)
        self.assertIn("Epstein", report)
        self.assertIn("Network Density", report)
    
    def test_skill_engine_execution(self):
        """Test skill engine action execution"""
        # Test flight log analysis
        log_data = """2024-01-15    Boeing    Teterboro    St. Thomas    Epstein; Maxwell    Pilot1"""
        result = self.skill.run('analyze_flight_logs', {'log_data': log_data})
        
        self.assertTrue(result['success'])
        self.assertIn('data', result)
        self.assertIn('total_flights', result['data'])
        self.assertEqual(result['data']['total_flights'], 1)
    
    def test_data_export(self):
        """Test data export functionality"""
        # Add some test data
        conn = sqlite3.connect(self.intel.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO entities (id, name, type, metadata) VALUES (?, ?, ?, ?)",
                      ('test1', 'Test Entity', 'person', '{}'))
        conn.commit()
        conn.close()
        
        # Test export
        success = self.intel.export_data('entities', 'csv', 'test_export.csv')
        self.assertTrue(success)
        
        # Verify file was created
        self.assertTrue(os.path.exists('test_export.csv'))
        
        # Clean up
        if os.path.exists('test_export.csv'):
            os.remove('test_export.csv')
    
    def test_error_handling(self):
        """Test error handling in skill execution"""
        # Test with invalid action
        result = self.skill.run('invalid_action', {})
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        
        # Test with missing parameters
        result = self.skill.run('analyze_flight_logs', {})
        self.assertTrue(result['success'])  # Should handle empty data gracefully
        self.assertIn('total_flights', result['data'])

if __name__ == '__main__':
    unittest.main()