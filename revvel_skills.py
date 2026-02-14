#!/usr/bin/env python3
"""
Revvel Expert Skills - Main Application
A comprehensive suite of 39 expert-level skills for legal, forensic, medical, and investigative work.
Built with Kimo (kimi-k2) via OpenRouter.
"""
import os
import sys
import json
import importlib.util
from pathlib import Path
from typing import Dict, List, Any

__version__ = "1.0.0"
__author__ = "Revvel AI Engine"

class RevvelSkillsEngine:
    """Main engine for loading and executing Revvel expert skills."""
    
    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self.loaded_skills = {}
        self.skill_metadata = {}
        
    def discover_skills(self) -> List[str]:
        """Discover all available skill modules."""
        if not self.skills_dir.exists():
            raise FileNotFoundError(f"Skills directory not found: {self.skills_dir}")
        
        skill_files = list(self.skills_dir.glob("*.py"))
        return [f.stem for f in skill_files if not f.stem.startswith("__")]
    
    def load_skill(self, skill_id: str) -> Any:
        """Load a skill module dynamically."""
        if skill_id in self.loaded_skills:
            return self.loaded_skills[skill_id]
        
        skill_path = self.skills_dir / f"{skill_id}.py"
        if not skill_path.exists():
            raise FileNotFoundError(f"Skill module not found: {skill_id}")
        
        spec = importlib.util.spec_from_file_location(skill_id, skill_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        self.loaded_skills[skill_id] = module
        
        # Extract metadata if available
        if hasattr(module, 'SKILL_METADATA'):
            self.skill_metadata[skill_id] = module.SKILL_METADATA
        
        return module
    
    def load_all_skills(self):
        """Load all available skills."""
        skill_ids = self.discover_skills()
        print(f"Discovering skills in {self.skills_dir}...")
        print(f"Found {len(skill_ids)} skills")
        
        for skill_id in skill_ids:
            try:
                self.load_skill(skill_id)
                print(f"  ✓ Loaded: {skill_id}")
            except Exception as e:
                print(f"  ✗ Failed to load {skill_id}: {e}")
    
    def get_skill_catalog(self) -> Dict[str, Any]:
        """Get a catalog of all loaded skills with metadata."""
        catalog = {}
        for skill_id, metadata in self.skill_metadata.items():
            catalog[skill_id] = {
                "name": metadata.get("name", skill_id),
                "version": metadata.get("version", "unknown"),
                "description": metadata.get("description", "No description available"),
                "capabilities": metadata.get("capabilities", []),
                "domain": metadata.get("domain", "general"),
            }
        return catalog
    
    def execute_skill(self, skill_id: str, method: str, *args, **kwargs) -> Any:
        """Execute a specific method from a skill module."""
        if skill_id not in self.loaded_skills:
            self.load_skill(skill_id)
        
        module = self.loaded_skills[skill_id]
        
        if not hasattr(module, method):
            raise AttributeError(f"Skill '{skill_id}' has no method '{method}'")
        
        func = getattr(module, method)
        return func(*args, **kwargs)
    
    def list_skills(self):
        """Print a formatted list of all available skills."""
        catalog = self.get_skill_catalog()
        
        print(f"\n{'='*80}")
        print(f"REVVEL EXPERT SKILLS CATALOG ({len(catalog)} skills)")
        print(f"{'='*80}\n")
        
        for skill_id, info in sorted(catalog.items()):
            print(f"  {info['name']}")
            print(f"    ID: {skill_id}")
            print(f"    Domain: {info['domain']}")
            print(f"    Version: {info['version']}")
            print(f"    Capabilities: {', '.join(info['capabilities'][:5])}")
            print(f"    Description: {info['description'][:100]}...")
            print()


def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Revvel Expert Skills - Comprehensive AI-powered expert system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  revvel_skills.py --list                    List all available skills
  revvel_skills.py --catalog                 Export skill catalog to JSON
  revvel_skills.py --skill dna_forensics     Load and inspect a specific skill
        """
    )
    
    parser.add_argument("--version", action="version", version=f"Revvel Skills v{__version__}")
    parser.add_argument("--list", action="store_true", help="List all available skills")
    parser.add_argument("--catalog", action="store_true", help="Export skill catalog to JSON")
    parser.add_argument("--skill", type=str, help="Load and inspect a specific skill")
    parser.add_argument("--skills-dir", type=str, default="skills", help="Path to skills directory")
    
    args = parser.parse_args()
    
    # Initialize engine
    engine = RevvelSkillsEngine(skills_dir=args.skills_dir)
    
    # Load all skills
    engine.load_all_skills()
    
    if args.list:
        engine.list_skills()
    
    elif args.catalog:
        catalog = engine.get_skill_catalog()
        output_file = "revvel_skills_catalog.json"
        with open(output_file, "w") as f:
            json.dump(catalog, f, indent=2)
        print(f"\nSkill catalog exported to: {output_file}")
        print(f"Total skills: {len(catalog)}")
    
    elif args.skill:
        skill_id = args.skill
        try:
            module = engine.load_skill(skill_id)
            print(f"\n{'='*80}")
            print(f"SKILL: {skill_id}")
            print(f"{'='*80}\n")
            
            if hasattr(module, 'SKILL_METADATA'):
                metadata = module.SKILL_METADATA
                print(f"Name: {metadata.get('name')}")
                print(f"Version: {metadata.get('version')}")
                print(f"Domain: {metadata.get('domain')}")
                print(f"Description: {metadata.get('description')}")
                print(f"\nCapabilities:")
                for cap in metadata.get('capabilities', []):
                    print(f"  - {cap}")
            
            if hasattr(module, 'EXPERT_PROMPTS'):
                prompts = module.EXPERT_PROMPTS
                print(f"\nExpert Prompts ({len(prompts)}):")
                for prompt_name in list(prompts.keys())[:5]:
                    print(f"  - {prompt_name}")
            
            if hasattr(module, 'INTEGRATION_POINTS'):
                integrations = module.INTEGRATION_POINTS
                print(f"\nIntegration Points ({len(integrations)}):")
                for int_name, int_info in list(integrations.items())[:5]:
                    print(f"  - {int_name}: {int_info.get('type', 'unknown')}")
            
            print()
        
        except Exception as e:
            print(f"Error loading skill '{skill_id}': {e}")
            sys.exit(1)
    
    else:
        # Default: show summary
        catalog = engine.get_skill_catalog()
        print(f"\n{'='*80}")
        print(f"REVVEL EXPERT SKILLS v{__version__}")
        print(f"{'='*80}")
        print(f"\nTotal Skills Loaded: {len(catalog)}")
        print(f"\nDomains:")
        
        domains = {}
        for skill_info in catalog.values():
            domain = skill_info.get('domain', 'general')
            domains[domain] = domains.get(domain, 0) + 1
        
        for domain, count in sorted(domains.items()):
            print(f"  {domain}: {count} skills")
        
        print(f"\nUse --list to see all skills")
        print(f"Use --catalog to export catalog to JSON")
        print(f"Use --skill <skill_id> to inspect a specific skill")
        print()


if __name__ == "__main__":
    main()
