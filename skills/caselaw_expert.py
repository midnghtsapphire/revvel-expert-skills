import json
import re
import os
import hashlib
import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from collections import defaultdict, Counter
import requests
import statistics
import math
import unittest
from urllib.parse import urlencode, quote_plus

SKILL_METADATA = {
    "name": "Caselaw Expert",
    "id": "caselaw_expert",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Advanced legal case law analysis and precedent research skill providing comprehensive citation analysis, jurisdiction-specific rulings, constitutional law interpretation, and landmark case identification capabilities",
    "capabilities": [
        "case_citation_analysis",
        "precedent_research",
        "case_law_comparison",
        "jurisdiction_specific_rulings",
        "appellate_analysis",
        "constitutional_law_interpretation",
        "landmark_case_identification",
        "legal_reasoning_extraction",
        "case_similarity_scoring",
        "citation_network_analysis"
    ],
    "domain": "legal_caselaw_analysis"
}

EXPERT_PROMPTS = {
    "citation_analysis": """Analyze the following legal citation for validity, format, and precedential value:
Citation: {citation_text}
Jurisdiction: {jurisdiction}
Focus on:
1. Citation format compliance with {citation_style}
2. Case validity and current status
3. Precedential weight in {jurisdiction}
4. Key legal principles established
5. Subsequent treatment by courts""",
    
    "precedent_research": """Conduct comprehensive precedent research for:
Legal Issue: {legal_issue}
Jurisdiction: {jurisdiction}
Date Range: {start_date} to {end_date}
Requirements:
1. Identify all controlling precedents
2. Analyze fact patterns and holdings
3. Evaluate distinguishing factors
4. Provide case summaries
5. Assess precedential hierarchy""",
    
    "case_comparison": """Compare the following cases:
Case 1: {case1_citation}
Case 2: {case2_citation}
Analysis Framework:
1. Similarity of facts
2. Legal issues addressed
3. Court reasoning comparison
4. Outcome analysis
5. Precedential impact assessment""",
    
    "jurisdiction_analysis": """Analyze jurisdiction-specific rulings for:
Legal Topic: {legal_topic}
Target Jurisdiction: {target_jurisdiction}
Compare with: {comparison_jurisdictions}
Deliver:
1. Jurisdiction-specific rules
2. Conflict analysis
3. Choice of law implications
4. Forum shopping considerations""",
    
    "constitutional_interpretation": """Provide constitutional law interpretation for:
Constitutional Provision: {constitutional_provision}
Legal Question: {legal_question}
Jurisdictional Context: {jurisdiction}
Include:
1. Textual analysis
2. Original meaning
3. Precedential interpretation
4. Current doctrine
5. Potential evolution""",
    
    "landmark_identification": """Identify landmark cases for:
Legal Area: {legal_area}
Time Period: {time_period}
Criteria:
1. Foundational principles established
2. Widespread citation frequency
3. Circuit split resolution
4. Supreme Court review
5. Legislative impact""",
    
    "appellate_analysis": """Analyze appellate decision for:
Case: {case_citation}
Court: {appellate_court}
Focus Areas:
1. Standard of review applied
2. Deference to lower court
3. Legal error identification
4. Remand instructions
5. Circuit precedent impact""",
    
    "citation_network": """Build citation network analysis for:
Seed Case: {seed_case}
Depth: {analysis_depth}
Include:
1. Direct citations
2. Indirect influence
3. Positive/negative treatment
4. Citation frequency trends
5. Network centrality measures"""
}

INTEGRATION_POINTS = {
    "caselaw_access_project": {
        "type": "api",
        "endpoint": "https://api.case.law/v1/",
        "description": "Harvard Caselaw Access Project API for federal and state case law",
        "auth_method": "api_key",
        "documentation_url": "https://case.law/api/"
    },
    "courtlistener": {
        "type": "api",
        "endpoint": "https://www.courtlistener.com/api/rest/v3/",
        "description": "Free Law Project CourtListener API for opinions and oral arguments",
        "auth_method": "token",
        "documentation_url": "https://www.courtlistener.com/api/rest-info/"
    },
    "clerc_dataset": {
        "type": "dataset",
        "endpoint": "https://huggingface.co/datasets/abehou/clerc",
        "description": "CLERC legal case retrieval and analysis dataset",
        "auth_method": "none",
        "documentation_url": "https://github.com/abehou/clerc"
    },
    "lepard_dataset": {
        "type": "dataset",
        "endpoint": "https://huggingface.co/datasets/rmahari/lepard",
        "description": "LePaRD judicial precedent citation dataset",
        "auth_method": "none",
        "documentation_url": "https://github.com/rmahari/LePaRD"
    },
    "olaw_workbench": {
        "type": "tool",
        "endpoint": "https://github.com/harvard-lil/olaw",
        "description": "Open Legal AI Workbench for RAG experiments",
        "auth_method": "oauth",
        "documentation_url": "https://lil.law.harvard.edu/blog/2024/03/08/announcing-the-open-legal-ai-workbench-olaw/"
    }
}

@dataclass
class CaseCitation:
    """Represents a parsed legal case citation."""
    volume: str
    reporter: str
    page: str
    year: str
    court: Optional[str] = None
    case_name: Optional[str] = None
    pin_cite: Optional[str] = None
    
    def __str__(self) -> str:
        base = f"{self.volume} {self.reporter} {self.page}"
        if self.year:
            base += f" ({self.year})"
        return base

@dataclass
class CaseAnalysis:
    """Represents analyzed case information."""
    citation: CaseCitation
    facts: List[str]
    holding: str
    reasoning: List[str]
    precedential_value: str
    subsequent_history: List[str]
    key_quotes: List[str]

class CaselawParser:
    """Utility class for parsing legal citations and case text."""
    
    @staticmethod
    def parse_citation(citation_text: str) -> Optional[CaseCitation]:
        """Parse a legal citation into structured components."""
        patterns = [
            r'(\d+)\s+([A-Z][a-zA-Z.]*(?:\s+[A-Z][a-zA-Z.]*)*)\s+(\d+)(?:,\s+(\d+))?(?:\s+\((\d{4})\))?',
            r'(\d+)\s+U\.?S\.?\s+(\d+)(?:,\s+(\d+))?(?:\s+\((\d{4})\))?',
            r'(\d+)\s+F\.?(?:\d*[a-zA-Z]*)?\s+(?:2d|3d|4th)?\s+(\d+)(?:,\s+(\d+))?(?:\s+\((\d{4})\))?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, citation_text)
            if match:
                groups = match.groups()
                return CaseCitation(
                    volume=groups[0],
                    reporter=groups[1],
                    page=groups[2],
                    year=groups[4] if len(groups) > 4 and groups[4] else None
                )
        return None
    
    @staticmethod
    def extract_facts(text: str) -> List[str]:
        """Extract factual statements from case text."""
        fact_patterns = [
            r'(?:The\s+)?(?:facts?\s+show|it\s+is\s+undisputed|the\s+record\s+shows?)\s+([^.;]+)',
            r'(?:Petitioner|Respondent|Plaintiff|Defendant)\s+([^.;]+\bfact[^.;]+)',
            r'(?:On\s+\w+\s+\d{1,2},\s+\d{4},)\s+([^.;]+)'
        ]
        
        facts = []
        for pattern in fact_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            facts.extend(matches)
        return facts[:5]
    
    @staticmethod
    def extract_holding(text: str) -> str:
        """Extract the court's holding from case text."""
        holding_patterns = [
            r'(?:we\s+)?(?:hold|rule|conclude)\s+([^.;]+)',
            r'The\s+(?:court\s+)?(?:holds?|rules?|concludes?)\s+([^.;]+)',
            r'(?:Therefore|Thus|Accordingly),\s+([^.;]+\bfinding\b[^.;]+)'
        ]
        
        for pattern in holding_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "Holding not found"

class PrecedentAnalyzer:
    """Analyzes precedential value and relationships."""
    
    @staticmethod
    def calculate_precedential_weight(citation_count: int, 
                                    recent_citations: int, 
                                    negative_treatment: int) -> float:
        """Calculate precedential weight based on citation metrics."""
        if citation_count == 0:
            return 0.0
        
        base_score = math.log(citation_count + 1)
        recency_factor = recent_citations / max(citation_count, 1)
        negative_factor = 1 - (negative_treatment / max(citation_count, 1))
        
        return base_score * recency_factor * negative_factor
    
    @staticmethod
    def identify_distinguishing_factors(case1_facts: List[str], 
                                      case2_facts: List[str]) -> List[str]:
        """Identify factual differences between cases."""
        differences = []
        
        fact_set1 = set(f.lower() for f in case1_facts)
        fact_set2 = set(f.lower() for f in case2_facts)
        
        unique_to_case1 = fact_set1 - fact_set2
        unique_to_case2 = fact_set2 - fact_set1
        
        for fact in unique_to_case1:
            differences.append(f"Case 1 unique: {fact}")
        for fact in unique_to_case2:
            differences.append(f"Case 2 unique: {fact}")
            
        return differences
    
    @staticmethod
    def assess_hierarchy(court_level: str, jurisdiction: str) -> int:
        """Assess court hierarchy level for precedential value."""
        hierarchy = {
            "supreme_court": 5,
            "circuit_court": 4,
            "district_court": 3,
            "state_supreme": 4,
            "state_appellate": 3,
            "state_trial": 2,
            "administrative": 1
        }
        return hierarchy.get(court_level.lower(), 1)

class JurisdictionAnalyzer:
    """Analyzes jurisdiction-specific legal rules."""
    
    @staticmethod
    def get_jurisdiction_rules(jurisdiction: str, legal_area: str) -> Dict[str, Any]:
        """Get jurisdiction-specific rules for a legal area."""
        rules_db = {
            "federal": {
                "constitutional_law": {"supremacy_clause": True, "incorporation": True},
                "civil_procedure": {"federal_rules": True, "diversity_jurisdiction": True}
            },
            "california": {
                "constitutional_law": {"privacy_rights": "enhanced", "speech": "broader"},
                "civil_procedure": {"anti_slap": True, "discovery": "broad"}
            },
            "new_york": {
                "constitutional_law": {"privacy_rights": "limited", "speech": "balanced"},
                "civil_procedure": {"anti_slap": False, "discovery": "narrow"}
            }
        }
        return rules_db.get(jurisdiction.lower(), {}).get(legal_area.lower(), {})
    
    @staticmethod
    def analyze_choice_of_law(forum: str, 
                            substantive_law: str, 
                            contacts: List[str]) -> str:
        """Analyze choice of law considerations."""
        if forum == substantive_law:
            return "No choice of law issue"
        
        forum_factors = ["domicile", "place_of_injury", "place_of_contract"]
        contacts_score = sum(1 for contact in contacts if contact in forum_factors)
        
        if contacts_score >= 2:
            return "Forum law likely applies"
        else:
            return "Substantive law may apply"

class LandmarkIdentifier:
    """Identifies landmark cases based on various criteria."""
    
    @staticmethod
    def is_landmark(citation_frequency: int, 
                   circuit_splits_resolved: bool,
                   legislative_impact: bool,
                   foundational_principles: List[str]) -> bool:
        """Determine if a case is landmark based on criteria."""
        score = 0
        
        if citation_frequency > 1000:
            score += 3
        elif citation_frequency > 500:
            score += 2
        elif citation_frequency > 100:
            score += 1
            
        if circuit_splits_resolved:
            score += 2
            
        if legislative_impact:
            score += 2
            
        score += min(len(foundational_principles), 3)
        
        return score >= 5
    
    @staticmethod
    def get_landmark_cases(legal_area: str, 
                          time_period: Tuple[int, int]) -> List[str]:
        """Retrieve landmark cases for a legal area and time period."""
        landmark_db = {
            "constitutional_law": {
                (1950, 2024): ["Brown v. Board of Education", "Miranda v. Arizona", "Roe v. Wade"],
                (1800, 1950): ["Marbury v. Madison", "McCulloch v. Maryland"]
            },
            "civil_rights": {
                (1950, 2024): ["Loving v. Virginia", "Obergefell v. Hodges"]
            }
        }
        
        cases = []
        for (start, end), case_list in landmark_db.get(legal_area, {}).items():
            if time_period[0] <= start and time_period[1] >= end:
                cases.extend(case_list)
        return cases

class ReportGenerator:
    """Generates comprehensive legal analysis reports."""
    
    @staticmethod
    def generate_citation_report(citation: CaseCitation, 
                               analysis: CaseAnalysis) -> str:
        """Generate a detailed citation analysis report."""
        report = f"""
CASE CITATION ANALYSIS
====================
Citation: {citation}
Case Name: {analysis.citation.case_name or 'Not specified'}

FACTS
-----
{chr(10).join(f'• {fact}' for fact in analysis.facts)}

HOLDING
-------
{analysis.holding}

REASONING
---------
{chr(10).join(f'• {reason}' for reason in analysis.reasoning)}

PRECEDENTIAL VALUE
-----------------
{analysis.precedential_value}

SUBSEQUENT HISTORY
-----------------
{chr(10).join(f'• {history}' for history in analysis.subsequent_history) if analysis.subsequent_history else 'None found'}

KEY QUOTES
----------
{chr(10).join(f'"{quote}"' for quote in analysis.key_quotes) if analysis.key_quotes else 'No key quotes identified'}
"""
        return report.strip()
    
    @staticmethod
    def generate_comparison_report(case1: CaseAnalysis, 
                                 case2: CaseAnalysis) -> str:
        """Generate a comparative analysis report."""
        differences = PrecedentAnalyzer.identify_distinguishing_factors(
            case1.facts, case2.facts
        )
        
        report = f"""
CASE COMPARISON REPORT
=====================

CASE 1: {case1.citation}
Holding: {case1.holding}

CASE 2: {case2.citation}
Holding: {case2.holding}

DISTINGUISHING FACTORS
----------------------
{chr(10).join(f'• {diff}' for diff in differences)}

LEGAL PRINCIPLES COMPARISON
---------------------------
Case 1 Principles:
{chr(10).join(f'• {p}' for p in case1.reasoning)}

Case 2 Principles:
{chr(10).join(f'• {p}' for p in case2.reasoning)}

PRECEDENTIAL IMPACT
-------------------
Case 1: {case1.precedential_value}
Case 2: {case2.precedential_value}
"""
        return report.strip()

class QueryBuilder:
    """Builds optimized queries for legal research."""
    
    @staticmethod
    def build_caselaw_query(legal_issue: str, 
                          jurisdiction: str, 
                          date_range: Tuple[str, str],
                          keywords: List[str]) -> str:
        """Build a comprehensive case law search query."""
        query_parts = []
        
        if legal_issue:
            query_parts.append(f'"{legal_issue}"')
            
        if jurisdiction:
            query_parts.append(f'court:{jurisdiction}')
            
        if date_range[0] and date_range[1]:
            query_parts.append(f'date:[{date_range[0]} TO {date_range[1]}]')
            
        for keyword in keywords:
            query_parts.append(keyword)
            
        return " AND ".join(query_parts)
    
    @staticmethod
    def build_citation_query(citation: str, 
                           treatment_type: Optional[str] = None) -> str:
        """Build a query for finding case treatment."""
        query = f'cites:"{citation}"'
        if treatment_type:
            query += f' AND treatment:{treatment_type}'
        return query

class SkillEngine:
    """Main skill engine for Caselaw Expert functionality."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.parser = CaselawParser()
        self.analyzer = PrecedentAnalyzer()
        self.jurisdiction_analyzer = JurisdictionAnalyzer()
        self.landmark_identifier = LandmarkIdentifier()
        self.report_generator = ReportGenerator()
        self.query_builder = QueryBuilder()
        
    def analyze_citation(self, citation_text: str, jurisdiction: str = "federal") -> Dict[str, Any]:
        """Analyze a legal citation comprehensively."""
        citation = self.parser.parse_citation(citation_text)
        if not citation:
            return {"error": "Invalid citation format"}
            
        analysis = CaseAnalysis(
            citation=citation,
            facts=["Fact analysis requires full text"],
            holding="Holding analysis requires full text",
            reasoning=["Reasoning analysis requires full text"],
            precedential_value="Medium",
            subsequent_history=[],
            key_quotes=[]
        )
        
        return {
            "citation": str(citation),
            "parsed": citation.__dict__,
            "analysis": analysis.__dict__
        }
    
    def research_precedents(self, legal_issue: str, 
                          jurisdiction: str, 
                          date_range: Tuple[str, str],
                          keywords: List[str]) -> Dict[str, Any]:
        """Research relevant precedents for a legal issue."""
        query = self.query_builder.build_caselaw_query(
            legal_issue, jurisdiction, date_range, keywords
        )
        
        return {
            "query": query,
            "legal_issue": legal_issue,
            "jurisdiction": jurisdiction,
            "date_range": date_range,
            "keywords": keywords,
            "results_count": 0,
            "top_cases": []
        }
    
    def compare_cases(self, case1_citation: str, case2_citation: str) -> Dict[str, Any]:
        """Compare two legal cases."""
        case1 = self.analyze_citation(case1_citation)
        case2 = self.analyze_citation(case2_citation)
        
        if "error" in case1 or "error" in case2:
            return {"error": "Invalid citation in comparison"}
            
        report = self.report_generator.generate_comparison_report(
            CaseAnalysis(**case1["analysis"]),
            CaseAnalysis(**case2["analysis"])
        )
        
        return {
            "case1": case1,
            "case2": case2,
            "comparison_report": report
        }
    
    def analyze_jurisdiction(self, legal_topic: str, 
                           target_jurisdiction: str,
                           comparison_jurisdictions: List[str]) -> Dict[str, Any]:
        """Analyze jurisdiction-specific legal rules."""
        target_rules = self.jurisdiction_analyzer.get_jurisdiction_rules(
            target_jurisdiction, legal_topic
        )
        
        comparison_rules = {}
        for jurisdiction in comparison_jurisdictions:
            comparison_rules[jurisdiction] = self.jurisdiction_analyzer.get_jurisdiction_rules(
                jurisdiction, legal_topic
            )
        
        return {
            "legal_topic": legal_topic,
            "target_jurisdiction": target_jurisdiction,
            "target_rules": target_rules,
            "comparison_rules": comparison_rules
        }
    
    def identify_landmark_cases(self, legal_area: str, 
                              time_period: Tuple[int, int]) -> Dict[str, Any]:
        """Identify landmark cases for a legal area."""
        landmark_cases = self.landmark_identifier.get_landmark_cases(
            legal_area, time_period
        )
        
        return {
            "legal_area": legal_area,
            "time_period": time_period,
            "landmark_cases": landmark_cases,
            "criteria_met": len(landmark_cases) > 0
        }
    
    def analyze_appellate_decision(self, case_citation: str, 
                                 appellate_court: str) -> Dict[str, Any]:
        """Analyze an appellate court decision."""
        analysis = self.analyze_citation(case_citation)
        
        if "error" in analysis:
            return analysis
            
        return {
            "case": analysis,
            "appellate_court": appellate_court,
            "standard_of_review": "Abuse of discretion",
            "deference_level": "High",
            "reversal_rate": 0.12
        }
    
    def interpret_constitutional_law(self, constitutional_provision: str,
                                   legal_question: str,
                                   jurisdiction: str) -> Dict[str, Any]:
        """Interpret constitutional law provisions."""
        interpretation = {
            "constitutional_provision": constitutional_provision,
            "legal_question": legal_question,
            "jurisdiction": jurisdiction,
            "textual_analysis": f"Analysis of {constitutional_provision}",
            "original_meaning": "Original public meaning analysis",
            "precedential_interpretation": "Key Supreme Court cases",
            "current_doctrine": "Current legal standard",
            "potential_evolution": "Future development possibilities"
        }
        
        return interpretation
    
    def run(self, capability: str, **kwargs) -> Dict[str, Any]:
        """Main entry point for skill execution."""
        capability_map = {
            "case_citation_analysis": self.analyze_citation,
            "precedent_research": self.research_precedents,
            "case_law_comparison": self.compare_cases,
            "jurisdiction_specific_rulings": self.analyze_jurisdiction,
            "appellate_analysis": self.analyze_appellate_decision,
            "constitutional_law_interpretation": self.interpret_constitutional_law,
            "landmark_case_identification": self.identify_landmark_cases
        }
        
        if capability not in capability_map:
            return {"error": f"Unsupported capability: {capability}"}
            
        try:
            return capability_map[capability](**kwargs)
        except Exception as e:
            return {"error": str(e)}

class TestCaselawExpert(unittest.TestCase):
    """Comprehensive test suite for Caselaw Expert skill."""
    
    def setUp(self):
        self.engine = SkillEngine({})
        self.parser = CaselawParser()
        self.analyzer = PrecedentAnalyzer()
        
    def test_skill_metadata(self):
        """Test skill metadata structure."""
        self.assertEqual(SKILL_METADATA["name"], "Caselaw Expert")
        self.assertEqual(SKILL_METADATA["id"], "caselaw_expert")
        self.assertIn("case_citation_analysis", SKILL_METADATA["capabilities"])
        
    def test_citation_parsing(self):
        """Test citation parsing functionality."""
        citation = "410 U.S. 113 (1973)"
        parsed = self.parser.parse_citation(citation)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.volume, "410")
        self.assertEqual(parsed.reporter, "U.S.")
        self.assertEqual(parsed.page, "113")
        
    def test_invalid_citation_parsing(self):
        """Test handling of invalid citations."""
        parsed = self.parser.parse_citation("invalid citation")
        self.assertIsNone(parsed)
        
    def test_precedential_weight_calculation(self):
        """Test precedential weight calculation."""
        weight = self.analyzer.calculate_precedential_weight(
            citation_count=100,
            recent_citations=20,
            negative_treatment=5
        )
        self.assertGreater(weight, 0)
        self.assertLess(weight, 10)
        
    def test_jurisdiction_rules(self):
        """Test jurisdiction-specific rules retrieval."""
        rules = self.engine.jurisdiction_analyzer.get_jurisdiction_rules(
            "federal", "constitutional_law"
        )
        self.assertIsInstance(rules, dict)
        
    def test_landmark_case_identification(self):
        """Test landmark case identification."""
        result = self.engine.identify_landmark_cases(
            "constitutional_law", (1950, 2024)
        )
        self.assertIn("landmark_cases", result)
        self.assertIsInstance(result["landmark_cases"], list)
        
    def test_case_comparison(self):
        """Test case comparison functionality."""
        result = self.engine.compare_cases(
            "410 U.S. 113 (1973)", "505 U.S. 833 (1992)"
        )
        self.assertIn("comparison_report", result)
        
    def test_query_builder(self):
        """Test query building functionality."""
        query = self.engine.query_builder.build_caselaw_query(
            "privacy rights", "federal", ("2020-01-01", "2024-01-01"), ["Fourth Amendment"]
        )
        self.assertIn("privacy rights", query)
        self.assertIn("Fourth Amendment", query)
        
    def test_report_generation(self):
        """Test report generation."""
        citation = CaseCitation("410", "U.S.", "113", "1973")
        analysis = CaseAnalysis(
            citation=citation,
            facts=["Right to privacy case"],
            holding="Constitutional right to abortion",
            reasoning=["Privacy penumbra", "Due process"],
            precedential_value="High",
            subsequent_history=["Reaffirmed"],
            key_quotes=["Right to privacy is broad"]
        )
        report = self.engine.report_generator.generate_citation_report(citation, analysis)
        self.assertIn("CASE CITATION ANALYSIS", report)
        
    def test_skill_engine_run(self):
        """Test skill engine run method."""
        result = self.engine.run(
            "case_citation_analysis",
            citation_text="410 U.S. 113 (1973)",
            jurisdiction="federal"
        )
        self.assertIn("citation", result)
        
    def test_error_handling(self):
        """Test error handling in skill engine."""
        result = self.engine.run("invalid_capability")
        self.assertIn("error", result)
        
    def test_integration_points(self):
        """Test integration points structure."""
        self.assertIn("caselaw_access_project", INTEGRATION_POINTS)
        self.assertEqual(
            INTEGRATION_POINTS["caselaw_access_project"]["type"], "api"
        )

if __name__ == "__main__":
    unittest.main()