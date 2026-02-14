import os
import json
import re
import shutil
import subprocess
import hashlib
import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import requests
import zipfile
import tempfile
import unittest
from collections import defaultdict
import uuid

SKILL_METADATA = {
    "name": "Expert Full-Stack App Developer — Soup to Nuts",
    "id": "fullstack_app_developer",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Complete full-stack application development from zero to production deployment. Covers UI/UX design with glassmorphism and neurodivergent-friendly patterns, React/TypeScript frontend, Express/tRPC backend, PostgreSQL, authentication, payments, mobile apps, testing, deployment, and green engineering practices.",
    "capabilities": [
        "glassmorphism_design_system",
        "neurodivergent_friendly_ui",
        "no_blue_light_mode",
        "wcag_aaa_accessibility",
        "react_typescript_frontend",
        "express_trpc_backend",
        "postgresql_database",
        "stripe_payments",
        "oauth_authentication",
        "mobile_react_native",
        "docker_deployment",
        "ci_cd_pipeline",
        "testing_suite",
        "seo_optimization",
        "green_engineering",
        "project_scaffolding",
        "code_generation",
        "deployment_automation"
    ],
    "domain": "full_stack_application_development"
}

EXPERT_PROMPTS = {
    "generate_complete_app": """
Create a complete full-stack application called "{app_name}" with the following requirements:
- Purpose: {purpose}
- Target audience: {target_audience}
- Core features: {core_features}
- Monetization model: {monetization}
- Platforms: {platforms}
- Special requirements: {special_requirements}

Include glassmorphism UI design, neurodivergent-friendly features, and full production deployment setup.
""",
    
    "design_glassmorphism_system": """
Design a comprehensive glassmorphism design system for {project_name} with:
- Primary color palette: {primary_colors}
- Transparency levels: {transparency_levels}
- Blur effects: {blur_intensity}
- Border styles: {border_styles}
- Include dark/light/warm modes
- Typography scale for {font_family}
- Spacing system based on {base_unit}
""",
    
    "create_neurodivergent_ui": """
Implement neurodivergent-friendly UI features for {app_name} including:
- ADHD-optimized layouts with {layout_preferences}
- Focus mode implementation
- Reduced animation toggle
- High contrast options
- Progress indicators for {task_types}
- Chunked content display
- Customizable layouts
""",
    
    "setup_react_frontend": """
Initialize React + TypeScript + Vite frontend for {project_name} with:
- Tailwind CSS configuration
- shadcn/ui component library
- State management with {state_management}
- Routing with {router_type}
- PWA setup with offline support
- SEO optimization
- Performance optimizations
""",
    
    "create_express_backend": """
Set up Express + tRPC + Drizzle backend for {project_name} with:
- PostgreSQL schema for {data_models}
- Authentication system ({auth_methods})
- Authorization with RBAC
- Rate limiting and security
- File upload handling
- Email system with {email_provider}
- Background job processing
""",
    
    "implement_stripe_integration": """
Implement complete Stripe integration for {project_name} with:
- Pricing tiers: {pricing_tiers}
- Subscription management
- Usage-based billing for {usage_metrics}
- Trial periods: {trial_days} days
- Promo codes and discounts
- Customer portal
- Revenue analytics
""",
    
    "setup_mobile_app": """
Create React Native/Expo mobile app for {project_name} with:
- Feature parity with web
- Push notifications
- Biometric authentication
- Deep linking
- Offline-first architecture
- App Store deployment
- OTA updates
""",
    
    "configure_deployment": """
Set up complete deployment pipeline for {project_name} including:
- Docker containerization
- CI/CD with GitHub Actions
- {deployment_platform} deployment
- Database migrations
- SSL/TLS configuration
- Monitoring and alerting
- Environment management
""",
    
    "implement_testing_suite": """
Create comprehensive testing suite for {project_name} with:
- Unit tests ({test_coverage}% coverage)
- Integration tests for {integration_points}
- E2E tests with Playwright
- Performance testing
- Accessibility testing
- Security testing
- Visual regression tests
""",
    
    "optimize_green_engineering": """
Implement green engineering practices for {project_name} including:
- Efficient algorithms for {performance_critical_features}
- Database query optimization
- Image optimization strategies
- CDN configuration
- Carbon footprint monitoring
- Bundle size optimization
- Server-side rendering decisions
- Caching strategies
""",
    
    "create_marketing_site": """
Build marketing landing page for {project_name} with:
- Hero section highlighting {value_proposition}
- Features section covering {key_features}
- Pricing page with {pricing_strategy}
- Testimonials and social proof
- SEO optimization
- A/B testing setup
- Analytics integration
"""
}

INTEGRATION_POINTS = {
    "stripe": {
        "type": "api",
        "endpoint": "https://api.stripe.com/v1",
        "description": "Payment processing and subscription management",
        "auth_method": "Bearer token",
        "documentation_url": "https://stripe.com/docs/api"
    },
    "postgresql": {
        "type": "database",
        "endpoint": "postgresql://localhost:5432",
        "description": "Primary database for application data",
        "auth_method": "Username/password",
        "documentation_url": "https://www.postgresql.org/docs/"
    },
    "resend": {
        "type": "api",
        "endpoint": "https://api.resend.com",
        "description": "Transactional email service",
        "auth_method": "Bearer token",
        "documentation_url": "https://resend.com/docs"
    },
    "sentry": {
        "type": "tool",
        "endpoint": "https://sentry.io/api",
        "description": "Error tracking and performance monitoring",
        "auth_method": "DSN token",
        "documentation_url": "https://docs.sentry.io/"
    },
    "vercel": {
        "type": "tool",
        "endpoint": "https://api.vercel.com",
        "description": "Frontend deployment platform",
        "auth_method": "Bearer token",
        "documentation_url": "https://vercel.com/docs/rest-api"
    },
    "railway": {
        "type": "tool",
        "endpoint": "https://backboard.railway.app/graphql/v2",
        "description": "Backend deployment platform",
        "auth_method": "Bearer token",
        "documentation_url": "https://docs.railway.app/"
    },
    "github": {
        "type": "tool",
        "endpoint": "https://api.github.com",
        "description": "Source control and CI/CD",
        "auth_method": "Personal access token",
        "documentation_url": "https://docs.github.com/en/rest"
    },
    "redis": {
        "type": "database",
        "endpoint": "redis://localhost:6379",
        "description": "Caching and session storage",
        "auth_method": "Password",
        "documentation_url": "https://redis.io/documentation"
    },
    "cloudflare_r2": {
        "type": "api",
        "endpoint": "https://api.cloudflare.com/client/v4",
        "description": "File storage and CDN",
        "auth_method": "API token",
        "documentation_url": "https://developers.cloudflare.com/r2/api/"
    },
    "expo": {
        "type": "tool",
        "endpoint": "https://exp.host/--/api/v2",
        "description": "React Native app development and deployment",
        "auth_method": "Bearer token",
        "documentation_url": "https://docs.expo.dev/workflow/expo-cli/"
    }
}

class FullStackAppDeveloper:
    """Expert full-stack application development skill for Revvel platform."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.project_name = self.config.get("project_name", "my-app")
        self.project_root = Path(self.config.get("project_root", "."))
        
    def generate_project_structure(self) -> Dict[str, Any]:
        """Generate complete project structure for full-stack application."""
        structure = {
            "frontend": {
                "src": {
                    "components": {},
                    "pages": {},
                    "hooks": {},
                    "lib": {},
                    "store": {},
                    "styles": {},
                    "types": {},
                    "utils": {}
                },
                "public": {},
                "tests": {}
            },
            "backend": {
                "src": {
                    "routes": {},
                    "services": {},
                    "models": {},
                    "middleware": {},
                    "utils": {},
                    "types": {}
                },
                "tests": {}
            },
            "mobile": {
                "src": {
                    "screens": {},
                    "components": {},
                    "services": {},
                    "utils": {}
                }
            },
            "shared": {
                "types": {},
                "utils": {}
            },
            "infrastructure": {
                "docker": {},
                "k8s": {},
                "terraform": {}
            },
            "docs": {},
            "scripts": {}
        }
        
        # Create directories
        for main_dir, subdirs in structure.items():
            self._create_nested_dirs(self.project_root / main_dir, subdirs)
            
        return structure
    
    def _create_nested_dirs(self, base_path: Path, structure: Dict[str, Any]):
        """Recursively create nested directory structure."""
        for name, content in structure.items():
            dir_path = base_path / name
            dir_path.mkdir(parents=True, exist_ok=True)
            if isinstance(content, dict) and content:
                self._create_nested_dirs(dir_path, content)
    
    def generate_package_json(self, project_type: str = "frontend") -> Dict[str, Any]:
        """Generate package.json for different project types."""
        base_package = {
            "name": self.project_name,
            "version": "1.0.0",
            "private": True,
            "scripts": {}
        }
        
        if project_type == "frontend":
            return {
                **base_package,
                "type": "module",
                "scripts": {
                    "dev": "vite",
                    "build": "tsc && vite build",
                    "preview": "vite preview",
                    "test": "vitest",
                    "test:ui": "vitest --ui",
                    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
                    "typecheck": "tsc --noEmit"
                },
                "dependencies": {
                    "react": "^18.2.0",
                    "react-dom": "^18.2.0",
                    "react-router-dom": "^6.8.0",
                    "zustand": "^4.4.0",
                    "tailwindcss": "^3.3.0",
                    "clsx": "^2.0.0",
                    "lucide-react": "^0.263.0"
                },
                "devDependencies": {
                    "@types/react": "^18.2.15",
                    "@types/react-dom": "^18.2.7",
                    "@vitejs/plugin-react": "^4.0.3",
                    "autoprefixer": "^10.4.14",
                    "postcss": "^8.4.24",
                    "typescript": "^5.0.2",
                    "vite": "^4.4.5",
                    "vitest": "^0.34.0",
                    "@testing-library/react": "^13.4.0",
                    "@testing-library/jest-dom": "^5.16.5"
                }
            }
        elif project_type == "backend":
            return {
                **base_package,
                "type": "module",
                "scripts": {
                    "dev": "tsx watch src/index.ts",
                    "build": "tsc",
                    "start": "node dist/index.js",
                    "db:generate": "drizzle-kit generate:pg",
                    "db:migrate": "tsx src/db/migrate.ts",
                    "db:studio": "drizzle-kit studio",
                    "test": "jest",
                    "test:watch": "jest --watch"
                },
                "dependencies": {
                    "express": "^4.18.2",
                    "@trpc/server": "^10.38.0",
                    "drizzle-orm": "^0.28.0",
                    "postgres": "^3.3.5",
                    "zod": "^3.22.0",
                    "bcryptjs": "^2.4.3",
                    "jsonwebtoken": "^9.0.2",
                    "cors": "^2.8.5",
                    "helmet": "^7.0.0",
                    "express-rate-limit": "^6.8.0",
                    "multer": "^1.4.5-lts.1",
                    "nodemailer": "^6.9.0",
                    "redis": "^4.6.0",
                    "bullmq": "^4.0.0"
                },
                "devDependencies": {
                    "@types/express": "^4.17.17",
                    "@types/bcryptjs": "^2.4.2",
                    "@types/jsonwebtoken": "^9.0.2",
                    "@types/cors": "^2.8.13",
                    "@types/multer": "^1.4.7",
                    "@types/nodemailer": "^6.4.8",
                    "tsx": "^3.12.7",
                    "typescript": "^5.0.2",
                    "drizzle-kit": "^0.19.0",
                    "jest": "^29.6.0",
                    "@types/jest": "^29.5.0",
                    "ts-jest": "^29.1.0"
                }
            }
        elif project_type == "mobile":
            return {
                **base_package,
                "main": "node_modules/expo/AppEntry.js",
                "scripts": {
                    "start": "expo start",
                    "android": "expo start --android",
                    "ios": "expo start --ios",
                    "web": "expo start --web",
                    "build:android": "eas build -p android",
                    "build:ios": "eas build -p ios",
                    "submit:android": "eas submit -p android",
                    "submit:ios": "eas submit -p ios"
                },
                "dependencies": {
                    "expo": "~49.0.0",
                    "react": "18.2.0",
                    "react-native": "0.72.0",
                    "expo-status-bar": "~1.6.0",
                    "expo-notifications": "~0.20.0",
                    "expo-secure-store": "~12.3.0",
                    "expo-local-authentication": "~13.4.0",
                    "@react-navigation/native": "^6.1.0",
                    "@react-navigation/native-stack": "^6.9.0",
                    "react-native-screens": "~3.22.0",
                    "react-native-safe-area-context": "4.6.0",
                    "zustand": "^4.4.0"
                },
                "devDependencies": {
                    "@babel/core": "^7.20.0",
                    "@types/react": "~18.2.0",
                    "@types/react-native": "~0.72.0",
                    "typescript": "^5.1.0"
                }
            }
        
        return base_package
    
    def generate_tailwind_config(self) -> Dict[str, Any]:
        """Generate Tailwind CSS configuration with glassmorphism support."""
        return {
            "content": [
                "./index.html",
                "./src/**/*.{js,ts,jsx,tsx}",
            ],
            "darkMode": "class",
            "theme": {
                "extend": {
                    "colors": {
                        "glass": {
                            "white": "rgba(255, 255, 255, 0.25)",
                            "black": "rgba(0, 0, 0, 0.25)",
                            "blur": "rgba(255, 255, 255, 0.1)",
                        },
                        "warm": {
                            "50": "#fefdf8",
                            "100": "#fefbf3",
                            "200": "#fdf6e4",
                            "300": "#faf0d4",
                            "400": "#f6e8c0",
                            "500": "#f1dfa8",
                            "600": "#ebd58e",
                            "700": "#e4c973",
                            "800": "#dcbc5a",
                            "900": "#d4ae42",
                        }
                    },
                    "backdropBlur": {
                        "xs": "2px",
                        "sm": "4px",
                        "md": "8px",
                        "lg": "12px",
                        "xl": "16px",
                        "2xl": "24px",
                    },
                    "animation": {
                        "fade-in": "fadeIn 0.5s ease-in-out",
                        "slide-up": "slideUp 0.3s ease-out",
                        "pulse-soft": "pulseSoft 2s infinite",
                    },
                    "keyframes": {
                        "fadeIn": {
                            "0%": { "opacity": "0" },
                            "100%": { "opacity": "1" }
                        },
                        "slideUp": {
                            "0%": { "transform": "translateY(10px)", "opacity": "0" },
                            "100%": { "transform": "translateY(0)", "opacity": "1" }
                        },
                        "pulseSoft": {
                            "0%, 100%": { "opacity": "1" },
                            "50%": { "opacity": "0.8" }
                        }
                    }
                }
            },
            "plugins": []
        }
    
    def generate_database_schema(self, models: List[Dict[str, Any]]) -> str:
        """Generate PostgreSQL schema using Drizzle ORM."""
        schema_content = """import { pgTable, serial, varchar, text, timestamp, boolean, integer, decimal, jsonb } from 'drizzle-orm/pg-core';
import { relations } from 'drizzle-orm';

"""
        
        for model in models:
            table_name = model["name"]
            fields = model["fields"]
            
            schema_content += f"export const {table_name} = pgTable('{table_name}', {{\n"
            
            for field in fields:
                field_type = field["type"]
                field_name = field["name"]
                constraints = field.get("constraints", [])
                
                schema_content += f"  {field_name}: {field_type}"
                if constraints:
                    schema_content += f".{'.'.join(constraints)}"
                schema_content += ",\n"
            
            schema_content += "});\n\n"
        
        # Add relations
        for model in models:
            if "relations" in model:
                table_name = model["name"]
                schema_content += f"export const {table_name}Relations = relations({table_name}, ({{"
                for relation in model["relations"]:
                    schema_content += f" {relation},"
                schema_content += "}));\n\n"
        
        return schema_content
    
    def generate_react_component(self, component_name: str, props: List[str], 
                               style_type: str = "glassmorphism") -> str:
        """Generate React component with specified styling."""
        props_str = ", ".join([f"{prop}: {self._get_ts_type(prop)}" for prop in props])
        
        component_content = f"""import React from 'react';
import {{ cn }} from '@/lib/utils';
import {{ cva, type VariantProps }} from 'class-variance-authority';

const {component_name.lower()}Variants = cva(
  "rounded-lg border transition-all duration-200",
  {{
    variants: {{
      variant: {{
        default: "bg-glass-white/50 border-white/20 backdrop-blur-md",
        warm: "bg-warm-50/50 border-warm-200/30 backdrop-blur-md",
        dark: "bg-glass-black/50 border-white/10 backdrop-blur-md",
      }},
      size: {{
        default: "p-4",
        sm: "p-2",
        lg: "p-6",
      }},
    }},
    defaultVariants: {{
      variant: "default",
      size: "default",
    }},
  }}
);

export interface {component_name}Props
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof {component_name.lower()}Variants> {{
  {props_str}
}}

export const {component_name} = React.forwardRef<HTMLDivElement, {component_name}Props>(
  ({{ className, variant, size, {", ".join(props)}, ...props }}, ref) => {{
    return (
      <div
        ref={{ref}}
        className={{cn({component_name.lower()}Variants({{ variant, size }}), className)}}
        {{...props}}
      >
        {{/* Component content */}}
      </div>
    );
  }}
);

{component_name}.displayName = "{component_name}";
"""
        
        return component_content
    
    def _get_ts_type(self, prop: str) -> str:
        """Map prop names to TypeScript types."""
        type_map = {
            "children": "React.ReactNode",
            "onClick": "() => void",
            "disabled": "boolean",
            "loading": "boolean",
            "value": "string",
            "onChange": "(value: string) => void",
            "className": "string"
        }
        return type_map.get(prop, "any")
    
    def generate_docker_compose(self, services: List[str]) -> str:
        """Generate Docker Compose configuration."""
        compose_content = """version: '3.8'

services:
"""
        
        if "postgres" in services:
            compose_content += """
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
"""
        
        if "redis" in services:
            compose_content += """
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
"""
        
        if "backend" in services:
            compose_content += """
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "3001:3001"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis
"""
        
        if "frontend" in services:
            compose_content += """
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=${VITE_API_URL}
"""
        
        compose_content += """
volumes:
  postgres_data:
  redis_data:
"""
        
        return compose_content
    
    def generate_github_actions(self, workflows: List[str]) -> str:
        """Generate GitHub Actions CI/CD pipeline."""
        workflow_content = """name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '18'

jobs:
"""
        
        if "test" in workflows:
            workflow_content += """
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          
      - name: Install dependencies
        run: npm ci
        
      - name: Run tests
        run: npm test
        
      - name: Run type check
        run: npm run typecheck
        
      - name: Run linting
        run: npm run lint
"""
        
        if "deploy" in workflows:
            workflow_content += """
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          
      - name: Install dependencies
        run: npm ci
        
      - name: Build application
        run: npm run build
        
      - name: Deploy to production
        run: |
          echo "Deploying to production..."
          # Add deployment commands here
"""
        
        return workflow_content
    
    def generate_nginx_config(self, domains: List[str]) -> str:
        """Generate Nginx configuration for production."""
        domain = domains[0] if domains else "localhost"
        
        return f"""server {{
    listen 80;
    server_name {domain} www.{domain};
    
    location /.well-known/acme-challenge/ {{
        root /var/www/certbot;
    }}
    
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {domain} www.{domain};
    
    ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;
    
    location / {{
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    location /api {{
        proxy_pass http://backend:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    location /trpc {{
        proxy_pass http://backend:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
    
    def generate_environment_files(self, environment: str) -> Dict[str, str]:
        """Generate environment configuration files."""
        env_configs = {
            "development": {
                "frontend": """VITE_API_URL=http://localhost:3001
VITE_ENV=development
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_key
""",
                "backend": """NODE_ENV=development
PORT=3001
DATABASE_URL=postgresql://user:password@localhost:5432/myapp_dev
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-jwt-secret
STRIPE_SECRET_KEY=sk_test_your_stripe_secret
RESEND_API_KEY=re_your_resend_key
""",
                "mobile": """EXPO_PUBLIC_API_URL=http://localhost:3001
EXPO_PUBLIC_ENV=development
"""
            },
            "production": {
                "frontend": """VITE_API_URL=https://api.yourapp.com
VITE_ENV=production
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_key
""",
                "backend": """NODE_ENV=production
PORT=3001
DATABASE_URL=postgresql://user:password@localhost:5432/myapp_prod
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-production-jwt-secret
STRIPE_SECRET_KEY=sk_live_your_stripe_secret
RESEND_API_KEY=re_your_resend_key
""",
                "mobile": """EXPO_PUBLIC_API_URL=https://api.yourapp.com
EXPO_PUBLIC_ENV=production
"""
            }
        }
        
        return env_configs.get(environment, env_configs["development"])
    
    def generate_readme(self, project_info: Dict[str, Any]) -> str:
        """Generate comprehensive README.md."""
        return f"""# {project_info.get('name', self.project_name)}

{project_info.get('description', 'A full-stack application built with modern web technologies.')}

## 🚀 Features

- ✨ **Glassmorphism UI Design** - Beautiful frosted glass effects
- 🧠 **Neurodivergent-Friendly** - ADHD-optimized interface
- 🌙 **No Blue Light Mode** - Warm color temperature options
- ♿ **WCAG 2.2 AAA Compliant** - Full accessibility support
- 📱 **Responsive Design** - Mobile, tablet, desktop, and TV support
- 🔒 **Secure Authentication** - OAuth, 2FA, magic links
- 💳 **Stripe Integration** - Subscriptions and payments
- 📊 **Analytics Dashboard** - Track user engagement
- 🧪 **Comprehensive Testing** - Unit, integration, E2E tests
- 🐳 **Docker Support** - Containerized deployment
- 🌱 **Green Engineering** - Optimized for minimal carbon footprint

## 🛠️ Tech Stack

### Frontend
- React 18 + TypeScript
- Vite for build tooling
- Tailwind CSS for styling
- shadcn/ui components
- Zustand for state management
- React Hook Form + Zod validation
- PWA support

### Backend
- Express.js + tRPC
- Drizzle ORM
- PostgreSQL database
- Redis caching
- BullMQ for background jobs
- Comprehensive security

### Mobile
- React Native + Expo
- Feature parity with web
- Push notifications
- Biometric authentication
- Offline-first architecture

## 🚦 Quick Start

### Prerequisites
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Stripe account

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd {self.project_name}
   ```

2. **Install dependencies**
   ```bash
   # Frontend
   cd frontend && npm install
   
   # Backend
   cd backend && npm install
   
   # Mobile
   cd mobile && npm install
   ```

3. **Set up environment variables**
   ```bash
   # Copy example env files
   cp frontend/.env.example frontend/.env
   cp backend/.env.example backend/.env
   cp mobile/.env.example mobile/.env
   
   # Fill in your actual values
   ```

4. **Set up the database**
   ```bash
   cd backend
   npm run db:generate
   npm run db:migrate
   ```

5. **Start development servers**
   ```bash
   # Terminal 1 - Backend
   cd backend && npm run dev
   
   # Terminal 2 - Frontend
   cd frontend && npm run dev
   
   # Terminal 3 - Mobile (optional)
   cd mobile && npm start
   ```

## 🧪 Testing

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e
```

## 🚀 Deployment

### Using Docker
```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Manual Deployment
See [deployment guide](./docs/deployment.md) for detailed instructions.

## 📚 Documentation

- [Frontend Guide](./docs/frontend.md)
- [Backend API](./docs/api.md)
- [Mobile Development](./docs/mobile.md)
- [Deployment](./docs/deployment.md)
- [Contributing](./docs/contributing.md)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
"""
    
    def generate_accessibility_config(self) -> Dict[str, Any]:
        """Generate accessibility configuration and guidelines."""
        return {
            "wcag_level": "AAA",
            "color_contrast": {
                "normal": 7,
                "large": 4.5
            },
            "font_sizes": {
                "minimum": 16,
                "scalable": True,
                "max_scale": 200
            },
            "keyboard_navigation": True,
            "screen_reader_support": True,
            "focus_indicators": {
                "color": "#0066cc",
                "width": "2px",
                "offset": "2px"
            },
            "reduced_motion": {
                "respects_preference": True,
                "animation_duration": "0.15s"
            },
            "dyslexia_friendly": {
                "font": "OpenDyslexic",
                "line_height": 1.5,
                "letter_spacing": "0.05em"
            }
        }
    
    def generate_stripe_webhook_handler(self) -> str:
        """Generate Stripe webhook handler for backend."""
        return """import { Router } from 'express';
import Stripe from 'stripe';
import { db } from '../db';
import { users, subscriptions } from '../db/schema';
import { eq } from 'drizzle-orm';

const router = Router();
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2023-10-16',
});

const endpointSecret = process.env.STRIPE_WEBHOOK_SECRET!;

router.post('/webhooks/stripe', async (req, res) => {
  const sig = req.headers['stripe-signature'] as string;
  
  let event: Stripe.Event;
  
  try {
    event = stripe.webhooks.constructEvent(req.body, sig, endpointSecret);
  } catch (err) {
    console.log(`Webhook signature verification failed.`, err);
    return res.status(400).send(`Webhook Error`);
  }

  switch (event.type) {
    case 'customer.subscription.created':
    case 'customer.subscription.updated':
      const subscription = event.data.object as Stripe.Subscription;
      
      await db.update(users)
        .set({ 
          subscriptionStatus: subscription.status,
          subscriptionId: subscription.id 
        })
        .where(eq(users.stripeCustomerId, subscription.customer as string));
      break;
      
    case 'customer.subscription.deleted':
      const deletedSubscription = event.data.object as Stripe.Subscription;
      
      await db.update(users)
        .set({ subscriptionStatus: 'canceled' })
        .where(eq(users.stripeCustomerId, deletedSubscription.customer as string));
      break;
      
    case 'invoice.payment_succeeded':
      const invoice = event.data.object as Stripe.Invoice;
      
      if (invoice.subscription) {
        await db.insert(subscriptions).values({
          userId: invoice.customer as string,
          stripeSubscriptionId: invoice.subscription as string,
          amount: invoice.amount_paid,
          status: 'active',
          periodStart: new Date(invoice.period_start * 1000),
          periodEnd: new Date(invoice.period_end * 1000),
        });
      }
      break;
  }

  res.json({ received: true });
});

export default router;
"""
    
    def generate_mobile_app_config(self) -> Dict[str, Any]:
        """Generate Expo/React Native configuration."""
        return {
            "expo": {
                "name": self.project_name,
                "slug": self.project_name.lower(),
                "version": "1.0.0",
                "orientation": "portrait",
                "icon": "./assets/icon.png",
                "userInterfaceStyle": "automatic",
                "splash": {
                    "image": "./assets/splash.png",
                    "resizeMode": "contain",
                    "backgroundColor": "#ffffff"
                },
                "assetBundlePatterns": ["**/*"],
                "ios": {
                    "supportsTablet": True,
                    "bundleIdentifier": f"com.yourcompany.{self.project_name.lower()}"
                },
                "android": {
                    "adaptiveIcon": {
                        "foregroundImage": "./assets/adaptive-icon.png",
                        "backgroundColor": "#ffffff"
                    },
                    "package": f"com.yourcompany.{self.project_name.lower()}"
                },
                "web": {
                    "favicon": "./assets/favicon.png"
                },
                "plugins": [
                    "expo-notifications",
                    "expo-secure-store",
                    "expo-local-authentication"
                ],
                "extra": {
                    "eas": {
                        "projectId": "your-project-id"
                    }
                }
            }
        }
    
    def generate_green_engineering_config(self) -> Dict[str, Any]:
        """Generate green engineering optimization configuration."""
        return {
            "performance_budget": {
                "javascript": 250000,
                "css": 50000,
                "images": 500000,
                "total": 1000000
            },
            "optimization_strategies": {
                "images": {
                    "formats": ["webp", "avif"],
                    "lazy_loading": True,
                    "responsive_sizing": True,
                    "compression": 85
                },
                "javascript": {
                    "code_splitting": True,
                    "tree_shaking": True,
                    "minification": True,
                    "compression": "gzip"
                },
                "css": {
                    "purge_unused": True,
                    "critical_css": True,
                    "minification": True
                },
                "caching": {
                    "static_assets": "1y",
                    "api_responses": "5m",
                    "html": "1h"
                }
            },
            "carbon_monitoring": {
                "track_co2_per_visit": True,
                "hosting_provider": "carbon_neutral",
                "cdn_locations": ["global", "regional"],
                "efficiency_score": 90
            }
        }
    
    def create_complete_app(self, app_config: Dict[str, Any]) -> str:
        """Generate complete application from configuration."""
        project_path = self.project_root / app_config["name"]
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Generate project structure
        self.generate_project_structure()
        
        # Create package.json files
        for project_type in ["frontend", "backend", "mobile"]:
            package_json = self.generate_package_json(project_type)
            with open(project_path / project_type / "package.json", "w") as f:
                json.dump(package_json, f, indent=2)
        
        # Create configuration files
        tailwind_config = self.generate_tailwind_config()
        with open(project_path / "frontend" / "tailwind.config.js", "w") as f:
            f.write(f"module.exports = {json.dumps(tailwind_config, indent=2)}")
        
        # Create environment files
        for env in ["development", "production"]:
            env_files = self.generate_environment_files(env)
            for project_type, content in env_files.items():
                env_path = project_path / project_type / f".env.{env}"
                with open(env_path, "w") as f:
                    f.write(content)
        
        # Create Docker configuration
        docker_compose = self.generate_docker_compose(["postgres", "redis", "backend", "frontend"])
        with open(project_path / "docker-compose.yml", "w") as f:
            f.write(docker_compose)
        
        # Create GitHub Actions
        github_workflow = self.generate_github_actions(["test", "deploy"])
        actions_dir = project_path / ".github" / "workflows"
        actions_dir.mkdir(parents=True, exist_ok=True)
        with open(actions_dir / "ci.yml", "w") as f:
            f.write(github_workflow)
        
        # Create README
        readme = self.generate_readme(app_config)
        with open(project_path / "README.md", "w") as f:
            f.write(readme)
        
        # Create additional configuration files
        nginx_config = self.generate_nginx_config([f"{app_config['name']}.com"])
        with open(project_path / "infrastructure" / "nginx.conf", "w") as f:
            f.write(nginx_config)
        
        # Create database schema
        sample_models = [
            {
                "name": "users",
                "fields": [
                    {"name": "id", "type": "serial('id')", "constraints": ["primaryKey()"]},
                    {"name": "email", "type": "varchar('email', { length: 255 })", "constraints": ["unique()"]},
                    {"name": "name", "type": "varchar('name', { length: 255 })"},
                    {"name": "createdAt", "type": "timestamp('created_at')", "constraints": ["defaultNow()"]},
                ]
            }
        ]
        db_schema = self.generate_database_schema(sample_models)
        with open(project_path / "backend" / "src" / "db" / "schema.ts", "w") as f:
            f.write(db_schema)
        
        return str(project_path)

class SkillEngine:
    """Main skill engine for full-stack app development."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.developer = FullStackAppDeveloper(self.config)
        
    def run(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute skill commands."""
        params = params or {}
        
        try:
            if command == "create_app":
                project_path = self.developer.create_complete_app(params)
                return {
                    "success": True,
                    "project_path": project_path,
                    "message": f"Successfully created app at {project_path}"
                }
            elif command == "generate_component":
                component = self.developer.generate_react_component(
                    params.get("name", "Button"),
                    params.get("props", ["children", "onClick"]),
                    params.get("style", "glassmorphism")
                )
                return {
                    "success": True,
                    "component": component
                }
            elif command == "generate_schema":
                schema = self.developer.generate_database_schema(params.get("models", []))
                return {
                    "success": True,
                    "schema": schema
                }
            elif command == "setup_deployment":
                docker_compose = self.developer.generate_docker_compose(
                    params.get("services", ["postgres", "redis", "backend", "frontend"])
                )
                github_workflow = self.developer.generate_github_actions(
                    params.get("workflows", ["test", "deploy"])
                )
                return {
                    "success": True,
                    "docker_compose": docker_compose,
                    "github_workflow": github_workflow
                }
            else:
                return {
                    "success": False,
                    "error": f"Unknown command: {command}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

class TestFullStackAppDeveloper(unittest.TestCase):
    """Comprehensive test suite for full-stack app developer skill."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = {"project_root": self.temp_dir, "project_name": "test-app"}
        self.developer = FullStackAppDeveloper(self.config)
        self.engine = SkillEngine(self.config)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_skill_metadata(self):
        """Test skill metadata structure."""
        self.assertEqual(SKILL_METADATA["name"], "Expert Full-Stack App Developer — Soup to Nuts")
        self.assertIn("glassmorphism_design_system", SKILL_METADATA["capabilities"])
        self.assertIn("green_engineering", SKILL_METADATA["capabilities"])
    
    def test_expert_prompts(self):
        """Test expert prompts contain required placeholders."""
        self.assertIn("{app_name}", EXPERT_PROMPTS["generate_complete_app"])
        self.assertIn("{purpose}", EXPERT_PROMPTS["generate_complete_app"])
        self.assertIn("{project_name}", EXPERT_PROMPTS["design_glassmorphism_system"])
    
    def test_integration_points(self):
        """Test integration points configuration."""
        self.assertIn("stripe", INTEGRATION_POINTS)
        self.assertEqual(INTEGRATION_POINTS["stripe"]["type"], "api")
        self.assertIn("postgresql", INTEGRATION_POINTS)
        self.assertEqual(INTEGRATION_POINTS["postgresql"]["type"], "database")
    
    def test_project_structure_generation(self):
        """Test project structure creation."""
        structure = self.developer.generate_project_structure()
        self.assertIn("frontend", structure)
        self.assertIn("backend", structure)
        self.assertIn("mobile", structure)
        
        # Check directories were created
        self.assertTrue((Path(self.temp_dir) / "frontend" / "src" / "components").exists())
        self.assertTrue((Path(self.temp_dir) / "backend" / "src" / "routes").exists())
    
    def test_package_json_generation(self):
        """Test package.json generation for different project types."""
        frontend_pkg = self.developer.generate_package_json("frontend")
        self.assertEqual(frontend_pkg["name"], "test-app")
        self.assertIn("react", frontend_pkg["dependencies"])
        self.assertIn("vite", frontend_pkg["devDependencies"])
        
        backend_pkg = self.developer.generate_package_json("backend")
        self.assertIn("express", backend_pkg["dependencies"])
        self.assertIn("drizzle-orm", backend_pkg["dependencies"])
    
    def test_tailwind_config_generation(self):
        """Test Tailwind configuration with glassmorphism support."""
        config = self.developer.generate_tailwind_config()
        self.assertIn("glass", config["theme"]["extend"]["colors"])
        self.assertIn("backdropBlur", config["theme"]["extend"])
        self.assertIn("warm", config["theme"]["extend"]["colors"])
    
    def test_database_schema_generation(self):
        """Test database schema generation."""
        models = [
            {
                "name": "users",
                "fields": [
                    {"name": "id", "type": "serial('id')", "constraints": ["primaryKey()"]},
                    {"name": "email", "type": "varchar('email', { length: 255 })", "constraints": ["unique()"]}
                ]
            }
        ]
        schema = self.developer.generate_database_schema(models)
        self.assertIn("pgTable('users'", schema)
        self.assertIn("serial('id')", schema)
        self.assertIn("varchar('email'", schema)
    
    def test_react_component_generation(self):
        """Test React component generation."""
        component = self.developer.generate_react_component(
            "GlassCard", 
            ["children", "onClick", "disabled"]
        )
        self.assertIn("GlassCard", component)
        self.assertIn("React.forwardRef", component)
        self.assertIn("glassmorphism", component)
    
    def test_docker_compose_generation(self):
        """Test Docker Compose configuration."""
        compose = self.developer.generate_docker_compose(["postgres", "redis", "backend"])
        self.assertIn("postgres:", compose)
        self.assertIn("redis:", compose)
        self.assertIn("backend:", compose)
        self.assertIn("image: postgres:15-alpine", compose)
    
    def test_github_actions_generation(self):
        """Test GitHub Actions workflow generation."""
        workflow = self.developer.generate_github_actions(["test", "deploy"])
        self.assertIn("CI/CD Pipeline", workflow)
        self.assertIn("runs-on: ubuntu-latest", workflow)
        self.assertIn("npm test", workflow)
    
    def test_nginx_config_generation(self):
        """Test Nginx configuration generation."""
        config = self.developer.generate_nginx_config(["example.com"])
        self.assertIn("server_name example.com", config)
        self.assertIn("listen 443 ssl http2", config)
        self.assertIn("proxy_pass", config)
    
    def test_environment_files_generation(self):
        """Test environment configuration files."""
        dev_env = self.developer.generate_environment_files("development")
        self.assertIn("NODE_ENV=development", dev_env["backend"])
        self.assertIn("VITE_ENV=development", dev_env["frontend"])
        
        prod_env = self.developer.generate_environment_files("production")
        self.assertIn("NODE_ENV=production", prod_env["backend"])
    
    def test_readme_generation(self):
        """Test README generation."""
        readme = self.developer.generate_readme({
            "name": "Test App",
            "description": "A test application"
        })
        self.assertIn("# Test App", readme)
        self.assertIn("## 🚀 Features", readme)
        self.assertIn("## 🛠️ Tech Stack", readme)
    
    def test_complete_app_creation(self):
        """Test complete app generation."""
        app_config = {
            "name": "complete-test-app",
            "description": "A complete test application"
        }
        project_path = self.developer.create_complete_app(app_config)
        self.assertTrue(Path(project_path).exists())
        self.assertTrue((Path(project_path) / "frontend" / "package.json").exists())
        self.assertTrue((Path(project_path) / "backend" / "package.json").exists())
        self.assertTrue((Path(project_path) / "docker-compose.yml").exists())
        self.assertTrue((Path(project_path) / "README.md").exists())
    
    def test_skill_engine_run(self):
        """Test skill engine command execution."""
        result = self.engine.run("create_app", {"name": "engine-test"})
        self.assertTrue(result["success"])
        self.assertIn("engine-test", result["project_path"])
        
        result = self.engine.run("generate_component", {
            "name": "TestButton",
            "props": ["children"]
        })
        self.assertTrue(result["success"])
        self.assertIn("TestButton", result["component"])
        
        result = self.engine.run("invalid_command")
        self.assertFalse(result["success"])
        self.assertIn("Unknown command", result["error"])
    
    def test_accessibility_config(self):
        """Test accessibility configuration."""
        config = self.developer.generate_accessibility_config()
        self.assertEqual(config["wcag_level"], "AAA")
        self.assertEqual(config["color_contrast"]["normal"], 7)
        self.assertTrue(config["keyboard_navigation"])
        self.assertTrue(config["screen_reader_support"])
    
    def test_green_engineering_config(self):
        """Test green engineering configuration."""
        config = self.developer.generate_green_engineering_config()
        self.assertIn("performance_budget", config)
        self.assertIn("optimization_strategies", config)
        self.assertIn("carbon_monitoring", config)
        self.assertEqual(config["performance_budget"]["javascript"], 250000)

if __name__ == "__main__":
    unittest.main()