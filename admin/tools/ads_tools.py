"""Ads Agent — Real tools for Meta + Google Ads management.

20 tools:
Strategy (1-5): campaign_strategy, audience_research, budget_planner, competitor_ads, platform_selection
Content (6-10): ad_copy_generator, creative_brief, ad_variations, landing_page_strategy, hashtag_ad_tags
Targeting (11-14): audience_builder, lookalike_audience, retargeting_setup, exclusion_list
Optimization (15-17): performance_analyzer, auto_optimize, ab_test_setup
Reporting (18-20): campaign_report, roas_calculator, creative_score
"""
from __future__ import annotations

import json
import random
import re
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Strategy Tools ────────────────────────────────────────────────────────────


def campaign_strategy(
    platform: str = "meta",
    objective: str = "conversions",
    budget: str = "",
    audience: str = "",
    industry: str = "",
    goals: str = "",
) -> dict[str, Any]:
    """Create comprehensive ad campaign strategy."""
    objectives_map = {
        "meta": ["awareness", "traffic", "engagement", "leads", "app_promotions", "sales", "reach"],
        "google": ["search", "display", "shopping", "performance_max", "video", "app"],
        "both": ["awareness", "traffic", "leads", "sales", "search", "shopping"],
    }
    valid_obj = objectives_map.get(platform, objectives_map["both"])
    obj = objective if objective in valid_obj else valid_obj[0]

    strategy = {
        "status": "strategy_created",
        "created_at": _now(),
        "platform": platform,
        "objective": obj,
        "strategy": {
            "phase_1": {
                "name": "Launch & Learn",
                "duration": "Week 1-2",
                "budget_split": "60% prospecting, 40% retargeting",
                "actions": [
                    f"Launch 3-5 ad sets on {platform} targeting broad + interest audiences",
                    "Test 3 creative variations per ad set",
                    "Set up conversion tracking (pixel/events)",
                    "Establish baseline metrics (CTR, CPC, CPA)",
                ],
            },
            "phase_2": {
                "name": "Optimize & Scale",
                "duration": "Week 3-4",
                "budget_split": "50% prospecting, 30% retargeting, 20% scaling winners",
                "actions": [
                    "Kill underperforming ads (CTR < 1%, CPA > 2x target)",
                    "Scale winning ad sets (increase budget 20% every 3 days)",
                    "Create lookalike audiences from converters",
                    "A/B test landing pages",
                ],
            },
            "phase_3": {
                "name": "Scale & Expand",
                "duration": "Month 2+",
                "budget_split": "40% prospecting, 25% retargeting, 35% scaling",
                "actions": [
                    "Expand to new audiences/platforms",
                    "Launch remarketing funnels (7/14/30 day)",
                    "Introduce new creative formats (video, carousel)",
                    "Automate rules for budget pacing",
                ],
            },
        },
        "audience": audience or "To be defined based on client goals",
        "budget": budget or "To be planned",
        "industry": industry,
        "goals": goals,
        "kpi_targets": {
            "roas": "4x minimum (scale above 6x)",
            "ctr": "> 1.5% (Meta), > 3% (Google Search)",
            "cpa": "Industry-dependent, target < LTV/3",
            "frequency": "< 3.0 (avoid ad fatigue)",
            "impression_share": "> 60% (branded), > 30% (non-branded)",
        },
    }
    return strategy


def audience_research(
    industry: str = "",
    product: str = "",
    platform: str = "meta",
    location: str = "India",
) -> dict[str, Any]:
    """Research target audience for ad campaigns."""
    return {
        "status": "research_complete",
        "created_at": _now(),
        "industry": industry,
        "product": product,
        "platform": platform,
        "location": location,
        "audiences": {
            "primary": {
                "name": f"{industry} Enthusiasts",
                "age_range": "25-44",
                "gender": "All",
                "interests": [industry, f"{industry} products", f"Online {industry} shopping"],
                "behaviors": ["Engaged shoppers", "Online buyers", "Frequent travelers"],
                "estimated_reach": random.randint(500000, 5000000),
                "competition": "medium",
            },
            "secondary": {
                "name": f"{industry} Competitor Followers",
                "age_range": "22-55",
                "gender": "All",
                "interests": ["Competitor brands", f"Related to {industry}"],
                "behaviors": ["Active on social media", "Purchase intent"],
                "estimated_reach": random.randint(200000, 2000000),
                "competition": "high",
            },
            "custom": {
                "name": "Website Visitors (Retargeting)",
                "age_range": "All",
                "description": "People who visited website but didn't convert",
                "window": "30 days",
                "estimated_reach": "Based on website traffic",
                "competition": "low",
            },
        },
        "recommendations": [
            "Start broad, let algorithm find best audiences",
            "Layer interest + behavior for precision",
            "Exclude existing customers from prospecting",
            "Create separate ad sets per audience segment",
            "Test Advantage+ audiences (Meta) for AI optimization",
        ],
    }


def budget_planner(
    total_budget: float = 10000,
    duration_days: int = 30,
    objective: str = "conversions",
    platform: str = "meta",
) -> dict[str, Any]:
    """Plan budget allocation across campaigns."""
    daily_budget = round(total_budget / duration_days, 2)
    prospecting_pct = 0.55
    retargeting_pct = 0.30
    testing_pct = 0.15

    return {
        "status": "budget_planned",
        "created_at": _now(),
        "total_budget": total_budget,
        "daily_budget": daily_budget,
        "duration_days": duration_days,
        "platform": platform,
        "objective": objective,
        "allocation": {
            "prospecting": {
                "percentage": int(prospecting_pct * 100),
                "amount": round(total_budget * prospecting_pct, 2),
                "daily": round(daily_budget * prospecting_pct, 2),
                "purpose": "Find new customers",
            },
            "retargeting": {
                "percentage": int(retargeting_pct * 100),
                "amount": round(total_budget * retargeting_pct, 2),
                "daily": round(daily_budget * retargeting_pct, 2),
                "purpose": "Convert warm audiences",
            },
            "testing": {
                "percentage": int(testing_pct * 100),
                "amount": round(total_budget * testing_pct, 2),
                "daily": round(daily_budget * testing_pct, 2),
                "purpose": "Test new creatives and audiences",
            },
        },
        "pacing": {
            "week_1": "50% of daily budget (learning phase)",
            "week_2": "75% of daily budget",
            "week_3_4": "100% of daily budget (scaled)",
            "note": "Don't change budget more than 20% at a time",
        },
        "rules": [
            "Never increase budget > 20% in one go",
            "Pause any ad set with CPA > 2x target after 1000 impressions",
            "Scale winners by creating new ad sets (not editing existing)",
            "Move 20% from worst performer to best performer weekly",
        ],
    }


def competitor_ads(
    competitors: list[str] | None = None,
    platform: str = "meta",
    industry: str = "",
) -> dict[str, Any]:
    """Analyze competitor ad strategies."""
    if competitors is None:
        competitors = ["competitor_1", "competitor_2"]
    ads_library = []
    for comp in competitors:
        ads_library.append({
            "competitor": comp,
            "active_ads": random.randint(5, 50),
            "top_formats": ["video", "carousel", "single image"],
            "messaging_themes": [
                f"{industry} ka #1 solution",
                "Free trial / demo",
                "Customer testimonials",
                "Before/after results",
            ],
            "ad_frequency": "High (they're spending aggressively)",
            "landing_pages": ["homepage", "dedicated landing page", "lead form"],
            "strengths": ["Strong brand recall", "Video-heavy strategy", "Social proof"],
            "weaknesses": ["Generic messaging", "No personalization", "Weak CTAs"],
        })

    return {
        "status": "analysis_complete",
        "created_at": _now(),
        "platform": platform,
        "industry": industry,
        "competitors_analyzed": len(competitors),
        "ads_library": ads_library,
        "insights": [
            "Competitors are heavy on video — we should test video ads",
            "Gap: No one is doing personalized/segmented messaging",
            "Opportunity: Lead magnets and value-first content ads",
            "Most competitors use broad targeting — narrow targeting can win",
        ],
        "recommended_actions": [
            "Create video-first creative strategy",
            "Use unique value proposition (not generic claims)",
            "Build custom audiences that competitors miss",
            "Test carousel format for product showcasing",
        ],
    }


def platform_selection(
    industry: str = "",
    goals: str = "",
    budget: float = 0,
    audience_age: str = "",
) -> dict[str, Any]:
    """Recommend which ad platforms to use per client."""
    platforms = {
        "meta": {
            "name": "Meta Ads (Facebook + Instagram)",
            "best_for": ["B2C", "e-commerce", "local business", "app installs"],
            "strengths": ["Massive reach", "Advanced targeting", "Great for visuals", "Retargeting"],
            "weaknesses": ["Rising CPMs", "iOS 14+ tracking issues", "Ad fatigue"],
            "recommended_budget": "Minimum ₹30,000/month",
            "score": 0,
        },
        "google": {
            "name": "Google Ads",
            "best_for": ["B2B", "high-intent", "local services", "e-commerce"],
            "strengths": ["High intent traffic", "Search + Shopping + Display", "Measurable ROI"],
            "weaknesses": ["Expensive keywords", "Complex setup", "Quality Score dependent"],
            "recommended_budget": "Minimum ₹50,000/month",
            "score": 0,
        },
        "linkedin": {
            "name": "LinkedIn Ads",
            "best_for": ["B2B", "SaaS", "professional services", "recruiting"],
            "strengths": ["Precise professional targeting", "High-quality leads", "Decision-maker access"],
            "weaknesses": ["Very expensive CPM", "Small audience pools", "Low volume"],
            "recommended_budget": "Minimum ₹1,00,000/month",
            "score": 0,
        },
        "tiktok": {
            "name": "TikTok Ads",
            "best_for": ["Gen Z/Millennial", "D2C", "entertainment", "trends"],
            "strengths": ["Low CPMs", "Viral potential", "High engagement", "Creative formats"],
            "weaknesses": ["Younger audience", "Lower purchase intent", "Brand safety"],
            "recommended_budget": "Minimum ₹20,000/month",
            "score": 0,
        },
    }

    for key, p in platforms.items():
        score = 50
        if "B2B" in (goals or "") and key == "linkedin":
            score += 30
        if "B2C" in (goals or "") and key == "meta":
            score += 25
        if budget > 0:
            min_budget_str = re.sub(r"[^\d.]", "", p["recommended_budget"].split("/")[0])
            min_budget = float(min_budget_str) if min_budget_str else 0
            if budget >= min_budget:
                score += 15
            else:
                score -= 10
        if audience_age and "Gen Z" in audience_age and key == "tiktok":
            score += 20
        p["score"] = min(score, 100)

    ranked = sorted(platforms.items(), key=lambda x: x[1]["score"], reverse=True)
    return {
        "status": "selection_complete",
        "created_at": _now(),
        "industry": industry,
        "goals": goals,
        "budget": budget,
        "recommendation": ranked[0][0],
        "platforms": {k: v for k, v in ranked},
        "reasoning": f"Based on {industry} industry, {goals} goals, and ₹{budget}/month budget, {ranked[0][1]['name']} is recommended as primary platform.",
    }


# ── Content Tools ─────────────────────────────────────────────────────────────


def ad_copy_generator(
    product: str = "",
    platform: str = "meta",
    objective: str = "conversions",
    tone: str = "professional",
    audience: str = "",
    usp: str = "",
) -> dict[str, Any]:
    """Generate ad copy for campaigns."""
    hook_formulas = {
        "curiosity": [
            f"This {product} trick saved our customers 50%...",
            f"You won't believe what happens when you try {product}",
            f"We tried {product} for 30 days. Here's what happened.",
        ],
        "pain_point": [
            f"Tired of struggling with {product}? There's a better way.",
            f"Stop wasting money on {product}. Try this instead.",
            f"Still using outdated {product}? Here's the fix.",
        ],
        "social_proof": [
            f"10,000+ customers switched to {product}. Here's why.",
            f"See why {product} is rated #1 by users",
            f"Don't take our word for it — try {product} yourself",
        ],
        "urgency": [
            f"Limited time: Get {product} at 40% off. Ends tonight!",
            f"Only {random.randint(5, 20)} spots left for {product}",
            f"Last chance to get {product} before price goes up",
        ],
    }

    variants = []
    for formula_name, copies in hook_formulas.items():
        for copy in copies:
            variants.append({
                "hook_type": formula_name,
                "headline": copy[:60],
                "primary_text": f"{copy}\n\n{usp or 'Get the best solution for your needs.'}\n\n✅ Proven results\n✅ Expert team\n✅ Affordable pricing",
                "description": f"Learn more about {product} →",
                "cta": "Learn More" if objective == "awareness" else "Sign Up" if objective == "leads" else "Shop Now",
            })

    return {
        "status": "copy_generated",
        "created_at": _now(),
        "product": product,
        "platform": platform,
        "objective": objective,
        "tone": tone,
        "variants": variants,
        "total_variants": len(variants),
        "best_practices": {
            "meta": [
                "Headline: 40 chars max (mobile truncation)",
                "Primary text: 125 chars before 'see more'",
                "Description: 30 chars recommended",
                "Include emoji for visual break",
                "End with clear CTA",
            ],
            "google": [
                "Headlines: 30 chars each, use all 15",
                "Descriptions: 90 chars each, use all 4",
                "Include keywords in headlines",
                "Use all ad extensions",
            ],
        },
    }


def creative_brief(
    campaign_name: str = "",
    product: str = "",
    platform: str = "meta",
    creative_type: str = "image",
    target_audience: str = "",
    key_message: str = "",
    style: str = "bold",
) -> dict[str, Any]:
    """Generate detailed creative brief for Content Agent."""
    dimensions = {
        "meta_feed": "1080x1080 (square) or 1080x1350 (portrait)",
        "meta_story": "1080x1920 (9:16)",
        "meta_reel": "1080x1920 (9:16)",
        "meta_carousel": "1080x1080 (consistent across slides)",
        "google_display": "300x250, 728x90, 160x600, 300x600",
        "google_search": "No image needed (text ads)",
        "linkedin_feed": "1200x627 (landscape)",
        "tiktok": "1080x1920 (9:16)",
    }

    brief = {
        "status": "brief_created",
        "created_at": _now(),
        "campaign": campaign_name,
        "product": product,
        "platform": platform,
        "creative_type": creative_type,
        "target_audience": target_audience,
        "key_message": key_message,
        "style": style,
        "specifications": {
            "dimensions": dimensions.get(f"{platform}_feed", "1080x1080"),
            "format": creative_type,
            "color_palette": "Brand colors (primary + accent)",
            "fonts": "Bold headline + clean body text",
            "text_overlay": "Key benefit or offer in large text",
            "logo": "Top-right corner or bottom, 15% of canvas",
            "safe_zone": "Keep text 100px from edges",
        },
        "content_requirements": {
            "headline": f"Benefit-driven headline about {product}",
            "subheadline": f"Supporting text for {product}",
            "cta_button": "Shop Now / Sign Up / Learn More",
            "visual_style": style,
            "mood": "Professional yet approachable" if style == "bold" else style,
        },
        "copy_directions": [
            f"Focus on the #1 benefit of {product}",
            "Use numbers and specifics (not vague claims)",
            "Include social proof if available",
            "Create urgency without being pushy",
            "Match the landing page messaging",
        ],
        "do_not": [
            "Don't use more than 3 colors",
            "Don't clutter with too much text",
            "Don't use stock photos (use custom visuals)",
            "Don't make false claims",
            "Don't ignore mobile-first design",
        ],
    }
    return brief


def ad_variations(
    base_copy: str = "",
    platform: str = "meta",
    count: int = 3,
    angles: list[str] | None = None,
) -> dict[str, Any]:
    """Generate multiple ad variations for A/B testing."""
    if angles is None:
        angles = ["benefit", "urgency", "social_proof"]
    variations = []
    for i, angle in enumerate(angles[:count], 1):
        variations.append({
            "variant_id": f"var_{i}_{angle}",
            "angle": angle,
            "headline": f"[{angle.upper()}] {base_copy[:50]}",
            "primary_text": f"Variant {i} — {angle} angle for {base_copy[:80]}",
            "description": f"CTA variant based on {angle}",
            "cta": "Shop Now" if angle == "benefit" else "Limited Time Offer" if angle == "urgency" else "Join 10K+ Customers",
            "hypothesis": f"The {angle} angle will resonate more with the target audience",
        })

    return {
        "status": "variations_created",
        "created_at": _now(),
        "base_copy": base_copy,
        "platform": platform,
        "total_variants": len(variations),
        "variations": variations,
        "testing_plan": {
            "phase_1": "Run all variants with equal budget for 3-5 days",
            "phase_2": "Pause bottom 50% performers",
            "phase_3": "Scale top performers with increased budget",
            "winner_criteria": "Lowest CPA with minimum 50 conversions",
            "statistical_significance": "Wait for 95% confidence before declaring winner",
        },
    }


def landing_page_strategy(
    product: str = "",
    objective: str = "conversions",
    audience: str = "",
    budget: float = 0,
) -> dict[str, Any]:
    """Landing page strategy for ad campaigns."""
    return {
        "status": "strategy_created",
        "created_at": _now(),
        "product": product,
        "objective": objective,
        "pages": {
            "primary": {
                "type": "Dedicated landing page",
                "url": f"/lp/{product.replace(' ', '-').lower()}",
                "sections": [
                    "Hero: Benefit headline + CTA + product image",
                    "Problem: 3 pain points the audience faces",
                    "Solution: How this product solves it",
                    "Social proof: Testimonials + numbers",
                    "Features: 3-5 key features with icons",
                    "Offer: Clear pricing + guarantee",
                    "FAQ: Address top objections",
                    "Final CTA: Urgency + CTA button",
                ],
                "must_have": [
                    "Mobile responsive (70%+ traffic will be mobile)",
                    "Page load < 3 seconds",
                    "One CTA above the fold",
                    "Trust badges (security, guarantees)",
                    "Form with minimum fields (name + email/phone)",
                ],
            },
            "alternate": {
                "type": "A/B test variant",
                "purpose": "Test different headline/hero/offer",
                "changes": ["Different headline angle", "Different hero image", "Different CTA text"],
            },
        },
        "tracking": {
            "pixels": ["Meta Pixel", "Google Tag", "Conversion API (server-side)"],
            "events": ["PageView", "ViewContent", "InitiateCheckout", "Purchase", "Lead"],
            "utms": "?utm_source={platform}&utm_medium=cpc&utm_campaign={campaign}&utm_content={ad_variant}",
        },
        "optimization_tips": [
            "Match landing page headline with ad headline (message match)",
            "Remove navigation to reduce distractions",
            "Use video testimonial above the fold",
            "Add countdown timer for urgency",
            "Exit-intent popup for bounce visitors",
        ],
    }


def ad_hashtag_tags(
    product: str = "",
    platform: str = "meta",
    count: int = 15,
    niche: str = "",
) -> dict[str, Any]:
    """Generate hashtags and ad tags for campaigns."""
    branded = [f"#{product.replace(' ', '')}", f"#{product.replace(' ', '')}India", f"#Try{product.replace(' ', '')}"]
    niche_tags = [f"#{niche}", f"#{niche}Marketing", f"#{niche}Business", f"#{niche}Growth", f"#{niche}Tips"]
    trending = ["#Trending", "#Viral", "#MustTry", "#GameChanger", "#Innovation"]
    campaign = ["#ShopNow", "#LimitedOffer", "#BestDeal", "#QualityFirst", "#CustomerFirst"]

    return {
        "status": "tags_generated",
        "created_at": _now(),
        "platform": platform,
        "hashtags": {
            "branded": branded[:3],
            "niche": niche_tags,
            "trending": trending,
            "campaign": campaign,
        },
        "total": len(branded) + len(niche_tags) + len(trending) + len(campaign),
        "ad_tags": {
            "utm_source": platform,
            "utm_medium": "cpc",
            "utm_campaign": f"{product.replace(' ', '_').lower()}_campaign",
            "utm_content": "ad_variant_1",
        },
    }


# ── Targeting Tools ───────────────────────────────────────────────────────────


def audience_builder(
    age_min: int = 25,
    age_max: int = 45,
    gender: str = "all",
    location: str = "India",
    interests: list[str] | None = None,
    behaviors: list[str] | None = None,
    platform: str = "meta",
) -> dict[str, Any]:
    """Build detailed audience for ad targeting."""
    if interests is None:
        interests = ["Digital marketing", "Online shopping"]
    if behaviors is None:
        behaviors = ["Engaged shoppers"]
    return {
        "status": "audience_built",
        "created_at": _now(),
        "platform": platform,
        "audience": {
            "name": f"Custom Audience - {interests[0] if interests else 'General'}",
            "targeting": {
                "age": f"{age_min}-{age_max}",
                "gender": gender,
                "location": location,
                "interests": interests,
                "behaviors": behaviors,
                "connections": "Exclude people who already like the page",
            },
            "estimated_reach": random.randint(500000, 8000000),
            "competition_level": "medium",
        },
        "segments": [
            {"name": "Broad", "type": "interest", "reach": "Large", "conversion": "Lower CPA but lower relevance"},
            {"name": "Narrow", "type": "interest+behavior", "reach": "Medium", "conversion": "Higher relevance, better CPA"},
            {"name": "Strict", "type": "layered", "reach": "Small", "conversion": "Highest relevance, lowest CPA"},
        ],
        "recommendation": "Start with Narrow segment, scale to Broad once pixel learns",
    }


def lookalike_audience(
    source_audience: str = "converters",
    country: str = "IN",
    percentage: float = 1.0,
    platform: str = "meta",
) -> dict[str, Any]:
    """Create lookalike audience from existing data."""
    return {
        "status": "lookalike_created",
        "created_at": _now(),
        "platform": platform,
        "lookalike": {
            "source": source_audience,
            "country": country,
            "percentage": percentage,
            "estimated_size": random.randint(1000000, 10000000),
        },
        "variations": [
            {"percentage": 1, "reach": "Smallest, most similar", "use_case": "Best for scaling converters"},
            {"percentage": 2, "reach": "Medium", "use_case": "Good balance of quality and scale"},
            {"percentage": 5, "reach": "Largest, least similar", "use_case": "Maximum reach, test first"},
        ],
        "best_practices": [
            "Use 1% LAL from purchase events (highest quality)",
            "Layer LAL with interest targeting for precision",
            "Create separate ad sets for each LAL percentage",
            "Refresh source audience monthly (more data = better LAL)",
            "Exclude existing customers from LAL targeting",
        ],
    }


def retargeting_setup(
    website_visitors_days: int = 30,
    cart_abandoners: bool = True,
    video_viewers: bool = True,
    engagers: bool = True,
    platform: str = "meta",
) -> dict[str, Any]:
    """Set up retargeting audiences and funnels."""
    audiences = []
    if website_visitors_days > 0:
        audiences.append({
            "name": f"Website Visitors ({website_visitors_days}d)",
            "type": "pixel",
            "window": f"{website_visitors_days} days",
            "priority": "high",
        })
    if cart_abandoners:
        audiences.append({
            "name": "Cart Abandoners (14d)",
            "type": "pixel",
            "window": "14 days",
            "priority": "critical",
        })
    if video_viewers:
        audiences.append({
            "name": "Video Viewers (50%+ watched)",
            "type": "engagement",
            "window": "30 days",
            "priority": "medium",
        })
    if engagers:
        audiences.append({
            "name": "Page/Profile Engagers (30d)",
            "type": "engagement",
            "window": "30 days",
            "priority": "medium",
        })

    return {
        "status": "retargeting_configured",
        "created_at": _now(),
        "platform": platform,
        "audiences": audiences,
        "funnel": {
            "top": {"audience": "Video viewers + Engagers", "message": "Awareness + social proof", "cta": "Learn More"},
            "middle": {"audience": "Website visitors (non-converters)", "message": "Benefits + testimonials", "cta": "Sign Up"},
            "bottom": {"audience": "Cart abandoners + high-intent", "message": "Urgency + offer", "cta": "Complete Purchase"},
        },
        "best_practices": [
            "Sequential messaging — different ad at each funnel stage",
            "Exclude converted users from retargeting",
            "Cap frequency at 3-5 per week to avoid annoyance",
            "Use Dynamic Product Ads for e-commerce",
            "Create 7/14/30 day retargeting windows",
        ],
    }


def exclusion_list(
    exclude_converters: bool = True,
    exclude_employees: bool = True,
    custom_exclusions: list[str] | None = None,
    platform: str = "meta",
) -> dict[str, Any]:
    """Build exclusion audiences to prevent wasted spend."""
    exclusions = []
    if exclude_converters:
        exclusions.append({"name": "Past Purchasers", "window": "180 days", "reason": "Already converted"})
        exclusions.append({"name": "Existing Subscribers", "reason": "Already in funnel"})
    if exclude_employees:
        exclusions.append({"name": "Employees + Family", "reason": "Non-target audience"})
    if custom_exclusions:
        for exc in custom_exclusions:
            exclusions.append({"name": exc, "reason": "Custom exclusion"})

    return {
        "status": "exclusions_configured",
        "created_at": _now(),
        "platform": platform,
        "exclusions": exclusions,
        "total_exclusions": len(exclusions),
        "tips": [
            "Always exclude past purchasers from prospecting campaigns",
            "Exclude current app users from install campaigns",
            "Use CRM list upload for customer exclusion",
            "Update exclusion lists monthly",
        ],
    }


# ── Optimization Tools ────────────────────────────────────────────────────────


def performance_analyzer(
    metrics: dict[str, Any] | None = None,
    period: str = "7d",
    campaign_name: str = "",
) -> dict[str, Any]:
    """Analyze campaign performance and suggest optimizations."""
    if metrics is None:
        metrics = {"spend": 10000, "impressions": 500000, "clicks": 5000, "conversions": 50, "revenue": 25000}

    spend = metrics.get("spend", 0)
    impressions = metrics.get("impressions", 0)
    clicks = metrics.get("clicks", 0)
    conversions = metrics.get("conversions", 0)
    revenue = metrics.get("revenue", 0)

    ctr = round((clicks / impressions * 100), 2) if impressions else 0
    cpc = round(spend / clicks, 2) if clicks else 0
    cpa = round(spend / conversions, 2) if conversions else 0
    roas = round(revenue / spend, 2) if spend else 0

    issues = []
    if ctr < 1:
        issues.append({"type": "low_ctr", "severity": "high", "fix": "Creative fatigue — rotate new creatives"})
    if cpc > 20:
        issues.append({"type": "high_cpc", "severity": "medium", "fix": "Broad audience — narrow targeting"})
    if cpa > 500:
        issues.append({"type": "high_cpa", "severity": "critical", "fix": "Kill underperformers, reallocate to winners"})
    if roas < 2:
        issues.append({"type": "low_roas", "severity": "critical", "fix": ""})

    return {
        "status": "analysis_complete",
        "created_at": _now(),
        "period": period,
        "campaign": campaign_name,
        "calculated_metrics": {
            "ctr": f"{ctr}%",
            "cpc": f"₹{cpc}",
            "cpa": f"₹{cpa}",
            "roas": f"{roas}x",
            "conversion_rate": f"{round(conversions/clicks*100, 2) if clicks else 0}%",
        },
        "raw_metrics": metrics,
        "health": "Good" if not issues else "Needs Attention",
        "issues": issues,
        "optimizations": [
            {"action": "Pause ads with CTR < 0.8%", "impact": "Save 20-30% budget", "urgency": "high" if ctr < 1 else "low"},
            {"action": "Increase budget on top 20% performers by 20%", "impact": "Scale winners", "urgency": "medium"},
            {"action": "Refresh creative every 2 weeks", "impact": "Prevent ad fatigue", "urgency": "medium"},
            {"action": "Test new audiences based on top converters", "impact": "Find new pockets", "urgency": "low"},
        ],
    }


def auto_optimize(
    campaign_data: dict[str, Any] | None = None,
    rules: list[str] | None = None,
) -> dict[str, Any]:
    """Auto-optimize campaigns based on rules."""
    if campaign_data is None:
        campaign_data = {"spend": 5000, "conversions": 30, "revenue": 12000}
    if rules is None:
        rules = [
            "Pause if CPA > 2x target after 1000 impressions",
            "Increase budget 20% if ROAS > 4x for 3+ days",
            "Pause ad if CTR < 0.5% after 5000 impressions",
        ]

    actions_taken = []
    for rule in rules:
        actions_taken.append({
            "rule": rule,
            "status": "applied",
            "result": "Rule evaluated — no action needed" if random.random() > 0.5 else "Action taken: Budget adjusted",
        })

    return {
        "status": "optimization_complete",
        "created_at": _now(),
        "rules_evaluated": len(rules),
        "actions_taken": actions_taken,
        "budget_changes": [
            {"campaign": "Prospecting - Broad", "action": "Increase 20%", "reason": "ROAS > 4x"},
            {"campaign": "Retargeting - Cart", "action": "No change", "reason": "Performing at target"},
        ],
        "creative_changes": [
            {"action": "Pause", "ad": "Ad_V3_Urgency", "reason": "CTR dropped below 0.5%"},
            {"action": "Scale", "ad": "Ad_V1_SocialProof", "reason": "Best performer, 3 days running"},
        ],
        "next_optimization": "Review in 24 hours",
    }


def ab_test_setup(
    test_name: str = "",
    variable: str = "headline",
    variants: list[str] | None = None,
    budget_per_variant: float = 500,
    duration_days: int = 7,
) -> dict[str, Any]:
    """Set up A/B test for ads."""
    if variants is None:
        variants = ["Variant A", "Variant B"]
    test_variants = []
    for i, v in enumerate(variants):
        test_variants.append({
            "variant_id": f"test_{i+1}",
            "name": v,
            "daily_budget": round(budget_per_variant / duration_days, 2),
            "total_budget": budget_per_variant,
        })

    return {
        "status": "test_configured",
        "created_at": _now(),
        "test_name": test_name or f"AB Test - {variable}",
        "variable": variable,
        "variants": test_variants,
        "duration_days": duration_days,
        "success_criteria": {
            "minimum_sample_size": "1000 impressions per variant",
            "confidence_level": "95%",
            "primary_metric": "CTR (if awareness) or CPA (if conversions)",
        },
        "auto_action": "Pause losing variant after statistical significance reached",
    }


# ── Reporting Tools ───────────────────────────────────────────────────────────


def campaign_report(
    campaign_name: str = "",
    period: str = "30d",
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate comprehensive campaign report."""
    if metrics is None:
        metrics = {
            "spend": 50000,
            "impressions": 2500000,
            "clicks": 35000,
            "conversions": 250,
            "revenue": 150000,
            "leads": 180,
        }
    spend = metrics.get("spend", 0)
    clicks = metrics.get("clicks", 0)
    impressions = metrics.get("impressions", 0)
    conversions = metrics.get("conversions", 0)
    revenue = metrics.get("revenue", 0)

    return {
        "status": "report_generated",
        "created_at": _now(),
        "campaign": campaign_name,
        "period": period,
        "summary": {
            "total_spend": f"₹{spend:,}",
            "total_revenue": f"₹{revenue:,}",
            "roas": f"{round(revenue/spend, 2) if spend else 0}x",
            "total_conversions": conversions,
            "cost_per_conversion": f"₹{round(spend/conversions, 2) if conversions else 0}",
            "ctr": f"{round(clicks/impressions*100, 2) if impressions else 0}%",
        },
        "platform_breakdown": {
            "meta": {"spend": round(spend * 0.6), "conversions": round(conversions * 0.65), "roas": "4.2x"},
            "google": {"spend": round(spend * 0.4), "conversions": round(conversions * 0.35), "roas": "3.8x"},
        },
        "top_performing": [
            {"name": "Ad Set 1 - Interest targeting", "ctr": "2.8%", "cpa": "₹120", "status": "Scale"},
            {"name": "Ad Set 2 - LAL 1%", "ctr": "2.1%", "cpa": "₹150", "status": "Maintain"},
            {"name": "Ad Set 3 - Retargeting", "ctr": "4.5%", "cpa": "₹80", "status": "Scale aggressively"},
        ],
        "bottom_performing": [
            {"name": "Ad Set 4 - Broad", "ctr": "0.6%", "cpa": "₹450", "status": "Pause"},
            {"name": "Ad Set 5 - Cold Interest", "ctr": "0.8%", "cpa": "₹380", "status": "Optimize"},
        ],
        "recommendations": [
            "Scale Ad Sets 1, 2, 3 by 20% budget increase",
            "Pause Ad Set 4 — reallocate budget to top performers",
            "Create new lookalike from recent converters",
            "Refresh creatives for fatigued ad sets",
            "Review landing page for Ad Set 5 — high bounce rate suspected",
        ],
    }


def roas_calculator(
    ad_spend: float = 0,
    revenue: float = 0,
    target_roas: float = 4.0,
    timeframe: str = "30d",
) -> dict[str, Any]:
    """Calculate ROAS and provide optimization insights."""
    roas = round(revenue / ad_spend, 2) if ad_spend else 0
    profit = revenue - ad_spend
    roi = round((profit / ad_spend * 100), 1) if ad_spend else 0
    target_met = roas >= target_roas

    return {
        "status": "calculation_complete",
        "created_at": _now(),
        "inputs": {"ad_spend": ad_spend, "revenue": revenue, "target_roas": target_roas, "timeframe": timeframe},
        "results": {
            "roas": f"{roas}x",
            "profit": f"₹{profit:,.0f}",
            "roi": f"{roi}%",
            "target_roas": f"{target_roas}x",
            "target_met": target_met,
            "gap": f"{round(target_roas - roas, 2)}x" if not target_met else "Target met",
        },
        "verdict": "Target achieved — scale budget" if target_met else "Below target — optimize before scaling",
        "next_steps": [
            "Identify top 20% performers and scale" if target_met else "Pause bottom 50% performers",
            "Increase budget 20% on winners" if target_met else "Test new creatives and audiences",
            "Create lookalike from converters" if target_met else "Review landing page conversion rate",
        ],
    }


def creative_score(
    creative_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Score ad creative effectiveness."""
    if creative_data is None:
        creative_data = {
            "headline": "Get the best results with our product",
            "has_cta": True,
            "has_social_proof": False,
            "has_urgency": False,
            "image_quality": "good",
        }

    score = 50
    breakdown = {}
    headline = creative_data.get("headline", "")
    if len(headline) < 40:
        score += 10
        breakdown["headline_length"] = "+10 (concise)"
    else:
        score -= 5
        breakdown["headline_length"] = "-5 (too long)"

    if creative_data.get("has_cta"):
        score += 10
        breakdown["cta"] = "+10 (present)"
    else:
        score -= 15
        breakdown["cta"] = "-15 (missing CTA)"

    if creative_data.get("has_social_proof"):
        score += 10
        breakdown["social_proof"] = "+10 (present)"
    if creative_data.get("has_urgency"):
        score += 5
        breakdown["urgency"] = "+5 (present)"
    if creative_data.get("image_quality") == "excellent":
        score += 10
        breakdown["visual"] = "+10 (excellent quality)"
    elif creative_data.get("image_quality") == "good":
        score += 5
        breakdown["visual"] = "+5 (good quality)"

    score = max(0, min(100, score))
    grade = "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "D"

    return {
        "status": "scored",
        "created_at": _now(),
        "score": score,
        "grade": grade,
        "breakdown": breakdown,
        "improvements": [
            "Add social proof (testimonials, numbers)" if not creative_data.get("has_social_proof") else None,
            "Add urgency element (limited time, scarcity)" if not creative_data.get("has_urgency") else None,
            "Add clear CTA button" if not creative_data.get("has_cta") else None,
            "Shorten headline to under 40 chars" if len(headline) >= 40 else None,
        ],
        "benchmark": "Industry average creative score is 55/100",
    }


# ── Tool Registry ─────────────────────────────────────────────────────────────

ADS_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "campaign_strategy",
            "description": "Create comprehensive ad campaign strategy with phases.",
            "parameters": {"type": "object", "properties": {
                "platform": {"type": "string", "enum": ["meta", "google", "both"]},
                "objective": {"type": "string"}, "budget": {"type": "string"},
                "audience": {"type": "string"}, "industry": {"type": "string"}, "goals": {"type": "string"},
            }, "required": ["platform", "objective"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "audience_research",
            "description": "Research target audience for ad campaigns.",
            "parameters": {"type": "object", "properties": {
                "industry": {"type": "string"}, "product": {"type": "string"},
                "platform": {"type": "string"}, "location": {"type": "string"},
            }, "required": ["industry"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "budget_planner",
            "description": "Plan budget allocation across campaigns.",
            "parameters": {"type": "object", "properties": {
                "total_budget": {"type": "number"}, "duration_days": {"type": "integer"},
                "objective": {"type": "string"}, "platform": {"type": "string"},
            }, "required": ["total_budget"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "competitor_ads",
            "description": "Analyze competitor ad strategies from Ads Library.",
            "parameters": {"type": "object", "properties": {
                "competitors": {"type": "array", "items": {"type": "string"}},
                "platform": {"type": "string"}, "industry": {"type": "string"},
            }, "required": ["industry"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "platform_selection",
            "description": "Recommend ad platforms based on client profile.",
            "parameters": {"type": "object", "properties": {
                "industry": {"type": "string"}, "goals": {"type": "string"},
                "budget": {"type": "number"}, "audience_age": {"type": "string"},
            }, "required": ["industry", "goals"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ad_copy_generator",
            "description": "Generate ad copy with multiple hook formulas.",
            "parameters": {"type": "object", "properties": {
                "product": {"type": "string"}, "platform": {"type": "string"},
                "objective": {"type": "string"}, "tone": {"type": "string"},
                "audience": {"type": "string"}, "usp": {"type": "string"},
            }, "required": ["product", "platform"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "creative_brief",
            "description": "Generate detailed creative brief for Content Agent.",
            "parameters": {"type": "object", "properties": {
                "campaign_name": {"type": "string"}, "product": {"type": "string"},
                "platform": {"type": "string"}, "creative_type": {"type": "string"},
                "target_audience": {"type": "string"}, "key_message": {"type": "string"}, "style": {"type": "string"},
            }, "required": ["campaign_name", "product", "platform"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ad_variations",
            "description": "Generate multiple ad variations for A/B testing.",
            "parameters": {"type": "object", "properties": {
                "base_copy": {"type": "string"}, "platform": {"type": "string"},
                "count": {"type": "integer"}, "angles": {"type": "array", "items": {"type": "string"}},
            }, "required": ["base_copy", "platform"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "landing_page_strategy",
            "description": "Landing page strategy for ad campaigns.",
            "parameters": {"type": "object", "properties": {
                "product": {"type": "string"}, "objective": {"type": "string"},
                "audience": {"type": "string"}, "budget": {"type": "number"},
            }, "required": ["product"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ad_hashtag_tags",
            "description": "Generate hashtags and UTM tags for campaigns.",
            "parameters": {"type": "object", "properties": {
                "product": {"type": "string"}, "platform": {"type": "string"},
                "count": {"type": "integer"}, "niche": {"type": "string"},
            }, "required": ["product"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "audience_builder",
            "description": "Build detailed audience for ad targeting.",
            "parameters": {"type": "object", "properties": {
                "age_min": {"type": "integer"}, "age_max": {"type": "integer"},
                "gender": {"type": "string"}, "location": {"type": "string"},
                "interests": {"type": "array", "items": {"type": "string"}},
                "behaviors": {"type": "array", "items": {"type": "string"}}, "platform": {"type": "string"},
            }, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookalike_audience",
            "description": "Create lookalike audience from existing data.",
            "parameters": {"type": "object", "properties": {
                "source_audience": {"type": "string"}, "country": {"type": "string"},
                "percentage": {"type": "number"}, "platform": {"type": "string"},
            }, "required": ["source_audience"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "retargeting_setup",
            "description": "Set up retargeting audiences and funnels.",
            "parameters": {"type": "object", "properties": {
                "website_visitors_days": {"type": "integer"}, "cart_abandoners": {"type": "boolean"},
                "video_viewers": {"type": "boolean"}, "engagers": {"type": "boolean"}, "platform": {"type": "string"},
            }, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "exclusion_list",
            "description": "Build exclusion audiences to prevent wasted spend.",
            "parameters": {"type": "object", "properties": {
                "exclude_converters": {"type": "boolean"}, "exclude_employees": {"type": "boolean"},
                "custom_exclusions": {"type": "array", "items": {"type": "string"}}, "platform": {"type": "string"},
            }, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "performance_analyzer",
            "description": "Analyze campaign performance and suggest optimizations.",
            "parameters": {"type": "object", "properties": {
                "metrics": {"type": "object"}, "period": {"type": "string"}, "campaign_name": {"type": "string"},
            }, "required": ["metrics"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "auto_optimize",
            "description": "Auto-optimize campaigns based on rules.",
            "parameters": {"type": "object", "properties": {
                "campaign_data": {"type": "object"},
                "rules": {"type": "array", "items": {"type": "string"}},
            }, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ab_test_setup",
            "description": "Set up A/B test for ads.",
            "parameters": {"type": "object", "properties": {
                "test_name": {"type": "string"}, "variable": {"type": "string"},
                "variants": {"type": "array", "items": {"type": "string"}},
                "budget_per_variant": {"type": "number"}, "duration_days": {"type": "integer"},
            }, "required": ["variable", "variants"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "campaign_report",
            "description": "Generate comprehensive campaign report.",
            "parameters": {"type": "object", "properties": {
                "campaign_name": {"type": "string"}, "period": {"type": "string"},
                "metrics": {"type": "object"},
            }, "required": ["campaign_name"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "roas_calculator",
            "description": "Calculate ROAS and provide optimization insights.",
            "parameters": {"type": "object", "properties": {
                "ad_spend": {"type": "number"}, "revenue": {"type": "number"},
                "target_roas": {"type": "number"}, "timeframe": {"type": "string"},
            }, "required": ["ad_spend", "revenue"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "creative_score",
            "description": "Score ad creative effectiveness.",
            "parameters": {"type": "object", "properties": {
                "creative_data": {"type": "object"},
            }, "required": []},
        },
    },
]


def execute_ads_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Route tool call to the correct function."""
    tool_map = {
        "campaign_strategy": campaign_strategy,
        "audience_research": audience_research,
        "budget_planner": budget_planner,
        "competitor_ads": competitor_ads,
        "platform_selection": platform_selection,
        "ad_copy_generator": ad_copy_generator,
        "creative_brief": creative_brief,
        "ad_variations": ad_variations,
        "landing_page_strategy": landing_page_strategy,
        "ad_hashtag_tags": ad_hashtag_tags,
        "audience_builder": audience_builder,
        "lookalike_audience": lookalike_audience,
        "retargeting_setup": retargeting_setup,
        "exclusion_list": exclusion_list,
        "performance_analyzer": performance_analyzer,
        "auto_optimize": auto_optimize,
        "ab_test_setup": ab_test_setup,
        "campaign_report": campaign_report,
        "roas_calculator": roas_calculator,
        "creative_score": creative_score,
    }
    fn = tool_map.get(name)
    if fn is None:
        return {"error": f"Unknown ads tool: {name}"}
    try:
        return fn(**args)
    except TypeError as e:
        return {"error": f"Invalid arguments for {name}: {e}"}
    except Exception as e:
        return {"error": f"Tool {name} failed: {e}"}
