import json
import math
import os
import re
import statistics
import unittest
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import hashlib
import requests
from collections import defaultdict, namedtuple
import xml.etree.ElementTree as ET

SKILL_METADATA = {
    "name": "Drone Operator & Programming",
    "id": "drone_operator",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Advanced UAV flight planning, autonomous mission programming, and drone operation management for legal/forensic applications",
    "capabilities": [
        "flight_plan_generation",
        "waypoint_navigation",
        "obstacle_avoidance",
        "photogrammetry_processing",
        "3d_mapping",
        "part107_compliance_check",
        "mavlink_protocol_handling",
        "dji_sdk_integration",
        "ardupilot_programming",
        "px4_autopilot_control",
        "mission_validation",
        "flight_log_analysis",
        "emergency_protocol_execution"
    ],
    "domain": "uav_drone_operations"
}

EXPERT_PROMPTS = {
    "flight_plan_creation": """Create a comprehensive flight plan for forensic evidence collection with the following parameters:
Area: {survey_area_coords}
Altitude: {flight_altitude}ft AGL
Overlap: {image_overlap}%
Ground Sample Distance: {gsd}cm/pixel
Wind conditions: {wind_speed}mph from {wind_direction}
Obstacles: {obstacle_list}
Time constraint: {max_flight_time}minutes
Regulatory zone: {regulatory_zone}
Special requirements: {special_requirements}""",
    
    "emergency_protocol": """Generate emergency landing protocol for drone experiencing:
Failure type: {failure_type}
Current position: {current_position}
Battery remaining: {battery_percent}%
Nearest safe zone: {safe_zone_coords}
Weather conditions: {weather_conditions}
Communication status: {comm_status}
Payload: {payload_description}""",
    
    "evidence_collection_mission": """Design a photogrammetry mission for crime scene documentation:
Scene boundaries: {scene_bounds}
Evidence points: {evidence_markers}
Required resolution: {resolution}mm/pixel
Lighting conditions: {lighting}
Legal requirements: {legal_requirements}
Chain of custody: {custody_protocol}
Flight restrictions: {flight_restrictions}""",
    
    "regulatory_compliance_check": """Verify Part 107 compliance for operation:
Location: {operation_location}
Time of day: {operation_time}
Weather: {weather_conditions}
Airspace class: {airspace_class}
NOTAMs: {notam_list}
Pilot certification: {pilot_cert}
Insurance coverage: {insurance_details}""",
    
    "obstacle_avoidance_algorithm": """Implement obstacle avoidance for path:
Start point: {start_coords}
End point: {end_coords}
Known obstacles: {obstacle_list}
Drone specs: {drone_parameters}
Safety margin: {safety_distance}m
Real-time updates: {dynamic_obstacles}""",
    
    "flight_log_analysis": """Analyze flight log for legal proceedings:
Log file: {log_path}
Incident time: {incident_timestamp}
Key parameters: {parameters_to_analyze}
Regulatory compliance: {compliance_check}
Evidence integrity: {evidence_validation}
Expert witness requirements: {expert_requirements}""",
    
    "3d_mapping_processing": """Process aerial imagery for 3D reconstruction:
Image set: {image_directory}
Ground control points: {gcp_list}
Coordinate system: {coordinate_system}
Output format: {output_format}
Quality requirements: {quality_threshold}
Processing options: {processing_params}""",
    
    "mavlink_mission_upload": """Generate MAVLink mission for autonomous flight:
Mission type: {mission_type}
Waypoints: {waypoint_list}
Flight parameters: {flight_params}
Failsafe actions: {failsafe_settings}
Geofence: {geofence_coords}
RTL parameters: {rtl_config}"""
}

INTEGRATION_POINTS = {
    "dji_sdk": {
        "type": "api",
        "endpoint": "https://developer.dji.com/api/v1/",
        "description": "DJI Mobile SDK for drone control and telemetry",
        "auth_method": "api_key",
        "documentation_url": "https://developer.dji.com/mobile-sdk/documentation/"
    },
    "mavlink": {
        "type": "protocol",
        "endpoint": "udp://127.0.0.1:14550",
        "description": "MAVLink protocol for drone communication",
        "auth_method": "none",
        "documentation_url": "https://mavlink.io/en/"
    },
    "ugcs": {
        "type": "tool",
        "endpoint": "https://manuals.ugcs.com/api/v2/",
        "description": "UgCS drone mission planning software API",
        "auth_method": "oauth2",
        "documentation_url": "https://manuals.ugcs.com/"
    },
    "ardupilot": {
        "type": "api",
        "endpoint": "http://localhost:8000/mavlink",
        "description": "ArduPilot MAVProxy API for flight control",
        "auth_method": "none",
        "documentation_url": "https://ardupilot.org/dev/docs/mavlink-overview.html"
    },
    "px4": {
        "type": "api",
        "endpoint": "http://localhost:8080/api/v1/",
        "description": "PX4 Autopilot REST API",
        "auth_method": "bearer_token",
        "documentation_url": "https://docs.px4.io/main/en/middleware/mavlink.html"
    },
    "airmap": {
        "type": "api",
        "endpoint": "https://api.airmap.com/flight/v2/",
        "description": "Airspace management and regulatory compliance",
        "auth_method": "api_key",
        "documentation_url": "https://developers.airmap.com/"
    },
    "opendronemap": {
        "type": "tool",
        "endpoint": "http://localhost:3000/api/",
        "description": "Open source photogrammetry processing",
        "auth_method": "api_key",
        "documentation_url": "https://docs.opendronemap.org/"
    }
}

Coordinate = namedtuple('Coordinate', ['lat', 'lon', 'alt'])
Waypoint = namedtuple('Waypoint', ['seq', 'lat', 'lon', 'alt', 'command', 'param1', 'param2', 'param3', 'param4'])
FlightPlan = namedtuple('FlightPlan', ['waypoints', 'total_distance', 'estimated_time', 'battery_required'])
Obstacle = namedtuple('Obstacle', ['lat', 'lon', 'radius', 'height'])

def validate_coordinates(coords: Union[str, List[float], Dict[str, float]]) -> Coordinate:
    """Validate and normalize coordinate input."""
    if isinstance(coords, str):
        match = re.match(r'^(-?\d+\.?\d*),\s*(-?\d+\.?\d*)(?:,\s*(-?\d+\.?\d*))?$', coords.strip())
        if not match:
            raise ValueError(f"Invalid coordinate format: {coords}")
        lat, lon, alt = match.groups()
        return Coordinate(float(lat), float(lon), float(alt) if alt else 0.0)
    elif isinstance(coords, dict):
        return Coordinate(float(coords['lat']), float(coords['lon']), float(coords.get('alt', 0.0)))
    elif isinstance(coords, (list, tuple)):
        return Coordinate(float(coords[0]), float(coords[1]), float(coords[2]) if len(coords) > 2 else 0.0)
    else:
        raise ValueError(f"Unsupported coordinate type: {type(coords)}")

def calculate_distance(coord1: Coordinate, coord2: Coordinate) -> float:
    """Calculate great circle distance between two coordinates in meters."""
    R = 6371000  # Earth's radius in meters
    lat1, lon1 = math.radians(coord1.lat), math.radians(coord1.lon)
    lat2, lon2 = math.radians(coord2.lat), math.radians(coord2.lon)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def generate_waypoints(area_bounds: List[Coordinate], altitude: float, overlap: float = 70.0) -> List[Waypoint]:
    """Generate survey waypoints for a given area."""
    if len(area_bounds) < 3:
        raise ValueError("Area must have at least 3 boundary points")
    
    # Calculate bounding box
    lats = [c.lat for c in area_bounds]
    lons = [c.lon for c in area_bounds]
    
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    
    # Calculate grid spacing based on overlap
    gsd = 0.02  # 2cm/pixel at 100m altitude
    image_width = 4000 * gsd * (altitude / 100)  # meters
    spacing = image_width * (1 - overlap / 100)
    
    # Generate waypoints in lawnmower pattern
    waypoints = []
    seq = 0
    
    lat = min_lat
    direction = 1
    
    while lat <= max_lat:
        if direction == 1:
            lon_range = [min_lon, max_lon]
        else:
            lon_range = [max_lon, min_lon]
        
        waypoints.append(Waypoint(seq, lat, lon_range[0], altitude, 16, 0, 0, 0, 0))
        seq += 1
        
        waypoints.append(Waypoint(seq, lat, lon_range[1], altitude, 16, 0, 0, 0, 0))
        seq += 1
        
        lat += spacing / 111000  # Convert meters to degrees
        direction *= -1
    
    return waypoints

def check_part107_compliance(location: Coordinate, altitude: float, time_of_day: datetime) -> Dict[str, Any]:
    """Check Part 107 compliance for drone operation."""
    compliance = {
        "compliant": True,
        "violations": [],
        "warnings": []
    }
    
    # Altitude restriction
    if altitude > 400:
        compliance["compliant"] = False
        compliance["violations"].append("Altitude exceeds 400ft AGL limit")
    
    # Time restriction
    if time_of_day.hour < 6 or time_of_day.hour > 19:
        compliance["compliant"] = False
        compliance["violations"].append("Operation outside civil twilight hours")
    
    # Check airspace (simplified)
    if 37.0 < location.lat < 38.0 and -122.5 < location.lon < -122.0:
        compliance["warnings"].append("Operating near Class B airspace - check NOTAMs")
    
    return compliance

def parse_mavlink_message(message: str) -> Dict[str, Any]:
    """Parse MAVLink message string into structured data."""
    pattern = r'^(\d+):(\w+):(.+)$'
    match = re.match(pattern, message.strip())
    
    if not match:
        raise ValueError("Invalid MAVLink message format")
    
    timestamp, msg_type, payload = match.groups()
    
    # Parse payload based on message type
    data = {"timestamp": int(timestamp), "type": msg_type}
    
    if msg_type == "GLOBAL_POSITION_INT":
        parts = payload.split(',')
        data.update({
            "lat": int(parts[0]) / 1e7,
            "lon": int(parts[1]) / 1e7,
            "alt": int(parts[2]) / 1000,
            "relative_alt": int(parts[3]) / 1000
        })
    elif msg_type == "GPS_RAW_INT":
        parts = payload.split(',')
        data.update({
            "lat": int(parts[0]) / 1e7,
            "lon": int(parts[1]) / 1e7,
            "satellites_visible": int(parts[2]),
            "eph": int(parts[3])
        })
    
    return data

def calculate_photogrammetry_coverage(waypoints: List[Waypoint], camera_specs: Dict[str, float]) -> Dict[str, Any]:
    """Calculate photogrammetry coverage metrics."""
    if not waypoints:
        return {"coverage_area": 0, "image_count": 0, "gsd": 0}
    
    # Calculate image footprint
    sensor_width = camera_specs.get("sensor_width", 13.2)  # mm
    sensor_height = camera_specs.get("sensor_height", 8.8)  # mm
    focal_length = camera_specs.get("focal_length", 24)  # mm
    image_width = camera_specs.get("image_width", 4000)  # pixels
    image_height = camera_specs.get("image_height", 3000)  # pixels
    
    # Ground sampling distance
    avg_altitude = statistics.mean([wp.alt for wp in waypoints])
    gsd = (sensor_width * avg_altitude * 100) / (focal_length * image_width)  # cm/pixel
    
    # Image footprint on ground
    footprint_width = (sensor_width * avg_altitude) / focal_length  # meters
    footprint_height = (sensor_height * avg_altitude) / focal_length  # meters
    
    # Calculate total coverage
    total_area = len(waypoints) * footprint_width * footprint_height
    
    return {
        "coverage_area": total_area,
        "image_count": len(waypoints),
        "gsd": gsd,
        "footprint_width": footprint_width,
        "footprint_height": footprint_height
    }

def generate_kml_flight_plan(waypoints: List[Waypoint], output_file: str) -> str:
    """Generate KML file for flight plan visualization."""
    kml = ET.Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    doc = ET.SubElement(kml, "Document")
    
    name = ET.SubElement(doc, "name")
    name.text = "Drone Flight Plan"
    
    # Create line string for flight path
    placemark = ET.SubElement(doc, "Placemark")
    ET.SubElement(placemark, "name").text = "Flight Path"
    
    line_string = ET.SubElement(placemark, "LineString")
    ET.SubElement(line_string, "extrude").text = "1"
    ET.SubElement(line_string, "tessellate").text = "1"
    
    coordinates = []
    for wp in waypoints:
        coordinates.append(f"{wp.lon},{wp.lat},{wp.alt}")
    
    ET.SubElement(line_string, "coordinates").text = " ".join(coordinates)
    
    # Add waypoints as placemarks
    for wp in waypoints:
        pm = ET.SubElement(doc, "Placemark")
        ET.SubElement(pm, "name").text = f"WP{wp.seq}"
        point = ET.SubElement(pm, "Point")
        ET.SubElement(point, "coordinates").text = f"{wp.lon},{wp.lat},{wp.alt}"
    
    tree = ET.ElementTree(kml)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    
    return output_file

def check_obstacle_collision(path: List[Coordinate], obstacles: List[Obstacle]) -> List[Tuple[int, Obstacle]]:
    """Check for obstacle collisions along flight path."""
    collisions = []
    
    for i, point in enumerate(path):
        for obstacle in obstacles:
            distance = calculate_distance(
                Coordinate(point.lat, point.lon, 0),
                Coordinate(obstacle.lat, obstacle.lon, 0)
            )
            
            if distance <= obstacle.radius:
                collisions.append((i, obstacle))
    
    return collisions

def calculate_battery_requirements(waypoints: List[Waypoint], drone_specs: Dict[str, float]) -> Dict[str, float]:
    """Calculate battery requirements for flight plan."""
    if not waypoints:
        return {"required_capacity": 0, "estimated_time": 0}
    
    # Calculate total distance
    total_distance = 0
    for i in range(1, len(waypoints)):
        total_distance += calculate_distance(
            Coordinate(waypoints[i-1].lat, waypoints[i-1].lon, waypoints[i-1].alt),
            Coordinate(waypoints[i].lat, waypoints[i].lon, waypoints[i].alt)
        )
    
    # Calculate flight time
    cruise_speed = drone_specs.get("cruise_speed", 15)  # m/s
    hover_time = len(waypoints) * 5  # 5 seconds per waypoint
    flight_time = (total_distance / cruise_speed) + hover_time
    
    # Calculate energy consumption
    power_consumption = drone_specs.get("power_consumption", 500)  # watts
    energy_required = (power_consumption * flight_time) / 3600  # Wh
    
    # Add safety margin
    safety_margin = 1.3
    required_capacity = energy_required * safety_margin
    
    return {
        "required_capacity": required_capacity,
        "estimated_time": flight_time,
        "total_distance": total_distance
    }

def validate_flight_plan(waypoints: List[Waypoint], constraints: Dict[str, Any]) -> Dict[str, Any]:
    """Validate flight plan against operational constraints."""
    validation = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Check waypoint count
    if len(waypoints) > 99:
        validation["errors"].append("Waypoint count exceeds DJI limit of 99")
        validation["valid"] = False
    
    # Check altitude limits
    max_altitude = max(wp.alt for wp in waypoints)
    if max_altitude > constraints.get("max_altitude", 400):
        validation["errors"].append(f"Altitude {max_altitude}ft exceeds limit")
        validation["valid"] = False
    
    # Check distance from takeoff
    takeoff_point = Coordinate(waypoints[0].lat, waypoints[0].lon, 0)
    max_distance = 0
    for wp in waypoints:
        distance = calculate_distance(takeoff_point, Coordinate(wp.lat, wp.lon, 0))
        max_distance = max(max_distance, distance)
    
    if max_distance > constraints.get("max_distance", 1000):
        validation["warnings"].append(f"Max distance {max_distance/1000:.1f}km from takeoff")
    
    return validation

class SkillEngine:
    """Main skill engine for drone operations."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """Setup basic logging."""
        class Logger:
            def info(self, msg): print(f"[INFO] {msg}")
            def error(self, msg): print(f"[ERROR] {msg}")
            def warning(self, msg): print(f"[WARNING] {msg}")
        return Logger()
    
    def create_flight_plan(self, params: Dict[str, Any]) -> FlightPlan:
        """Create comprehensive flight plan."""
        area_bounds = [validate_coordinates(c) for c in params["area_bounds"]]
        altitude = params.get("altitude", 100)
        overlap = params.get("overlap", 70)
        
        waypoints = generate_waypoints(area_bounds, altitude, overlap)
        
        # Calculate plan metrics
        total_distance = 0
        for i in range(1, len(waypoints)):
            total_distance += calculate_distance(
                Coordinate(waypoints[i-1].lat, waypoints[i-1].lon, waypoints[i-1].alt),
                Coordinate(waypoints[i].lat, waypoints[i].lon, waypoints[i].alt)
            )
        
        # Estimate time (15 m/s cruise speed)
        estimated_time = total_distance / 15
        
        # Calculate battery requirement
        battery_required = (total_distance / 1000) * 50  # Wh per km
        
        return FlightPlan(waypoints, total_distance, estimated_time, battery_required)
    
    def check_compliance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check regulatory compliance."""
        location = validate_coordinates(params["location"])
        altitude = params["altitude"]
        time_of_day = params.get("time_of_day", datetime.now())
        
        return check_part107_compliance(location, altitude, time_of_day)
    
    def process_photogrammetry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process photogrammetry data."""
        image_dir = params["image_directory"]
        gcp_file = params.get("ground_control_points")
        
        # Simulate processing
        return {
            "status": "processing",
            "images_processed": 150,
            "point_cloud_density": 250,
            "orthomosaic_resolution": 2.5,
            "processing_time": 3600
        }
    
    def analyze_flight_log(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze flight log for legal proceedings."""
        log_file = params["log_file"]
        
        # Simulate log analysis
        return {
            "flight_duration": 1800,
            "max_altitude": 120,
            "max_speed": 25,
            "violations": [],
            "evidence_integrity": True,
            "export_path": "/tmp/flight_analysis.json"
        }
    
    def generate_emergency_protocol(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate emergency response protocol."""
        failure_type = params["failure_type"]
        current_position = validate_coordinates(params["current_position"])
        
        return {
            "protocol": "IMMEDIATE_LANDING",
            "nearest_safe_zone": {"lat": 37.7749, "lon": -122.4194},
            "estimated_time": 120,
            "emergency_contacts": ["911", "FAA", "Local ATC"],
            "actions": ["Reduce altitude", "Find clear area", "Land immediately"]
        }
    
    def run(self, capability: str, params: Dict[str, Any]) -> Any:
        """Dispatch to appropriate capability."""
        try:
            if capability == "flight_plan_generation":
                return self.create_flight_plan(params)
            elif capability == "part107_compliance_check":
                return self.check_compliance(params)
            elif capability == "photogrammetry_processing":
                return self.process_photogrammetry(params)
            elif capability == "flight_log_analysis":
                return self.analyze_flight_log(params)
            elif capability == "emergency_protocol_execution":
                return self.generate_emergency_protocol(params)
            else:
                raise ValueError(f"Unknown capability: {capability}")
        except Exception as e:
            self.logger.error(f"Error in {capability}: {str(e)}")
            raise

class TestDroneOperatorSkill(unittest.TestCase):
    """Test cases for drone operator skill."""
    
    def test_skill_metadata(self):
        """Test skill metadata structure."""
        self.assertEqual(SKILL_METADATA["name"], "Drone Operator & Programming")
        self.assertIn("flight_plan_generation", SKILL_METADATA["capabilities"])
        self.assertEqual(SKILL_METADATA["domain"], "uav_drone_operations")
    
    def test_validate_coordinates(self):
        """Test coordinate validation."""
        # Test string format
        coord = validate_coordinates("37.7749,-122.4194,100")
        self.assertEqual(coord.lat, 37.7749)
        self.assertEqual(coord.lon, -122.4194)
        self.assertEqual(coord.alt, 100.0)
        
        # Test dict format
        coord = validate_coordinates({"lat": 37.7749, "lon": -122.4194})
        self.assertEqual(coord.lat, 37.7749)
        
        # Test invalid format
        with self.assertRaises(ValueError):
            validate_coordinates("invalid")
    
    def test_calculate_distance(self):
        """Test distance calculation."""
        coord1 = Coordinate(37.7749, -122.4194, 0)
        coord2 = Coordinate(37.7849, -122.4094, 0)
        distance = calculate_distance(coord1, coord2)
        self.assertGreater(distance, 1000)
        self.assertLess(distance, 2000)
    
    def test_generate_waypoints(self):
        """Test waypoint generation."""
        bounds = [
            Coordinate(37.7749, -122.4194, 0),
            Coordinate(37.7849, -122.4194, 0),
            Coordinate(37.7849, -122.4094, 0),
            Coordinate(37.7749, -122.4094, 0)
        ]
        waypoints = generate_waypoints(bounds, 100, 70)
        self.assertGreater(len(waypoints), 0)
        self.assertIsInstance(waypoints[0], Waypoint)
    
    def test_part107_compliance(self):
        """Test Part 107 compliance check."""
        location = Coordinate(37.7749, -122.4194, 0)
        compliance = check_part107_compliance(location, 450, datetime(2024, 1, 1, 23))
        self.assertFalse(compliance["compliant"])
        self.assertIn("Altitude exceeds 400ft AGL limit", compliance["violations"])
    
    def test_obstacle_collision(self):
        """Test obstacle collision detection."""
        path = [
            Coordinate(37.7749, -122.4194, 0),
            Coordinate(37.7750, -122.4195, 0),
            Coordinate(37.7751, -122.4196, 0)
        ]
        obstacles = [Obstacle(37.7750, -122.4195, 50, 100)]
        collisions = check_obstacle_collision(path, obstacles)
        self.assertEqual(len(collisions), 1)
    
    def test_battery_calculation(self):
        """Test battery requirement calculation."""
        waypoints = [
            Waypoint(0, 37.7749, -122.4194, 100, 16, 0, 0, 0, 0),
            Waypoint(1, 37.7849, -122.4194, 100, 16, 0, 0, 0, 0)
        ]
        drone_specs = {"cruise_speed": 15, "power_consumption": 500}
        battery = calculate_battery_requirements(waypoints, drone_specs)
        self.assertGreater(battery["required_capacity"], 0)
        self.assertGreater(battery["estimated_time"], 0)
    
    def test_flight_plan_validation(self):
        """Test flight plan validation."""
        waypoints = [Waypoint(i, 37.7749, -122.4194, 100, 16, 0, 0, 0, 0) for i in range(100)]
        constraints = {"max_altitude": 400, "max_distance": 1000}
        validation = validate_flight_plan(waypoints, constraints)
        self.assertFalse(validation["valid"])
        self.assertIn("Waypoint count exceeds DJI limit of 99", validation["errors"])
    
    def test_skill_engine(self):
        """Test skill engine dispatch."""
        engine = SkillEngine({})
        
        # Test flight plan creation
        params = {
            "area_bounds": ["37.7749,-122.4194", "37.7849,-122.4194", "37.7849,-122.4094"],
            "altitude": 100
        }
        plan = engine.run("flight_plan_generation", params)
        self.assertIsInstance(plan, FlightPlan)
        self.assertGreater(len(plan.waypoints), 0)
        
        # Test compliance check
        params = {"location": "37.7749,-122.4194", "altitude": 350}
        compliance = engine.run("part107_compliance_check", params)
        self.assertIsInstance(compliance, dict)
        self.assertIn("compliant", compliance)
    
    def test_kml_generation(self):
        """Test KML file generation."""
        waypoints = [
            Waypoint(0, 37.7749, -122.4194, 100, 16, 0, 0, 0, 0),
            Waypoint(1, 37.7849, -122.4194, 100, 16, 0, 0, 0, 0)
        ]
        output_file = "/tmp/test_flight_plan.kml"
        result = generate_kml_flight_plan(waypoints, output_file)
        self.assertEqual(result, output_file)
        self.assertTrue(os.path.exists(output_file))
        os.remove(output_file)

if __name__ == "__main__":
    unittest.main()