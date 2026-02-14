#!/usr/bin/env python3
"""
Code Review and Fix Script using DeepSeek V3.2 Speciale
Fixes syntax errors in generated skill modules.
"""
import os
import requests
import json
from pathlib import Path

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-r1"  # DeepSeek V3.2 Speciale

# Skills with syntax errors that need fixing
BROKEN_SKILLS = [
    "expert_witness",
    "neurodegenerative",
    "anti_aging",
    "cardiovascular",
    "medical_doctor",
    "nanotech_surgery",
    "hawaiian_genealogy",
    "advanced_manufacturing",
    "web_scraper",
    "biocomposites_formulation",
    "epstein_files_intel",
    "stealth_lead_gen",
]

SYSTEM_PROMPT = """You are DeepSeek V3.2 Speciale, an expert Python code reviewer and debugger.

Your task is to fix syntax errors in Python code while preserving all functionality and structure.

CRITICAL RULES:
1. Fix ONLY syntax errors (unterminated strings, unmatched brackets, invalid characters, indentation)
2. Do NOT change the logic, structure, or functionality of the code
3. Do NOT remove or simplify any features
4. Preserve all comments, docstrings, and metadata
5. Output ONLY the corrected Python code
6. No markdown, no explanations, just pure Python code
"""

def fix_skill_file(skill_id: str) -> bool:
    """Fix syntax errors in a skill file using DeepSeek."""
    skill_path = Path(f"skills/{skill_id}.py")
    
    if not skill_path.exists():
        print(f"  ✗ File not found: {skill_path}")
        return False
    
    # Read the broken code
    with open(skill_path, "r", encoding="utf-8", errors="ignore") as f:
        broken_code = f.read()
    
    user_prompt = f"""Fix all syntax errors in this Python code. Preserve all functionality, structure, and features.

The code has syntax errors that prevent it from being imported. Common issues include:
- Unterminated string literals
- Unmatched brackets/parentheses
- Invalid characters (e.g., Chinese colon instead of ASCII colon)
- Indentation errors
- Unclosed dictionaries or lists

Output ONLY the corrected Python code with no markdown formatting.

```python
{broken_code}
```"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://revvel.app",
        "X-Title": "Revvel Code Review",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,  # Low temperature for precise fixes
        "max_tokens": 32000,
    }

    try:
        print(f"  → Reviewing {skill_id}...")
        resp = requests.post(ENDPOINT, headers=headers, json=payload, timeout=300)
        resp.raise_for_status()
        data = resp.json()

        if "choices" in data and len(data["choices"]) > 0:
            fixed_code = data["choices"][0]["message"]["content"]
            
            # Strip markdown code fences if present
            if fixed_code.startswith("```python"):
                fixed_code = fixed_code[len("```python"):].strip()
            if fixed_code.startswith("```"):
                fixed_code = fixed_code[3:].strip()
            if fixed_code.endswith("```"):
                fixed_code = fixed_code[:-3].strip()
            
            # Write the fixed code
            with open(skill_path, "w", encoding="utf-8") as f:
                f.write(fixed_code)
            
            print(f"  ✓ Fixed: {skill_id} ({len(fixed_code)} chars)")
            return True
        else:
            print(f"  ✗ Unexpected response for {skill_id}")
            return False
    
    except Exception as e:
        print(f"  ✗ Error fixing {skill_id}: {e}")
        return False


def main():
    print(f"\n{'='*80}")
    print(f"CODE REVIEW WITH DEEPSEEK V3.2 SPECIALE")
    print(f"{'='*80}\n")
    print(f"Fixing {len(BROKEN_SKILLS)} skills with syntax errors...\n")
    
    results = {}
    for skill_id in BROKEN_SKILLS:
        success = fix_skill_file(skill_id)
        results[skill_id] = "success" if success else "failed"
    
    print(f"\n{'='*80}")
    print("REVIEW SUMMARY")
    print(f"{'='*80}")
    
    success_count = sum(1 for v in results.values() if v == "success")
    failed_count = len(results) - success_count
    
    print(f"  Fixed:  {success_count}/{len(BROKEN_SKILLS)}")
    print(f"  Failed: {failed_count}/{len(BROKEN_SKILLS)}")
    
    if failed_count > 0:
        print(f"\nFailed skills:")
        for skill_id, status in results.items():
            if status == "failed":
                print(f"  - {skill_id}")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
