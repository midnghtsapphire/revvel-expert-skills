#/usr/bin/env python3
"""
Meta/Facebook Marketing Skill

This skill provides a comprehensive suite of tools for Meta/Facebook marketing experts.
"""

import json, re, os, math, hashlib, statistics, requests
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple
import unittest
import logging
import argparse
from pathlib import Path

# ==================================================================================================
#        SKILL METADATA
# ==================================================================================================

SKILL_METADATA = {
    "name": "Meta/Facebook Marketing Expert",
    "id": "meta_facebook_marketing",
    "version": "1.0.0",
    "author": "Revvel AI Engine",
    "description": "A comprehensive skill for Meta/Facebook marketing, including ad creation, campaign management, analytics, and platform-specific features.",
    "domain": "Social Media Marketing",
    "capabilities": [
        "ad_creation",
        "campaign_management",
        "content_calendar_generation",
        "audience_targeting",
        "analytics_and_reporting",
        "hashtag_and_keyword_research",
        "trend_analysis",
        "competitor_analysis",
        "influencer_identification",
        "roi_tracking",
        "quick_ad_generation",
        "facebook_ads_manager_integration",
        "pixel_tracking_setup",
        "lookalike_audience_creation",
        "advantage_plus_campaigns",
        "reels_ad_creation"
    ]
}

# ==================================================================================================
#        EXPERT PROMPTS
# ==================================================================================================

EXPERT_PROMPTS = {
    "generate_ad_copy": {
        "description": "Generate compelling ad copy for a specific product and target audience.",
        "prompt": "Create 3 variations of ad copy for a Facebook ad promoting '{product_name}'. The target audience is {target_audience}. The key benefit to highlight is {key_benefit}. The tone should be {tone}. Include a strong call-to-action."
    },
    "create_campaign_strategy": {
        "description": "Develop a full Facebook campaign strategy.",
        "prompt": "Outline a comprehensive Facebook marketing campaign strategy for launching '{product_name}'. The budget is {budget} for a duration of {duration_weeks} weeks. The primary objective is {objective} (e.g., conversions, brand awareness). Define target audiences, ad formats, and a content plan."
    },
    "analyze_performance": {
        "description": "Analyze campaign performance data and provide optimization recommendations.",
        "prompt": "Analyze the following Facebook Ads performance data: {data}. Identify key trends, top-performing ads, and underperforming areas. Provide at least 5 actionable recommendations to improve campaign ROI."
    },
    "suggest_reels_idea": {
        "description": "Generate a creative idea for a Facebook Reel ad.",
        "prompt": "Brainstorm a concept for a 15-30 second Facebook Reel to promote '{product_name}'. The Reel should be engaging, visually appealing, and align with current trends. The target audience is {target_audience}. Provide a brief storyboard or shot list."
    },
    "lookalike_audience_strategy": {
        "description": "Define a strategy for creating and using Lookalike Audiences.",
        "prompt": "Describe a strategy for creating and leveraging Facebook Lookalike Audiences for '{company_name}'. What source audiences should be used (e.g., customer list, website visitors, video viewers)? What percentage match (1%, 2-5%, etc.) should be tested? How would you structure a campaign to test these audiences?"
    }
}

# ==================================================================================================
#        CORE EXPERT CLASSES
# ==================================================================================================

class AdCreator:
    """Handles the creation of various Facebook ad formats."""

    def generate_text_ad(self, product_name: str, target_audience: str, key_benefit: str, tone: str = "persuasive", cta: str = "Learn More") -> Dict[str, str]:
        """Generates compelling text-based ad copy."""
        prompt = EXPERT_PROMPTS["generate_ad_copy"]["prompt"].format(
            product_name=product_name,
            target_audience=target_audience,
            key_benefit=key_benefit,
            tone=tone
        )
        # In a real implementation, this would call a language model.
        # For this skill, we'll simulate the output.
        return {
            "headline": f"Discover {product_name}!",
            "primary_text": f"Tired of {target_audience}'s biggest problem? {product_name} helps you {key_benefit}. Try it now and see the difference!",
            "description": f"The perfect solution for {target_audience}.",
            "cta": cta
        }

    def generate_image_ad_spec(self, product_name: str, image_style: str) -> Dict[str, str]:
        """Provides specifications for an image ad."""
        return {
            "recommendation": f"For {product_name}, use a high-resolution image showcasing the product in use. Style: {image_style}. Aspect ratio: 1.91:1 for feed, 9:16 for Stories.",
            "image_url_placeholder": "https://example.com/image.jpg"
        }

    def generate_video_ad_spec(self, product_name: str, video_length_seconds: int) -> Dict[str, str]:
        """Provides specifications for a video ad."""
        return {
            "recommendation": f"Create a {video_length_seconds}-second video for {product_name}. Start with a strong hook. Show, don't just tell. End with a clear call to action.",
            "video_url_placeholder": "https://example.com/video.mp4"
        }

    def generate_carousel_ad_spec(self, product_name: str, num_cards: int) -> Dict[str, Any]:
        """Provides specifications for a carousel ad."""
        cards = []
        for i in range(num_cards):
            cards.append({
                "headline": f"{product_name} - Feature {i+1}",
                "description": f"Benefit of feature {i+1}",
                "image_url_placeholder": f"https://example.com/carousel_{i+1}.jpg",
                "link": f"https://example.com/product/feature{i+1}"
            })
        return {"cards": cards}

    def generate_reels_ad_concept(self, product_name: str, target_audience: str) -> Dict[str, str]:
        """Generates a concept for a Facebook Reels ad."""
        prompt = EXPERT_PROMPTS["suggest_reels_idea"]["prompt"].format(
            product_name=product_name,
            target_audience=target_audience
        )
        return {
            "concept": f"A fast-paced, music-driven Reel showing diverse people enjoying {product_name}. Use quick cuts and trending audio. Text overlay: ‘Upgrade your day with {product_name}!’. Final shot: Logo and CTA.",
            "storyboard_summary": "1. Quick shot of problem. 2. {product_name} is introduced. 3. Montage of happy users. 4. CTA."
        }

class CampaignManager:
    """Manages the lifecycle of Facebook campaigns."""

    def create_campaign_plan(self, product_name: str, budget: float, duration_weeks: int, objective: str) -> Dict[str, Any]:
        """Creates a high-level campaign plan."""
        return {
            "product_name": product_name,
            "budget": budget,
            "duration_weeks": duration_weeks,
            "objective": objective,
            "recommendation": "Start with a brand awareness campaign, then retarget engaged users with a conversion campaign. Use a mix of image, video, and carousel ads."
        }

    def optimize_budget_allocation(self, performance_data: Dict[str, Any]) -> Dict[str, str]:
        """Suggests budget reallocation based on performance."""
        # Dummy implementation
        return {"recommendation": "Shift 20% of budget from underperforming ad set to the top-performing one."}

    def suggest_ab_test(self) -> Dict[str, str]:
        """Suggests an A/B test to run."""
        return {"recommendation": "Test two different headlines against each other to see which one has a higher CTR."}

    def setup_advantage_plus_campaign(self, product_name: str, budget: float, target_audience_broad: str) -> Dict[str, Any]:
        """Provides a setup for an Advantage+ campaign."""
        return {
            "campaign_type": "Advantage+ Shopping Campaign",
            "product_name": product_name,
            "budget": budget,
            "target_audience_broad": target_audience_broad,
            "recommendation": "Let Meta's AI find the best audience for you. Provide high-quality creative and a clear conversion event."
        }

class ContentCalendar:
    """Generates and manages content calendars."""

    def generate_calendar(self, topic: str, posts_per_week: int) -> List[Dict[str, str]]:
        """Generates a week of content ideas."""
        calendar = []
        post_types = ["Image Post", "Video Clip", "Link to Blog", "Poll", "User-Generated Content Feature"]
        for i in range(posts_per_week):
            calendar.append({
                "day": i + 1,
                "post_idea": f"Post about {topic} - angle {i+1}",
                "format": post_types[i % len(post_types)],
                "caption_starter": f"Let's talk about {topic}...\n"
            })
        return calendar

class AudienceTargeter:
    """Defines and segments target audiences."""

    def define_core_audience(self, demographics: Dict[str, Any], interests: List[str]) -> Dict[str, Any]:
        """Defines a core audience based on demographics and interests."""
        return {
            "demographics": demographics,
            "interests": interests,
            "name": "Core Audience Segment"
        }

    def create_lookalike_strategy(self, source_audience: str, country: str) -> Dict[str, str]:
        """Outlines a strategy for creating Lookalike Audiences."""
        return {
            "source_audience": source_audience,
            "country": country,
            "recommendation": "Create a 1% Lookalike audience from your customer list for high similarity. Also, test a 1-3% Lookalike from website visitors for broader reach."
        }

    def setup_pixel_tracking(self, website_url: str) -> Dict[str, str]:
        """Generates a dummy Meta Pixel code and setup instructions."""
        pixel_id = f"PIXEL_{hashlib.sha1(website_url.encode()).hexdigest()[:10]}"
        return {
            "pixel_id": pixel_id,
            "setup_instructions": "1. Add the Meta Pixel base code to the header of your website. 2. Set up standard events like 'PageView', 'AddToCart', and 'Purchase'. 3. Verify the pixel is firing correctly using the Meta Pixel Helper browser extension.",
            "pixel_code_snippet": f"<!-- Meta Pixel Code -->\n<script>\n!function(f,b,e,v,n,t,s)\n{{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)}};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}}(window, document,'script','https://connect.facebook.net/en_US/fbevents.js');\nfbq('init', '{pixel_id}');\nfbq('track', 'PageView');\n</script>\n<noscript><img height=\"1\" width=\"1\" style=\"display:none\" src=\"https://www.facebook.com/tr?id={pixel_id}&ev=PageView&noscript=1\"/></noscript>\n<!-- End Meta Pixel Code -->"
        }

class AnalyticsReporter:
    """Analyzes data and generates reports."""

    def analyze_performance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes campaign performance and provides insights."""
        # Dummy analysis
        insights = {
            "summary": "Campaign is performing well, with a high CTR but low conversion rate.",
            "recommendations": [
                "Optimize landing page to improve conversion rate.",
                "Increase budget for the best-performing ad set.",
                "Pause the ad with the lowest CTR."
            ],
            "key_metrics": {
                "ctr": data.get("ctr", 0.02),
                "cpc": data.get("cpc", 1.50),
                "conversion_rate": data.get("conversion_rate", 0.01)
            }
        }
        return insights

class KeywordResearcher:
    """Researches hashtags and keywords."""

    def get_related_hashtags(self, topic: str, count: int = 5) -> List[str]:
        """Gets related hashtags for a given topic."""
        # Dummy implementation
        base_hashtags = [f"#{topic}", f"#{topic}love", f"#{topic}tips", f"#{topic}life", f"#{topic}community"]
        return base_hashtags[:count]

    def get_interest_targeting_suggestions(self, keyword: str) -> List[str]:
        """Suggests interest targeting options related to a keyword."""
        return [f"{keyword} enthusiasts", f"People who like pages about {keyword}", f"Engaged shoppers who have shown interest in {keyword}"]

class TrendAnalyzer:
    """Analyzes market and platform trends."""

    def get_current_trends(self) -> List[Dict[str, str]]:
        """Identifies current marketing trends on Facebook."""
        return [
            {"trend": "Short-form video (Reels)", "implication": "Prioritize creating engaging Reels to capture attention."},
            {"trend": "Interactive content", "implication": "Use polls, quizzes, and stickers in Stories and posts to boost engagement."},
            {"trend": "Authenticity and UGC", "implication": "Feature real customer photos and testimonials in your ads."},
            {"trend": "AI-powered campaigns (Advantage+)", "implication": "Test Advantage+ campaigns to leverage Meta's machine learning for optimization."}
        ]

class CompetitorAnalyzer:
    """Analyzes competitor strategies."""

    def analyze_competitor_ads(self, competitor_page_url: str) -> Dict[str, Any]:
        """Provides a summary of a competitor's ad strategy."""
        return {
            "summary": f"Competitor at {competitor_page_url} is running mainly video ads focusing on price promotions.",
            "common_themes": ["Discounts", "Limited-time offers", "New arrivals"],
            "ad_format_mix": {"video": 0.6, "image": 0.3, "carousel": 0.1}
        }

class InfluencerIdentifier:
    """Identifies relevant influencers for collaborations."""

    def find_influencers(self, niche: str, follower_range: Tuple[int, int] = (10000, 100000)) -> List[Dict[str, Any]]:
        """Finds potential influencers in a given niche and follower range."""
        # Dummy data
        return [
            {"name": "Influencer One", "followers": 55000, "engagement_rate": 3.5, "niche": niche},
            {"name": "Influencer Two", "followers": 25000, "engagement_rate": 5.2, "niche": niche},
            {"name": "Influencer Three", "followers": 89000, "engagement_rate": 2.8, "niche": niche}
        ]

class ROITracker:
    """Tracks and calculates return on investment."""

    def calculate_roi(self, ad_spend: float, revenue: float) -> float:
        """Calculates ROI from ad spend and revenue."""
        if ad_spend == 0: return 0
        return ((revenue - ad_spend) / ad_spend) * 100

    def calculate_roas(self, ad_spend: float, revenue: float) -> float:
        """Calculates Return On Ad Spend (ROAS)."""
        if ad_spend == 0: return 0
        return revenue / ad_spend

class QuickAdGenerator:
    """Generates ads quickly for immediate posting."""

    def generate_quick_text_ad(self, product_name: str, benefit: str) -> Dict[str, str]:
        """Generates a simple text ad that can be used immediately."""
        return {
            "headline": f"{product_name}: The Ultimate Solution!",
            "primary_text": f"Finally, a way to {benefit}. Get {product_name} today! #ad #{product_name.lower()}\n\nShop Now!",
            "cta": "Shop Now"
        }

    def generate_quick_image_ad(self, product_name: str, benefit: str, image_url: str) -> Dict[str, Any]:
        """Generates a simple image ad package."""
        text_ad = self.generate_quick_text_ad(product_name, benefit)
        text_ad['image_url'] = image_url
        return text_ad

class ComplianceChecker:
    """Checks ads against Facebook's advertising policies."""

    def check_ad_copy(self, ad_copy: Dict[str, str]) -> List[str]:
        """Performs a basic check for common policy violations."""
        warnings = []
        text_to_check = ad_copy.get("primary_text", "") + " " + ad_copy.get("headline", "")
        
        if re.search(r'\byou\b', text_to_check, re.IGNORECASE):
            warnings.append("Warning: Using 'you' or 'your' can sometimes imply personal attributes. Review carefully against Facebook's policy.")
        
        if re.search(r'\b(lose weight|fat loss|get rid of debt)\b', text_to_check, re.IGNORECASE):
            warnings.append("Warning: Ad copy contains phrases related to sensitive topics (e.g., weight loss, financial distress) that are highly scrutinized. Ensure claims are realistic and not misleading.")

        if len(ad_copy.get("primary_text", "")) > 900:
            warnings.append("Warning: Primary text is very long, which may impact performance and user experience.")
            
        if ad_copy.get("cta", "").lower() == "click here":
            warnings.append("Warning: 'Click Here' is a low-quality CTA. Use more descriptive calls to action like 'Shop Now' or 'Learn More'.")

        return warnings

# ==================================================================================================
#        MCP TOOL DEFINITIONS
# ==================================================================================================

TOOLS = [
    {
        "tool_name": "meta_generate_ad_copy",
        "description": "Generate compelling ad copy for a Meta/Facebook ad.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string"},
                "target_audience": {"type": "string"},
                "key_benefit": {"type": "string"},
                "tone": {"type": "string", "default": "persuasive"},
                "cta": {"type": "string", "default": "Learn More"}
            },
            "required": ["product_name", "target_audience", "key_benefit"]
        }
    },
    {
        "tool_name": "meta_get_trends",
        "description": "Get current marketing trends on Meta/Facebook.",
        "input_schema": {}
    }
]

# ==================================================================================================
#        FASTAPI ROUTER
# ==================================================================================================

def create_fastapi_router(skill_manager):
    """Creates a FastAPI router for this skill."""
    from fastapi import APIRouter, Depends

    router = APIRouter()
    ad_creator = AdCreator()

    @router.post("/generate-ad-copy")
    def generate_ad_copy_endpoint(product_name: str, target_audience: str, key_benefit: str, tone: str = "persuasive", cta: str = "Learn More"):
        return ad_creator.generate_text_ad(product_name, target_audience, key_benefit, tone, cta)

    @router.get("/trends")
    def get_trends_endpoint():
        trend_analyzer = TrendAnalyzer()
        return trend_analyzer.get_current_trends()

    return router

# ==================================================================================================
#        UNIT TESTS
# ==================================================================================================

class TestMetaFacebookMarketingSkill(unittest.TestCase):

    def setUp(self):
        """Set up test instances of all expert classes."""
        self.ad_creator = AdCreator()
        self.campaign_manager = CampaignManager()
        self.content_calendar = ContentCalendar()
        self.audience_targeter = AudienceTargeter()
        self.analytics_reporter = AnalyticsReporter()
        self.keyword_researcher = KeywordResearcher()
        self.trend_analyzer = TrendAnalyzer()
        self.competitor_analyzer = CompetitorAnalyzer()
        self.influencer_identifier = InfluencerIdentifier()
        self.roi_tracker = ROITracker()
        self.quick_ad_generator = QuickAdGenerator()
        self.compliance_checker = ComplianceChecker()

    def test_ad_copy_generation(self):
        """Test basic ad copy generation."""
        ad_copy = self.ad_creator.generate_text_ad("NewCo", "tech enthusiasts", "boost productivity")
        self.assertIsInstance(ad_copy, dict)
        self.assertIn("headline", ad_copy)
        self.assertIn("NewCo", ad_copy["headline"])

    def test_reels_ad_concept(self):
        """Test Reels ad concept generation."""
        concept = self.ad_creator.generate_reels_ad_concept("SuperDrink", "athletes")
        self.assertIsInstance(concept, dict)
        self.assertIn("concept", concept)
        self.assertIn("SuperDrink", concept["concept"])

    def test_campaign_planning(self):
        """Test campaign plan creation."""
        plan = self.campaign_manager.create_campaign_plan("GadgetX", 5000, 4, "conversions")
        self.assertEqual(plan["budget"], 5000)
        self.assertEqual(plan["objective"], "conversions")

    def test_advantage_plus_setup(self):
        """Test Advantage+ campaign setup recommendation."""
        setup = self.campaign_manager.setup_advantage_plus_campaign("WidgetZ", 1000, "US adults 25-54")
        self.assertEqual(setup["campaign_type"], "Advantage+ Shopping Campaign")
        self.assertIn("Meta\'s AI", setup["recommendation"])

    def test_content_calendar(self):
        """Test content calendar generation."""
        calendar = self.content_calendar.generate_calendar("fitness", 3)
        self.assertEqual(len(calendar), 3)
        self.assertEqual(calendar[0]["day"], 1)

    def test_lookalike_strategy(self):
        """Test Lookalike Audience strategy creation."""
        strategy = self.audience_targeter.create_lookalike_strategy("Website Visitors", "CA")
        self.assertIn("1% Lookalike", strategy["recommendation"])
        self.assertEqual(strategy["country"], "CA")

    def test_pixel_setup(self):
        """Test Meta Pixel setup instruction generation."""
        pixel_info = self.audience_targeter.setup_pixel_tracking("https://my-awesome-site.com")
        self.assertTrue(pixel_info["pixel_id"].startswith("PIXEL_"))
        self.assertIn("Meta Pixel Helper", pixel_info["setup_instructions"])
        self.assertIn(pixel_info["pixel_id"], pixel_info["pixel_code_snippet"])

    def test_performance_analysis(self):
        """Test dummy performance analysis."""
        report = self.analytics_reporter.analyze_performance({"ctr": 0.03, "cpc": 1.2})
        self.assertIn("recommendations", report)
        self.assertEqual(report["key_metrics"]["ctr"], 0.03)

    def test_hashtag_research(self):
        """Test hashtag suggestion functionality."""
        hashtags = self.keyword_researcher.get_related_hashtags("baking", 3)
        self.assertEqual(len(hashtags), 3)
        self.assertIn("#baking", hashtags)

    def test_trend_analysis(self):
        """Test trend analysis functionality."""
        trends = self.trend_analyzer.get_current_trends()
        self.assertIsInstance(trends, list)
        self.assertGreater(len(trends), 0)
        self.assertIn("trend", trends[0])

    def test_roi_calculation(self):
        """Test ROI and ROAS calculations."""
        roi = self.roi_tracker.calculate_roi(ad_spend=100, revenue=500)
        roas = self.roi_tracker.calculate_roas(ad_spend=100, revenue=500)
        self.assertAlmostEqual(roi, 400.0)
        self.assertAlmostEqual(roas, 5.0)

    def test_quick_ad_generator(self):
        """Test the quick ad generation for immediate use."""
        ad = self.quick_ad_generator.generate_quick_image_ad("QuickBook", "read faster", "http://image.url/book.jpg")
        self.assertIn("QuickBook", ad["headline"])
        self.assertIn("Shop Now", ad["cta"])
        self.assertEqual(ad["image_url"], "http://image.url/book.jpg")

    def test_compliance_checker(self):
        """Test the compliance checker for various ad copy issues."""
        good_copy = {"primary_text": "A great new product.", "headline": "Check it out!", "cta": "Learn More"}
        bad_copy_you = {"primary_text": "Are you tired? You need this.", "headline": "Feel Better Now"}
        bad_copy_claim = {"primary_text": "Guaranteed to help you lose weight in 3 days.", "headline": "Fast Weight Loss"}
        bad_copy_cta = {"primary_text": "Our product is amazing.", "headline": "Get it now", "cta": "Click Here"}
        
        self.assertEqual(len(self.compliance_checker.check_ad_copy(good_copy)), 0)
        self.assertTrue(any("personal attributes" in w for w in self.compliance_checker.check_ad_copy(bad_copy_you)))
        self.assertTrue(any("sensitive topics" in w for w in self.compliance_checker.check_ad_copy(bad_copy_claim)))
        self.assertTrue(any("low-quality CTA" in w for w in self.compliance_checker.check_ad_copy(bad_copy_cta)))


# ==================================================================================================
#        CLI INTERFACE
# ==================================================================================================

def main():
    parser = argparse.ArgumentParser(description="Meta/Facebook Marketing Skill CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Ad generation command
    ad_parser = subparsers.add_parser("generate_ad", help="Generate a new ad creative")
    ad_parser.add_argument("--product", required=True, help="Product name")
    ad_parser.add_argument("--audience", required=True, help="Target audience description")
    ad_parser.add_argument("--benefit", required=True, help="Key benefit to highlight")

    # Trend analysis command
    trends_parser = subparsers.add_parser("get_trends", help="Get current marketing trends")

    # Compliance check command
    compliance_parser = subparsers.add_parser("check_compliance", help="Check ad copy for compliance")
    compliance_parser.add_argument("--headline", required=True, help="Ad headline")
    compliance_parser.add_argument("--primary_text", required=True, help="Ad primary text")

    args = parser.parse_args()

    if args.command == "generate_ad":
        ad_creator = AdCreator()
        ad_copy = ad_creator.generate_text_ad(args.product, args.audience, args.benefit)
        print(json.dumps(ad_copy, indent=2))
    elif args.command == "get_trends":
        trend_analyzer = TrendAnalyzer()
        trends = trend_analyzer.get_current_trends()
        print(json.dumps(trends, indent=2))
    elif args.command == "check_compliance":
        checker = ComplianceChecker()
        warnings = checker.check_ad_copy({
            "headline": args.headline,
            "primary_text": args.primary_text
        })
        if warnings:
            print("Compliance Warnings:")
            for warning in warnings:
                print(f"- {warning}")
        else:
            print("No obvious compliance issues found.")

if __name__ == "__main__":
    main()
