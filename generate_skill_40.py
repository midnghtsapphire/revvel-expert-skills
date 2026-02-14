#!/usr/bin/env python3
"""
Generate Skill #40: Expert Full-Stack App Developer using Kimo
"""
import os
import requests

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "moonshotai/kimi-k2"

SKILL_INFO = {
    "id": "fullstack_app_developer",
    "name": "Expert Full-Stack App Developer — Soup to Nuts",
    "description": """Every single piece of building a production app from zero to deployed. UI/UX DESIGN: Glassmorphism design system (Revvel's preferred aesthetic — frosted glass, blur effects, transparency, subtle borders), neurodivergent-friendly design (ADHD-optimized: clear hierarchy, minimal distractions, progress indicators, chunked content, high contrast options, customizable layouts, focus mode, reduced animation option), NO BLUE LIGHT mode (warm color palette option, night mode, f.lux-style color temperature adjustment, dark mode with warm tones, configurable color temperature slider), accessibility (WCAG 2.2 AAA compliance, screen reader support, keyboard navigation, dyslexia-friendly fonts like OpenDyslexic, adjustable text size/spacing), best-in-class images and graphics (AI-generated hero images, custom illustrations, icon systems, Lottie animations, SVG optimization), responsive design (mobile-first, tablet, desktop, TV), micro-interactions and haptic feedback, onboarding flow design (progressive disclosure, tooltips, walkthrough), design token system (colors, spacing, typography, shadows, borders — all configurable). FRONTEND: React + TypeScript + Vite (Revvel's stack), Tailwind CSS + shadcn/ui component library, state management (Zustand or Jotai), form handling (React Hook Form + Zod validation), routing (React Router or TanStack Router), PWA support (service workers, offline mode, push notifications), performance optimization (code splitting, lazy loading, tree shaking, bundle analysis), SEO (meta tags, Open Graph, structured data, sitemap generation), analytics integration (Google Analytics, Mixpanel, PostHog), error boundaries and crash reporting (Sentry), internationalization (i18n — multi-language support). BACKEND: Express + tRPC + Drizzle ORM (Revvel's stack), PostgreSQL database design (schema, migrations, indexes, constraints), authentication system (email/password, OAuth — Google/Apple/GitHub, magic links, 2FA/MFA), authorization (RBAC — role-based access control, permissions system), API design (REST and/or tRPC endpoints), rate limiting and DDoS protection, input validation and sanitization, file upload handling (S3/R2, image optimization, CDN), email system (transactional emails, templates, Resend/SendGrid), background jobs (Bull/BullMQ queue processing), WebSocket support (real-time features), caching (Redis), logging and monitoring (structured logging, health checks). SUBSCRIPTION & PAYMENTS: Stripe integration (checkout, subscriptions, customer portal, webhooks), pricing page design (free/pro/enterprise tiers), trial periods and grace periods, usage-based billing option, invoice generation, promo codes and discounts, subscription lifecycle management (upgrade, downgrade, cancel, pause), revenue analytics dashboard, tax handling (Stripe Tax). LOGIN & AUTH: Email/password with bcrypt hashing, OAuth providers (Google, Apple, GitHub, Facebook), magic link authentication, two-factor authentication (TOTP, SMS, email), session management (JWT + refresh tokens or session cookies), password reset flow, email verification flow, account deletion (GDPR compliance), social login linking (connect multiple providers to one account). MARKETING & GROWTH: Landing page builder (hero, features, pricing, testimonials, FAQ, CTA), SEO optimization (Search Everywhere Optimization — Google, ChatGPT, Perplexity, TikTok), blog/content system, email marketing integration (drip campaigns, newsletters), referral system, social sharing, App Store Optimization (ASO) for mobile, A/B testing framework, user feedback collection (in-app surveys, NPS), changelog/what's new system. ECO CODE / GREEN ENGINEERING: Efficient algorithms (minimize CPU cycles), optimized database queries (N+1 prevention, query planning), image optimization (WebP/AVIF, responsive images, lazy loading), CDN utilization (minimize server load), carbon footprint estimation per deployment, green hosting recommendations (carbon-neutral providers), minimal JavaScript bundle sizes, server-side rendering where beneficial, caching strategies to reduce redundant computation, efficient CI/CD pipelines (minimize build times and resources). TESTING: Unit tests (Vitest for frontend, Jest for backend), integration tests, E2E tests (Playwright), API tests, performance tests (Lighthouse, k6), accessibility tests (axe-core), visual regression tests, load testing, security testing (OWASP ZAP). DEPLOYMENT: Docker containerization, CI/CD pipeline (GitHub Actions), auto-deploy to Play Store and Apple App Store (Expo/EAS), web deployment (Vercel, DigitalOcean, Railway), database migrations in CI, environment management (dev, staging, production), SSL/TLS configuration, domain and DNS setup, monitoring and alerting (uptime, errors, performance). MOBILE (React Native / Expo): Expo managed workflow, native module integration when needed, push notifications (Expo Notifications, FCM, APNs), deep linking, App Store submission automation, over-the-air updates (EAS Update), biometric authentication (FaceID, fingerprint), camera, location, contacts integration, offline-first with sync. This skill should be able to GENERATE a complete app from a description."""
}

SYSTEM_PROMPT = """You are Kimo, an expert Python developer building production-grade skill modules for Revvel, a legal/forensic AI platform. You write clean, well-documented, fully functional Python code.

CRITICAL RULES:
1. Output ONLY valid Python code — no markdown, no ```python blocks, no explanatory text before or after the code.
2. The code must be a complete, self-contained Python module.
3. Include ALL imports at the top.
4. Every function must have full docstrings and type hints.
5. Include a SKILL_METADATA dict at module level.
6. Include EXPERT_PROMPTS dict with at least 8 expert-level prompt templates.
7. Include INTEGRATION_POINTS dict listing APIs, databases, and tools.
8. Include a comprehensive test class using unittest at the bottom.
9. All utility functions must be real, working implementations (not stubs).
10. Use requests, json, os, re, datetime, hashlib, collections, statistics, math as needed.
11. Do NOT use any external packages beyond the Python standard library plus requests.
12. The module must be importable and all tests must pass when run.
"""

user_prompt = f"""Generate a complete, production-grade Python module for the Revvel platform skill: **{SKILL_INFO['name']}**

Domain coverage: {SKILL_INFO['description']}

The module MUST include:

1. SKILL_METADATA = {{
    "name": "{SKILL_INFO['name']}",
    "id": "{SKILL_INFO['id']}",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "...",
    "capabilities": [...list of capabilities...],
    "domain": "...",
}}

2. EXPERT_PROMPTS = {{}} — At least 10 expert-level prompt templates for different use cases in this domain. Each prompt should be a multi-line string with placeholders like {{variable_name}}.

3. INTEGRATION_POINTS = {{}} — Dict mapping integration names to dicts with keys: "type" (api/database/tool), "endpoint", "description", "auth_method", "documentation_url"

4. At least 15 utility functions that provide REAL implementations:
   - Project scaffolding generators
   - Code template generators
   - Configuration file generators
   - Deployment script generators
   - Database schema generators
   - API endpoint generators
   - Component generators
   - Testing framework setup
   - CI/CD pipeline generators
   - Helper/utility functions specific to the domain

5. A SkillEngine class that:
   - Has an __init__ that accepts config dict
   - Has methods for each major capability
   - Has a run() method that dispatches to the right capability
   - Has proper error handling and logging
   - Can generate complete app projects from descriptions

6. A test class (unittest.TestCase) with at least 10 test methods covering:
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
    "max_tokens": 32000,
    "top_p": 0.9,
}

print(f"\n{'='*80}")
print(f"GENERATING SKILL #40: {SKILL_INFO['name']}")
print(f"{'='*80}\n")
print(f"Using Kimo (kimi-k2) via OpenRouter...")

try:
    resp = requests.post(ENDPOINT, headers=headers, json=payload, timeout=600)
    resp.raise_for_status()
    data = resp.json()

    if "choices" in data and len(data["choices"]) > 0:
        content = data["choices"][0]["message"]["content"]
        
        # Strip markdown code fences if present
        if content.startswith("```python"):
            content = content[len("```python"):].strip()
        if content.startswith("```"):
            content = content[3:].strip()
        if content.endswith("```"):
            content = content[:-3].strip()
        
        output_path = f"skills/{SKILL_INFO['id']}.py"
        with open(output_path, "w") as f:
            f.write(content)
        
        print(f"\n✓ Generated: {output_path}")
        print(f"  Size: {len(content)} characters")
        print(f"  Lines: {len(content.splitlines())}")
        print(f"\n{'='*80}\n")
    else:
        print(f"\n✗ Unexpected response from API")
        print(f"{data}")

except Exception as e:
    print(f"\n✗ Error: {e}")
