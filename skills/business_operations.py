import json
import re
import os
import math
import hashlib
import statistics
import unittest
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
import requests

SKILL_METADATA = {
    "name": "Automated Business Operations Suite",
    "id": "business_operations",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "Comprehensive automation suite for running multiple small businesses including review content generation, rental management, gig economy tracking, and team building operations with real tax calculations and business analytics.",
    "capabilities": [
        "review_content_generation",
        "seo_optimization",
        "affiliate_link_management",
        "ad_revenue_tracking",
        "social_media_automation",
        "rental_inventory_management",
        "rental_agreement_generation",
        "payment_tracking",
        "gig_income_consolidation",
        "mileage_tracking",
        "tax_calculation",
        "business_analytics",
        "task_management",
        "team_performance_tracking"
    ],
    "domain": "business_automation"
}

EXPERT_PROMPTS = {
    "review_generation": """Generate a comprehensive product review for {product_name} based on the following specifications:
Product Category: {category}
Key Features: {features}
Price Point: {price}
Target Audience: {audience}
Include pros, cons, rating out of 10, and SEO-optimized conclusion with affiliate disclosure.""",
    
    "seo_optimization": """Optimize the following blog post for SEO:
Title: {title}
Current Content: {content}
Target Keywords: {keywords}
Competitor URLs: {competitor_urls}
Provide improved title, meta description, header structure, and keyword density analysis.""",
    
    "rental_agreement": """Create a legally compliant rental agreement for:
Item: {item_name}
Rental Period: {start_date} to {end_date}
Customer: {customer_name}
Rental Rate: ${daily_rate}/day
Security Deposit: ${security_deposit}
Include terms for damage, late returns, and insurance requirements.""",
    
    "gig_tax_calculation": """Calculate quarterly estimated taxes for:
Total Gig Income: ${total_income}
Business Expenses: ${expenses}
Mileage: {mileage} miles
Business Structure: {business_type}
State: {state}
Include federal, state, and self-employment tax calculations.""",
    
    "inventory_analysis": """Analyze rental inventory performance:
Inventory List: {inventory_data}
Rental History: {rental_history}
Calculate utilization rates, ROI per item, depreciation schedules, and recommend optimization strategies.""",
    
    "social_media_schedule": """Create a social media posting schedule for:
Platform: {platform}
Content Type: {content_type}
Frequency: {posts_per_week} posts/week
Target Audience: {audience}
Include optimal posting times, hashtag strategies, and engagement tactics.""",
    
    "team_performance": """Generate performance metrics for team:
Team Members: {team_members}
Task Completion Data: {task_data}
Time Period: {time_period}
Calculate productivity scores, identify bottlenecks, and recommend improvements.""",
    
    "revenue_forecasting": """Forecast business revenue based on:
Historical Data: {historical_revenue}
Seasonal Patterns: {seasonal_data}
Market Trends: {market_trends}
Growth Rate: {growth_rate}
Provide 12-month projections with confidence intervals."""
}

INTEGRATION_POINTS = {
    "amazon_associates_api": {
        "type": "api",
        "endpoint": "https://webservices.amazon.com/paapi5/searchitems",
        "description": "Amazon Product Advertising API for affiliate link generation",
        "auth_method": "AWS Signature",
        "documentation_url": "https://webservices.amazon.com/paapi5/documentation/"
    },
    "google_adsense_api": {
        "type": "api",
        "endpoint": "https://www.googleapis.com/adsense/v1.4",
        "description": "Google AdSense API for revenue tracking",
        "auth_method": "OAuth 2.0",
        "documentation_url": "https://developers.google.com/adsense/management"
    },
    "tiktok_api": {
        "type": "api",
        "endpoint": "https://open-api.tiktok.com/platform/v1/",
        "description": "TikTok API for content posting and analytics",
        "auth_method": "OAuth 2.0",
        "documentation_url": "https://developers.tiktok.com/doc/tiktok-api-v1/"
    },
    "instagram_basic_display": {
        "type": "api",
        "endpoint": "https://graph.instagram.com",
        "description": "Instagram Basic Display API for media posting",
        "auth_method": "OAuth 2.0",
        "documentation_url": "https://developers.facebook.com/docs/instagram-basic-display-api"
    },
    "quickbooks_api": {
        "type": "api",
        "endpoint": "https://sandbox-quickbooks.api.intuit.com/v3/company",
        "description": "QuickBooks Online API for accounting integration",
        "auth_method": "OAuth 2.0",
        "documentation_url": "https://developer.intuit.com/app/portal/home"
    },
    "google_maps_api": {
        "type": "api",
        "endpoint": "https://maps.googleapis.com/maps/api/directions/json",
        "description": "Google Maps API for mileage tracking",
        "auth_method": "API Key",
        "documentation_url": "https://developers.google.com/maps/documentation/directions"
    }
}

def parse_product_data(product_text: str) -> Dict[str, Any]:
    """Parse Vine product data into structured format."""
    data = {}
    patterns = {
        'name': r'Product Name:\s*(.+?)\n',
        'category': r'Category:\s*(.+?)\n',
        'price': r'Price:\s*\$?(\d+\.?\d*)',
        'rating': r'Rating:\s*(\d+\.?\d*)',
        'features': r'Features:\s*(.+?)(?:\n|$)',
        'brand': r'Brand:\s*(.+?)\n'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, product_text, re.IGNORECASE)
        if match:
            if key == 'price':
                data[key] = float(match.group(1))
            elif key == 'rating':
                data[key] = float(match.group(1))
            elif key == 'features':
                data[key] = [f.strip() for f in match.group(1).split(',')]
            else:
                data[key] = match.group(1).strip()
    
    return data

def calculate_se_component(taxable_income: float, business_type: str = "sole_proprietorship") -> float:
    """Calculate self-employment tax component."""
    if business_type in ["s_corp", "c_corp"]:
        return 0.0
    
    se_tax_rate = 0.9235
    social_security_rate = 0.124
    medicare_rate = 0.029
    
    se_income = taxable_income * se_tax_rate
    
    social_security_tax = min(se_income * social_security_rate, 160200 * social_security_rate)
    medicare_tax = se_income * medicare_rate
    
    if taxable_income > 200000:
        medicare_tax += (taxable_income - 200000) * 0.009
    
    return social_security_tax + medicare_tax

def calculate_quarterly_tax(gig_income: float, expenses: float, mileage: float, 
                         business_type: str = "sole_proprietorship", state: str = "CA") -> Dict[str, float]:
    """Calculate quarterly estimated taxes."""
    taxable_income = gig_income - expenses - (mileage * 0.655)
    
    federal_brackets = [(0, 11000, 0.10), (11000, 44725, 0.12), (44725, 95375, 0.22),
                       (95375, 182100, 0.24), (182100, 231250, 0.32)]
    
    federal_tax = 0
    for low, high, rate in federal_brackets:
        if taxable_income > low:
            federal_tax += (min(taxable_income, high) - low) * rate
    
    se_tax = calculate_se_component(taxable_income, business_type)
    
    state_rates = {"CA": 0.0929, "NY": 0.0685, "TX": 0.0, "FL": 0.0}
    state_tax = taxable_income * state_rates.get(state, 0.05)
    
    total_tax = federal_tax + se_tax + state_tax
    quarterly_payment = total_tax / 4
    
    return {
        "federal_tax": federal_tax,
        "self_employment_tax": se_tax,
        "state_tax": state_tax,
        "total_tax": total_tax,
        "quarterly_payment": quarterly_payment,
        "taxable_income": taxable_income
    }

def generate_rental_agreement(item_name: str, customer_name: str, start_date: str, 
                            end_date: str, daily_rate: float, security_deposit: float) -> str:
    """Generate a rental agreement document."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    rental_days = (end - start).days
    
    total_cost = rental_days * daily_rate
    
    agreement = f"""
RENTAL AGREEMENT

This Rental Agreement is entered into on {datetime.now().strftime("%B %d, %Y")}

PARTIES:
Lessor: [Business Name]
Lessee: {customer_name}

ITEM DETAILS:
Rental Item: {item_name}
Rental Period: {start_date} to {end_date} ({rental_days} days)
Daily Rate: ${daily_rate:.2f}
Total Rental Cost: ${total_cost:.2f}
Security Deposit: ${security_deposit:.2f}

TERMS AND CONDITIONS:
1. Lessee agrees to return the item in the same condition as received
2. Late returns will incur a fee of ${daily_rate:.2f} per day
3. Damage beyond normal wear will be deducted from security deposit
4. Insurance is {('required' if security_deposit > 500 else 'recommended')}
5. Payment due in full before item release

Total Amount Due: ${total_cost + security_deposit:.2f}

Signature: _____________________ Date: ___________
"""
    return agreement

def calculate_inventory_metrics(inventory_data: List[Dict], rental_history: List[Dict]) -> Dict[str, Any]:
    """Calculate key inventory performance metrics."""
    total_items = len(inventory_data)
    active_items = len([i for i in inventory_data if i.get('status') == 'active'])
    
    total_revenue = sum(r.get('rental_fee', 0) for r in rental_history)
    total_rentals = len(rental_history)
    
    utilization_rates = {}
    for item in inventory_data:
        item_id = item.get('id')
        item_rentals = [r for r in rental_history if r.get('item_id') == item_id]
        days_rented = sum((datetime.strptime(r['end_date'], "%Y-%m-%d") - 
                          datetime.strptime(r['start_date'], "%Y-%m-%d")).days 
                         for r in item_rentals)
        utilization_rates[item_id] = (days_rented / 365) * 100 if days_rented > 0 else 0
    
    avg_utilization = statistics.mean(utilization_rates.values()) if utilization_rates else 0
    
    roi_data = {}
    for item in inventory_data:
        item_cost = item.get('purchase_price', 0)
        item_revenue = sum(r.get('rental_fee', 0) for r in rental_history 
                          if r.get('item_id') == item.get('id'))
        roi_data[item.get('id')] = ((item_revenue - item_cost) / item_cost * 100) if item_cost > 0 else 0
    
    return {
        "total_items": total_items,
        "active_items": active_items,
        "total_revenue": total_revenue,
        "total_rentals": total_rentals,
        "average_utilization": avg_utilization,
        "utilization_rates": utilization_rates,
        "roi_percentages": roi_data
    }

def optimize_social_schedule(platform: str, audience: str, posts_per_week: int) -> Dict[str, Any]:
    """Generate optimal social media posting schedule."""
    platform_configs = {
        "tiktok": {"best_times": ["9:00", "12:00", "19:00"], "max_daily": 3},
        "instagram": {"best_times": ["11:00", "14:00", "17:00"], "max_daily": 2},
        "youtube": {"best_times": ["14:00", "18:00", "20:00"], "max_daily": 1}
    }
    
    config = platform_configs.get(platform, {"best_times": ["12:00"], "max_daily": 2})
    
    posts_per_day = min(posts_per_week / 7, config["max_daily"])
    schedule = []
    
    for day in range(7):
        if len(schedule) < posts_per_week:
            time = config["best_times"][day % len(config["best_times"])]
            schedule.append({
                "day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][day],
                "time": time,
                "platform": platform
            })
    
    return {
        "schedule": schedule,
        "posts_per_day": posts_per_day,
        "total_posts": posts_per_week,
        "engagement_tips": [
            f"Use trending hashtags for {platform}",
            "Post consistently at optimal times",
            "Engage with comments within first hour",
            "Cross-promote on other platforms"
        ]
    }

def consolidate_gig_income(gig_data: List[Dict]) -> Dict[str, Any]:
    """Consolidate income from multiple gig platforms."""
    platform_totals = defaultdict(float)
    monthly_totals = defaultdict(float)
    expense_totals = defaultdict(float)
    
    for gig in gig_data:
        platform = gig.get('platform', 'unknown')
        amount = gig.get('amount', 0)
        date = gig.get('date', '')
        expenses = gig.get('expenses', 0)
        
        platform_totals[platform] += amount
        expense_totals[platform] += expenses
        
        if date:
            month_key = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m")
            monthly_totals[month_key] += amount
    
    total_income = sum(platform_totals.values())
    total_expenses = sum(expense_totals.values())
    net_income = total_income - total_expenses
    
    return {
        "platform_breakdown": dict(platform_totals),
        "monthly_breakdown": dict(monthly_totals),
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_income": net_income,
        "average_monthly": statistics.mean(monthly_totals.values()) if monthly_totals else 0
    }

def calculate_mileage_deduction(mileage_data: List[Dict], rate: float = 0.655) -> Dict[str, Any]:
    """Calculate mileage deduction for tax purposes."""
    total_miles = sum(trip.get('miles', 0) for trip in mileage_data)
    business_miles = sum(trip.get('miles', 0) for trip in mileage_data 
                        if trip.get('purpose') == 'business')
    personal_miles = total_miles - business_miles
    
    deduction = business_miles * rate
    
    trip_summary = defaultdict(int)
    for trip in mileage_data:
        purpose = trip.get('purpose', 'unknown')
        trip_summary[purpose] += trip.get('miles', 0)
    
    return {
        "total_miles": total_miles,
        "business_miles": business_miles,
        "personal_miles": personal_miles,
        "deduction_amount": deduction,
        "mileage_breakdown": dict(trip_summary),
        "rate_used": rate
    }

def generate_performance_report(team_data: List[Dict], task_data: List[Dict]) -> Dict[str, Any]:
    """Generate team performance analytics."""
    member_stats = defaultdict(lambda: {"tasks_completed": 0, "tasks_overdue": 0, "avg_completion_time": []})
    
    for task in task_data:
        assignee = task.get('assignee')
        if assignee:
            if task.get('status') == 'completed':
                member_stats[assignee]["tasks_completed"] += 1
                if task.get('completion_time'):
                    member_stats[assignee]["avg_completion_time"].append(task['completion_time'])
            elif task.get('status') == 'overdue':
                member_stats[assignee]["tasks_overdue"] += 1
    
    performance_scores = {}
    for member, stats in member_stats.items():
        completion_rate = stats["tasks_completed"] / (stats["tasks_completed"] + stats["tasks_overdue"]) * 100
        avg_time = statistics.mean(stats["avg_completion_time"]) if stats["avg_completion_time"] else 0
        performance_scores[member] = {
            "completion_rate": completion_rate,
            "avg_completion_time": avg_time,
            "tasks_completed": stats["tasks_completed"],
            "tasks_overdue": stats["tasks_overdue"],
            "productivity_score": (completion_rate * 0.7) + ((1 / (avg_time + 1)) * 100 * 0.3)
        }
    
    team_completion_rate = statistics.mean([s["completion_rate"] for s in performance_scores.values()])
    
    return {
        "individual_performance": performance_scores,
        "team_completion_rate": team_completion_rate,
        "top_performer": max(performance_scores.items(), key=lambda x: x[1]["productivity_score"])[0] if performance_scores else None,
        "improvement_areas": [member for member, stats in performance_scores.items() if stats["completion_rate"] < 80]
    }

class SkillEngine:
    """Main engine for Automated Business Operations Suite."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = self._setup_logger()
        self.capabilities = {
            "review_content_generation": self.generate_review_content,
            "seo_optimization": self.optimize_seo,
            "affiliate_link_management": self.manage_affiliate_links,
            "ad_revenue_tracking": self.track_ad_revenue,
            "social_media_automation": self.automate_social_media,
            "rental_inventory_management": self.manage_rental_inventory,
            "rental_agreement_generation": self.generate_rental_agreement,
            "payment_tracking": self.track_payments,
            "gig_income_consolidation": self.consolidate_gig_income,
            "mileage_tracking": self.track_mileage,
            "tax_calculation": self.calculate_taxes,
            "business_analytics": self.analyze_business,
            "task_management": self.manage_tasks,
            "team_performance_tracking": self.track_team_performance
        }
    
    def _setup_logger(self):
        """Setup basic logging."""
        import logging
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        return logger
    
    def generate_review_content(self, product_data: Dict[str, Any]) -> str:
        """Generate review content from product data."""
        try:
            product_info = parse_product_data(str(product_data))
            rating = product_info.get('rating', 7.5)
            
            review = f"""
Product Review: {product_info.get('name', 'Unknown Product')}

The {product_info.get('category', 'product')} from {product_info.get('brand', 'the manufacturer')} 
offers solid performance with its key features including {', '.join(product_info.get('features', []))}.

Pros:
- Good build quality
- Competitive pricing at ${product_info.get('price', 0):.2f}
- Suitable for {product_info.get('category', 'general use')}

Cons:
- May require learning curve
- Limited availability

Rating: {rating}/10

[Affiliate Disclosure: This review contains affiliate links. We may earn a commission at no extra cost to you.]
"""
            return review.strip()
        except Exception as e:
            self.logger.error(f"Error generating review: {str(e)}")
            return ""
    
    def optimize_seo(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize content for SEO."""
        try:
            title = content_data.get('title', '')
            content = content_data.get('content', '')
            keywords = content_data.get('keywords', [])
            
            word_count = len(content.split())
            keyword_density = {}
            
            for keyword in keywords:
                occurrences = content.lower().count(keyword.lower())
                density = (occurrences / word_count) * 100 if word_count > 0 else 0
                keyword_density[keyword] = density
            
            return {
                "optimized_title": f"{title} - Complete Guide {datetime.now().year}",
                "meta_description": f"Complete review and analysis of {title}. Learn about features, pricing, and alternatives.",
                "word_count": word_count,
                "keyword_density": keyword_density,
                "recommendations": [
                    "Add more internal links",
                    "Optimize images with alt text",
                    "Improve page loading speed",
                    "Add schema markup"
                ]
            }
        except Exception as e:
            self.logger.error(f"SEO optimization error: {str(e)}")
            return {}
    
    def manage_affiliate_links(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage affiliate links for products."""
        try:
            product_name = product_data.get('name', '')
            asin = product_data.get('asin', '')
            
            affiliate_links = {
                "amazon": f"https://www.amazon.com/dp/{asin}/?tag=your-affiliate-id",
                "walmart": f"https://www.walmart.com/search?q={product_name.replace(' ', '+')}",
                "target": f"https://www.target.com/s/{product_name.replace(' ', '+')}"
            }
            
            return {
                "product": product_name,
                "links": affiliate_links,
                "tracking_codes": {
                    "amazon": "your-affiliate-id",
                    "campaign": f"review_{datetime.now().strftime('%Y%m')}"
                }
            }
        except Exception as e:
            self.logger.error(f"Affiliate link error: {str(e)}")
            return {}
    
    def track_ad_revenue(self, revenue_data: List[Dict]) -> Dict[str, Any]:
        """Track advertising revenue."""
        try:
            total_revenue = sum(r.get('revenue', 0) for r in revenue_data)
            platform_breakdown = defaultdict(float)
            
            for revenue in revenue_data:
                platform = revenue.get('platform', 'unknown')
                platform_breakdown[platform] += revenue.get('revenue', 0)
            
            return {
                "total_revenue": total_revenue,
                "platform_breakdown": dict(platform_breakdown),
                "avg_daily_revenue": total_revenue / 30,
                "top_platform": max(platform_breakdown.items(), key=lambda x: x[1])[0] if platform_breakdown else None
            }
        except Exception as e:
            self.logger.error(f"Ad revenue tracking error: {str(e)}")
            return {}
    
    def automate_social_media(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Automate social media posting."""
        try:
            platform = post_data.get('platform', 'instagram')
            content = post_data.get('content', '')
            schedule = post_data.get('schedule', False)
            
            optimized_schedule = optimize_social_schedule(
                platform, 
                post_data.get('audience', 'general'),
                post_data.get('frequency', 7)
            )
            
            return {
                "platform": platform,
                "content_preview": content[:100] + "...",
                "schedule": optimized_schedule["schedule"],
                "hashtags": ["#business", "#automation", "#productivity"],
                "status": "scheduled" if schedule else "ready_to_post"
            }
        except Exception as e:
            self.logger.error(f"Social media automation error: {str(e)}")
            return {}
    
    def manage_rental_inventory(self, inventory_data: List[Dict]) -> Dict[str, Any]:
        """Manage rental inventory."""
        try:
            available_items = [i for i in inventory_data if i.get('status') == 'available']
            rented_items = [i for i in inventory_data if i.get('status') == 'rented']
            maintenance_items = [i for i in inventory_data if i.get('status') == 'maintenance']
            
            total_value = sum(i.get('purchase_price', 0) for i in inventory_data)
            
            return {
                "total_items": len(inventory_data),
                "available": len(available_items),
                "rented": len(rented_items),
                "maintenance": len(maintenance_items),
                "total_value": total_value,
                "utilization_rate": (len(rented_items) / len(inventory_data) * 100) if inventory_data else 0
            }
        except Exception as e:
            self.logger.error(f"Inventory management error: {str(e)}")
            return {}
    
    def generate_rental_agreement(self, rental_data: Dict[str, Any]) -> str:
        """Generate rental agreement."""
        try:
            return generate_rental_agreement(
                rental_data.get('item_name', ''),
                rental_data.get('customer_name', ''),
                rental_data.get('start_date', ''),
                rental_data.get('end_date', ''),
                rental_data.get('daily_rate', 0),
                rental_data.get('security_deposit', 0)
            )
        except Exception as e:
            self.logger.error(f"Rental agreement error: {str(e)}")
            return ""
    
    def track_payments(self, payment_data: List[Dict]) -> Dict[str, Any]:
        """Track payments."""
        try:
            total_paid = sum(p.get('amount', 0) for p in payment_data if p.get('status') == 'paid')
            total_pending = sum(p.get('amount', 0) for p in payment_data if p.get('status') == 'pending')
            overdue_payments = [p for p in payment_data if p.get('status') == 'overdue']
            
            return {
                "total_paid": total_paid,
                "total_pending": total_pending,
                "overdue_count": len(overdue_payments),
                "overdue_amount": sum(p.get('amount', 0) for p in overdue_payments),
                "collection_rate": (total_paid / (total_paid + total_pending) * 100) if (total_paid + total_pending) > 0 else 0
            }
        except Exception as e:
            self.logger.error(f"Payment tracking error: {str(e)}")
            return {}
    
    def consolidate_gig_income(self, gig_data: List[Dict]) -> Dict[str, Any]:
        """Consolidate gig income."""
        try:
            return consolidate_gig_income(gig_data)
        except Exception as e:
            self.logger.error(f"Gig income consolidation error: {str(e)}")
            return {}
    
    def track_mileage(self, mileage_data: List[Dict]) -> Dict[str, Any]:
        """Track mileage."""
        try:
            return calculate_mileage_deduction(mileage_data)
        except Exception as e:
            self.logger.error(f"Mileage tracking error: {str(e)}")
            return {}
    
    def calculate_taxes(self, tax_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate taxes."""
        try:
            return calculate_quarterly_tax(
                tax_data.get('gig_income', 0),
                tax_data.get('expenses', 0),
                tax_data.get('mileage', 0),
                tax_data.get('business_type', 'sole_proprietorship'),
                tax_data.get('state', 'CA')
            )
        except Exception as e:
            self.logger.error(f"Tax calculation error: {str(e)}")
            return {}
    
    def analyze_business(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze business performance."""
        try:
            revenue = business_data.get('revenue', [])
            expenses = business_data.get('expenses', [])
            
            total_revenue = sum(revenue)
            total_expenses = sum(expenses)
            net_profit = total_revenue - total_expenses
            
            profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
            
            return {
                "total_revenue": total_revenue,
                "total_expenses": total_expenses,
                "net_profit": net_profit,
                "profit_margin": profit_margin,
                "roi": (net_profit / total_expenses * 100) if total_expenses > 0 else 0,
                "break_even_point": total_expenses / (total_revenue / 30) if total_revenue > 0 else 0
            }
        except Exception as e:
            self.logger.error(f"Business analysis error: {str(e)}")
            return {}
    
    def manage_tasks(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage tasks."""
        try:
            tasks = task_data.get('tasks', [])
            completed = len([t for t in tasks if t.get('status') == 'completed'])
            pending = len([t for t in tasks if t.get('status') == 'pending'])
            
            return {
                "total_tasks": len(tasks),
                "completed": completed,
                "pending": pending,
                "completion_rate": (completed / len(tasks) * 100) if tasks else 0,
                "priority_breakdown": {
                    "high": len([t for t in tasks if t.get('priority') == 'high']),
                    "medium": len([t for t in tasks if t.get('priority') == 'medium']),
                    "low": len([t for t in tasks if t.get('priority') == 'low'])
                }
            }
        except Exception as e:
            self.logger.error(f"Task management error: {str(e)}")
            return {}
    
    def track_team_performance(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track team performance."""
        try:
            return generate_performance_report(
                performance_data.get('team_members', []),
                performance_data.get('task_data', [])
            )
        except Exception as e:
            self.logger.error(f"Team performance tracking error: {str(e)}")
            return {}
    
    def run(self, capability: str, data: Dict[str, Any]) -> Any:
        """Run the specified capability."""
        if capability not in self.capabilities:
            raise ValueError(f"Unknown capability: {capability}")
        
        return self.capabilities[capability](data)

class TestBusinessOperationsSuite(unittest.TestCase):
    """Test cases for Business Operations Suite."""
    
    def test_metadata_validation(self):
        """Test metadata structure."""
        self.assertEqual(SKILL_METADATA["name"], "Automated Business Operations Suite")
        self.assertEqual(SKILL_METADATA["id"], "business_operations")
        self.assertIn("review_content_generation", SKILL_METADATA["capabilities"])
        self.assertEqual(len(SKILL_METADATA["capabilities"]), 14)
    
    def test_product_data_parsing(self):
        """Test product data parsing."""
        product_text = """
        Product Name: Test Widget
        Category: Electronics
        Price: $99.99
        Rating: 8.5
        Features: Fast, Reliable, Affordable
        Brand: TestBrand
        """
        result = parse_product_data(product_text)
        self.assertEqual(result['name'], 'Test Product')
        self.assertEqual(result['price'], 99.99)
        self.assertEqual(result['rating'], 8.5)
        self.assertEqual(len(result['features']), 3)
    
    def test_tax_calculation(self):
        """Test quarterly tax calculation."""
        result = calculate_quarterly_tax(
            gig_income=50000,
            expenses=10000,
            mileage=5000,
            business_type="sole_proprietorship",
            state="CA"
        )
        self.assertIn("federal_tax", result)
        self.assertIn("self_employment_tax", result)
        self.assertIn("state_tax", result)
        self.assertGreater(result["total_tax"], 0)
        self.assertEqual(result["quarterly_payment"], result["total_tax"] / 4)
    
    def test_rental_agreement_generation(self):
        """Test rental agreement generation."""
        agreement = generate_rental_agreement(
            "Camera Lens",
            "John Doe",
            "2024-01-01",
            "2024-01-07",
            25.0,
            100.0
        )
        self.assertIn("RENTAL AGREEMENT", agreement)
        self.assertIn("John Doe", agreement)
        self.assertIn("$175.00", agreement)  # 7 days * $25 + $100 deposit
    
    def test_inventory_metrics(self):
        """Test inventory metrics calculation."""
        inventory = [
            {"id": 1, "purchase_price": 500, "status": "active"},
            {"id": 2, "purchase_price": 300, "status": "active"}
        ]
        rental_history = [
            {"item_id": 1, "start_date": "2024-01-01", "end_date": "2024-01-08", "rental_fee": 100},
            {"item_id": 2, "start_date": "2024-01-01", "end_date": "2024-01-04", "rental_fee": 60}
        ]
        result = calculate_inventory_metrics(inventory, rental_history)
        self.assertEqual(result["total_items"], 2)
        self.assertEqual(result["total_revenue"], 160)
        self.assertEqual(result["total_rentals"], 2)
    
    def test_social_schedule_optimization(self):
        """Test social media schedule optimization."""
        result = optimize_social_schedule("tiktok", "young adults", 14)
        self.assertEqual(len(result["schedule"]), 14)
        self.assertEqual(result["total_posts"], 14)
        self.assertIn("engagement_tips", result)
    
    def test_gig_income_consolidation(self):
        """Test gig income consolidation."""
        gig_data = [
            {"platform": "Uber", "amount": 500, "date": "2024-01-15", "expenses": 50},
            {"platform": "Lyft", "amount": 300, "date": "2024-01-16", "expenses": 30},
            {"platform": "Uber", "amount": 400, "date": "2024-01-20", "expenses": 40}
        ]
        result = consolidate_gig_income(gig_data)
        self.assertEqual(result["total_income"], 1200)
        self.assertEqual(result["total_expenses"], 120)
        self.assertEqual(result["net_income"], 1080)
        self.assertEqual(result["platform_breakdown"]["Uber"], 900)
    
    def test_mileage_deduction_calculation(self):
        """Test mileage deduction calculation."""
        mileage_data = [
            {"miles": 100, "purpose": "business"},
            {"miles": 50, "purpose": "personal"},
            {"miles": 75, "purpose": "business"}
        ]
        result = calculate_mileage_deduction(mileage_data)
        self.assertEqual(result["total_miles"], 225)
        self.assertEqual(result["business_miles"], 175)
        self.assertEqual(result["deduction_amount"], 175 * 0.655)
    
    def test_team_performance_report(self):
        """Test team performance reporting."""
        team_members = ["Alice", "Bob", "Charlie"]
        task_data = [
            {"assignee": "Alice", "status": "completed", "completion_time": 4},
            {"assignee": "Bob", "status": "overdue"},
            {"assignee": "Alice", "status": "completed", "completion_time": 3},
            {"assignee": "Charlie", "status": "completed", "completion_time": 5}
        ]
        result = generate_performance_report(team_members, task_data)
        self.assertIn("Alice", result["individual_performance"])
        self.assertEqual(result["team_completion_rate"], 75)
        self.assertEqual(result["top_performer"], "Alice")
    
    def test_skill_engine_initialization(self):
        """Test SkillEngine initialization."""
        config = {"api_key": "test_key", "debug": True}
        engine = SkillEngine(config)
        self.assertEqual(engine.config, config)
        self.assertIn("review_content_generation", engine.capabilities)
    
    def test_skill_engine_review_generation(self):
        """Test SkillEngine review generation."""
        engine = SkillEngine({})
        product_data = {"name": "Test Product", "category": "Tech", "price": 99}
        result = engine.generate_review_content(product_data)
        self.assertIn("Product Review", result)
        self.assertIn("Test Product", result)
    
    def test_skill_engine_error_handling(self):
        """Test SkillEngine error handling."""
        engine = SkillEngine({})
        with self.assertRaises(ValueError):
            engine.run("invalid_capability", {})

if __name__ == '__main__':
    unittest.main()