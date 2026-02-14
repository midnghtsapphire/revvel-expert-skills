# Revvel Expert Skills

**39 Custom Expert-Level Skills for Legal, Forensic, Medical, and Investigative Work**

Built with **Kimo (kimi-k2)** via OpenRouter API.

---

## Overview

Revvel Expert Skills is a comprehensive Python application containing 39 production-grade expert skill modules spanning multiple domains:

- **Legal & Forensic**: DNA forensics, caselaw analysis, legal brief writing, cold case analysis, expert witness preparation
- **Medical & Healthcare**: Medical diagnosis, transplant surgery, neurodegenerative diseases, anti-aging research, ophthalmology
- **Intelligence & Investigation**: PRECOG predictive analysis, Epstein files intelligence, human trafficking tracking, OSINT, dark web monitoring
- **Technology & Engineering**: Cybersecurity, malware analysis, deepfake detection, drone programming, LiDAR, satellite imagery, 3D printing
- **Business & Operations**: Tax automation, multi-business operations, Twilio call center, lead generation, inventory management
- **Specialized Domains**: Ground-penetrating radar body detection, biocomposites formulation, nanotech surgery, genealogy research

Each skill module includes:
- ✅ Complete Python implementation with utility functions
- ✅ Expert-level prompt templates
- ✅ API/database integration points
- ✅ Comprehensive unit tests
- ✅ Full documentation

---

## Installation

### Prerequisites

- Python 3.8+
- pip or pip3

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Usage

### List All Skills

```bash
python3 revvel_skills.py --list
```

### Export Skill Catalog

```bash
python3 revvel_skills.py --catalog
```

This generates `revvel_skills_catalog.json` with metadata for all 39 skills.

### Inspect a Specific Skill

```bash
python3 revvel_skills.py --skill dna_forensics
```

### Run Tests

```bash
python3 -m pytest skills/ -v
```

Or run tests for a specific skill:

```bash
python3 -m pytest skills/dna_forensics.py -v
```

---

## Skill Catalog

### Legal & Forensic (10 skills)

1. **DNA Forensics Scientist** - DNA analysis, CODIS queries, genealogical DNA, degraded samples
2. **Caselaw Expert** - Case citation analysis, precedent research, jurisdiction-specific rulings
3. **Legal Brief Writing** - Motion drafting, appellate briefs, Bluebook citation
4. **LexisNexis Integration** - Legal research automation, Shepard's citation checking
5. **Expert Witness** - Daubert compliance, expert testimony, deposition preparation
6. **Medical Expert Witness** - Medical malpractice evaluation, standard of care analysis
7. **Patent & IP** - USPTO patent search, prior art analysis, trademark search
8. **Victim Advocacy** - Victim impact statements, VAWA compliance, protective orders
9. **Cold Case Analysis** - Evidence re-examination, DNA genealogy, timeline reconstruction
10. **Forensic Accounting** - Financial fraud detection, asset tracing, money laundering

### Medical & Healthcare (9 skills)

11. **Medical Doctor / Physician Expert** - Diagnostic reasoning, ICD-10/11 coding, drug interactions
12. **Transplant Surgery & Reconstructive Expert** - Organ transplants, face/limb transplants, VCA
13. **Neurodegenerative Disease Formulations** - Parkinson's, Alzheimer's, experimental treatments
14. **Glaucoma & Ophthalmology** - IOP management, optic nerve analysis, emerging therapies
15. **Anti-Aging Research & Formulations** - Longevity research, NAD+ precursors, senolytics
16. **Cardiovascular Disease Research** - Heart disease modeling, lipid analysis, emerging therapies
17. **Nanotech Surgery & Skin Repair Expert** - Nanoparticle drug delivery, tattoo removal, wound healing

### Intelligence & Investigation (7 skills)

18. **PRECOG (Precognitive Analysis Tool)** - Predictive intelligence, pattern recognition, threat assessment
19. **Epstein Files Intelligence Analysis** - Court document scraping, relationship mapping, fact verification
20. **Human Trafficking Intelligence & Dark Web Tracker** - Trafficking data, offender tracking, dark web monitoring
21. **Unrestricted Web & Social Media Scraper** - OSINT, profile discovery, historical content recovery
22. **Stealth Lead Generator — Insurance & Life Events** - Life event scraping, lead scoring, campaign management
23. **Presidential/Government Resources** - Executive orders, FOIA automation, federal court records
24. **Government Topography & GIS Resources** - USGS National Map, NOAA data, FEMA flood maps

### Technology & Engineering (8 skills)

25. **Elite Cybersecurity, Deepfake & Malware Expert** - Penetration testing, malware analysis, deepfake detection
26. **Ground-Penetrating Radar / Microwave Body Detection** - GPR signal processing, anomaly detection, forensic use
27. **Satellite & Remote Sensing** - Sentinel/Landsat data, multispectral analysis, change detection
28. **Drone Operator & Programming** - UAV flight planning, DJI SDK, MAVLink, photogrammetry
29. **LiDAR Expert** - Point cloud processing, terrain modeling, building extraction
30. **Mechanical Engineering & Materials Science** - FEA, material selection, GD&T, failure analysis
31. **Expert 3D Printing & Advanced Manufacturing** - FDM/SLA/SLS, injection mold design, CNC integration
32. **Biocomposites & Eco-Materials Formulation** - Basalt fiber, taro biopolymers, novel material formulation

### Business & Operations (5 skills)

33. **Expert Tax Automation & Multi-Business Strategist** - Federal/state tax calculation, entity optimization
34. **Automated Business Operations Suite** - Review blog automation, rental business, gig economy tracking
35. **Twilio Expert Multi-Business Call Center** - Multi-tenant IVR, AI call answering, SMS campaigns
36. **Stealth Inventory Tracker & Amazon/Vine Silent Scraper** - Amazon intelligence, Vine tracking, stealth mode

### Specialized Domains (2 skills)

37. **Hawaiian History & Genealogy Expert** - Ali'i genealogy, Hawaiian Kingdom history, land records
38. **Portuguese & Maori/NZ Genealogy Expert** - Portuguese emigration, Māori whakapapa, Polynesian migration
39. **Historical Research & Archives** - NARA access, Library of Congress, genealogy records

---

## Architecture

```
revvel-expert-skills/
├── revvel_skills.py          # Main application entry point
├── skills/                    # 39 skill modules
│   ├── dna_forensics.py
│   ├── caselaw_expert.py
│   ├── legal_brief_writing.py
│   ├── ... (36 more)
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── LICENSE                    # License file
└── tests/                     # Additional test files (optional)
```

Each skill module follows this structure:

```python
# Metadata
SKILL_METADATA = {
    "name": "Skill Name",
    "id": "skill_id",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "...",
    "capabilities": [...],
    "domain": "...",
}

# Expert prompts
EXPERT_PROMPTS = {...}

# Integration points
INTEGRATION_POINTS = {...}

# Utility functions
def function_name(...):
    ...

# Skill engine class
class SkillEngine:
    ...

# Unit tests
class TestSkillName(unittest.TestCase):
    ...
```

---

## Binary Distribution

To package as a standalone binary using PyInstaller:

```bash
pyinstaller --onefile --name revvel-skills revvel_skills.py
```

The binary will be in `dist/revvel-skills`.

---

## Development

### Code Review

All code has been reviewed with **DeepSeek V3.2 Speciale** for quality assurance.

### Testing

Run all tests:

```bash
python3 -m pytest skills/ -v --tb=short
```

### Adding New Skills

1. Create a new Python file in `skills/` following the template structure
2. Include SKILL_METADATA, EXPERT_PROMPTS, INTEGRATION_POINTS
3. Implement utility functions and SkillEngine class
4. Add comprehensive unit tests
5. Update this README

---

## License

Proprietary - Revvel Platform

---

## Credits

**Generated by**: Kimo (moonshotai/kimi-k2) via OpenRouter  
**Code Review**: DeepSeek V3.2 Speciale  
**Platform**: Revvel AI Engine  
**Author**: MIDNGHTSAPPHIRE

---

## Support

For issues, questions, or feature requests, please open an issue on GitHub:  
https://github.com/MIDNGHTSAPPHIRE/revvel-expert-skills

---

## Changelog

### v1.0.0 (2026-02-14)

- Initial release with 39 expert skills
- Comprehensive coverage across legal, medical, intelligence, technology, and business domains
- Full Python implementations with tests
- CLI interface for skill management
- PyInstaller packaging support
