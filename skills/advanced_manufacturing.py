import json
import math
import os
import re
import statistics
import unittest
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union
import hashlib
import requests


SKILL_METADATA = {
    "name": "Expert 3D Printing & Advanced Manufacturing",
    "id": "advanced_manufacturing",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Comprehensive 3D printing and advanced manufacturing optimization covering FDM/SLA/SLS/DLP/DMLS, injection molding, CNC integration, generative design, cost estimation, and quality control.",
    "capabilities": [
        "gcode_generation",
        "print_optimization",
        "injection_mold_design",
        "mold_flow_simulation",
        "cost_estimation",
        "quality_control_protocols",
        "topology_optimization",
        "print_farm_management",
        "material_testing",
        "post_processing_analysis"
    ],
    "domain": "advanced_manufacturing"
}

EXPERT_PROMPTS = {
    "gcode_optimization": """Optimize G-code for {printer_type} printing {material} with {layer_height}mm layers.
    Object dimensions: {dimensions}
    Requirements: {requirements}
    Current issues: {issues}
    Return optimized G-code with improved speed, quality, and material usage.""",
    
    "injection_mold_design": """Design injection mold for {part_name} made of {material}.
    Part volume: {volume} cm³
    Expected production: {production_volume} units
    Requirements: {design_requirements}
    Include gating system, runner design, cooling channels, draft angles, and shrinkage compensation.""",
    
    "cost_analysis": """Calculate manufacturing cost for {process} producing {quantity} units of {part_name}.
    Material: {material}
    Machine time: {machine_time} hours
    Labor rate: ${labor_rate}/hour
    Include material, machine, labor, overhead, and post-processing costs.""",
    
    "topology_optimization": """Optimize topology for {part_name} under {loading_conditions}.
    Material: {material}
    Manufacturing constraints: {constraints}
    Weight reduction target: {weight_reduction}%
    Maintain structural integrity under {max_stress} MPa.""",
    
    "quality_inspection": """Generate quality control protocol for {process} manufacturing {part_name}.
    Critical dimensions: {critical_dimensions}
    Tolerances: {tolerances}
    Material properties: {material_properties}
    Include inspection methods, sampling plans, and acceptance criteria.""",
    
    "print_farm_scheduling": """Optimize print farm schedule for {num_printers} printers producing {parts_list}.
    Deadline: {deadline}
    Priority parts: {priority_parts}
    Minimize makespan and maximize printer utilization.""",
    
    "material_testing": """Design material testing protocol for {material} printed parts.
    Test types: {test_types}
    Sample geometry: {geometry}
    Expected properties: {expected_properties}
    Include statistical analysis plan.""",
    
    "post_processing": """Determine optimal post-processing sequence for {part_name} printed with {material}.
    Current surface roughness: {surface_roughness} μm
    Target finish: {target_finish}
    Include annealing, vapor smoothing, and CNC finishing steps."""
}

INTEGRATION_POINTS = {
    "octoprint_api": {
        "type": "api",
        "endpoint": "http://{printer_ip}/api",
        "description": "OctoPrint API for printer control and monitoring",
        "auth_method": "api_key",
        "documentation_url": "https://docs.octoprint.org/en/master/api/"
    },
    "prusaslicer": {
        "type": "tool",
        "endpoint": "local",
        "description": "PrusaSlicer CLI for G-code generation",
        "auth_method": "none",
        "documentation_url": "https://help.prusa3d.com/article/command-line-slicing_2838"
    },
    "moldflow": {
        "type": "tool",
        "endpoint": "local",
        "description": "Autodesk Moldflow for injection molding simulation",
        "auth_method": "license",
        "documentation_url": "https://www.autodesk.com/products/moldflow/overview"
    },
    "material_database": {
        "type": "database",
        "endpoint": "postgresql://localhost:5432/materials",
        "description": "Material properties database",
        "auth_method": "credentials",
        "documentation_url": "internal"
    },
    "cost_calculator": {
        "type": "api",
        "endpoint": "https://api.revvel.com/manufacturing/cost",
        "description": "Manufacturing cost estimation API",
        "auth_method": "bearer_token",
        "documentation_url": "https://docs.revvel.com/manufacturing/cost"
    }
}


def parse_gcode(gcode_text: str) -> Dict[str, Any]:
    """Parse G-code file and extract key parameters."""
    lines = gcode_text.strip().split('\n')
    metadata = {
        'total_lines': len(lines),
        'estimated_time': 0,
        'filament_used': 0,
        'layer_height': None,
        'temperatures': {},
        'commands': defaultdict(int)
    }
    
    for line in lines:
        line = line.strip()
        if line.startswith(';'):
            if 'estimated printing time' in line.lower():
                time_str = line.split(':', 1)[1].strip()
                metadata['estimated_time'] = parse_time_string(time_str)
            elif 'filament used' in line.lower():
                filament_str = line.split(':', 1)[1].strip()
                metadata['filament_used'] = parse_filament_length(filament_str)
            elif 'layer height' in line.lower():
                height_str = line.split(':', 1)[1].strip()
                metadata['layer_height'] = float(height_str.replace('mm', '').strip())
        else:
            cmd = line.split()[0] if line else ''
            if cmd in ['G0', 'G1', 'G2', 'G3', 'M104', 'M109', 'M140', 'M190']:
                metadata['commands'][cmd] += 1
    
    return metadata


def parse_time_string(time_str: str) -> int:
    """Convert time string (e.g., '1h 23m 45s') to seconds."""
    total_seconds = 0
    parts = re.findall(r'(\d+)([hms])', time_str.lower())
    for value, unit in parts:
        value = int(value)
        if unit == 'h':
            total_seconds += value * 3600
        elif unit == 'm':
            total_seconds += value * 60
        elif unit == 's':
            total_seconds += value
    return total_seconds


def parse_filament_length(filament_str: str) -> float:
    """Parse filament length from string (e.g., '1.23m' or '1234.5mm')."""
    filament_str = filament_str.lower().strip()
    if 'm' in filament_str:
        return float(filament_str.replace('m', '').strip())
    elif 'mm' in filament_str:
        return float(filament_str.replace('mm', '').strip()) / 1000
    return 0.0


def calculate_injection_mold_cost(
    part_volume: float,
    material: str,
    cavitation: int = 1,
    complexity: str = "medium"
) -> Dict[str, float]:
    """Calculate injection mold cost based on part characteristics."""
    base_rates = {
        "low": 800,
        "medium": 1200,
        "high": 2000
    }
    
    material_multipliers = {
        "abs": 1.0,
        "pc": 1.3,
        "nylon": 1.2,
        "pp": 0.8,
        "pe": 0.9
    }
    
    base_cost = base_rates.get(complexity, 1200) * part_volume * cavitation
    material_multiplier = material_multipliers.get(material.lower(), 1.0)
    
    mold_cost = base_cost * material_multiplier
    machining_cost = mold_cost * 0.4
    design_cost = mold_cost * 0.2
    
    return {
        'total_mold_cost': mold_cost,
        'machining_cost': machining_cost,
        'design_cost': design_cost,
        'cost_per_cavity': mold_cost / cavitation
    }


def optimize_print_settings(
    material: str,
    layer_height: float,
    desired_quality: str = "standard"
) -> Dict[str, Any]:
    """Optimize print settings based on material and quality requirements."""
    settings = {
        "abs": {
            "standard": {"temperature": 230, "speed": 50, "fan": 30},
            "high": {"temperature": 235, "speed": 40, "fan": 20},
            "draft": {"temperature": 225, "speed": 60, "fan": 50}
        },
        "pla": {
            "standard": {"temperature": 200, "speed": 50, "fan": 100},
            "high": {"temperature": 205, "speed": 30, "fan": 100},
            "draft": {"temperature": 195, "speed": 70, "fan": 100}
        },
        "petg": {
            "standard": {"temperature": 240, "speed": 40, "fan": 50},
            "high": {"temperature": 245, "speed": 30, "fan": 40},
            "draft": {"temperature": 235, "speed": 50, "fan": 60}
        }
    }
    
    material_settings = settings.get(material.lower(), settings["pla"])
    quality_settings = material_settings.get(desired_quality, material_settings["standard"])
    
    # Adjust for layer height
    layer_factor = layer_height / 0.2
    adjusted_speed = max(20, min(quality_settings["speed"] / layer_factor, 80))
    
    return {
        'temperature': quality_settings["temperature"],
        'print_speed': adjusted_speed,
        'fan_speed': quality_settings["fan"],
        'layer_height': layer_height,
        'material': material
    }


def calculate_cooling_time(
    wall_thickness: float,
    material: str,
    mold_temp: float = 25,
    melt_temp: float = 200
) -> float:
    """Calculate cooling time for injection molded part."""
    thermal_diffusivity = {
        "abs": 0.12,
        "pc": 0.13,
        "nylon": 0.11,
        "pp": 0.10,
        "pe": 0.09
    }
    
    alpha = thermal_diffusivity.get(material.lower(), 0.11)
    delta_t = melt_temp - mold_temp
    
    # Simplified cooling time calculation
    cooling_time = (wall_thickness ** 2) / (math.pi ** 2 * alpha) * math.log(4 / math.pi)
    
    return max(cooling_time, 1.0)


def generate_quality_report(
    measurements: List[float],
    tolerance: float,
    specification: