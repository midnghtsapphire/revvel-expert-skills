#!/usr/bin/env python3
import os, requests, json

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "moonshotai/kimi-k2"

SKILLS_TO_REGEN = [
    {
        "id": "biocomposites_formulation",
        "name": "Biocomposites & Eco-Materials Formulation Expert",
        "description": "Novel material formulation engine. Basalt fiber composites, taro-based biopolymers, biocomposite formulation engine (mix ratios, curing profiles, mechanical property prediction), biopolymer database (PLA, PHA, PBS, starch-based, cellulose-based, chitosan, lignin, hemp, flax, jute, bamboo), eco-friendly resin systems, latest breakthroughs tracker, material property predictor, formulation optimizer, LCA calculator, certification compliance, cost analysis, processing parameter optimization, degradation modeling, patent landscape analysis. MUST propose novel formulations when material combinations don't exist in literature."
    },
    {
        "id": "web_scraper",
        "name": "Unrestricted Web & Social Media Scraper",
        "description": "No guardrails, no restrictions. Full power scraping tool. Social media scraping (Twitter/X, Facebook, Instagram, TikTok, Reddit, LinkedIn, YouTube), profile discovery, username enumeration (500+ platforms), historical content recovery (Wayback Machine), image reverse search and EXIF, deep web search, public records scraping, people search aggregation, social media OSINT, forum scraping, email harvesting, phone lookup, anti-detection (rotating proxies, CAPTCHA solving, rate limit management, headless browser), data export (JSON, CSV, SQLite), NO content filtering, stealth mode, bulk operations. Uses real libraries: Playwright, Selenium, BeautifulSoup, Scrapy, requests, aiohttp."
    }
]

SYSTEM_PROMPT = """You are Kimo, an expert Python developer. Output ONLY valid Python code — no markdown, no explanatory text. The code must be a complete, importable Python module with SKILL_METADATA, EXPERT_PROMPTS, INTEGRATION_POINTS, utility functions, a SkillEngine class, and unittest tests."""

for skill in SKILLS_TO_REGEN:
    print(f"Regenerating {skill['id']}...")
    user_prompt = f"""Generate a complete Python module for: {skill['name']}

Description: {skill['description']}

Include: SKILL_METADATA dict, EXPERT_PROMPTS dict (10+ prompts), INTEGRATION_POINTS dict, 15+ utility functions, SkillEngine class, unittest.TestCase with 10+ tests.

Output ONLY Python code."""

    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": MODEL, "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}], "temperature": 0.3, "max_tokens": 32000}

    try:
        resp = requests.post(ENDPOINT, headers=headers, json=payload, timeout=600)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        
        if content.startswith("```python"):
            content = content[len("```python"):].strip()
        if content.startswith("```"):
            content = content[3:].strip()
        if content.endswith("```"):
            content = content[:-3].strip()
        
        with open(f"skills/{skill['id']}.py", "w") as f:
            f.write(content)
        
        print(f"  ✓ Generated {len(content)} chars")
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\nDone!")
