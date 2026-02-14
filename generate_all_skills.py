#!/usr/bin/env python3
"""
Revvel Expert Skills Generator (Final Optimized Version)
Generates all 33 expert skills using Kimo (kimi-k2) via OpenRouter in parallel.
"""
import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Import SKILLS from the main generation script
with open('/home/ubuntu/revvel-expert-skills/generate_skills.py', 'r') as f:
    content = f.read()
    # Extract just the SKILLS list
    skills_section = content.split('SKILLS = [')[1].split('\n]\n')[0]
    exec(f'SKILLS = [{skills_section}\n]')

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "moonshotai/kimi-k2"

SYSTEM_PROMPT = """You are Kimo, an expert Python developer building production-grade skill modules for Revvel, a legal/forensic AI platform. You write clean, well-documented, fully functional Python code.

CRITICAL RULES:
1. Output ONLY valid Python code — no markdown, no ```python blocks, no explanatory text before or after the code.
2. The code must be a complete, self-contained Python module.
3. Include ALL imports at the top.
4. Every function must have full docstrings and type hints.
5. Include a SKILL_METADATA dict at module level.
6. Include EXPERT_PROMPTS dict with at least 5 expert-level prompt templates.
7. Include INTEGRATION_POINTS dict listing APIs, databases, and tools.
8. Include a comprehensive test class using unittest at the bottom.
9. All utility functions must be real, working implementations (not stubs).
10. Use requests, json, os, re, datetime, hashlib, collections, statistics, math as needed.
11. Do NOT use any external packages beyond the Python standard library plus requests.
12. The module must be importable and all tests must pass when run.
"""

def generate_skill(skill_info):
    """Call Kimo via OpenRouter to generate a single skill module."""
    filepath = f"skills/{skill_info['id']}.py"
    
    # Skip if already exists and is substantial
    if os.path.exists(filepath):
        file_size = os.path.getsize(filepath)
        if file_size > 5000:
            return {
                "id": skill_info['id'],
                "status": "skipped",
                "file": filepath,
                "size": file_size,
                "message": f"Already exists ({file_size} bytes)"
            }
    
    user_prompt = f"""Generate a complete, production-grade Python module for the Revvel platform skill: **{skill_info['name']}**

Domain coverage: {skill_info['description']}

The module MUST include:

1. SKILL_METADATA = {{
    "name": "{skill_info['name']}",
    "id": "{skill_info['id']}",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "...",
    "capabilities": [...list of capabilities...],
    "domain": "...",
}}

2. EXPERT_PROMPTS = {{}} — At least 8 expert-level prompt templates for different use cases in this domain. Each prompt should be a multi-line string with placeholders like {{variable_name}}.

3. INTEGRATION_POINTS = {{}} — Dict mapping integration names to dicts with keys: "type" (api/database/tool), "endpoint", "description", "auth_method", "documentation_url"

4. At least 10 utility functions that provide REAL implementations:
   - Data parsing and validation functions
   - Analysis and computation functions  
   - Report generation functions
   - Query builder functions
   - Template rendering functions
   - Helper/utility functions specific to the domain

5. A SkillEngine class that:
   - Has an __init__ that accepts config dict
   - Has methods for each major capability
   - Has a run() method that dispatches to the right capability
   - Has proper error handling and logging

6. A test class (unittest.TestCase) with at least 8 test methods covering:
   - Metadata validation
   - Each major utility function
   - The SkillEngine class
   - Edge cases and error handling

Output ONLY the Python code. No markdown. No explanation. Just pure Python starting with the imports."""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://revvel.app",
        "X-Title": "Revvel Expert Skills Generator",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 16000,
        "top_p": 0.9,
    }

    try:
        start_time = time.time()
        resp = requests.post(ENDPOINT, headers=headers, json=payload, timeout=300)
        resp.raise_for_status()
        data = resp.json()
        elapsed = time.time() - start_time

        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0]["message"]["content"]
            # Strip markdown code fences if present
            if content.startswith("```python"):
                content = content[len("```python"):].strip()
            if content.startswith("```"):
                content = content[3:].strip()
            if content.endswith("```"):
                content = content[:-3].strip()
            
            with open(filepath, "w") as f:
                f.write(content)
            
            return {
                "id": skill_info['id'],
                "status": "success",
                "file": filepath,
                "size": len(content),
                "elapsed": elapsed,
                "message": f"Generated {len(content)} chars in {elapsed:.1f}s"
            }
        else:
            return {
                "id": skill_info['id'],
                "status": "failed",
                "message": f"Unexpected response: {json.dumps(data)[:200]}"
            }
    except Exception as e:
        return {
            "id": skill_info['id'],
            "status": "failed",
            "message": f"Error: {str(e)}"
        }


def main():
    os.makedirs("skills", exist_ok=True)
    
    print(f"\n{'='*80}")
    print(f"REVVEL EXPERT SKILLS GENERATOR — FINAL BUILD")
    print(f"Total skills to generate: {len(SKILLS)}")
    print(f"Using model: {MODEL}")
    print(f"Concurrent workers: 5")
    print(f"{'='*80}\n")
    
    results = {}
    start_time = time.time()
    
    # Use ThreadPoolExecutor for parallel generation
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_skill = {executor.submit(generate_skill, skill): skill for skill in SKILLS}
        
        completed = 0
        for future in as_completed(future_to_skill):
            skill = future_to_skill[future]
            try:
                result = future.result()
                results[result['id']] = result
                completed += 1
                
                status_icon = "✓" if result['status'] == "success" else ("⊙" if result['status'] == "skipped" else "✗")
                progress = f"[{completed}/{len(SKILLS)}]"
                print(f"{status_icon} {progress:10s} {skill['name']:55s} | {result['message']}")
                
            except Exception as exc:
                results[skill['id']] = {
                    "id": skill['id'],
                    "status": "failed",
                    "message": f"Exception: {exc}"
                }
                completed += 1
                print(f"✗ [{completed}/{len(SKILLS)}] {skill['name']:55s} | Exception: {exc}")
    
    total_elapsed = time.time() - start_time
    
    # Summary
    print(f"\n{'='*80}")
    print("GENERATION SUMMARY")
    print(f"{'='*80}")
    
    success = sum(1 for v in results.values() if v["status"] == "success")
    skipped = sum(1 for v in results.values() if v["status"] == "skipped")
    failed = sum(1 for v in results.values() if v["status"] == "failed")
    
    print(f"  Success:       {success}/{len(SKILLS)}")
    print(f"  Skipped:       {skipped}/{len(SKILLS)}")
    print(f"  Failed:        {failed}/{len(SKILLS)}")
    print(f"  Total time:    {total_elapsed:.1f}s")
    print(f"  Avg per skill: {total_elapsed/len(SKILLS):.1f}s")
    print(f"{'='*80}\n")
    
    with open("generation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: generation_results.json\n")
    
    if failed > 0:
        print("FAILED SKILLS:")
        for skill_id, result in results.items():
            if result['status'] == 'failed':
                print(f"  - {skill_id}: {result['message']}")
        print()


if __name__ == "__main__":
    main()
