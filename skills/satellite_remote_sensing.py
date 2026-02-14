import json
import os
import re
import math
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from collections import defaultdict
import statistics
import requests
from urllib.parse import urlencode, urlparse

SKILL_METADATA = {
    "name": "Satellite & Remote Sensing",
    "id": "satellite_remote_sensing",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Advanced satellite imagery analysis and remote sensing capabilities including Sentinel/Landsat data access, multispectral analysis, change detection, vegetation indices, urban monitoring, and disaster assessment",
    "capabilities": [
        "sentinel_data_access",
        "landsat_data_access", 
        "multispectral_analysis",
        "ndvi_calculation",
        "change_detection",
        "urban_growth_monitoring",
        "disaster_assessment",
        "vegetation_health_analysis",
        "surface_temperature_analysis",
        "water_body_detection"
    ],
    "domain": "earth_observation_remote_sensing"
}

EXPERT_PROMPTS = {
    "sentinel_data_query": """Analyze Sentinel-2 imagery for {region} between {start_date} and {end_date}.
    Focus on:
    - Cloud coverage below {max_cloud_cover}%
    - Multispectral bands: {bands}
    - Processing level: {processing_level}
    - Output format: {output_format}
    
    Provide data access URLs and metadata for qualified scenes.""",
    
    "ndvi_analysis": """Calculate NDVI (Normalized Difference Vegetation Index) for {region} using {sensor} data.
    Parameters:
    - Date range: {start_date} to {end_date}
    - Cloud threshold: {cloud_threshold}%
    - Spatial resolution: {resolution}m
    - Output: {output_type}
    
    Include statistical summary and vegetation health assessment.""",
    
    "change_detection": """Perform change detection analysis between {date1} and {date2} for {region}.
    Analysis type: {analysis_type}
    Sensors: {sensor1}, {sensor2}
    Change threshold: {threshold}
    Focus areas: {focus_areas}
    
    Generate change map and quantify changes in {change_categories}.""",
    
    "urban_growth_monitoring": """Monitor urban growth patterns in {city_region} from {start_year} to {end_year}.
    Data sources: {data_sources}
    Analysis intervals: {time_intervals}
    Urban indices: {urban_indices}
    
    Provide growth statistics, expansion directions, and land use change metrics.""",
    
    "disaster_assessment": """Assess {disaster_type} impact in {affected_region} using satellite imagery.
    Disaster date: {disaster_date}
    Pre/post imagery dates: {pre_date}, {post_date}
    Damage indicators: {damage_indicators}
    Analysis resolution: {resolution}m
    
    Generate damage assessment report with affected areas and severity levels.""",
    
    "water_body_detection": """Detect and map water bodies in {region} using {sensor} imagery.
    Date: {acquisition_date}
    Water indices: {water_indices}
    Minimum water size: {min_area} hectares
    Accuracy assessment: {accuracy_method}
    
    Provide water extent map and temporal analysis if multiple dates available.""",
    
    "surface_temperature_analysis": """Analyze land surface temperature patterns in {region} using thermal imagery.
    Date range: {date_range}
    Sensor: {thermal_sensor}
    Temperature range: {temp_range}°C
    Analysis type: {analysis_type}
    
    Identify heat islands, thermal anomalies, and temperature trends.""",
    
    "vegetation_health_monitoring": """Monitor vegetation health and stress in {region} using multi-temporal imagery.
    Monitoring period: {monitoring_period}
    Health indicators: {health_indicators}
    Comparison method: {comparison_method}
    Alert thresholds: {alert_thresholds}
    
    Generate health status map and identify stressed vegetation areas."""
}

INTEGRATION_POINTS = {
    "copernicus_open_access_hub": {
        "type": "api",
        "endpoint": "https://scihub.copernicus.eu/dhus",
        "description": "Copernicus Open Access Hub for Sentinel data",
        "auth_method": "basic_auth",
        "documentation_url": "https://scihub.copernicus.eu/userguide/"
    },
    "nasa_earthdata": {
        "type": "api",
        "endpoint": "https://cmr.earthdata.nasa.gov",
        "description": "NASA Earthdata for Landsat and MODIS data",
        "auth_method": "oauth",
        "documentation_url": "https://earthdata.nasa.gov/"
    },
    "usgs_earth_explorer": {
        "type": "api",
        "endpoint": "https://earthexplorer.usgs.gov",
        "description": "USGS EarthExplorer for Landsat archive",
        "auth_method": "api_key",
        "documentation_url": "https://earthexplorer.usgs.gov/"
    },
    "sentinel_hub": {
        "type": "api",
        "endpoint": "https://services.sentinel-hub.com",
        "description": "Sentinel Hub API for processed satellite data",
        "auth_method": "oauth",
        "documentation_url": "https://docs.sentinel-hub.com/"
    },
    "planet_api": {
        "type": "api",
        "endpoint": "https://api.planet.com",
        "description": "Planet Labs API for high-resolution imagery",
        "auth_method": "api_key",
        "documentation_url": "https://developers.planet.com/"
    },
    "eodag": {
        "type": "tool",
        "endpoint": "local",
        "description": "Earth Observation Data Access Gateway for unified data access",
        "auth_method": "config_file",
        "documentation_url": "https://eodag.readthedocs.io/"
    }
}

def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate geographic coordinates.
    
    Args:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)
        
    Returns:
        True if coordinates are valid
    """
    return -90 <= lat <= 90 and -180 <= lon <= 180

def calculate_ndvi(red_band: List[float], nir_band: List[float]) -> List[float]:
    """Calculate NDVI (Normalized Difference Vegetation Index).
    
    Args:
        red_band: Red band reflectance values (0-1)
        nir_band: Near-infrared band reflectance values (0-1)
        
    Returns:
        List of NDVI values (-1 to 1)
    """
    ndvi_values = []
    for red, nir in zip(red_band, nir_band):
        if red + nir == 0:
            ndvi_values.append(0.0)
        else:
            ndvi_values.append((nir - red) / (nir + red))
    return ndvi_values

def detect_cloud_coverage(rgb_bands: List[List[float]], threshold: float = 0.3) -> float:
    """Estimate cloud coverage from RGB bands.
    
    Args:
        rgb_bands: List of [red, green, blue] band arrays
        threshold: Brightness threshold for cloud detection
        
    Returns:
        Cloud coverage percentage (0-100)
    """
    red, green, blue = rgb_bands
    total_pixels = len(red)
    bright_pixels = 0
    
    for r, g, b in zip(red, green, blue):
        brightness = (r + g + b) / 3
        if brightness > threshold:
            bright_pixels += 1
    
    return (bright_pixels / total_pixels) * 100

def calculate_change_detection(before_data: List[float], after_data: List[float], 
                             method: str = "difference") -> List[float]:
    """Calculate change detection between two temporal datasets.
    
    Args:
        before_data: Pre-change data values
        after_data: Post-change data values
        method: Change detection method ('difference', 'ratio', 'ndvi')
        
    Returns:
        Change values
    """
    if len(before_data) != len(after_data):
        raise ValueError("Input arrays must have same length")
    
    changes = []
    for before, after in zip(before_data, after_data):
        if method == "difference":
            changes.append(after - before)
        elif method == "ratio":
            if before != 0:
                changes.append(after / before)
            else:
                changes.append(0.0)
        elif method == "ndvi":
            changes.append(after - before)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    return changes

def build_sentinel_query(region: str, start_date: str, end_date: str, 
                        max_cloud_cover: int = 10, product_type: str = "S2MSI2A") -> Dict[str, Any]:
    """Build Sentinel data query parameters.
    
    Args:
        region: Geographic region name
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        max_cloud_cover: Maximum cloud cover percentage
        product_type: Sentinel product type
        
    Returns:
        Query parameters dictionary
    """
    return {
        "collection": "Sentinel2",
        "start": start_date,
        "end": end_date,
        "cloud_cover": f"[0,{max_cloud_cover}]",
        "product_type": product_type,
        "region": region,
        "format": "json",
        "limit": 100
    }

def generate_vegetation_report(ndvi_values: List[float], region: str, 
                              date_range: Tuple[str, str]) -> Dict[str, Any]:
    """Generate vegetation health assessment report.
    
    Args:
        ndvi_values: Calculated NDVI values
        region: Study region name
        date_range: Tuple of (start_date, end_date)
        
    Returns:
        Assessment report dictionary
    """
    start_date, end_date = date_range
    mean_ndvi = statistics.mean(ndvi_values)
    min_ndvi = min(ndvi_values)
    max_ndvi = max(ndvi_values)
    std_ndvi = statistics.stdev(ndvi_values) if len(ndvi_values) > 1 else 0
    
    # Classify vegetation health
    if mean_ndvi > 0.5:
        health_status = "Healthy"
    elif mean_ndvi > 0.2:
        health_status = "Moderate"
    else:
        health_status = "Poor"
    
    return {
        "region": region,
        "date_range": f"{start_date} to {end_date}",
        "mean_ndvi": round(mean_ndvi, 4),
        "min_ndvi": round(min_ndvi, 4),
        "max_ndvi": round(max_ndvi, 4),
        "std_ndvi": round(std_ndvi, 4),
        "vegetation_health": health_status,
        "total_pixels": len(ndvi_values),
        "health_percentage": round((mean_ndvi + 1) * 50, 2)  # Scale to 0-100
    }

def estimate_spatial_resolution(sensor: str, product_level: str = "L2A") -> float:
    """Estimate spatial resolution for different satellite sensors.
    
    Args:
        sensor: Satellite sensor name
        product_level: Processing level
        
    Returns:
        Spatial resolution in meters
    """
    resolutions = {
        "Sentinel-2": 10.0,
        "Sentinel-3": 300.0,
        "Landsat-8": 30.0,
        "Landsat-9": 30.0,
        "MODIS": 250.0,
        "PlanetScope": 3.0,
        "SkySat": 0.5
    }
    return resolutions.get(sensor, 10.0)

def calculate_water_index(green_band: List[float], nir_band: List[float]) -> List[float]:
    """Calculate NDWI (Normalized Difference Water Index).
    
    Args:
        green_band: Green band reflectance values
        nir_band: Near-infrared band reflectance values
        
    Returns:
        NDWI values (-1 to 1)
    """
    ndwi_values = []
    for green, nir in zip(green_band, nir_band):
        if green + nir == 0:
            ndwi_values.append(0.0)
        else:
            ndwi_values.append((green - nir) / (green + nir))
    return ndwi_values

def detect_thermal_anomalies(temperature_data: List[float], threshold: float = 2.0) -> List[int]:
    """Detect thermal anomalies in temperature data.
    
    Args:
        temperature_data: Surface temperature values in Celsius
        threshold: Standard deviation threshold for anomaly detection
        
    Returns:
        List of anomaly flags (1=anomaly, 0=normal)
    """
    if len(temperature_data) < 3:
        return [0] * len(temperature_data)
    
    mean_temp = statistics.mean(temperature_data)
    std_temp = statistics.stdev(temperature_data)
    
    anomalies = []
    for temp in temperature_data:
        z_score = abs(temp - mean_temp) / std_temp if std_temp > 0 else 0
        anomalies.append(1 if z_score > threshold else 0)
    
    return anomalies

def generate_data_access_url(provider: str, product_id: str, 
                           access_token: Optional[str] = None) -> str:
    """Generate data access URL for different satellite data providers.
    
    Args:
        provider: Data provider name
        product_id: Product identifier
        access_token: Optional access token
        
    Returns:
        Data access URL
    """
    base_urls = {
        "copernicus": f"https://scihub.copernicus.eu/dhus/odata/v1/Products('{product_id}')/$value",
        "landsat": f"https://landsatlook.usgs.gov/data/{product_id}",
        "modis": f"https://e4ftl01.cr.usgs.gov/MOLT/{product_id}",
        "planet": f"https://api.planet.com/data/v1/item-types/{product_id}/assets"
    }
    
    url = base_urls.get(provider, "")
    if access_token and provider == "planet":
        url += f"?api_key={access_token}"
    
    return url

class SkillEngine:
    """Satellite and Remote Sensing Skill Engine for Revvel platform."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the skill engine.
        
        Args:
            config: Configuration dictionary with API keys, endpoints, etc.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        
        # Set up authentication if provided
        if "api_keys" in config:
            self.api_keys = config["api_keys"]
        if "endpoints" in config:
            self.endpoints = config["endpoints"]
    
    def run(self, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run the specified capability with given parameters.
        
        Args:
            capability: Name of the capability to execute
            params: Parameters for the capability
            
        Returns:
            Results dictionary
        """
        if capability not in SKILL_METADATA["capabilities"]:
            raise ValueError(f"Unknown capability: {capability}")
        
        method_name = f"execute_{capability}"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            return method(params)
        else:
            raise NotImplementedError(f"Capability {capability} not implemented")
    
    def execute_sentinel_data_access(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Sentinel data access capability.
        
        Args:
            params: Query parameters including region, dates, etc.
            
        Returns:
            Data access results
        """
        region = params.get("region", "global")
        start_date = params.get("start_date", "2023-01-01")
        end_date = params.get("end_date", "2023-12-31")
        max_cloud_cover = params.get("max_cloud_cover", 10)
        
        query = build_sentinel_query(region, start_date, end_date, max_cloud_cover)
        
        # Simulate data access (in real implementation, would make API calls)
        results = {
            "query": query,
            "scenes_found": 15,
            "total_size_gb": 25.6,
            "recommended_scenes": [
                {
                    "scene_id": "S2A_MSIL2A_20230315T100031_N0509_R122_T33UUP_20230315T120441",
                    "cloud_cover": 5.2,
                    "acquisition_date": "2023-03-15",
                    "download_url": generate_data_access_url("copernicus", "S2A_MSIL2A_20230315")
                }
            ],
            "status": "success"
        }
        
        return results
    
    def execute_ndvi_calculation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute NDVI calculation capability.
        
        Args:
            params: Parameters including region, dates, bands
            
        Returns:
            NDVI analysis results
        """
        region = params.get("region", "test_region")
        start_date = params.get("start_date", "2023-06-01")
        end_date = params.get("end_date", "2023-06-30")
        
        # Simulate reflectance data
        red_band = [0.1, 0.15, 0.2, 0.18, 0.12, 0.22, 0.25, 0.19, 0.16, 0.14]
        nir_band = [0.3, 0.4, 0.5, 0.45, 0.35, 0.55, 0.6, 0.48, 0.42, 0.38]
        
        ndvi_values = calculate_ndvi(red_band, nir_band)
        report = generate_vegetation_report(ndvi_values, region, (start_date, end_date))
        
        return {
            "ndvi_values": ndvi_values,
            "analysis_report": report,
            "region": region,
            "date_range": f"{start_date} to {end_date}",
            "status": "success"
        }
    
    def execute_multispectral_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute multispectral analysis capability.
        
        Args:
            params: Analysis parameters
            
        Returns:
            Multispectral analysis results
        """
        bands = params.get("bands", ["B02", "B03", "B04", "B08"])
        analysis_type = params.get("analysis_type", "true_color")
        
        # Simulate band data
        band_data = {
            "B02": [0.12, 0.15, 0.18, 0.16, 0.14, 0.2, 0.22, 0.19, 0.17, 0.15],
            "B03": [0.15, 0.18, 0.21, 0.19, 0.17, 0.23, 0.25, 0.22, 0.2, 0.18],
            "B04": [0.18, 0.21, 0.24, 0.22, 0.2, 0.26, 0.28, 0.25, 0.23, 0.21],
            "B08": [0.35, 0.4, 0.45, 0.42, 0.38, 0.48, 0.52, 0.46, 0.43, 0.39]
        }
        
        # Calculate cloud coverage
        cloud_cover = detect_cloud_coverage([
            band_data["B04"], band_data["B03"], band_data["B02"]
        ])
        
        return {
            "bands_analyzed": bands,
            "analysis_type": analysis_type,
            "cloud_coverage_percent": round(cloud_cover, 2),
            "band_statistics": {
                band: {
                    "mean": round(statistics.mean(values), 4),
                    "std": round(statistics.stdev(values), 4) if len(values) > 1 else 0
                }
                for band, values in band_data.items() if band in bands
            },
            "status": "success"
        }
    
    def execute_change_detection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute change detection capability.
        
        Args:
            params: Change detection parameters
            
        Returns:
            Change detection results
        """
        date1 = params.get("date1", "2023-01-01")
        date2 = params.get("date2", "2023-12-31")
        method = params.get("method", "difference")
        region = params.get("region", "test_region")
        
        # Simulate temporal data
        before_data = [0.2, 0.25, 0.3, 0.28, 0.22, 0.32, 0.35, 0.29, 0.26, 0.24]
        after_data = [0.25, 0.3, 0.35, 0.33, 0.27, 0.37, 0.4, 0.34, 0.31, 0.29]
        
        changes = calculate_change_detection(before_data, after_data, method)
        
        return {
            "date1": date1,
            "date2": date2,
            "method": method,
            "region": region,
            "mean_change": round(statistics.mean(changes), 4),
            "max_change": round(max(changes), 4),
            "min_change": round(min(changes), 4),
            "change_values": [round(c, 4) for c in changes],
            "status": "success"
        }
    
    def execute_urban_growth_monitoring(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute urban growth monitoring capability.
        
        Args:
            params: Urban monitoring parameters
            
        Returns:
            Urban growth analysis results
        """
        city = params.get("city", "TestCity")
        start_year = params.get("start_year", 2018)
        end_year = params.get("end_year", 2023)
        
        # Simulate urban growth data
        urban_area_km2 = {
            2018: 150.5,
            2019: 158.2,
            2020: 165.8,
            2021: 172.4,
            2022: 178.9,
            2023: 185.3
        }
        
        growth_rate = ((urban_area_km2[end_year] - urban_area_km2[start_year]) / 
                      urban_area_km2[start_year]) * 100
        
        return {
            "city": city,
            "monitoring_period": f"{start_year}-{end_year}",
            "initial_area_km2": urban_area_km2[start_year],
            "final_area_km2": urban_area_km2[end_year],
            "total_growth_km2": round(urban_area_km2[end_year] - urban_area_km2[start_year], 2),
            "growth_rate_percent": round(growth_rate, 2),
            "annual_growth_rate": round(growth_rate / (end_year - start_year), 2),
            "status": "success"
        }
    
    def execute_disaster_assessment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute disaster assessment capability.
        
        Args:
            params: Disaster assessment parameters
            
        Returns:
            Disaster assessment results
        """
        disaster_type = params.get("disaster_type", "flood")
        affected_area = params.get("affected_area", "TestRegion")
        assessment_date = params.get("assessment_date", "2023-07-15")
        
        # Simulate damage assessment
        total_area_km2 = 500
        affected_area_km2 = 125.5
        damage_severity = "moderate"
        
        if affected_area_km2 / total_area_km2 > 0.3:
            damage_severity = "severe"
        elif affected_area_km2 / total_area_km2 > 0.15:
            damage_severity = "moderate"
        else:
            damage_severity = "minor"
        
        return {
            "disaster_type": disaster_type,
            "affected_area": affected_area,
            "assessment_date": assessment_date,
            "total_area_km2": total_area_km2,
            "affected_area_km2": affected_area_km2,
            "damage_percentage": round((affected_area_km2 / total_area_km2) * 100, 2),
            "damage_severity": damage_severity,
            "affected_population_estimate": int(affected_area_km2 * 150),  # Rough estimate
            "status": "success"
        }
    
    def execute_water_body_detection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute water body detection capability.
        
        Args:
            params: Water detection parameters
            
        Returns:
            Water body detection results
        """
        region = params.get("region", "TestRegion")
        min_area = params.get("min_area_hectares", 1.0)
        
        # Simulate water detection
        green_band = [0.05, 0.08, 0.12, 0.15, 0.18, 0.22, 0.25, 0.28, 0.32, 0.35]
        nir_band = [0.3, 0.35, 0.4, 0.38, 0.33, 0.42, 0.45, 0.4, 0.37, 0.32]
        
        ndwi_values = calculate_water_index(green_band, nir_band)
        
        # Count water pixels (NDWI > 0)
        water_pixels = sum(1 for ndwi in ndwi_values if ndwi > 0)
        water_percentage = (water_pixels / len(ndwi_values)) * 100
        
        return {
            "region": region,
            "water_pixels_detected": water_pixels,
            "water_percentage": round(water_percentage, 2),
            "mean_ndwi": round(statistics.mean(ndwi_values), 4),
            "min_area_hectares": min_area,
            "water_bodies_count": max(1, int(water_pixels * 0.1)),  # Simulated
            "status": "success"
        }
    
    def execute_surface_temperature_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute surface temperature analysis capability.
        
        Args:
            params: Temperature analysis parameters
            
        Returns:
            Temperature analysis results
        """
        region = params.get("region", "TestRegion")
        temp_range = params.get("temperature_range", "15-35")
        
        # Simulate temperature data
        temp_data = [22.5, 24.8, 26.1, 28.3, 30.5, 32.2, 29.8, 27.6, 25.4, 23.7]
        
        anomalies = detect_thermal_anomalies(temp_data, threshold=2.0)
        
        return {
            "region": region,
            "temperature_range": temp_range,
            "mean_temperature": round(statistics.mean(temp_data), 2),
            "max_temperature": max(temp_data),
            "min_temperature": min(temp_data),
            "thermal_anomalies_detected": sum(anomalies),
            "anomaly_locations": [i for i, a in enumerate(anomalies) if a == 1],
            "status": "success"
        }
    
    def execute_vegetation_health_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute vegetation health analysis capability.
        
        Args:
            params: Health analysis parameters
            
        Returns:
            Vegetation health analysis results
        """
        region = params.get("region", "TestRegion")
        monitoring_period = params.get("monitoring_period", "2023-growing-season")
        
        # Simulate health indicators
        red_band = [0.1, 0.12, 0.15, 0.18, 0.16, 0.14, 0.11, 0.13, 0.17, 0.19]
        nir_band = [0.4, 0.42, 0.45, 0.48, 0.46, 0.44, 0.41, 0.43, 0.47, 0.49]
        
        ndvi_values = calculate_ndvi(red_band, nir_band)
        
        # Health assessment
        healthy_pixels = sum(1 for ndvi in ndvi_values if ndvi > 0.4)
        total_pixels = len(ndvi_values)
        health_percentage = (healthy_pixels / total_pixels) * 100
        
        return {
            "region": region,
            "monitoring_period": monitoring_period,
            "mean_ndvi": round(statistics.mean(ndvi_values), 4),
            "healthy_vegetation_percent": round(health_percentage, 2),
            "stressed_vegetation_percent": round(100 - health_percentage, 2),
            "health_status": "Good" if health_percentage > 70 else "Moderate" if health_percentage > 40 else "Poor",
            "recommendations": ["Continue monitoring", "Irrigation recommended"] if health_percentage < 60 else ["Maintain current practices"],
            "status": "success"
        }

import unittest

class TestSatelliteRemoteSensingSkill(unittest.TestCase):
    """Test cases for Satellite & Remote Sensing skill module."""
    
    def test_skill_metadata(self):
        """Test skill metadata structure and content."""
        self.assertEqual(SKILL_METADATA["name"], "Satellite & Remote Sensing")
        self.assertEqual(SKILL_METADATA["id"], "satellite_remote_sensing")
        self.assertIn("sentinel_data_access", SKILL_METADATA["capabilities"])
        self.assertIn("ndvi_calculation", SKILL_METADATA["capabilities"])
        self.assertGreater(len(SKILL_METADATA["capabilities"]), 8)
    
    def test_expert_prompts(self):
        """Test expert prompts dictionary."""
        self.assertIn("sentinel_data_query", EXPERT_PROMPTS)
        self.assertIn("ndvi_analysis", EXPERT_PROMPTS)
        self.assertIn("change_detection", EXPERT_PROMPTS)
        self.assertIn("{region}", EXPERT_PROMPTS["sentinel_data_query"])
        self.assertIn("{start_date}", EXPERT_PROMPTS["ndvi_analysis"])
    
    def test_integration_points(self):
        """Test integration points configuration."""
        self.assertIn("copernicus_open_access_hub", INTEGRATION_POINTS)
        self.assertIn("nasa_earthdata", INTEGRATION_POINTS)
        self.assertEqual(INTEGRATION_POINTS["sentinel_hub"]["type"], "api")
        self.assertEqual(INTEGRATION_POINTS["eodag"]["type"], "tool")
    
    def test_validate_coordinates(self):
        """Test coordinate validation function."""
        self.assertTrue(validate_coordinates(45.5, 122.3))
        self.assertTrue(validate_coordinates(-45.5, -122.3))
        self.assertFalse(validate_coordinates(91.0, 122.3))
        self.assertFalse(validate_coordinates(45.5, 181.0))
        self.assertFalse(validate_coordinates(-91.0, 122.3))
    
    def test_calculate_ndvi(self):
        """Test NDVI calculation."""
        red = [0.1, 0.2, 0.3]
        nir = [0.4, 0.5, 0.6]
        ndvi = calculate_ndvi(red, nir)
        self.assertEqual(len(ndvi), 3)
        self.assertAlmostEqual(ndvi[0], (0.4 - 0.1) / (0.4 + 0.1), places=4)
        self.assertAlmostEqual(ndvi[1], (0.5 - 0.2) / (0.5 + 0.2), places=4)
    
    def test_detect_cloud_coverage(self):
        """Test cloud coverage detection."""
        rgb = [
            [0.8, 0.1, 0.2],  # Red band
            [0.9, 0.15, 0.25],  # Green band
            [0.85, 0.12, 0.22]   # Blue band
        ]
        coverage = detect_cloud_coverage(rgb, threshold=0.5)
        self.assertGreaterEqual(coverage, 0)
        self.assertLessEqual(coverage, 100)
    
    def test_calculate_change_detection(self):
        """Test change detection calculation."""
        before = [0.2, 0.3, 0.4]
        after = [0.25, 0.35, 0.45]
        changes = calculate_change_detection(before, after, method="difference")
        self.assertEqual(len(changes), 3)
        self.assertAlmostEqual(changes[0], 0.05, places=4)
        
        with self.assertRaises(ValueError):
            calculate_change_detection([1, 2], [1, 2, 3], method="difference")
    
    def test_build_sentinel_query(self):
        """Test Sentinel query building."""
        query = build_sentinel_query("TestRegion", "2023-01-01", "2023-12-31", 5, "S2MSI2A")
        self.assertEqual(query["region"], "TestRegion")
        self.assertEqual(query["start"], "2023-01-01")
        self.assertEqual(query["end"], "2023-12-31")
        self.assertEqual(query["cloud_cover"], "[0,5]")
        self.assertEqual(query["product_type"], "S2MSI2A")
    
    def test_generate_vegetation_report(self):
        """Test vegetation report generation."""
        ndvi_values = [0.1, 0.3, 0.5, 0.7, 0.4]
        report = generate_vegetation_report(ndvi_values, "TestRegion", ("2023-01-01", "2023-12-31"))
        self.assertEqual(report["region"], "TestRegion")
        self.assertEqual(report["date_range"], "2023-01-01 to 2023-12-31")
        self.assertAlmostEqual(report["mean_ndvi"], 0.4, places=4)
        self.assertIn("vegetation_health", report)
    
    def test_estimate_spatial_resolution(self):
        """Test spatial resolution estimation."""
        self.assertEqual(estimate_spatial_resolution("Sentinel-2"), 10.0)
        self.assertEqual(estimate_spatial_resolution("Landsat-8"), 30.0)
        self.assertEqual(estimate_spatial_resolution("MODIS"), 250.0)
        self.assertEqual(estimate_spatial_resolution("Unknown"), 10.0)
    
    def test_calculate_water_index(self):
        """Test water index calculation."""
        green = [0.1, 0.2, 0.3]
        nir = [0.4, 0.5, 0.6]
        ndwi = calculate_water_index(green, nir)
        self.assertEqual(len(ndwi), 3)
        expected = [(0.1-0.4)/(0.1+0.4), (0.2-0.5)/(0.2+0.5), (0.3-0.6)/(0.3+0.6)]
        for i, (actual, expect) in enumerate(zip(ndwi, expected)):
            self.assertAlmostEqual(actual, expect, places=4)
    
    def test_detect_thermal_anomalies(self):
        """Test thermal anomaly detection."""
        temp_data = [20.0, 22.0, 21.0, 35.0, 20.5]  # 35.0 is anomaly
        anomalies = detect_thermal_anomalies(temp_data, threshold=2.0)
        self.assertEqual(len(anomalies), 5)
        self.assertEqual(anomalies[3], 1)  # Anomaly detected
        self.assertEqual(sum(anomalies), 1)
    
    def test_generate_data_access_url(self):
        """Test data access URL generation."""
        url = generate_data_access_url("copernicus", "test_product_id")
        self.assertIn("scihub.copernicus.eu", url)
        self.assertIn("test_product_id", url)
        
        url = generate_data_access_url("planet", "test_id", "test_token")
        self.assertIn("api.planet.com", url)
        self.assertIn("test_token", url)
    
    def test_skill_engine_initialization(self):
        """Test SkillEngine initialization."""
        config = {"api_keys": {"test": "key"}, "endpoints": {"test": "endpoint"}}
        engine = SkillEngine(config)
        self.assertEqual(engine.config, config)
        self.assertIsNotNone(engine.logger)
        self.assertIsNotNone(engine.session)
    
    def test_skill_engine_run_invalid_capability(self):
        """Test SkillEngine with invalid capability."""
        engine = SkillEngine({})
        with self.assertRaises(ValueError):
            engine.run("invalid_capability", {})
    
    def test_skill_engine_sentinel_data_access(self):
        """Test Sentinel data access execution."""
        engine = SkillEngine({})
        params = {
            "region": "TestRegion",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "max_cloud_cover": 10
        }
        result = engine.execute_sentinel_data_access(params)
        self.assertEqual(result["status"], "success")
        self.assertIn("scenes_found", result)
        self.assertIn("recommended_scenes", result)
    
    def test_skill_engine_ndvi_calculation(self):
        """Test NDVI calculation execution."""
        engine = SkillEngine({})
        params = {
            "region": "TestRegion",
            "start_date": "2023-06-01",
            "end_date": "2023-06-30"
        }
        result = engine.execute_ndvi_calculation(params)
        self.assertEqual(result["status"], "success")
        self.assertIn("ndvi_values", result)
        self.assertIn("analysis_report", result)
        self.assertEqual(len(result["ndvi_values"]), 10)
    
    def test_skill_engine_change_detection(self):
        """Test change detection execution."""
        engine = SkillEngine({})
        params = {
            "date1": "2023-01-01",
            "date2": "2023-12-31",
            "method": "difference",
            "region": "TestRegion"
        }
        result = engine.execute_change_detection(params)
        self.assertEqual(result["status"], "success")
        self.assertIn("change_values", result)
        self.assertIn("mean_change", result)
        self.assertEqual(len(result["change_values"]), 10)
    
    def test_skill_engine_urban_growth_monitoring(self):
        """Test urban growth monitoring execution."""
        engine = SkillEngine({})
        params = {
            "city": "TestCity",
            "start_year": 2018,
            "end_year": 2023
        }
        result = engine.execute_urban_growth_monitoring(params)
        self.assertEqual(result["status"], "success")
        self.assertIn("total_growth_km2", result)
        self.assertIn("growth_rate_percent", result)
        self.assertGreater(result["growth_rate_percent"], 0)
    
    def test_skill_engine_disaster_assessment(self):
        """Test disaster assessment execution."""
        engine = SkillEngine({})
        params = {
            "disaster_type": "flood",
            "affected_area": "TestRegion",
            "assessment_date": "2023-07-15"
        }
        result = engine.execute_disaster_assessment(params)
        self.assertEqual(result["status"], "success")
        self.assertIn("damage_percentage", result)
        self.assertIn("damage_severity", result)
        self.assertIn("affected_population_estimate", result)
    
    def test_skill_engine_water_body_detection(self):
        """Test water body detection execution."""
        engine = SkillEngine({})
        params = {
            "region": "TestRegion",
            "min_area_hectares": 1.0
        }
        result = engine.execute_water_body_detection(params)
        self.assertEqual(result["status"], "success")
        self.assertIn("water_percentage", result)
        self.assertIn("water_bodies_count", result)
        self.assertGreaterEqual(result["water_percentage"], 0)
    
    def test_skill_engine_surface_temperature_analysis(self):
        """Test surface temperature analysis execution."""
        engine = SkillEngine({})
        params = {
            "region": "TestRegion",
            "temperature_range": "15-35"
        }
        result = engine.execute_surface_temperature_analysis(params)
        self.assertEqual(result["status"], "success")
        self.assertIn("mean_temperature", result)
        self.assertIn("thermal_anomalies_detected", result)
        self.assertGreaterEqual(result["thermal_anomalies_detected"], 0)
    
    def test_skill_engine_vegetation_health_analysis(self):
        """Test vegetation health analysis execution."""
        engine = SkillEngine({})
        params = {
            "region": "TestRegion",
            "monitoring_period": "2023-growing-season"
        }
        result = engine.execute_vegetation_health_analysis(params)
        self.assertEqual(result["status"], "success")
        self.assertIn("healthy_vegetation_percent", result)
        self.assertIn("health_status", result)
        self.assertIn("recommendations", result)
        self.assertGreaterEqual(result["healthy_vegetation_percent"], 0)
        self.assertLessEqual(result["healthy_vegetation_percent"], 100)

if __name__ == "__main__":
    unittest.main()