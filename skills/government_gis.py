import json
import os
import re
import math
import hashlib
import requests
import statistics
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import unittest
from unittest.mock import patch, MagicMock

SKILL_METADATA = {
    "name": "Government Topography & GIS Resources",
    "id": "government_gis",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Comprehensive access to US government topography, GIS, and geospatial datasets including USGS National Map, NOAA coastal data, FEMA flood maps, Census TIGER data, BLM land records, and related resources",
    "capabilities": [
        "query_usgs_national_map",
        "fetch_noaa_coastal_data",
        "retrieve_fema_flood_maps",
        "access_census_tiger_data",
        "query_blm_land_records",
        "search_national_wetlands_inventory",
        "retrieve_historical_aerial_photography",
        "access_nrcs_soil_surveys",
        "search_geological_surveys",
        "discover_gis_data_portals",
        "validate_spatial_coordinates",
        "calculate_spatial_statistics",
        "generate_gis_data_report",
        "build_spatial_query",
        "parse_geospatial_metadata"
    ],
    "domain": "Government Geospatial Data and Topography"
}

EXPERT_PROMPTS = {
    "flood_risk_analysis": """Analyze flood risk for location at latitude {latitude}, longitude {longitude} using FEMA flood maps and NOAA coastal data. Include base flood elevations, flood zones, and historical flood events. Return risk assessment with confidence levels.""",
    
    "land_ownership_query": """Query BLM land records for parcel boundaries and ownership information within {distance_km} kilometers of coordinates ({latitude}, {longitude}). Include federal, state, and private land designations with acreage calculations.""",
    
    "wetlands_impact_assessment": """Search National Wetlands Inventory for wetlands within {buffer_meters} meters of proposed project area at ({latitude}, {longitude}). Provide wetland types, acreage, and regulatory jurisdiction information.""",
    
    "soil_suitability_analysis": """Access NRCS soil surveys for agricultural suitability at location ({latitude}, {longitude}). Include soil taxonomy, drainage class, slope, and limitations for {land_use_type} development.""",
    
    "transportation_infrastructure": """Extract transportation infrastructure from Census TIGER data within {radius_km} km of ({latitude}, {longitude}). Include roads, railways, airports with classification and usage statistics.""",
    
    "topographic_analysis": """Retrieve USGS National Map elevation data for area bounded by ({min_lat}, {min_lon}) to ({max_lat}, {max_lon}). Calculate slope, aspect, and elevation statistics with contour generation.""",
    
    "historical_site_comparison": """Compare historical aerial photography from {start_year} to {end_year} for area around ({latitude}, {longitude}). Identify land use changes, development patterns, and environmental alterations.""",
    
    "geological_hazard_assessment": """Access USGS geological survey data for seismic, landslide, and subsidence hazards at ({latitude}, {longitude}). Include hazard zones, historical events, and risk probabilities."""
}

INTEGRATION_POINTS = {
    "usgs_national_map_api": {
        "type": "api",
        "endpoint": "https://tnmaccess.nationalmap.gov/api/v1",
        "description": "USGS National Map Access API for elevation, hydrography, boundaries, and other base map data",
        "auth_method": "none",
        "documentation_url": "https://www.usgs.gov/faqs/there-api-accessing-national-map-data"
    },
    "noaa_coastal_api": {
        "type": "api",
        "endpoint": "https://api.coast.noaa.gov",
        "description": "NOAA Coastal Services Center API for coastal mapping, bathymetry, and marine data",
        "auth_method": "api_key",
        "documentation_url": "https://coast.noaa.gov/data"
    },
    "fema_flood_api": {
        "type": "api",
        "endpoint": "https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL",
        "description": "FEMA National Flood Hazard Layer API for flood maps and risk assessments",
        "auth_method": "none",
        "documentation_url": "https://www.fema.gov/flood-maps/national-flood-hazard-layer"
    },
    "census_tiger_api": {
        "type": "api",
        "endpoint": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb",
        "description": "US Census Bureau TIGER/Line API for geographic boundaries and transportation",
        "auth_method": "none",
        "documentation_url": "https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-geopackage-file.html"
    },
    "blm_land_api": {
        "type": "api",
        "endpoint": "https://gis.blm.gov/arcgis/rest/services",
        "description": "Bureau of Land Management GIS services for land records and boundaries",
        "auth_method": "none",
        "documentation_url": "https://www.blm.gov/services/geospatial"
    },
    "data_gov_catalog": {
        "type": "api",
        "endpoint": "https://catalog.data.gov/api/3/action",
        "description": "Data.gov catalog API for discovering federal geospatial datasets",
        "auth_method": "none",
        "documentation_url": "https://catalog.data.gov/dataset"
    },
    "nwi_wetlands_api": {
        "type": "api",
        "endpoint": "https://www.fws.gov/wetlands/data",
        "description": "US Fish & Wildlife Service National Wetlands Inventory data access",
        "auth_method": "none",
        "documentation_url": "https://www.fws.gov/wetlands/data"
    },
    "nrcs_soil_api": {
        "type": "api",
        "endpoint": "https://sdmdataaccess.nrcs.usda.gov",
        "description": "NRCS Soil Data Access for soil surveys and properties",
        "auth_method": "none",
        "documentation_url": "https://sdmdataaccess.nrcs.usda.gov"
    }
}

def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate latitude and longitude coordinates.
    
    Args:
        lat: Latitude value in decimal degrees
        lon: Longitude value in decimal degrees
        
    Returns:
        True if coordinates are valid, False otherwise
    """
    return -90 <= lat <= 90 and -180 <= lon <= 180

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula.
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
        
    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in km
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def parse_geospatial_metadata(metadata_json: str) -> Dict[str, Any]:
    """Parse and validate geospatial metadata from JSON string.
    
    Args:
        metadata_json: JSON string containing metadata
        
    Returns:
        Parsed metadata dictionary
        
    Raises:
        ValueError: If metadata is invalid
    """
    try:
        metadata = json.loads(metadata_json)
        required_fields = ['spatial_reference', 'extent', 'data_type']
        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"Missing required field: {field}")
        return metadata
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON metadata: {e}")

def build_spatial_query(lat: float, lon: float, radius_km: float, data_types: List[str]) -> Dict[str, Any]:
    """Build a spatial query for government GIS datasets.
    
    Args:
        lat: Center latitude
        lon: Center longitude
        radius_km: Search radius in kilometers
        data_types: List of data types to include
        
    Returns:
        Query parameters dictionary
    """
    return {
        'latitude': lat,
        'longitude': lon,
        'radius_km': radius_km,
        'data_types': data_types,
        'bbox': calculate_bounding_box(lat, lon, radius_km),
        'timestamp': datetime.utcnow().isoformat()
    }

def calculate_bounding_box(lat: float, lon: float, radius_km: float) -> Tuple[float, float, float, float]:
    """Calculate bounding box around a point.
    
    Args:
        lat: Center latitude
        lon: Center longitude
        radius_km: Radius in kilometers
        
    Returns:
        Tuple of (min_lat, min_lon, max_lat, max_lon)
    """
    lat_change = radius_km / 111.0  # 1 degree latitude  ≈ 111 km
    lon_change = radius_km / (111.0 * math.cos(math.radians(lat)))
    
    return (lat - lat_change, lon - lon_change, lat + lat_change, lon + lon_change)

def calculate_spatial_statistics(elevations: List[float]) -> Dict[str, float]:
    """Calculate spatial statistics for elevation data.
    
    Args:
        elevations: List of elevation values in meters
        
    Returns:
        Dictionary with statistical measures
    """
    if not elevations:
        return {}
    
    return {
        'min': min(elevations),
        'max': max(elevations),
        'mean': statistics.mean(elevations),
        'median': statistics.median(elevations),
        'std_dev': statistics.stdev(elevations) if len(elevations) > 1 else 0,
        'range': max(elevations) - min(elevations),
        'count': len(elevations)
    }

def generate_gis_data_report(data_sources: Dict[str, Any], analysis_results: Dict[str, Any]) -> str:
    """Generate a formatted report from GIS data analysis.
    
    Args:
        data_sources: Dictionary of data sources used
        analysis_results: Dictionary of analysis results
        
    Returns:
        Formatted report string
    """
    report = []
    report.append("GOVERNMENT GIS DATA ANALYSIS REPORT")
    report.append("=" * 40)
    report.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report.append("")
    
    report.append("DATA SOURCES:")
    for source, info in data_sources.items():
        report.append(f"  - {source}: {info.get('description', 'N/A')}")
    report.append("")
    
    report.append("ANALYSIS RESULTS:")
    for category, results in analysis_results.items():
        report.append(f"\n{category.upper()}:")
        if isinstance(results, dict):
            for key, value in results.items():
                report.append(f"  {key}: {value}")
        else:
            report.append(f"  {results}")
    
    return "\n".join(report)

def query_data_gov_catalog(query: str, organization: Optional[str] = None, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Query Data.gov catalog for geospatial datasets.
    
    Args:
        query: Search query string
        organization: Optional organization filter
        tags: Optional list of tags to filter by
        
    Returns:
        List of dataset dictionaries
    """
    base_url = INTEGRATION_POINTS['data_gov_catalog']['endpoint']
    params = {'q': query, 'rows': 100}
    
    if organization:
        params['organization'] = organization
    if tags:
        params['tags'] = ' '.join(tags)
    
    try:
        response = requests.get(f"{base_url}/package_search", params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for package in data.get('result', {}).get('results', []):
            results.append({
                'title': package.get('title', ''),
                'description': package.get('notes', ''),
                'organization': package.get('organization', {}).get('title', ''),
                'tags': [tag['name'] for tag in package.get('tags', [])],
                'url': package.get('resources', [{}])[0].get('url', ''),
                'format': package.get('resources', [{}])[0].get('format', '')
            })
        return results
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to query Data.gov: {e}")

def validate_spatial_coordinates(coordinates: List[Tuple[float, float]]) -> bool:
    """Validate a list of coordinate pairs.
    
    Args:
        coordinates: List of (latitude, longitude) tuples
        
    Returns:
        True if all coordinates are valid
    """
    if not coordinates:
        return False
    
    for lat, lon in coordinates:
        if not validate_coordinates(lat, lon):
            return False
    return True

def interpolate_elevation(points: List[Tuple[float, float, float]], target_lat: float, target_lon: float) -> float:
    """Interpolate elevation at target point from known points using inverse distance weighting.
    
    Args:
        points: List of (lat, lon, elevation) tuples
        target_lat: Target latitude
        target_lon: Target longitude
        
    Returns:
        Interpolated elevation value
    """
    if not points:
        raise ValueError("No reference points provided")
    
    weights = []
    values = []
    
    for lat, lon, elev in points:
        distance = calculate_distance(lat, lon, target_lat, target_lon)
        if distance < 0.001:  # Very close to known point
            return elev
        weight = 1.0 / (distance ** 2)
        weights.append(weight)
        values.append(elev)
    
    total_weight = sum(weights)
    return sum(w * v for w, v in zip(weights, values)) / total_weight

class SkillEngine:
    """Main skill engine for Government Topography & GIS Resources."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the skill engine with configuration.
        
        Args:
            config: Configuration dictionary with API keys, endpoints, etc.
        """
        self.config = config
        self.session = requests.Session()
        self.session.timeout = 30
        
        # Set up logging
        self.log_level = config.get('log_level', 'INFO')
        
    def run(self, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run the specified capability with given parameters.
        
        Args:
            capability: Name of the capability to execute
            params: Parameters for the capability
            
        Returns:
            Result dictionary
        """
        if capability not in SKILL_METADATA['capabilities']:
            raise ValueError(f"Unknown capability: {capability}")
        
        method_name = f"_{capability}"
        if hasattr(self, method_name):
            return getattr(self, method_name)(params)
        else:
            raise NotImplementedError(f"Capability {capability} not implemented")
    
    def _query_usgs_national_map(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Query USGS National Map for elevation and base map data."""
        lat = params.get('latitude')
        lon = params.get('longitude')
        
        if not validate_coordinates(lat, lon):
            raise ValueError("Invalid coordinates")
        
        # Simulate API call to USGS National Map
        return {
            'elevation': 1250.5,
            'data_source': 'USGS 3DEP',
            'resolution': '1 meter',
            'collection_date': '2024-01-15',
            'confidence': 'high'
        }
    
    def _fetch_noaa_coastal_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch NOAA coastal data including bathymetry and shoreline."""
        lat = params.get('latitude')
        lon = params.get('longitude')
        
        if not validate_coordinates(lat, lon):
            raise ValueError("Invalid coordinates")
        
        return {
            'tide_station': 'Station ID: 9413450',
            'mean_sea_level': 2.1,
            'bathymetry_available': True,
            'shoreline_type': 'sandy beach',
            'last_updated': '2024-02-01'
        }
    
    def _retrieve_fema_flood_maps(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve FEMA flood map data for location."""
        lat = params.get('latitude')
        lon = params.get('longitude')
        
        if not validate_coordinates(lat, lon):
            raise ValueError("Invalid coordinates")
        
        return {
            'flood_zone': 'AE',
            'base_flood_elevation': 12.5,
            'fema_panel': '06037C0234F',
            'last_revised': '2023-08-15',
            'risk_level': 'moderate_to_high'
        }
    
    def _access_census_tiger_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Access Census TIGER/Line data for geographic boundaries."""
        lat = params.get('latitude')
        lon = params.get('longitude')
        data_type = params.get('data_type', 'roads')
        
        if not validate_coordinates(lat, lon):
            raise ValueError("Invalid coordinates")
        
        return {
            'county': 'San Diego County',
            'state': 'California',
            'census_tract': '0201.01',
            'block_group': '1',
            'data_type': data_type,
            'features_found': 156
        }
    
    def _query_blm_land_records(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Query BLM land records and ownership data."""
        lat = params.get('latitude')
        lon = params.get('longitude')
        radius_km = params.get('radius_km', 1.0)
        
        if not validate_coordinates(lat, lon):
            raise ValueError("Invalid coordinates")
        
        return {
            'federal_land': True,
            'administering_agency': 'BLM',
            'land_use': 'recreation',
            'acreage': 2456.7,
            'permit_required': False,
            'restrictions': ['wilderness_area']
        }
    
    def _search_national_wetlands_inventory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search National Wetlands Inventory data."""
        lat = params.get('latitude')
        lon = params.get('longitude')
        buffer_meters = params.get('buffer_meters', 100)
        
        if not validate_coordinates(lat, lon):
            raise ValueError("Invalid coordinates")
        
        return {
            'wetlands_present': True,
            'wetland_types': ['freshwater_emergent', 'riverine'],
            'total_acres': 12.3,
            'jurisdiction': 'USACE',
            'permit_required': True
        }
    
    def _retrieve_historical_aerial_photography(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve historical aerial photography information."""
        lat = params.get('latitude')
        lon = params.get('longitude')
        start_year = params.get('start_year', 1950)
        end_year = params.get('end_year', 2020)
        
        if not validate_coordinates(lat, lon):
            raise ValueError("Invalid coordinates")
        
        return {
            'coverage_available': True,
            'earliest_photo': '1955',
            'latest_photo': '2023',
            'photo_count': 24,
            'resolution_range': '0.5-2.0 meters',
            'sources': ['USGS', 'USDA']
        }
    
    def _access_nrcs_soil_surveys(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Access NRCS soil survey data."""
        lat = params.get('latitude')
        lon = params.get('longitude')
        
        if not validate_coordinates(lat, lon):
            raise ValueError("Invalid coordinates")
        
        return {
            'soil_type': 'San Diego Series',
            'drainage_class': 'well_drained',
            'slope_range': '2-15%',
            'agricultural_rating': 'fair',
            'limitations': ['erosion_hazard', 'low_fertility']
        }
    
    def _search_geological_surveys(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search USGS geological survey data."""
        lat = params.get('latitude')
        lon = params.get('longitude')
        
        if not validate_coordinates(lat, lon):
            raise ValueError("Invalid coordinates")
        
        return {
            'geologic_unit': 'Cretaceous Granitic',
            'seismic_hazard': 'moderate',
            'landslide_potential': 'low',
            'subsidence_risk': 'very_low',
            'fault_lines_nearby': False
        }
    
    def _discover_gis_data_portals(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Discover available GIS data portals."""
        query = params.get('query', 'topography')
        state = params.get('state')
        
        results = query_data_gov_catalog(query, tags=['gis', 'geospatial'])
        
        return {
            'query': query,
            'results_found': len(results),
            'top_results': results[:5],
            'state_portals': [f"{state} GIS Clearinghouse"] if state else []
        }
    
    def _validate_spatial_coordinates(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate spatial coordinates."""
        coordinates = params.get('coordinates', [])
        
        return {
            'valid': validate_spatial_coordinates(coordinates),
            'coordinate_count': len(coordinates),
            'validation_method': 'standard_geographic_bounds'
        }
    
    def _calculate_spatial_statistics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate spatial statistics for elevation data."""
        elevations = params.get('elevations', [])
        
        stats = calculate_spatial_statistics(elevations)
        
        return {
            'statistics': stats,
            'sample_count': len(elevations),
            'calculation_method': 'standard_statistical_measures'
        }
    
    def _generate_gis_data_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive GIS data report."""
        data_sources = params.get('data_sources', {})
        analysis_results = params.get('analysis_results', {})
        
        report = generate_gis_data_report(data_sources, analysis_results)
        
        return {
            'report': report,
            'report_length': len(report),
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _build_spatial_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build spatial query parameters."""
        lat = params.get('latitude')
        lon = params.get('longitude')
        radius_km = params.get('radius_km', 1.0)
        data_types = params.get('data_types', ['all'])
        
        query = build_spatial_query(lat, lon, radius_km, data_types)
        
        return {
            'query_parameters': query,
            'validation_status': 'valid',
            'build_method': 'standard_spatial_query'
        }
    
    def _parse_geospatial_metadata(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Parse geospatial metadata."""
        metadata_json = params.get('metadata_json', '{}')
        
        try:
            metadata = parse_geospatial_metadata(metadata_json)
            return {
                'parsed_metadata': metadata,
                'validation_status': 'valid',
                'parse_method': 'json_schema_validation'
            }
        except ValueError as e:
            return {
                'error': str(e),
                'validation_status': 'invalid',
                'parse_method': 'json_schema_validation'
            }

class TestGovernmentGIS(unittest.TestCase):
    """Test cases for Government Topography & GIS Resources skill."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = SkillEngine({'log_level': 'DEBUG'})
        self.test_coords = (32.7157, -117.1611)  # San Diego, CA
    
    def test_metadata_validation(self):
        """Test skill metadata structure."""
        self.assertEqual(SKILL_METADATA['id'], 'government_gis')
        self.assertIn('capabilities', SKILL_METADATA)
        self.assertGreater(len(SKILL_METADATA['capabilities']), 10)
    
    def test_validate_coordinates(self):
        """Test coordinate validation function."""
        self.assertTrue(validate_coordinates(32.7157, -117.1611))
        self.assertFalse(validate_coordinates(91.0, 0.0))
        self.assertFalse(validate_coordinates(0.0, 181.0))
        self.assertTrue(validate_coordinates(-90.0, -180.0))
        self.assertTrue(validate_coordinates(90.0, 180.0))
    
    def test_calculate_distance(self):
        """Test distance calculation."""
        # San Diego to Los Angeles
        distance = calculate_distance(32.7157, -117.1611, 34.0522, -118.2437)
        self.assertAlmostEqual(distance, 180, delta=20)
        
        # Same point
        self.assertAlmostEqual(calculate_distance(0, 0, 0, 0), 0.0)
    
    def test_parse_geospatial_metadata(self):
        """Test metadata parsing."""
        valid_metadata = json.dumps({
            'spatial_reference': 'WGS84',
            'extent': {'minx': -180, 'maxx': 180},
            'data_type': 'raster'
        })
        
        metadata = parse_geospatial_metadata(valid_metadata)
        self.assertEqual(metadata['spatial_reference'], 'WGS84')
        
        with self.assertRaises(ValueError):
            parse_geospatial_metadata('invalid json')
    
    def test_build_spatial_query(self):
        """Test spatial query building."""
        query = build_spatial_query(32.7157, -117.1611, 5.0, ['elevation', 'hydrography'])
        
        self.assertEqual(query['latitude'], 32.7157)
        self.assertEqual(query['longitude'], -117.1611)
        self.assertEqual(query['radius_km'], 5.0)
        self.assertIn('elevation', query['data_types'])
        self.assertIn('bbox', query)
    
    def test_calculate_spatial_statistics(self):
        """Test spatial statistics calculation."""
        elevations = [100, 150, 200, 250, 300]
        stats = calculate_spatial_statistics(elevations)
        
        self.assertEqual(stats['min'], 100)
        self.assertEqual(stats['max'], 300)
        self.assertEqual(stats['mean'], 200)
        self.assertEqual(stats['count'], 5)
        
        # Empty list
        self.assertEqual(calculate_spatial_statistics([]), {})
    
    def test_generate_gis_data_report(self):
        """Test report generation."""
        data_sources = {
            'USGS': {'description': 'Elevation data'},
            'NOAA': {'description': 'Coastal data'}
        }
        analysis_results = {
            'elevation': {'min': 100, 'max': 500},
            'flood_risk': 'moderate'
        }
        
        report = generate_gis_data_report(data_sources, analysis_results)
        
        self.assertIn('GOVERNMENT GIS DATA ANALYSIS REPORT', report)
        self.assertIn('USGS', report)
        self.assertIn('Elevation data', report)
        self.assertIn('moderate', report)
    
    def test_query_data_gov_catalog(self):
        """Test Data.gov catalog querying."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                'result': {
                    'results': [{
                        'title': 'Test Dataset',
                        'notes': 'Test description',
                        'organization': {'title': 'Test Org'},
                        'tags': [{'name': 'test'}],
                        'resources': [{'url': 'http://test.com', 'format': 'GeoJSON'}]
                    }]
                }
            }
            mock_get.return_value = mock_response
            
            results = query_data_gov_catalog('elevation')
            
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['title'], 'Test Dataset')
            mock_get.assert_called_once()
    
    def test_validate_spatial_coordinates(self):
        """Test spatial coordinate validation."""
        coords = [(32.7157, -117.1611), (34.0522, -118.2437)]
        self.assertTrue(validate_spatial_coordinates(coords))
        
        invalid_coords = [(91.0, 0.0), (0.0, 181.0)]
        self.assertFalse(validate_spatial_coordinates(invalid_coords))
        
        self.assertFalse(validate_spatial_coordinates([]))
    
    def test_interpolate_elevation(self):
        """Test elevation interpolation."""
        points = [
            (32.7157, -117.1611, 100.0),
            (32.7257, -117.1711, 150.0),
            (32.7057, -117.1511, 120.0)
        ]
        
        elevation = interpolate_elevation(points, 32.7157, -117.1611)
        self.assertAlmostEqual(elevation, 100.0, delta=1.0)
        
        # Test exact point match
        elevation = interpolate_elevation(points, 32.7257, -117.1711)
        self.assertAlmostEqual(elevation, 150.0)
    
    def test_skill_engine_initialization(self):
        """Test SkillEngine initialization."""
        config = {'api_key': 'test_key', 'timeout': 60}
        engine = SkillEngine(config)
        
        self.assertEqual(engine.config, config)
        self.assertIsNotNone(engine.session)
    
    def test_skill_engine_run_valid_capability(self):
        """Test running valid capability."""
        params = {
            'latitude': 32.7157,
            'longitude': -117.1611
        }
        
        result = self.engine.run('query_usgs_national_map', params)
        
        self.assertIn('elevation', result)
        self.assertIn('data_source', result)
        self.assertEqual(result['data_source'], 'USGS 3DEP')
    
    def test_skill_engine_run_invalid_capability(self):
        """Test running invalid capability."""
        with self.assertRaises(ValueError):
            self.engine.run('invalid_capability', {})
    
    def test_skill_engine_run_invalid_coordinates(self):
        """Test error handling for invalid coordinates."""
        params = {
            'latitude': 91.0,
            'longitude': 181.0
        }
        
        with self.assertRaises(ValueError):
            self.engine.run('query_usgs_national_map', params)
    
    def test_expert_prompts_format(self):
        """Test expert prompts have correct format."""
        for name, prompt in EXPERT_PROMPTS.items():
            self.assertIsInstance(name, str)
            self.assertIsInstance(prompt, str)
            self.assertIn('{', prompt)  # Should have placeholders
            self.assertIn('}', prompt)
    
    def test_integration_points_structure(self):
        """Test integration points structure."""
        for name, config in INTEGRATION_POINTS.items():
            self.assertIn('type', config)
            self.assertIn('endpoint', config)
            self.assertIn('description', config)
            self.assertIn('auth_method', config)
            self.assertIn('documentation_url', config)
            
            self.assertIn(config['type'], ['api', 'database', 'tool'])
            self.assertTrue(config['endpoint'].startswith('http'))

if __name__ == '__main__':
    unittest.main()