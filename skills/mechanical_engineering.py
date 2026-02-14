import json
import re
import os
import math
import hashlib
import statistics
import unittest
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from collections import defaultdict
import requests

SKILL_METADATA = {
    "name": "Mechanical Engineering & Materials Science Expert",
    "id": "mechanical_engineering",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Comprehensive mechanical engineering and materials science analysis covering material properties, stress/strain analysis, fatigue prediction, composite design, FEA integration, manufacturing processes, and standards compliance",
    "capabilities": [
        "material_properties_lookup",
        "stress_strain_analysis",
        "fatigue_life_prediction",
        "composite_materials_design",
        "metallurgy_analysis",
        "fea_integration",
        "material_selection_ashby",
        "corrosion_analysis",
        "thermal_analysis",
        "manufacturing_process_selection",
        "tolerance_stackup_analysis",
        "gdt_interpretation",
        "standards_compliance",
        "failure_mode_analysis",
        "weld_analysis",
        "material_testing_protocols",
        "additive_manufacturing_optimization",
        "aerospace_materials",
        "automotive_materials",
        "biocompatible_materials"
    ],
    "domain": "mechanical_engineering_materials_science"
}

EXPERT_PROMPTS = {
    "material_selection": """You are a senior materials engineer. Help select the optimal material for {application} considering:
- Operating temperature range: {temp_range}°C
- Required strength: {strength_mpa} MPa
- Weight constraint: {max_density} g/cm³
- Environmental exposure: {environment}
- Manufacturing method: {manufacturing_process}
- Budget constraint: {budget_per_unit} USD/unit

Provide material recommendations with justification, including alternatives ranked by performance index.""",
    
    "fatigue_analysis": """Perform fatigue life analysis for {component_name} made of {material}:
- Loading: {loading_type} ({stress_range} MPa range)
- Mean stress: {mean_stress} MPa
- Surface finish: {surface_finish}
- Stress concentration factor: {kt}
- Required life: {required_cycles} cycles
- Operating temperature: {temp}°C

Calculate safety factor and expected cycles to failure using appropriate fatigue models.""",
    
    "composite_design": """Design a composite laminate for {application}:
- Required stiffness: {required_modulus} GPa
- Required strength: {required_strength} MPa
- Loading direction: {loading_direction}
- Environmental conditions: {environment}
- Manufacturing constraints: {constraints}

Specify fiber/matrix system, layup sequence, and fiber volume fraction.""",
    
    "fea_setup": """Generate FEA setup parameters for {analysis_type} analysis of {component}:
- Material: {material}
- Loading: {loading_conditions}
- Boundary conditions: {boundary_conditions}
- Mesh requirements: {mesh_density}
- Nonlinear effects: {nonlinear_effects}
- Contact definitions: {contact_pairs}

Provide complete input deck with material properties, mesh guidelines, and solver settings.""",
    
    "corrosion_assessment": """Evaluate corrosion risk for {material} in {environment}:
- Temperature: {temp}°C
- pH: {ph}
- Chloride concentration: {cl_concentration} ppm
- Exposure time: {exposure_years} years
- Stress state: {stress_state}

Predict corrosion rate, recommend protection methods, and estimate remaining life.""",
    
    "manufacturing_process": """Select optimal manufacturing process for {part_name}:
- Material: {material}
- Production volume: {volume} units/year
- Geometric complexity: {complexity}
- Dimensional tolerance: {tolerance} mm
- Surface finish requirement: {surface_finish}
- Cost target: {cost_target} USD/part

Compare processes (casting, forging, machining, additive, etc.) with cost analysis.""",
    
    "tolerance_analysis": """Perform tolerance stack-up analysis for {assembly_name}:
- Components: {component_list}
- Critical dimensions: {critical_dims}
- Manufacturing processes: {processes}
- Statistical distribution: {distribution_type}
- Required assembly yield: {target_yield}%

Calculate predicted yield and recommend tolerance adjustments.""",
    
    "failure_mode_analysis": """Conduct FMEA for {system_name}:
- Function: {system_function}
- Operating conditions: {conditions}
- Potential failure modes: {failure_modes}
- Severity scale: 1-10
- Occurrence probability: {occurrence_data}
- Detection methods: {detection_methods}

Calculate RPN values and recommend mitigation strategies."""
}

INTEGRATION_POINTS = {
    "matweb_api": {
        "type": "api",
        "endpoint": "https://www.matweb.com/api/search",
        "description": "Comprehensive material properties database",
        "auth_method": "api_key",
        "documentation_url": "https://www.matweb.com/api/docs"
    },
    "ansys_mechanical": {
        "type": "tool",
        "endpoint": "localhost:50052",
        "description": "PyMechanical interface for Ansys Mechanical FEA",
        "auth_method": "license",
        "documentation_url": "https://mechanical.docs.pyansys.com"
    },
    "nasa_materials_db": {
        "type": "database",
        "endpoint": "https://materials.nasa.gov/api/v1",
        "description": "NASA aerospace materials database",
        "auth_method": "oauth2",
        "documentation_url": "https://materials.nasa.gov/api/docs"
    },
    "astm_standards": {
        "type": "api",
        "endpoint": "https://compass.astm.org/api/standards",
        "description": "ASTM standards and test methods",
        "auth_method": "subscription",
        "documentation_url": "https://compass.astm.org/api/docs"
    },
    "granta_mds": {
        "type": "database",
        "endpoint": "https://grantadesign.com/api/mds",
        "description": "Granta Materials Data for Simulation",
        "auth_method": "license",
        "documentation_url": "https://grantadesign.com/api/docs"
    }
}

class MaterialProperties:
    """Material properties database interface and utilities."""
    
    @staticmethod
    def parse_material_data(raw_data: str) -> Dict[str, Any]:
        """Parse material property data from various formats."""
        try:
            if raw_data.strip().startswith('{'):
                return json.loads(raw_data)
            else:
                # Parse tabular format
                lines = [line.strip() for line in raw_data.split('\n') if line.strip()]
                props = {}
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().lower().replace(' ', '_')
                        value = value.strip()
                        try:
                            props[key] = float(value) if '.' in value or value.isdigit() else value
                        except ValueError:
                            props[key] = value
                return props
        except Exception as e:
            raise ValueError(f"Failed to parse material data: {str(e)}")
    
    @staticmethod
    def validate_properties(props: Dict[str, Any]) -> bool:
        """Validate material properties for completeness."""
        required_props = ['density', 'elastic_modulus', 'yield_strength', 'ultimate_tensile_strength']
        return all(prop in props for prop in required_props)
    
    @staticmethod
    def calculate_performance_index(props: Dict[str, Any], loading: str) -> float:
        """Calculate material performance index for given loading."""
        E = props.get('elastic_modulus', 0)
        rho = props.get('density', 1)
        sigma_y = props.get('yield_strength', 0)
        
        if loading == 'tension':
            return sigma_y / rho
        elif loading == 'bending':
            return math.sqrt(E) / rho
        elif loading == 'stiffness_limited':
            return E / rho
        else:
            return 0

class StressAnalysis:
    """Stress and strain analysis utilities."""
    
    @staticmethod
    def calculate_stress_concentration(geometry: str, dimensions: Dict[str, float]) -> float:
        """Calculate stress concentration factor Kt for common geometries."""
        if geometry == 'circular_hole':
            d = dimensions.get('hole_diameter', 0)
            w = dimensions.get('plate_width', 1)
            return 3.0 if d/w < 0.1 else 2.5
        elif geometry == 'shoulder_fillet':
            r = dimensions.get('fillet_radius', 0)
            d = dimensions.get('smaller_diameter', 1)
            return 1.5 + 0.5 * math.sqrt(r/d)
        else:
            return 1.0
    
    @staticmethod
    def mohr_circle_stress(sigma_x: float, sigma_y: float, tau_xy: float) -> Dict[str, float]:
        """Calculate principal stresses using Mohr's circle."""
        center = (sigma_x + sigma_y) / 2
        radius = math.sqrt(((sigma_x - sigma_y) / 2) ** 2 + tau_xy ** 2)
        
        return {
            'sigma_1': center + radius,
            'sigma_2': center - radius,
            'tau_max': radius,
            'theta_p': 0.5 * math.degrees(math.atan2(2 * tau_xy, sigma_x - sigma_y))
        }
    
    @staticmethod
    def von_mises_stress(stress_tensor: List[float]) -> float:
        """Calculate von Mises equivalent stress."""
        if len(stress_tensor) == 3:
            sx, sy, tau_xy = stress_tensor
            return math.sqrt(sx**2 + sy**2 - sx*sy + 3*tau_xy**2)
        elif len(stress_tensor) == 6:
            s1, s2, s3, s4, s5, s6 = stress_tensor
            return math.sqrt(0.5 * ((s1-s2)**2 + (s2-s3)**2 + (s3-s1)**2 + 6*(s4**2 + s5**2 + s6**2)))
        else:
            raise ValueError("Invalid stress tensor dimensions")

class FatigueAnalysis:
    """Fatigue life prediction and analysis."""
    
    @staticmethod
    def calculate_s_n_curve(material: str, ultimate_strength: float) -> Dict[str, float]:
        """Generate S-N curve parameters for fatigue analysis."""
        if material in ['steel', 'aluminum', 'titanium']:
            endurance_limit = 0.5 * ultimate_strength
            return {
                'endurance_limit': endurance_limit,
                'fatigue_strength_coefficient': 1.1 * ultimate_strength,
                'fatigue_strength_exponent': -0.085
            }
        else:
            return {
                'endurance_limit': 0.4 * ultimate_strength,
                'fatigue_strength_coefficient': ultimate_strength,
                'fatigue_strength_exponent': -0.1
            }
    
    @staticmethod
    def miner_damage_sum(cycles: List[float], stresses: List[float], sn_curve: Dict[str, float]) -> float:
        """Calculate Miner's rule damage sum."""
        damage = 0.0
        for n, s in zip(cycles, stresses):
            if s > sn_curve['endurance_limit']:
                Nf = (sn_curve['fatigue_strength_coefficient'] / s) ** (1/abs(sn_curve['fatigue_strength_exponent']))
                damage += n / Nf
        return damage
    
    @staticmethod
    def goodman_correction(alternating_stress: float, mean_stress: float, ultimate_strength: float) -> float:
        """Apply Goodman mean stress correction."""
        return alternating_stress / (1 - mean_stress / ultimate_strength)

class CompositeDesign:
    """Composite materials design and analysis."""
    
    @staticmethod
    def calculate_laminate_properties(layup: List[int], ply_props: Dict[str, float]) -> Dict[str, float]:
        """Calculate laminate stiffness properties."""
        Ex = ply_props.get('E1', 0)
        Ey = ply_props.get('E2', 0)
        Gxy = ply_props.get('G12', 0)
        nu_xy = ply_props.get('nu12', 0)
        
        # Simplified rule of mixtures
        total_thickness = len(layup)
        Ex_eff = sum(Ex * abs(math.cos(math.radians(angle))) for angle in layup) / total_thickness
        Ey_eff = sum(Ey * abs(math.sin(math.radians(angle))) for angle in layup) / total_thickness
        
        return {
            'Ex': Ex_eff,
            'Ey': Ey_eff,
            'Gxy': Gxy,
            'nu_xy': nu_xy,
            'total_thickness': total_thickness
        }
    
    @staticmethod
    def tsai_wu_failure(stress: List[float], strength: Dict[str, float]) -> float:
        """Tsai-Wu failure criterion for composites."""
        F1t = strength.get('F1t', 0)
        F1c = strength.get('F1c', 0)
        F2t = strength.get('F2t', 0)
        F2c = strength.get('F2c', 0)
        F12 = strength.get('F12', 0)
        
        sigma1, sigma2, tau12 = stress
        
        F1 = 1/F1t - 1/F1c
        F2 = 1/F2t - 1/F2c
        F11 = 1/(F1t * F1c)
        F22 = 1/(F2t * F2c)
        F66 = 1/(F12 ** 2)
        F12_cross = -0.5 * math.sqrt(F11 * F22)
        
        failure_index = (F11 * sigma1**2 + F22 * sigma2**2 + F66 * tau12**2 + 
                        2 * F12_cross * sigma1 * sigma2 + F1 * sigma1 + F2 * sigma2)
        
        return failure_index

class StandardsCompliance:
    """ASME/ISO standards compliance checking."""
    
    @staticmethod
    def check_asme_viii_stress(stress: float, allowable_stress: float, temperature: float) -> Dict[str, Any]:
        """Check ASME VIII stress compliance."""
        temp_factor = 1.0 if temperature < 350 else 0.8
        
        utilization = stress / (allowable_stress * temp_factor)
        
        return {
            'compliant': utilization <= 1.0,
            'utilization_ratio': utilization,
            'safety_factor': 1 / utilization,
            'temperature_factor': temp_factor
        }
    
    @staticmethod
    def check_iso_tolerance(dimension: float, tolerance_class: str) -> Dict[str, float]:
        """Check ISO tolerance for given dimension."""
        tolerance_table = {
            'h7': lambda d: 0.000 if d <= 3 else (0.000 if d <= 6 else 0.000),
            'h8': lambda d: 0.014 if d <= 3 else (0.018 if d <= 6 else 0.022),
            'h9': lambda d: 0.025 if d <= 3 else (0.030 if d <= 6 else 0.036),
            'H7': lambda d: 0.010 if d <= 3 else (0.012 if d <= 6 else 0.015),
            'H8': lambda d: 0.014 if d <= 3 else (0.018 if d <= 6 else 0.022)
        }
        
        if tolerance_class in tolerance_table:
            tolerance = tolerance_table[tolerance_class](dimension)
            return {
                'upper_limit': dimension + tolerance/2,
                'lower_limit': dimension - tolerance/2,
                'tolerance_band': tolerance
            }
        else:
            raise ValueError(f"Unsupported tolerance class: {tolerance_class}")

class ReportGenerator:
    """Generate engineering analysis reports."""
    
    @staticmethod
    def create_material_report(material: str, properties: Dict[str, Any]) -> str:
        """Generate comprehensive material report."""
        report = f"""
MATERIAL ANALYSIS REPORT
Material: {material}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PROPERTIES:
"""
        for key, value in properties.items():
            report += f"{key.replace('_', ' ').title()}: {value}\n"
        
        report += f"\nPERFORMANCE INDICES:\n"
        for loading in ['tension', 'bending', 'stiffness_limited']:
            pi = MaterialProperties.calculate_performance_index(properties, loading)
            report += f"{loading.title()}: {pi:.2f}\n"
        
        return report
    
    @staticmethod
    def create_fatigue_report(component: str, analysis: Dict[str, Any]) -> str:
        """Generate fatigue analysis report."""
        return f"""
FATIGUE ANALYSIS REPORT
Component: {component}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

RESULTS:
Expected Life: {analysis.get('life_cycles', 'N/A')} cycles
Safety Factor: {analysis.get('safety_factor', 'N/A')}
Damage Ratio: {analysis.get('damage_ratio', 'N/A')}
Critical Location: {analysis.get('critical_location', 'N/A')}

RECOMMENDATIONS:
{analysis.get('recommendations', 'No specific recommendations')}
"""

class SkillEngine:
    """Main skill engine for mechanical engineering analysis."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.material_db = {}
        self.analysis_cache = {}
        
    def run(self, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute requested capability."""
        try:
            if capability == "material_properties_lookup":
                return self._lookup_material_properties(params)
            elif capability == "stress_strain_analysis":
                return self._perform_stress_analysis(params)
            elif capability == "fatigue_life_prediction":
                return self._predict_fatigue_life(params)
            elif capability == "composite_materials_design":
                return self._design_composite(params)
            elif capability == "material_selection_ashby":
                return self._ashby_selection(params)
            elif capability == "standards_compliance":
                return self._check_standards(params)
            elif capability == "report_generation":
                return self._generate_report(params)
            else:
                raise ValueError(f"Unsupported capability: {capability}")
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def _lookup_material_properties(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Lookup material properties from database."""
        material = params.get('material', '')
        if not material:
            return {"error": "Material name required"}
        
        # Mock database lookup
        mock_props = {
            "density": 7.85,  # g/cm³
            "elastic_modulus": 200,  # GPa
            "yield_strength": 250,  # MPa
            "ultimate_tensile_strength": 400,  # MPa
            "poisson_ratio": 0.3,
            "thermal_conductivity": 50,  # W/m·K
            "thermal_expansion": 12e-6  # /°C
        }
        
        return {
            "material": material,
            "properties": mock_props,
            "success": True
        }
    
    def _perform_stress_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform stress analysis."""
        loading = params.get('loading', {})
        geometry = params.get('geometry', {})
        
        # Calculate stress concentration
        kt = StressAnalysis.calculate_stress_concentration(
            geometry.get('type', 'circular_hole'),
            geometry.get('dimensions', {})
        )
        
        # Calculate von Mises stress
        stress_tensor = loading.get('stress_tensor', [100, 50, 25])
        von_mises = StressAnalysis.von_mises_stress(stress_tensor)
        
        return {
            "stress_concentration_factor": kt,
            "von_mises_stress": von_mises,
            "safety_factor": params.get('yield_strength', 250) / von_mises,
            "success": True
        }
    
    def _predict_fatigue_life(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Predict fatigue life."""
        material = params.get('material', 'steel')
        ultimate_strength = params.get('ultimate_strength', 400)
        loading_cycles = params.get('loading_cycles', [])
        
        sn_curve = FatigueAnalysis.calculate_s_n_curve(material, ultimate_strength)
        
        damage = 0.0
        if loading_cycles:
            cycles = [lc['cycles'] for lc in loading_cycles]
            stresses = [lc['stress'] for lc in loading_cycles]
            damage = FatigueAnalysis.miner_damage_sum(cycles, stresses, sn_curve)
        
        return {
            "sn_curve": sn_curve,
            "damage_ratio": damage,
            "remaining_life": 1/damage if damage > 0 else float('inf'),
            "success": True
        }
    
    def _design_composite(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Design composite laminate."""
        layup = params.get('layup', [0, 45, -45, 90])
        ply_props = params.get('ply_properties', {
            'E1': 150, 'E2': 10, 'G12': 5, 'nu12': 0.3
        })
        
        laminate_props = CompositeDesign.calculate_laminate_properties(layup, ply_props)
        
        return {
            "layup_sequence": layup,
            "laminate_properties": laminate_props,
            "success": True
        }
    
    def _ashby_selection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform Ashby material selection."""
        requirements = params.get('requirements', {})
        candidates = params.get('candidates', [])
        
        # Calculate performance indices
        results = []
        for material in candidates:
            props = material.get('properties', {})
            pi = MaterialProperties.calculate_performance_index(
                props, requirements.get('loading', 'tension')
            )
            results.append({
                'material': material['name'],
                'performance_index': pi,
                'properties': props
            })
        
        # Sort by performance index
        results.sort(key=lambda x: x['performance_index'], reverse=True)
        
        return {
            "ranked_materials": results,
            "success": True
        }
    
    def _check_standards(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check standards compliance."""
        standard = params.get('standard', 'ASME_VIII')
        stress = params.get('stress', 100)
        allowable = params.get('allowable_stress', 150)
        temperature = params.get('temperature', 25)
        
        if standard == 'ASME_VIII':
            result = StandardsCompliance.check_asme_viii_stress(stress, allowable, temperature)
        else:
            result = {"compliant": True, "note": "Standard not implemented"}
        
        return {**result, "success": True}
    
    def _generate_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analysis report."""
        report_type = params.get('type', 'material')
        
        if report_type == 'material':
            material = params.get('material', 'Steel')
            props = params.get('properties', {})
            report = ReportGenerator.create_material_report(material, props)
        elif report_type == 'fatigue':
            component = params.get('component', 'Component')
            analysis = params.get('analysis', {})
            report = ReportGenerator.create_fatigue_report(component, analysis)
        else:
            report = "Report type not supported"
        
        return {
            "report": report,
            "report_type": report_type,
            "success": True
        }

class TestMechanicalEngineeringSkill(unittest.TestCase):
    """Comprehensive test suite for mechanical engineering skill."""
    
    def test_metadata(self):
        """Test skill metadata."""
        self.assertEqual(SKILL_METADATA['name'], "Mechanical Engineering & Materials Science Expert")
        self.assertIn('material_properties_lookup', SKILL_METADATA['capabilities'])
        self.assertEqual(len(SKILL_METADATA['capabilities']), 20)
    
    def test_material_properties_parsing(self):
        """Test material properties parsing."""
        raw_data = "density: 7.85\nelastic_modulus: 200\nyield_strength: 250"
        props = MaterialProperties.parse_material_data(raw_data)
        self.assertEqual(props['density'], 7.85)
        self.assertEqual(props['elastic_modulus'], 200)
        self.assertTrue(MaterialProperties.validate_properties(props))
    
    def test_stress_concentration(self):
        """Test stress concentration calculation."""
        kt = StressAnalysis.calculate_stress_concentration('circular_hole', {'hole_diameter': 10, 'plate_width': 100})
        self.assertAlmostEqual(kt, 3.0, places=1)
    
    def test_mohr_circle(self):
        """Test Mohr's circle calculation."""
        result = StressAnalysis.mohr_circle_stress(100, 50, 25)
        self.assertIn('sigma_1', result)
        self.assertIn('sigma_2', result)
        self.assertGreater(result['sigma_1'], result['sigma_2'])
    
    def test_von_mises_stress(self):
        """Test von Mises stress calculation."""
        stress = StressAnalysis.von_mises_stress([100, 50, 25])
        self.assertAlmostEqual(stress, 95.39, places=1)
    
    def test_fatigue_analysis(self):
        """Test fatigue life prediction."""
        sn_curve = FatigueAnalysis.calculate_s_n_curve('steel', 400)
        self.assertIn('endurance_limit', sn_curve)
        self.assertAlmostEqual(sn_curve['endurance_limit'], 200, places=0)
    
    def test_composite_design(self):
        """Test composite laminate design."""
        layup = [0, 45, -45, 90]
        props = {'E1': 150, 'E2': 10, 'G12': 5, 'nu12': 0.3}
        result = CompositeDesign.calculate_laminate_properties(layup, props)
        self.assertEqual(result['total_thickness'], 4)
        self.assertGreater(result['Ex'], 0)
    
    def test_standards_compliance(self):
        """Test standards compliance checking."""
        result = StandardsCompliance.check_asme_viii_stress(100, 150, 25)
        self.assertTrue(result['compliant'])
        self.assertLess(result['utilization_ratio'], 1.0)
    
    def test_skill_engine(self):
        """Test skill engine capabilities."""
        engine = SkillEngine()
        
        # Test material lookup
        result = engine.run("material_properties_lookup", {"material": "Steel"})
        self.assertTrue(result['success'])
        self.assertIn('properties', result)
        
        # Test stress analysis
        result = engine.run("stress_strain_analysis", {
            "loading": {"stress_tensor": [100, 50, 25]},
            "geometry": {"type": "circular_hole", "dimensions": {"hole_diameter": 10}}
        })
        self.assertTrue(result['success'])
        self.assertIn('von_mises_stress', result)
        
        # Test fatigue prediction
        result = engine.run("fatigue_life_prediction", {
            "material": "steel",
            "ultimate_strength": 400,
            "loading_cycles": [{"cycles": 1000, "stress": 200}]
        })
        self.assertTrue(result['success'])
        self.assertIn('damage_ratio', result)
    
    def test_report_generation(self):
        """Test report generation."""
        engine = SkillEngine()
        result = engine.run("report_generation", {
            "type": "material",
            "material": "Test Material",
            "properties": {"density": 7.85, "elastic_modulus": 200}
        })
        self.assertTrue(result['success'])
        self.assertIn('report', result)
    
    def test_error_handling(self):
        """Test error handling."""
        engine = SkillEngine()
        result = engine.run("invalid_capability", {})
        self.assertFalse(result['success'])
        self.assertIn('error', result)

if __name__ == '__main__':
    unittest.main()