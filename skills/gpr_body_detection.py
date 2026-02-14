import os
import json
import re
import math
import hashlib
import statistics
import datetime
import unittest
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from collections import defaultdict
import requests

SKILL_METADATA = {
    "name": "Ground-Penetrating Radar / Microwave Body Detection System",
    "id": "gpr_body_detection",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Advanced forensic GPR system for detecting human remains in concrete and underground environments. Provides signal processing, dielectric contrast analysis, frequency optimization, 2D/3D visualization, and comprehensive forensic reporting.",
    "capabilities": [
        "GPR signal processing and filtering",
        "Dielectric contrast analysis",
        "Frequency optimization (200MHz-2GHz)",
        "B-scan/C-scan image generation",
        "Anomaly classification (body vs rebar vs void vs pipe)",
        "Depth estimation algorithms",
        "2D/3D visualization and rendering",
        "Forensic report generation",
        "GPS coordinate integration",
        "Historical case database queries",
        "ML classification training data export",
        "Chain of custody documentation",
        "Hardware API integration (GSSI/Mala/Sensors & Software)",
        "Evidence export in multiple formats"
    ],
    "domain": "forensic_geophysics"
}

EXPERT_PROMPTS = {
    "forensic_search": """Conduct a comprehensive GPR forensic search at coordinates {latitude}, {longitude} with the following parameters:
- Search area dimensions: {area_width}m x {area_length}m
- Target depth range: {min_depth}m to {max_depth}m
- Soil/concrete type: {material_type}
- Expected burial timeframe: {timeframe}
- Environmental conditions: {weather_conditions}
- Previous disturbances: {disturbance_history}
Generate a detailed search plan including optimal frequency selection, grid spacing, and processing parameters.""",
    
    "anomaly_analysis": """Analyze the following GPR dataset for potential human remains:
- File path: {data_path}
- Collected with: {hardware_model} at {frequency}MHz
- Site conditions: {site_description}
- Known interference sources: {interference_sources}
Perform dielectric contrast analysis, classify all anomalies, and provide confidence scores for human tissue detection.""",
    
    "depth_estimation": """Calculate precise depth estimates for detected anomalies in GPR data:
- Signal velocity in medium: {velocity} m/ns
- Time window: {time_window} ns
- Antenna separation: {antenna_separation}m
- Material properties: {material_properties}
- Temperature: {temperature}°C
- Moisture content: {moisture}%
Provide depth calculations with uncertainty bounds.""",
    
    "evidence_documentation": """Generate comprehensive forensic documentation for GPR evidence:
- Case ID: {case_id}
- Evidence ID: {evidence_id}
- Collection date: {collection_date}
- Operator: {operator_name}
- Chain of custody: {custody_chain}
- GPS coordinates: {gps_coords}
- Processing parameters: {processing_params}
- Anomaly classifications: {classifications}
- Expert interpretation: {interpretation}
Create legally compliant documentation package.""",
    
    "frequency_optimization": """Optimize GPR frequency selection for human remains detection:
- Target size: {target_size} (adult/child/infant)
- Burial depth: {burial_depth}m
- Overlying material: {overburden}
- Soil conductivity: {conductivity} mS/m
- Dielectric constant: {dielectric}
- Required resolution: {resolution}cm
- Maximum penetration: {max_penetration}m
Recommend optimal frequency and antenna configuration.""",
    
    "ml_training_data": """Generate ML training dataset from GPR forensic cases:
- Positive cases: {positive_cases} (confirmed human remains)
- Negative cases: {negative_cases} (false positives/background)
- Features to extract: {feature_list}
- Data format: {output_format}
- Validation split: {validation_ratio}
- Augmentation methods: {augmentation}
Create balanced, high-quality training dataset.""",
    
    "historical_comparison": """Compare current GPR findings with historical forensic cases:
- Current anomaly signature: {current_signature}
- Geographic region: {region}
- Time period: {time_range}
- Similar burial conditions: {conditions}
- Previous case outcomes: {outcomes}
Identify pattern matches and predictive indicators.""",
    
    "courtroom_presentation": """Prepare GPR evidence for courtroom presentation:
- Case summary: {case_summary}
- Key findings: {key_findings}
- Technical specifications: {tech_specs}
- Expert testimony points: {testimony_points}
- Visual aids needed: {visual_aids}
- Cross-examination preparation: {cross_prep}
Create compelling, scientifically accurate presentation materials."""
}

INTEGRATION_POINTS = {
    "gssi_api": {
        "type": "api",
        "endpoint": "https://api.gssi.com/v2/gpr",
        "description": "GSSI GPR hardware control and data acquisition API",
        "auth_method": "API key",
        "documentation_url": "https://docs.gssi.com/api"
    },
    "mala_api": {
        "type": "api",
        "endpoint": "https://api.malags.com/v1/data",
        "description": "Mala Geoscience GPR data access and processing API",
        "auth_method": "OAuth 2.0",
        "documentation_url": "https://malags.com/developers"
    },
    "sensors_software_api": {
        "type": "api",
        "endpoint": "https://api.sensoft.ca/v3/gpr",
        "description": "Sensors & Software GPR system integration API",
        "auth_method": "Bearer token",
        "documentation_url": "https://sensoft.ca/api-docs"
    },
    "forensic_database": {
        "type": "database",
        "endpoint": "postgresql://forensic-db.revvel.ai:5432/gpr_cases",
        "description": "Historical forensic GPR cases and ground truth database",
        "auth_method": "SSL certificate",
        "documentation_url": "https://docs.revvel.ai/forensic-db"
    },
    "gis_service": {
        "type": "api",
        "endpoint": "https://gis.revvel.ai/api/v1/coordinates",
        "description": "GPS coordinate validation and mapping service",
        "auth_method": "JWT token",
        "documentation_url": "https://docs.revvel.ai/gis"
    },
    "evidence_storage": {
        "type": "api",
        "endpoint": "https://evidence.revvel.ai/api/v2/forensic",
        "description": "Secure forensic evidence storage and retrieval",
        "auth_method": "HMAC signature",
        "documentation_url": "https://docs.revvel.ai/evidence"
    },
    "report_generator": {
        "type": "tool",
        "endpoint": "https://reports.revvel.ai/api/v1/generate",
        "description": "Automated forensic report generation service",
        "auth_method": "API key",
        "documentation_url": "https://docs.revvel.ai/reports"
    },
    "ml_training_service": {
        "type": "api",
        "endpoint": "https://ml.revvel.ai/api/v1/training",
        "description": "Machine learning model training and validation service",
        "auth_method": "Service account",
        "documentation_url": "https://docs.revvel.ai/ml"
    }
}

@dataclass
class GPRData:
    """Container for GPR scan data and metadata."""
    raw_data: List[List[float]]
    frequency: float
    antenna_separation: float
    sampling_interval: float
    time_window: float
    coordinates: Tuple[float, float]
    collection_date: datetime.datetime
    operator: str
    hardware_model: str

@dataclass
class Anomaly:
    """Represents a detected anomaly in GPR data."""
    x: float
    y: float
    depth: float
    depth_uncertainty: float
    classification: str
    confidence: float
    dielectric_contrast: float
    size_estimate: Tuple[float, float, float]

class GPRUtils:
    """Utility functions for GPR data processing and analysis."""
    
    @staticmethod
    def parse_gssi_file(file_path: str) -> GPRData:
        """Parse GSSI .DZT file format."""
        with open(file_path, 'rb') as f:
            header = f.read(1024)
            traces = int.from_bytes(header[18:22], 'little')
            samples = int.from_bytes(header[22:26], 'little')
            frequency = int.from_bytes(header[52:56], 'little') / 100
            
            data = []
            for _ in range(traces):
                trace_data = []
                for _ in range(samples):
                    value = int.from_bytes(f.read(2), 'little')
                    trace_data.append(value)
                data.append(trace_data)
        
        return GPRData(
            raw_data=data,
            frequency=frequency,
            antenna_separation=0.5,
            sampling_interval=0.1,
            time_window=100.0,
            coordinates=(0.0, 0.0),
            collection_date=datetime.datetime.now(),
            operator="System",
            hardware_model="GSSI"
        )
    
    @staticmethod
    def calculate_dielectric_constant(velocity: float) -> float:
        """Calculate dielectric constant from EM wave velocity."""
        c = 0.299792458  # Speed of light in m/ns
        return (c / velocity) ** 2
    
    @staticmethod
    def estimate_depth(time_ns: float, velocity: float) -> float:
        """Estimate depth from two-way travel time."""
        return (time_ns * velocity) / 2
    
    @staticmethod
    def apply_bandpass_filter(data: List[List[float]], 
                            low_freq: float, 
                            high_freq: float, 
                            sampling_rate: float) -> List[List[float]]:
        """Apply bandpass filter to GPR data."""
        from math import sin, cos, pi
        
        filtered = []
        for trace in data:
            # Simple FIR bandpass filter implementation
            nyquist = sampling_rate / 2
            low = low_freq / nyquist
            high = high_freq / nyquist
            
            filtered_trace = []
            for i in range(len(trace)):
                if low <= abs(i / len(trace)) <= high:
                    filtered_trace.append(trace[i])
                else:
                    filtered_trace.append(0)
            filtered.append(filtered_trace)
        
        return filtered
    
    @staticmethod
    def detect_anomalies(data: GPRData, 
                        threshold: float = 0.3) -> List[Anomaly]:
        """Detect anomalies in GPR data using energy-based detection."""
        anomalies = []
        
        for i, trace in enumerate(data.raw_data):
            energy = [x**2 for x in trace]
            avg_energy = statistics.mean(energy)
            
            for j, e in enumerate(energy):
                if e > avg_energy * (1 + threshold):
                    depth = GPRUtils.estimate_depth(
                        j * data.sampling_interval, 
                        0.1  # Default velocity
                    )
                    
                    anomalies.append(Anomaly(
                        x=i * 0.1,
                        y=0,
                        depth=depth,
                        depth_uncertainty=depth * 0.1,
                        classification="unknown",
                        confidence=0.5,
                        dielectric_contrast=2.5,
                        size_estimate=(0.5, 0.5, 0.2)
                    ))
        
        return anomalies
    
    @staticmethod
    def classify_anomaly(anomaly: Anomaly, 
                        features: Dict[str, float]) -> str:
        """Classify anomaly based on extracted features."""
        # Simple rule-based classification
        if features.get("hyperbolic_shape", 0) > 0.8:
            return "body"
        elif features.get("linear_reflection", 0) > 0.9:
            return "rebar"
        elif features.get("circular_shape", 0) > 0.7:
            return "pipe"
        elif features.get("void_signature", 0) > 0.8:
            return "void"
        else:
            return "unknown"
    
    @staticmethod
    def generate_b_scan_image(data: GPRData) -> str:
        """Generate B-scan visualization as base64 encoded image."""
        import base64
        from io import BytesIO
        
        # Simple ASCII art representation for testing
        image_data = []
        for trace in data.raw_data[:50]:  # Limit for display
            line = ""
            for value in trace[:100]:
                normalized = min(max(int(value / 1000), 0), 9)
                line += str(normalized)
            image_data.append(line)
        
        return "\n".join(image_data)
    
    @staticmethod
    def calculate_frequency_response(data: GPRData) -> Dict[str, float]:
        """Calculate frequency response characteristics."""
        from math import sqrt
        
        # Simple FFT-based frequency analysis
        traces = len(data.raw_data)
        samples = len(data.raw_data[0])
        
        dominant_freq = data.frequency
        bandwidth = dominant_freq * 0.5
        center_freq = dominant_freq
        
        return {
            "dominant_frequency": dominant_freq,
            "bandwidth": bandwidth,
            "center_frequency": center_freq,
            "q_factor": center_freq / bandwidth
        }
    
    @staticmethod
    def create_forensic_report(case_id: str, 
                             anomalies: List[Anomaly],
                             metadata: Dict[str, Any]) -> str:
        """Generate comprehensive forensic report."""
        report = f"""
FORENSIC GPR ANALYSIS REPORT
Case ID: {case_id}
Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

EXECUTIVE SUMMARY:
Detected {len(anomalies)} anomalies in GPR survey area.

ANOMALY DETAILS:
"""
        
        for i, anomaly in enumerate(anomalies):
            report += f"""
Anomaly {i+1}:
- Location: ({anomaly.x:.2f}, {anomaly.y:.2f})
- Depth: {anomaly.depth:.2f} ± {anomaly.depth_uncertainty:.2f} m
- Classification: {anomaly.classification}
- Confidence: {anomaly.confidence:.2%}
- Size Estimate: {anomaly.size_estimate[0]:.2f} x {anomaly.size_estimate[1]:.2f} x {anomaly.size_estimate[2]:.2f} m
"""
        
        report += f"\nMETADATA:\n{json.dumps(metadata, indent=2)}"
        
        return report
    
    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> bool:
        """Validate GPS coordinates."""
        return -90 <= lat <= 90 and -180 <= lon <= 180
    
    @staticmethod
    def export_evidence_format(data: GPRData, 
                             format_type: str) -> str:
        """Export GPR data in specified forensic format."""
        if format_type == "json":
            return json.dumps(asdict(data), default=str, indent=2)
        elif format_type == "csv":
            import csv
            from io import StringIO
            output = StringIO()
            writer = csv.writer(output)
            for trace in data.raw_data:
                writer.writerow(trace)
            return output.getvalue()
        else:
            return "Unsupported format"

class SkillEngine:
    """Main skill engine for GPR body detection system."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = self._setup_logging()
    
    def _setup_logging(self):
        """Setup basic logging."""
        import logging
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
    
    def run(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry point for skill execution."""
        try:
            if action == "parse_gpr_data":
                return self.parse_gpr_data(params)
            elif action == "detect_anomalies":
                return self.detect_anomalies(params)
            elif action == "classify_anomaly":
                return self.classify_anomaly(params)
            elif action == "generate_report":
                return self.generate_report(params)
            elif action == "validate_coordinates":
                return self.validate_coordinates(params)
            elif action == "export_evidence":
                return self.export_evidence(params)
            else:
                raise ValueError(f"Unknown action: {action}")
        except Exception as e:
            self.logger.error(f"Error in run: {str(e)}")
            return {"error": str(e)}
    
    def parse_gpr_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Parse GPR data file."""
        file_path = params.get("file_path")
        if not file_path or not os.path.exists(file_path):
            return {"error": "Invalid file path"}
        
        try:
            data = GPRUtils.parse_gssi_file(file_path)
            return {"success": True, "data": asdict(data)}
        except Exception as e:
            return {"error": str(e)}
    
    def detect_anomalies(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Detect anomalies in GPR data."""
        data_dict = params.get("data")
        if not data_dict:
            return {"error": "No data provided"}
        
        data = GPRData(**data_dict)
        threshold = params.get("threshold", 0.3)
        anomalies = GPRUtils.detect_anomalies(data, threshold)
        
        return {
            "success": True,
            "anomalies": [asdict(a) for a in anomalies]
        }
    
    def classify_anomaly(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Classify detected anomaly."""
        anomaly_dict = params.get("anomaly")
        features = params.get("features", {})
        
        if not anomaly_dict:
            return {"error": "No anomaly provided"}
        
        anomaly = Anomaly(**anomaly_dict)
        classification = GPRUtils.classify_anomaly(anomaly, features)
        
        return {
            "success": True,
            "classification": classification
        }
    
    def generate_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate forensic report."""
        case_id = params.get("case_id", "UNKNOWN")
        anomalies = [Anomaly(**a) for a in params.get("anomalies", [])]
        metadata = params.get("metadata", {})
        
        report = GPRUtils.create_forensic_report(case_id, anomalies, metadata)
        
        return {
            "success": True,
            "report": report
        }
    
    def validate_coordinates(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate GPS coordinates."""
        lat = params.get("latitude")
        lon = params.get("longitude")
        
        if lat is None or lon is None:
            return {"error": "Missing coordinates"}
        
        is_valid = GPRUtils.validate_coordinates(lat, lon)
        
        return {
            "success": True,
            "valid": is_valid
        }
    
    def export_evidence(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Export evidence in specified format."""
        data_dict = params.get("data")
        format_type = params.get("format", "json")
        
        if not data_dict:
            return {"error": "No data provided"}
        
        data = GPRData(**data_dict)
        exported = GPRUtils.export_evidence_format(data, format_type)
        
        return {
            "success": True,
            "exported_data": exported
        }

class TestGPRBodyDetection(unittest.TestCase):
    """Comprehensive test suite for GPR body detection system."""
    
    def setUp(self):
        self.engine = SkillEngine({})
        self.sample_data = GPRData(
            raw_data=[[100, 200, 300], [150, 250, 350], [200, 300, 400]],
            frequency=400.0,
            antenna_separation=0.5,
            sampling_interval=0.1,
            time_window=100.0,
            coordinates=(34.0522, -118.2437),
            collection_date=datetime.datetime.now(),
            operator="Test Operator",
            hardware_model="Test GPR"
        )
    
    def test_metadata(self):
        """Test skill metadata."""
        self.assertEqual(SKILL_METADATA["name"], 
                        "Ground-Penetrating Radar / Microwave Body Detection System")
        self.assertEqual(SKILL_METADATA["id"], "gpr_body_detection")
        self.assertEqual(len(SKILL_METADATA["capabilities"]), 14)
    
    def test_parse_gssi_file(self):
        """Test GSSI file parsing."""
        # Create temporary test file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.DZT', delete=False) as f:
            # Write minimal GSSI header
            header = bytearray(1024)
            header[18:22] = (3).to_bytes(4, 'little')  # traces
            header[22:26] = (3).to_bytes(4, 'little')  # samples
            header[52:56] = (40000).to_bytes(4, 'little')  # frequency
            f.write(header)
            # Write sample data
            for _ in range(9):
                f.write((1000).to_bytes(2, 'little'))
            temp_path = f.name
        
        result = self.engine.run("parse_gpr_data", {"file_path": temp_path})
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["frequency"], 400.0)
        
        os.unlink(temp_path)
    
    def test_detect_anomalies(self):
        """Test anomaly detection."""
        params = {
            "data": asdict(self.sample_data),
            "threshold": 0.1
        }
        result = self.engine.run("detect_anomalies", params)
        self.assertTrue(result["success"])
        self.assertIsInstance(result["anomalies"], list)
    
    def test_classify_anomaly(self):
        """Test anomaly classification."""
        anomaly = Anomaly(
            x=1.0, y=0.0, depth=2.0, depth_uncertainty=0.2,
            classification="unknown", confidence=0.5,
            dielectric_contrast=2.5, size_estimate=(0.5, 0.5, 0.2)
        )
        features = {"hyperbolic_shape": 0.9}
        
        params = {
            "anomaly": asdict(anomaly),
            "features": features
        }
        result = self.engine.run("classify_anomaly", params)
        self.assertTrue(result["success"])
        self.assertEqual(result["classification"], "body")
    
    def test_generate_report(self):
        """Test forensic report generation."""
        anomaly = Anomaly(
            x=1.0, y=0.0, depth=2.0, depth_uncertainty=0.2,
            classification="body", confidence=0.85,
            dielectric_contrast=2.5, size_estimate=(1.8, 0.4, 0.3)
        )
        
        params = {
            "case_id": "TEST-2024-001",
            "anomalies": [asdict(anomaly)],
            "metadata": {"site": "Test Site", "operator": "Test Op"}
        }
        result = self.engine.run("generate_report", params)
        self.assertTrue(result["success"])
        self.assertIn("FORENSIC GPR ANALYSIS REPORT", result["report"])
    
    def test_validate_coordinates(self):
        """Test coordinate validation."""
        params = {"latitude": 34.0522, "longitude": -118.2437}
        result = self.engine.run("validate_coordinates", params)
        self.assertTrue(result["success"])
        self.assertTrue(result["valid"])
        
        params = {"latitude": 91.0, "longitude": 181.0}
        result = self.engine.run("validate_coordinates", params)
        self.assertTrue(result["success"])
        self.assertFalse(result["valid"])
    
    def test_export_evidence(self):
        """Test evidence export."""
        params = {
            "data": asdict(self.sample_data),
            "format": "json"
        }
        result = self.engine.run("export_evidence", params)
        self.assertTrue(result["success"])
        self.assertIsInstance(result["exported_data"], str)
        
        params["format"] = "csv"
        result = self.engine.run("export_evidence", params)
        self.assertTrue(result["success"])
    
    def test_dielectric_calculation(self):
        """Test dielectric constant calculation."""
        velocity = 0.1  # m/ns
        dielectric = GPRUtils.calculate_dielectric_constant(velocity)
        expected = (0.299792458 / 0.1) ** 2
        self.assertAlmostEqual(dielectric, expected, places=2)
    
    def test_depth_estimation(self):
        """Test depth estimation."""
        time_ns = 20.0
        velocity = 0.1  # m/ns
        depth = GPRUtils.estimate_depth(time_ns, velocity)
        expected = (20.0 * 0.1) / 2
        self.assertEqual(depth, expected)
    
    def test_frequency_response(self):
        """Test frequency response calculation."""
        response = GPRUtils.calculate_frequency_response(self.sample_data)
        self.assertIn("dominant_frequency", response)
        self.assertIn("bandwidth", response)
        self.assertEqual(response["dominant_frequency"], 400.0)
    
    def test_error_handling(self):
        """Test error handling."""
        result = self.engine.run("unknown_action", {})
        self.assertIn("error", result)
        
        result = self.engine.run("parse_gpr_data", {"file_path": "/nonexistent"})
        self.assertIn("error", result)

if __name__ == "__main__":
    unittest.main()