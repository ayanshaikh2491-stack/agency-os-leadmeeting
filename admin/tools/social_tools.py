"""Social Tools — Real tools for Social Media Agent.

10 tools:
1. content_calendar — Generate content calendar
2. hashtag_research — Find relevant hashtags
3. posting_schedule — Best times to post
4. competitor_analysis — Analyze competitor social presence
5. trend_research — Find trending topics
6. engagement_strategy — Plan community management
7. platform_strategy — Platform-specific strategy
8. content_gap_analysis — What competitors post that you don't
9. audience_analysis — Target audience insights
10. growth_tactics — Follower acquisition plan
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════════════════
# 1. CONTENT CALENDAR
# ═══════════════════════════════════════════════════════════════════════════════

def content_calendar(
    platform: str = "instagram",
    duration: str = "1 week",
    niche: str = "",
    brand_tone: str = "professional",
) -> dict[str, Any]:
    """Generate a content calendar for social media."""
    days_map = {"1 week": 7, "2 weeks": 14, "1 month": 30, "3 months": 90}
    num_days = days_map.get(duration, 7)

    content_mix = {
        "educational": 30,
        "entertaining": 25,
        "inspirational": 20,
        "promotional": 15,
        "user_generated": 10,
    }

    post_types = {
        "instagram": ["carousel", "reel", "single_image", "story", "collab"],
        "linkedin": ["text_post", "article", "carousel", "video", "poll"],
        "twitter": ["thread", "single_tweet", "poll", "quote_tweet", "space"],
        "facebook": ["image_post", "video", "link_share", "event", "live"],
        "tiktok": ["trending_sound", "tutorial", "behind_scenes", "duet", "stitch"],
    }

    days = []
    platform_types = post_types.get(platform, post_types["instagram"])
    start_date = datetime.now()

    for i in range(num_days):
        date = start_date + timedelta(days=i)
        day_name = date.strftime("%A")

        # Content mix rotation
        categories = list(content_mix.keys())
        category = categories[i % len(categories)]

        post_type = platform_types[i % len(platform_types)]

        days.append({
            "date": date.strftime("%Y-%m-%d"),
            "day": day_name,
            "content_type": post_type,
            "category": category,
            "topic": f"{category.title()} post about {niche or 'industry'}",
            "caption_note": f"{brand_tone} tone, include CTA",
            "hashtags_note": f"Mix of niche + trending hashtags",
        })

    return {
        "platform": platform,
        "duration": duration,
        "total_posts": len(days),
        "content_mix": content_mix,
        "calendar": days,
        "generated_at": _now(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 2. HASHTAG RESEARCH
# ═══════════════════════════════════════════════════════════════════════════════

def hashtag_research(
    niche: str = "",
    platform: str = "instagram",
    count: int = 30,
) -> dict[str, Any]:
    """Find relevant hashtags for a niche."""
    # Curated hashtag database by niche
    niche_hashtags = {
        "fitness": {
            "high_volume": ["#fitness", "#workout", "#gym", "#fit", "#fitnessmotivation", "#health", "#training", "#bodybuilding", "#motivation", "#lifestyle"],
            "medium_volume": ["#fitnessjourney", "#fitfam", "#gains", "#homeworkout", "#fitnessmodel", "#gymlife", "#personaltrainer", "#getfit", "#strong", "#exercise"],
            "low_volume": ["#fitnessgoals", "#fitnessaddict", "#fitnesslife", "#fitnessgear", "#fitnessfood", "#fitnessfun", "#fitnessblog", "#fitnesstips", "#fitnesslove", "#fitnessdaily"],
        },
        "marketing": {
            "high_volume": ["#marketing", "#digitalmarketing", "#socialmedia", "#branding", "#business", "#entrepreneur", "#contentmarketing", "#seo", "#advertising", "#onlinebusiness"],
            "medium_volume": ["#marketingtips", "#socialmediamarketing", "#emailmarketing", "#marketingstrategy", "#growthhacking", "#copywriting", "#affiliatemarketing", "#ppc", "#marketingdigital", "#marketingsocial"],
            "low_volume": ["#marketing101", "#marketingagency", "#marketingonline", "#marketingpro", "#marketinggenius", "#marketingmindset", "#marketinglife", "#marketingtools", "#marketingcontent", "#marketingcoach"],
        },
        "food": {
            "high_volume": ["#food", "#foodie", "#foodporn", "#instafood", "#delicious", "#yummy", "#homemade", "#cooking", "#recipe", "#foodstagram"],
            "medium_volume": ["#foodphotography", "#healthyeating", "#foodblogger", "#easyrecipe", "#mealprep", "#foodlover", "#vegan", "#plantbased", "#glutenfree", "#cleaneating"],
            "low_volume": ["#foodblog", "#foodoftheday", "#foodgasm", "#foodiesofinstagram", "#foodhacks", "#foodstyle", "#foodart", "#foodforthought", "#foodreview", "#foodcom"],
        },
        "tech": {
            "high_volume": ["#technology", "#tech", "#innovation", "#ai", "#coding", "#programming", "#startup", "#software", "#developer", "#digital"],
            "medium_volume": ["#machinelearning", "#python", "#javascript", "#webdevelopment", "#cybersecurity", "#blockchain", "#iot", "#cloudcomputing", "#datascience", "#ux"],
            "low_volume": ["#techstartup", "#techlife", "#techtips", "#techie", "#technews", "#techtalk", "#techcommunity", "#techinnovation", "#techworld", "#techguru"],
        },
        "fashion": {
            "high_volume": ["#fashion", "#style", "#ootd", "#fashionblogger", "#streetstyle", "#fashionista", "#love", "#instagood", "#beautiful", "#photooftheday"],
            "medium_volume": ["#fashionstyle", "#outfitoftheday", "#fashiondiaries", "#lookoftheday", "#fashiondaily", "#outfitinspo", "#styleinspo", "#fashiontrends", "#womensfashion", "#mensfashion"],
            "low_volume": ["#fashionblog", "#fashionlover", "#fashionaddict", "#fashiongram", "#fashionweek", "#fashiondesign", "#fashionphotography", "#fashionstyle", "#fashionootd", "#fashiondaily"],
        },
    }

    # Get hashtags for niche, or generate generic ones
    niche_lower = niche.lower().strip()
    found = False
    for key in niche_hashtags:
        if key in niche_lower or niche_lower in key:
            tags = niche_hashtags[key]
            found = True
            break

    if not found:
        # Generate generic hashtags from niche words
        words = niche_lower.split() if niche_lower else ["business"]
        tags = {
            "high_volume": [f"#{w}" for w in words[:5]],
            "medium_volume": [f"{w}tips" for w in words[:5]],
            "low_volume": [f"{w}community" for w in words[:5]],
        }

    # Platform-specific limits
    limits = {"instagram": 30, "linkedin": 5, "twitter": 3, "tiktok": 5, "facebook": 3}
    max_tags = min(count, limits.get(platform, 30))

    all_tags = []
    for tier in ["high_volume", "medium_volume", "low_volume"]:
        all_tags.extend(tags.get(tier, []))

    selected = all_tags[:max_tags]

    return {
        "niche": niche,
        "platform": platform,
        "total": len(selected),
        "hashtags": selected,
        "by_tier": {
            "high_volume": tags.get("high_volume", [])[:10],
            "medium_volume": tags.get("medium_volume", [])[:10],
            "low_volume": tags.get("low_volume", [])[:10],
        },
        "platform_limit": limits.get(platform, 30),
        "generated_at": _now(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 3. POSTING SCHEDULE
# ═══════════════════════════════════════════════════════════════════════════════

def posting_schedule(
    platform: str = "instagram",
    timezone_offset: int = 5,
    audience: str = "general",
) -> dict[str, Any]:
    """Best times to post on each platform."""
    schedules = {
        "instagram": {
            "best_times": ["6:00 AM", "12:00 PM", "5:00 PM", "7:00 PM"],
            "best_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "avoid": ["Saturday morning", "Sunday late night"],
            "frequency": "1-2 posts/day, 3-5 stories/day",
            "peak_engagement": "11 AM - 1 PM, 7 PM - 9 PM",
        },
        "linkedin": {
            "best_times": ["7:30 AM", "12:00 PM", "5:00 PM"],
            "best_days": ["Tuesday", "Wednesday", "Thursday"],
            "avoid": ["Weekends", "Monday morning", "Friday afternoon"],
            "frequency": "1 post/day, 2-3 articles/week",
            "peak_engagement": "8 AM - 10 AM, 12 PM - 1 PM",
        },
        "twitter": {
            "best_times": ["8:00 AM", "12:00 PM", "5:00 PM", "9:00 PM"],
            "best_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "avoid": ["Saturday", "Sunday"],
            "frequency": "3-5 tweets/day, 1-2 threads/week",
            "peak_engagement": "9 AM - 11 AM, 7 PM - 9 PM",
        },
        "facebook": {
            "best_times": ["9:00 AM", "1:00 PM", "4:00 PM"],
            "best_days": ["Wednesday", "Thursday", "Friday"],
            "avoid": ["Saturday morning"],
            "frequency": "1-2 posts/day",
            "peak_engagement": "1 PM - 4 PM",
        },
        "tiktok": {
            "best_times": ["7:00 AM", "12:00 PM", "7:00 PM", "10:00 PM"],
            "best_days": ["Tuesday", "Thursday", "Friday", "Saturday"],
            "avoid": ["Sunday early morning"],
            "frequency": "1-3 videos/day",
            "peak_engagement": "7 PM - 10 PM",
        },
    }

    schedule = schedules.get(platform, schedules["instagram"])

    return {
        "platform": platform,
        "timezone": f"UTC+{timezone_offset}",
        "audience": audience,
        **schedule,
        "generated_at": _now(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 4. COMPETITOR ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def competitor_analysis(
    competitors: list[str],
    platform: str = "instagram",
    niche: str = "",
) -> dict[str, Any]:
    """Analyze competitor social media presence."""
    results = []
    for comp in competitors[:5]:
        results.append({
            "username": comp,
            "platform": platform,
            "estimated_followers": "N/A (requires API access)",
            "posting_frequency": "Analyze manually or via social listening tools",
            "content_themes": [f"Theme 1 for {comp}", f"Theme 2 for {comp}"],
            "engagement_style": "Check their top posts for engagement patterns",
            "strengths": [f"Strong {niche} content" if niche else "Consistent posting"],
            "gaps": ["Opportunity to differentiate"],
            "note": "Full analysis requires social media API access (Instagram Graph API, etc.)",
        })

    return {
        "platform": platform,
        "niche": niche,
        "competitors_analyzed": len(results),
        "results": results,
        "recommendations": [
            "Analyze top-performing posts for content themes",
            "Identify posting frequency gaps",
            "Study engagement patterns (comments, shares, saves)",
            "Look for content gaps you can fill",
        ],
        "generated_at": _now(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 5. TREND RESEARCH
# ═══════════════════════════════════════════════════════════════════════════════

def trend_research(
    niche: str = "",
    platform: str = "instagram",
) -> dict[str, Any]:
    """Find trending topics and content ideas."""
    # Trending categories
    trends = {
        "evergreen": [
            "How-to tutorials",
            "Behind-the-scenes content",
            "User-generated content",
            "Before/after transformations",
            "Day-in-the-life",
            "Tips and tricks",
            "Myth busting",
            "FAQ answers",
        ],
        "engagement_drivers": [
            "Polls and questions",
            "This or That",
            "Caption contests",
            "Fill in the blank",
            "Hot takes / opinions",
            "Controversial topics (careful)",
            "Community highlights",
        ],
        "viral_formats": [
            "Carousel posts (swipe-through)",
            "Short-form video (Reels/TikTok)",
            "Memes (niche-relevant)",
            "Trending audio + original content",
            "Duet/Stitch with trending content",
            "Infographics",
            "Quotes with branded design",
        ],
    }

    return {
        "niche": niche,
        "platform": platform,
        "trends": trends,
        "content_ideas": [
            f"Share a {niche} tip carousel",
            f"Behind-the-scenes of your {niche} process",
            f"User spotlight / testimonial",
            f"Trending format adapted to {niche}",
            f"Educational Reel about {niche}",
        ],
        "generated_at": _now(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 6. ENGAGEMENT STRATEGY
# ═══════════════════════════════════════════════════════════════════════════════

def engagement_strategy(
    platform: str = "instagram",
    goals: str = "community building",
    audience_size: str = "small",
) -> dict[str, Any]:
    """Plan community management and engagement."""
    strategies = {
        "daily": [
            "Respond to all comments within 1 hour",
            "Like and reply to 10 posts in your niche",
            "Engage with 5 stories from followers",
            "Send 3-5 DMs to new followers (welcome message)",
        ],
        "weekly": [
            "Run a poll or question sticker",
            "Go live once a week",
            "Feature a follower/user-generated content",
            "Collaborate with a micro-influencer",
        ],
        "monthly": [
            "Analyze top-performing content",
            "Adjust content mix based on engagement data",
            "Run a giveaway or contest",
            "Review and update hashtag strategy",
        ],
    }

    return {
        "platform": platform,
        "goals": goals,
        "audience_size": audience_size,
        "strategies": strategies,
        "response_time_target": "< 1 hour for comments, < 24 hours for DMs",
        "engagement_rules": [
            "Always respond to negative feedback professionally",
            "Never delete negative comments (address them)",
            "Use personal tone, not corporate speak",
            "Ask questions in every caption",
        ],
        "generated_at": _now(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 7. PLATFORM STRATEGY
# ═══════════════════════════════════════════════════════════════════════════════

def platform_strategy(
    industry: str = "",
    goals: str = "brand awareness",
    budget: str = "organic_only",
) -> dict[str, Any]:
    """Platform-specific strategy recommendations."""
    platforms = {
        "instagram": {
            "best_for": ["Visual brands", "Lifestyle", "Fashion", "Food", "Travel", "Fitness"],
            "content_types": ["Reels", "Carousels", "Stories", "Lives"],
            "growth_tactics": ["Hashtag strategy", "Reels algorithm", "Collaborations", "Engagement pods"],
            "monetization": ["Brand partnerships", "Affiliate links", "Shopping features"],
            "priority": "high" if industry in ["fashion", "food", "fitness", "travel", "lifestyle"] else "medium",
        },
        "linkedin": {
            "best_for": ["B2B", "Professional services", "SaaS", "Consulting", "Tech"],
            "content_types": ["Text posts", "Articles", "Carousels", "Polls", "Documents"],
            "growth_tactics": ["Thought leadership", "Employee advocacy", "Newsletter", "Events"],
            "monetization": ["Lead generation", "Partnerships", "Speaking opportunities"],
            "priority": "high" if industry in ["b2b", "saas", "consulting", "tech", "professional"] else "medium",
        },
        "twitter": {
            "best_for": ["Tech", "News", "Media", "Personal brands", "Startups"],
            "content_types": ["Threads", "Tweets", "Polls", "Spaces", "Quote tweets"],
            "growth_tactics": ["Thread virality", "Engagement with thought leaders", "Trending topics"],
            "monetization": ["Newsletter", "Speaking", "Consulting"],
            "priority": "high" if industry in ["tech", "news", "media", "startups"] else "low",
        },
        "tiktok": {
            "best_for": ["Gen Z", "Entertainment", "Education", "D2C brands"],
            "content_types": ["Short video", "Trending sounds", "Duets", "Stitches", "Lives"],
            "growth_tactics": ["Trending audio", "Hashtag challenges", "Series content"],
            "monetization": ["Creator fund", "Brand deals", "TikTok Shop"],
            "priority": "high" if industry in ["entertainment", "education", "d2c"] else "medium",
        },
    }

    recommended = []
    for platform, info in platforms.items():
        if info["priority"] == "high":
            recommended.append(platform)

    return {
        "industry": industry,
        "goals": goals,
        "budget": budget,
        "platforms": platforms,
        "recommended_order": recommended or ["instagram", "linkedin"],
        "strategy_notes": [
            "Start with 1-2 platforms, expand later",
            "Cross-post adapted content (not identical)",
            "Each platform needs native content style",
        ],
        "generated_at": _now(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 8. CONTENT GAP ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def content_gap_analysis(
    your_content: list[str],
    competitor_content: list[str],
    niche: str = "",
) -> dict[str, Any]:
    """Find content gaps vs competitors."""
    your_set = set(c.lower().strip() for c in your_content)
    comp_set = set(c.lower().strip() for c in competitor_content)

    gaps = comp_set - your_set
    your_unique = your_set - comp_set

    return {
        "niche": niche,
        "your_content_count": len(your_content),
        "competitor_content_count": len(competitor_content),
        "gaps": list(gaps)[:20],
        "gap_count": len(gaps),
        "your_unique": list(your_unique)[:10],
        "recommendations": [
            f"Create content about: {g}" for g in list(gaps)[:5]
        ],
        "generated_at": _now(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 9. AUDIENCE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def audience_analysis(
    industry: str = "",
    platform: str = "instagram",
    location: str = "India",
) -> dict[str, Any]:
    """Target audience insights."""
    audiences = {
        "fitness": {
            "age_groups": ["18-24", "25-34", "35-44"],
            "gender_split": "60% male, 40% female",
            "interests": ["Gym", "Nutrition", "Supplements", "Running", "Yoga"],
            "pain_points": ["Lack of motivation", "Confusing information", "Time constraints"],
            "content_preferences": ["Quick tips", "Transformation stories", "Workout videos", "Meal prep"],
        },
        "marketing": {
            "age_groups": ["25-34", "35-44", "18-24"],
            "gender_split": "55% male, 45% female",
            "interests": ["Business growth", "AI tools", "Social media", "Analytics"],
            "pain_points": ["Low ROI", "Algorithm changes", "Content creation burnout"],
            "content_preferences": ["Case studies", "Tool reviews", "Strategy breakdowns", "Templates"],
        },
        "tech": {
            "age_groups": ["18-24", "25-34"],
            "gender_split": "65% male, 35% female",
            "interests": ["AI", "Programming", "Startups", "Gadgets", "Open source"],
            "pain_points": ["Keeping up with trends", "Information overload", "Skill gaps"],
            "content_preferences": ["Tutorials", "Product demos", "Industry news", "Code snippets"],
        },
    }

    default = {
        "age_groups": ["18-24", "25-34", "35-44"],
        "gender_split": "Balanced",
        "interests": ["Industry-specific content", "Trends", "Education", "Entertainment"],
        "pain_points": ["Information overload", "Time constraints", "Decision fatigue"],
        "content_preferences": ["Quick tips", "Visual content", "Stories", "How-to guides"],
    }

    industry_lower = industry.lower().strip()
    data = default
    for key in audiences:
        if key in industry_lower or industry_lower in key:
            data = audiences[key]
            break

    return {
        "industry": industry,
        "platform": platform,
        "location": location,
        **data,
        "engagement_tips": [
            "Post when audience is most active",
            "Use language they relate to",
            "Address their pain points directly",
            "Show social proof (testimonials, results)",
        ],
        "generated_at": _now(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 10. GROWTH TACTICS
# ═══════════════════════════════════════════════════════════════════════════════

def growth_tactics(
    current_followers: int = 0,
    platform: str = "instagram",
    niche: str = "",
    budget: str = "organic",
) -> dict[str, Any]:
    """Follower acquisition plan."""
    level = "starter" if current_followers < 1000 else "growing" if current_followers < 10000 else "established"

    tactics = {
        "starter": [
            "Post consistently (1-2x/day)",
            "Use 20-30 relevant hashtags",
            "Engage with 50 accounts in your niche daily",
            "Collaborate with accounts your size",
            "Join engagement pods/communities",
            "Use Reels/TikTok for discoverability",
        ],
        "growing": [
            "Collaborate with micro-influencers (10K-50K)",
            "Run targeted giveaways",
            "Invest in content quality (better photos/videos)",
            "Build an email list from social",
            "Cross-promote on other platforms",
            "Create shareable carousel content",
        ],
        "established": [
            "Partner with macro-influencers",
            "Launch branded hashtag challenge",
            "Invest in paid ads for reach",
            "Create original research/data content",
            "Build community (Discord, Facebook Group)",
            "Monetize: courses, merchandise, consulting",
        ],
    }

    return {
        "current_followers": current_followers,
        "level": level,
        "platform": platform,
        "niche": niche,
        "budget": budget,
        "tactics": tactics.get(level, tactics["starter"]),
        "milestones": {
            "1K": "Instagram: Can add link in bio, more credibility",
            "10K": "Instagram: Swipe-up stories, more brand deals",
            "50K": "Significant brand deal opportunities",
            "100K": "Macro-influencer status, speaking opportunities",
        },
        "generated_at": _now(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

SOCIAL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "content_calendar",
            "description": "Generate a content calendar with post types, topics, and categories for any platform and duration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {"type": "string", "description": "instagram, linkedin, twitter, facebook, tiktok"},
                    "duration": {"type": "string", "description": "1 week, 2 weeks, 1 month, 3 months", "default": "1 week"},
                    "niche": {"type": "string", "description": "Client's niche/industry"},
                    "brand_tone": {"type": "string", "description": "professional, casual, fun, authoritative", "default": "professional"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "hashtag_research",
            "description": "Find relevant hashtags organized by volume tiers (high, medium, low) for any niche and platform.",
            "parameters": {
                "type": "object",
                "properties": {
                    "niche": {"type": "string", "description": "Client's niche"},
                    "platform": {"type": "string", "default": "instagram"},
                    "count": {"type": "integer", "description": "Number of hashtags", "default": 30},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "posting_schedule",
            "description": "Best times and days to post on each platform with frequency recommendations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {"type": "string", "default": "instagram"},
                    "timezone_offset": {"type": "integer", "description": "UTC offset", "default": 5},
                    "audience": {"type": "string", "description": "general, professionals, students", "default": "general"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "competitor_analysis",
            "description": "Analyze competitor social media presence: content themes, engagement, gaps.",
            "parameters": {
                "type": "object",
                "properties": {
                    "competitors": {"type": "array", "items": {"type": "string"}, "description": "Competitor usernames or handles"},
                    "platform": {"type": "string", "default": "instagram"},
                    "niche": {"type": "string"},
                },
                "required": ["competitors"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "trend_research",
            "description": "Find trending topics, content formats, and viral ideas for any niche.",
            "parameters": {
                "type": "object",
                "properties": {
                    "niche": {"type": "string"},
                    "platform": {"type": "string", "default": "instagram"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "engagement_strategy",
            "description": "Plan community management: daily/weekly/monthly engagement tactics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {"type": "string", "default": "instagram"},
                    "goals": {"type": "string", "description": "community building, lead gen, brand awareness", "default": "community building"},
                    "audience_size": {"type": "string", "description": "small, medium, large", "default": "small"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "platform_strategy",
            "description": "Platform-specific strategy: which platforms to prioritize based on industry and goals.",
            "parameters": {
                "type": "object",
                "properties": {
                    "industry": {"type": "string"},
                    "goals": {"type": "string", "default": "brand awareness"},
                    "budget": {"type": "string", "description": "organic_only, small_budget, large_budget", "default": "organic_only"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "content_gap_analysis",
            "description": "Find content gaps: what competitors post that you don't.",
            "parameters": {
                "type": "object",
                "properties": {
                    "your_content": {"type": "array", "items": {"type": "string"}, "description": "Your current content topics"},
                    "competitor_content": {"type": "array", "items": {"type": "string"}, "description": "Competitor content topics"},
                    "niche": {"type": "string"},
                },
                "required": ["your_content", "competitor_content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "audience_analysis",
            "description": "Target audience insights: demographics, interests, pain points, content preferences.",
            "parameters": {
                "type": "object",
                "properties": {
                    "industry": {"type": "string"},
                    "platform": {"type": "string", "default": "instagram"},
                    "location": {"type": "string", "default": "India"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "growth_tactics",
            "description": "Follower acquisition plan based on current size, platform, and budget.",
            "parameters": {
                "type": "object",
                "properties": {
                    "current_followers": {"type": "integer", "default": 0},
                    "platform": {"type": "string", "default": "instagram"},
                    "niche": {"type": "string"},
                    "budget": {"type": "string", "description": "organic, small_budget, large_budget", "default": "organic"},
                },
                "required": [],
            },
        },
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL EXECUTION ROUTER
# ═══════════════════════════════════════════════════════════════════════════════

def execute_social_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Route tool call to actual function."""
    dispatch = {
        "content_calendar": lambda a: content_calendar(a.get("platform", "instagram"), a.get("duration", "1 week"), a.get("niche", ""), a.get("brand_tone", "professional")),
        "hashtag_research": lambda a: hashtag_research(a.get("niche", ""), a.get("platform", "instagram"), a.get("count", 30)),
        "posting_schedule": lambda a: posting_schedule(a.get("platform", "instagram"), a.get("timezone_offset", 5), a.get("audience", "general")),
        "competitor_analysis": lambda a: competitor_analysis(a.get("competitors", []), a.get("platform", "instagram"), a.get("niche", "")),
        "trend_research": lambda a: trend_research(a.get("niche", ""), a.get("platform", "instagram")),
        "engagement_strategy": lambda a: engagement_strategy(a.get("platform", "instagram"), a.get("goals", "community building"), a.get("audience_size", "small")),
        "platform_strategy": lambda a: platform_strategy(a.get("industry", ""), a.get("goals", "brand awareness"), a.get("budget", "organic_only")),
        "content_gap_analysis": lambda a: content_gap_analysis(a.get("your_content", []), a.get("competitor_content", []), a.get("niche", "")),
        "audience_analysis": lambda a: audience_analysis(a.get("industry", ""), a.get("platform", "instagram"), a.get("location", "India")),
        "growth_tactics": lambda a: growth_tactics(a.get("current_followers", 0), a.get("platform", "instagram"), a.get("niche", ""), a.get("budget", "organic")),
    }
    fn = dispatch.get(name)
    if fn:
        try:
            return fn(args)
        except Exception as e:
            logger.exception("Social tool failed: %s", name)
            return {"error": str(e), "status": "failed"}
    return {"error": f"Unknown tool: {name}", "status": "failed"}
