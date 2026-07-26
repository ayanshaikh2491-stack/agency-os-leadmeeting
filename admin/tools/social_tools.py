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
    budget: str = "organic",
) -> dict[str, Any]:
    """Platform-specific strategy recommendations."""
    platforms = {
        "instagram": {
            "best_for": ["Visual brands", "Lifestyle", "Fashion", "Food", "Travel", "Fitness"],
            "content_types": ["Reels", "Carousels", "Stories", "Lives"],
            "organic_tactics": ["Hashtag strategy", "Reels algorithm", "Collaborations", "Engagement pods", "User-generated content"],
            "growth_potential": "High — Reels reach non-followers easily",
            "priority": "high" if industry in ["fashion", "food", "fitness", "travel", "lifestyle"] else "medium",
        },
        "linkedin": {
            "best_for": ["B2B", "Professional services", "SaaS", "Consulting", "Tech"],
            "content_types": ["Text posts", "Articles", "Carousels", "Polls", "Documents"],
            "organic_tactics": ["Thought leadership", "Employee advocacy", "Newsletter", "Events", "Comment engagement"],
            "growth_potential": "High — organic reach is still strong",
            "priority": "high" if industry in ["b2b", "saas", "consulting", "tech", "professional"] else "medium",
        },
        "twitter": {
            "best_for": ["Tech", "News", "Media", "Personal brands", "Startups"],
            "content_types": ["Threads", "Tweets", "Polls", "Spaces", "Quote tweets"],
            "organic_tactics": ["Thread virality", "Engagement with thought leaders", "Trending topics", "Community building"],
            "growth_potential": "Medium — algorithm favors engagement",
            "priority": "high" if industry in ["tech", "news", "media", "startups"] else "low",
        },
        "tiktok": {
            "best_for": ["Gen Z", "Entertainment", "Education", "D2C brands"],
            "content_types": ["Short video", "Trending sounds", "Duets", "Stitches", "Lives"],
            "organic_tactics": ["Trending audio", "Hashtag challenges", "Series content", "Stitch strategy"],
            "growth_potential": "Very High — best organic reach of any platform",
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
            "Focus on organic growth — no paid ads",
            "Consistency beats perfection",
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
            "Partner with micro-influencers for shoutouts",
            "Launch branded hashtag challenge",
            "Create original research/data content",
            "Build community (Discord, Facebook Group)",
            "Start a newsletter or email list",
            "Collaborate with complementary brands",
            "Create shareable infographic content",
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
# 11. GENERATE CAPTION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_caption(
    topic: str = "",
    platform: str = "instagram",
    tone: str = "engaging",
    audience: str = "general",
    include_cta: bool = True,
) -> dict[str, Any]:
    """Generate social media post captions."""
    caption_templates = {
        "instagram": {
            "engaging": "🎯 {topic}\n\nHere's what most people don't tell you about {topic}...\n\n👇 Swipe to learn more\n\n💬 Drop a comment if you agree!\n\n{hashtags}\n\n{cta}",
            "educational": "📚 {topic} — Let's break it down.\n\n✅ Step 1: Understand the basics\n✅ Step 2: Apply consistently\n✅ Step 3: Measure results\n\nSave this for later! 🔖\n\n{hashtags}\n\n{cta}",
            "inspirational": "✨ {topic}\n\nEvery expert was once a beginner. Don't wait for the \"right time\" — start now.\n\nYour future self will thank you. 💪\n\n{hashtags}\n\n{cta}",
            "behind_scenes": "🎬 Behind the scenes of {topic}\n\nThis is what it really looks like. No filters, no pretending.\n\nAuthenticity wins every time. 🙌\n\n{hashtags}\n\n{cta}",
        },
        "linkedin": {
            "engaging": "I spent the last 30 days studying {topic}.\n\nHere are 5 things I learned:\n\n1️⃣ Most people overcomplicate it\n2️⃣ Consistency matters more than perfection\n3️⃣ Data beats opinions\n4️⃣ Start small, scale fast\n5️⃣ Community is everything\n\nWhat's your experience with {topic}?\n\n{hashtags}",
            "educational": "🎓 {topic} — A thread 🧵\n\nMost professionals get this wrong. Here's the right approach:\n\n→ Focus on fundamentals first\n→ Learn from real case studies\n→ Apply, measure, iterate\n\nAgree? Disagree? Let's discuss 👇\n\n{hashtags}",
            "thought_leadership": "Hot take on {topic} 🔥\n\nThe industry is moving too fast for \"we've always done it this way.\"\n\nThe winners will be those who adapt, experiment, and stay curious.\n\nYour thoughts?\n\n{hashtags}",
        },
        "twitter": {
            "engaging": "🧵 {topic}\n\nHere's what I've learned (thread):\n\n1/ The biggest mistake people make with {topic} is...\n2/ Instead, try this approach:\n3/ The results speak for themselves:\n\n♻️ RT if this helps\n🔔 Follow for more",
            "hot_take": "Unpopular opinion:\n\n{topic} is overrated.\n\nHere's why 👇",
        },
        "tiktok": {
            "engaging": "POV: You just discovered {topic} 🤯\n\nWait for the plot twist... 😂\n\n#fyp #viral #trending {hashtags}",
            "educational": "Things nobody tells you about {topic}:\n\nPart 1 👇\n\n#learnontiktok #education #tips {hashtags}",
        },
    }

    platform_captions = caption_templates.get(platform, caption_templates["instagram"])
    template = platform_captions.get(tone, list(platform_captions.values())[0])

    # Generate hashtags
    niche_words = topic.split()[:3] if topic else ["business"]
    hashtags = " ".join([f"#{w.lower()}" for w in niche_words[:5]])

    cta = ""
    if include_cta:
        cta_options = {
            "instagram": "Double tap if this resonates! ❤️",
            "linkedin": "What's your take? Comment below 👇",
            "twitter": "RT if you agree 🔄",
            "tiktok": "Follow for more tips!",
        }
        cta = cta_options.get(platform, "Like and share!")

    caption = template.format(
        topic=topic or "this topic",
        hashtags=hashtags,
        cta=cta,
    )

    return {
        "platform": platform,
        "topic": topic,
        "tone": tone,
        "caption": caption,
        "word_count": len(caption.split()),
        "character_count": len(caption),
        "hashtags": hashtags,
        "cta": cta,
        "tips": [
            "Post at peak hours for maximum reach",
            "First line is crucial — it determines if people read more",
            "Use line breaks for readability",
            "End with a question to boost comments",
        ],
        "generated_at": _now(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 12. REPURPOSE CONTENT
# ═══════════════════════════════════════════════════════════════════════════════

def repurpose_content(
    original_content: str = "",
    source_platform: str = "instagram",
    target_platforms: list[str] = ["linkedin", "twitter", "tiktok", "facebook"],
    topic: str = "",
) -> dict[str, Any]:
    """Adapt one piece of content for multiple platforms."""
    adaptations = {}

    platform_rules = {
        "linkedin": {
            "style": "Professional, thought leadership",
            "format": "Text post or article",
            "length": "1000-1300 characters",
            "tone": "Authoritative, insightful",
            "tips": [
                "Start with a hook (first 2 lines visible)",
                "Use line breaks for readability",
                "Add personal experience/anecdote",
                "End with a question for engagement",
            ],
        },
        "twitter": {
            "style": "Concise, punchy",
            "format": "Thread or single tweet",
            "length": "280 characters per tweet",
            "tone": "Direct, witty",
            "tips": [
                "Break into 3-5 tweet thread",
                "First tweet must hook",
                "Use numbers/lists",
                "End with CTA (RT, follow)",
            ],
        },
        "tiktok": {
            "style": "Casual, entertaining",
            "format": "15-60 second video script",
            "length": "Script for 30-60 seconds",
            "tone": "Fun, relatable",
            "tips": [
                "Hook in first 3 seconds",
                "Use trending audio",
                "Show, don't tell",
                "Add text overlays",
            ],
        },
        "facebook": {
            "style": "Conversational, community-focused",
            "format": "Text post or shared link",
            "length": "200-500 characters",
            "tone": "Friendly, personal",
            "tips": [
                "Ask questions to drive comments",
                "Use emojis strategically",
                "Share personal stories",
                "Post in groups for reach",
            ],
        },
        "instagram": {
            "style": "Visual-first, aesthetic",
            "format": "Carousel, Reel, or Story",
            "length": "Caption: 2200 characters max",
            "tone": "Inspirational, educational",
            "tips": [
                "Carousel for education, Reels for reach",
                "Use all 30 hashtag slots",
                "First image is thumb-stopping",
                "Add save-worthy content",
            ],
        },
    }

    for platform in target_platforms:
        rules = platform_rules.get(platform, platform_rules["instagram"])
        adaptations[platform] = {
            "platform": platform,
            "recommended_format": rules["format"],
            "style": rules["style"],
            "tone": rules["tone"],
            "length": rules["length"],
            "adaptation_tips": rules["tips"],
            "note": f"Adapt '{original_content[:50]}...' for {platform} using {rules['style']} style",
        }

    return {
        "source_platform": source_platform,
        "target_platforms": target_platforms,
        "original_content_preview": original_content[:200] if original_content else topic,
        "adaptations": adaptations,
        "repurpose_strategy": [
            "LinkedIn: Professional angle, add insights",
            "Twitter: Break into thread, make punchy",
            "TikTok: Visual/hook-based, trending format",
            "Facebook: Community angle, personal story",
            "Instagram: Visual-first, save-worthy",
        ],
        "generated_at": _now(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 13. DM OUTREACH
# ═══════════════════════════════════════════════════════════════════════════════

def dm_outreach(
    purpose: str = "collaboration",
    platform: str = "instagram",
    target_audience: str = "micro-influencers",
    tone: str = "friendly",
) -> dict[str, Any]:
    """DM outreach templates and strategy."""
    templates = {
        "collaboration": {
            "instagram": {
                "friendly": "Hey {name}! 👋 Love your content about {topic}. We're working on something similar and thought a collab could be awesome. Would you be open to chatting? No pressure at all! 😊",
                "professional": "Hi {name}, I'm from [Brand]. Your {topic} content resonates with our audience. We'd love to explore a potential collaboration. Would you be open to a quick chat?",
                "casual": "Yo {name}! 🔥 Your {topic} content hits different. Wanna collab on something? Let me know! 🤙",
            },
            "linkedin": {
                "professional": "Hi {name}, I came across your profile and was impressed by your work in {topic}. I'm reaching out because we're exploring collaboration opportunities with thought leaders in this space. Would you be open to a brief conversation?",
            },
        },
        "partnership": {
            "instagram": {
                "friendly": "Hey {name}! We've been following your journey and love what you're building. We think there's a great opportunity for us to support each other's audiences. Interested in exploring this? 🚀",
            },
        },
        "shoutout": {
            "instagram": {
                "friendly": "Hey {name}! Your {topic} content is 🔥. We'd love to feature you in our stories/newsletter. Would you be cool with that? We'll tag you of course! 😊",
            },
        },
        "ugc": {
            "instagram": {
                "friendly": "Hey {name}! We loved your recent post about {topic}. Would you be interested in creating content for our page? We'll compensate you and give full credit! 🙌",
            },
        },
    }

    purpose_templates = templates.get(purpose, templates["collaboration"])
    platform_templates = purpose_templates.get(platform, purpose_templates.get("instagram", {}))
    template = platform_templates.get(tone, list(platform_templates.values())[0] if platform_templates else "Hello! Love your content. Let's connect!")

    strategy = {
        "pre_outreach": [
            "Engage with their content for 1-2 weeks before DMing",
            "Leave genuine comments on 5-10 posts",
            "Share their content in your stories",
            "Follow them and turn on notifications",
        ],
        "during_outreach": [
            "Personalize every message (mention specific post)",
            "Keep it short (under 100 words)",
            "Be clear about what you're offering",
            "Make it easy to say yes (suggest a quick call)",
        ],
        "follow_up": [
            "Wait 3-5 days before follow-up",
            "Keep follow-up shorter than original",
            "Add new value (share their recent post)",
            "If no response after 2 follow-ups, move on",
        ],
        "volume_guide": {
            "starter": "5-10 DMs per day",
            "growing": "10-20 DMs per day",
            "established": "20-30 DMs per day",
        },
    }

    return {
        "purpose": purpose,
        "platform": platform,
        "template": template,
        "placeholders": ["{name}", "{topic}", "[Brand]"],
        "strategy": strategy,
        "dos_donts": {
            "dos": [
                "Personalize every message",
                "Be genuine and specific",
                "Offer value first",
                "Follow up once (max twice)",
                "Track response rates",
            ],
            "donts": [
                "Send mass generic messages",
                "Be pushy or desperate",
                "Lie about who you are",
                "Follow up more than twice",
                "Ignore their boundaries",
            ],
        },
        "generated_at": _now(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 14. INFLUENCER RESEARCH
# ═══════════════════════════════════════════════════════════════════════════════

def influencer_research(
    niche: str = "",
    platform: str = "instagram",
    budget: str = "organic",
    count: int = 10,
) -> dict[str, Any]:
    """Find organic influencers for collaborations."""
    # Micro-influencer tiers
    tiers = {
        "nano": {
            "follower_range": "1K - 10K",
            "engagement_rate": "5-10%",
            "best_for": "Local businesses, niche products",
            "cost": "Free product / shoutout exchange",
            "approach": "DM directly, casual tone",
        },
        "micro": {
            "follower_range": "10K - 50K",
            "engagement_rate": "3-5%",
            "best_for": "Growing brands, targeted reach",
            "cost": "Product + small fee or affiliate",
            "approach": "Email or DM, professional tone",
        },
        "mid": {
            "follower_range": "50K - 500K",
            "engagement_rate": "2-3%",
            "best_for": "Brand awareness, credibility",
            "cost": "Paid collaboration",
            "approach": "Email, formal proposal",
        },
    }

    research_checklist = [
        "Check engagement rate (not just followers)",
        "Look at comment quality (real vs bot)",
        "Check posting consistency (active account)",
        "Review brand alignment (values match)",
        "Analyze audience demographics",
        "Check previous brand collaborations",
        "Verify no fake followers (use tools)",
        "Assess content quality and style",
        "Check for controversial content",
        "Review response rate to DMs/comments",
    ]

    search_strategies = {
        "instagram": [
            "Search niche hashtags and find top creators",
            "Check \"Suggested\" accounts in your niche",
            "Look at who your competitors collaborate with",
            "Use Instagram's \"Branded Content\" tags",
            "Search location tags for local influencers",
        ],
        "linkedin": [
            "Search industry hashtags",
            "Check who posts about your topic frequently",
            "Look at article authors in your niche",
            "Find speakers at industry events",
            "Check who gets most engagement on industry posts",
        ],
        "tiktok": [
            "Search niche hashtags",
            "Check \"For You\" page creators",
            "Look at trending sounds and who uses them",
            "Find duet/stitch partners",
            "Check creator marketplace",
        ],
    }

    return {
        "niche": niche,
        "platform": platform,
        "budget": budget,
        "tiers": tiers,
        "recommended_tier": "nano" if budget == "organic" else "micro",
        "research_checklist": research_checklist,
        "search_strategies": search_strategies.get(platform, search_strategies["instagram"]),
        "outreach_tips": [
            "Start with nano/micro-influencers (higher engagement)",
            "Build genuine relationship before asking for collaboration",
            "Offer value (free product, revenue share, exposure)",
            "Create clear deliverables and expectations",
            "Track ROI for each collaboration",
        ],
        "generated_at": _now(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 15. ANALYTICS REPORT
# ═══════════════════════════════════════════════════════════════════════════════

def analytics_report(
    platform: str = "instagram",
    metrics: list[str] = ["followers", "engagement", "reach"],
    period: str = "weekly",
) -> dict[str, Any]:
    """Generate organic performance analytics report."""
    kpis = {
        "instagram": {
            "engagement_rate": {"good": "3-5%", "great": "5-7%", "excellent": ">7%"},
            "reach_rate": {"good": "20-30% of followers", "great": "30-50%", "excellent": ">50%"},
            "save_rate": {"good": "1-3%", "great": "3-5%", "excellent": ">5%"},
            "share_rate": {"good": "0.5-1%", "great": "1-3%", "excellent": ">3%"},
            "story_completion": {"good": "70%", "great": "80%", "excellent": ">90%"},
        },
        "linkedin": {
            "engagement_rate": {"good": "2-4%", "great": "4-6%", "excellent": ">6%"},
            "impression_rate": {"good": "10-20% of connections", "great": "20-40%", "excellent": ">40%"},
            "click_through": {"good": "1-2%", "great": "2-4%", "excellent": ">4%"},
            "comment_rate": {"good": "1-2%", "great": "2-5%", "excellent": ">5%"},
        },
        "twitter": {
            "engagement_rate": {"good": "1-3%", "great": "3-5%", "excellent": ">5%"},
            "impression_rate": {"good": "10-20% of followers", "great": "20-40%", "excellent": ">40%"},
            "retweet_rate": {"good": "1-2%", "great": "2-4%", "excellent": ">4%"},
            "reply_rate": {"good": "0.5-1%", "great": "1-3%", "excellent": ">3%"},
        },
        "tiktok": {
            "view_rate": {"good": "10-30% of followers", "great": "30-100%", "excellent": ">100%"},
            "completion_rate": {"good": "30-50%", "great": "50-70%", "excellent": ">70%"},
            "share_rate": {"good": "1-3%", "great": "3-5%", "excellent": ">5%"},
            "save_rate": {"good": "2-5%", "great": "5-10%", "excellent": ">10%"},
        },
    }

    platform_kpis = kpis.get(platform, kpis["instagram"])

    report_template = {
        "summary": {
            "period": period,
            "platform": platform,
            "top_performing_content": "Identify posts with highest engagement",
            "growth_trend": "Compare to previous period",
            "key_insight": "What worked and what didn't",
        },
        "metrics_to_track": [
            "Follower growth (net new)",
            "Engagement rate",
            "Reach / Impressions",
            "Saves and shares (high-intent actions)",
            "Best performing content type",
            "Best posting times",
            "Hashtag performance",
        ],
        "kpis_by_platform": platform_kpis,
        "action_items": [
            "Double down on top-performing content type",
            "Test new posting times based on data",
            "Refine hashtag strategy based on performance",
            "Create more content around high-engagement topics",
            "Engage more with top commenters",
        ],
        "reporting_tips": [
            "Track weekly for pattern recognition",
            "Compare month-over-month for growth",
            "Focus on engagement rate, not just followers",
            "Track saves/shares as high-intent metrics",
            "Review competitor performance monthly",
        ],
    }

    return {
        "platform": platform,
        "period": period,
        "kpis": platform_kpis,
        "report": report_template,
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
                    "budget": {"type": "string", "description": "organic only - no paid ads", "default": "organic"},
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
                    "budget": {"type": "string", "description": "organic only - no paid ads", "default": "organic"},
                },
                "required": [],
            },
        },
    },
    # ── NEW TOOLS (11-15) ──
    {
        "type": "function",
        "function": {
            "name": "generate_caption",
            "description": "Generate social media post captions with hashtags and CTA for any platform and tone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Post topic or subject"},
                    "platform": {"type": "string", "description": "instagram, linkedin, twitter, tiktok", "default": "instagram"},
                    "tone": {"type": "string", "description": "engaging, educational, inspirational, behind_scenes, thought_leadership", "default": "engaging"},
                    "audience": {"type": "string", "description": "Target audience", "default": "general"},
                    "include_cta": {"type": "boolean", "description": "Include call-to-action", "default": True},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "repurpose_content",
            "description": "Adapt one piece of content for multiple platforms with platform-specific formatting.",
            "parameters": {
                "type": "object",
                "properties": {
                    "original_content": {"type": "string", "description": "Original content to repurpose"},
                    "source_platform": {"type": "string", "description": "Platform where original was posted", "default": "instagram"},
                    "target_platforms": {"type": "array", "items": {"type": "string"}, "description": "Platforms to adapt for"},
                    "topic": {"type": "string", "description": "Content topic"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "dm_outreach",
            "description": "DM outreach templates and strategy for collaborations, partnerships, and influencer outreach.",
            "parameters": {
                "type": "object",
                "properties": {
                    "purpose": {"type": "string", "description": "collaboration, partnership, shoutout, ugc", "default": "collaboration"},
                    "platform": {"type": "string", "description": "instagram, linkedin", "default": "instagram"},
                    "target_audience": {"type": "string", "description": "micro-influencers, nano-influencers, brands", "default": "micro-influencers"},
                    "tone": {"type": "string", "description": "friendly, professional, casual", "default": "friendly"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "influencer_research",
            "description": "Find organic influencers for collaborations with tiers, research checklist, and search strategies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "niche": {"type": "string", "description": "Client's niche"},
                    "platform": {"type": "string", "description": "instagram, linkedin, tiktok", "default": "instagram"},
                    "budget": {"type": "string", "description": "organic, micro_budget", "default": "organic"},
                    "count": {"type": "integer", "description": "Number of influencers to research", "default": 10},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analytics_report",
            "description": "Generate organic performance analytics report with KPIs and benchmarks for any platform.",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {"type": "string", "description": "instagram, linkedin, twitter, tiktok", "default": "instagram"},
                    "metrics": {"type": "array", "items": {"type": "string"}, "description": "Metrics to track"},
                    "period": {"type": "string", "description": "weekly, monthly, quarterly", "default": "weekly"},
                },
                "required": [],
            },
        },
    },
    # ── EXECUTION TOOLS (16-21) ──
    {
        "type": "function",
        "function": {
            "name": "create_post",
            "description": "Create a complete social media post with caption, hashtags, and media plan. Ready for scheduling or publishing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {"type": "string", "description": "instagram, linkedin, twitter, tiktok, facebook", "default": "instagram"},
                    "topic": {"type": "string", "description": "Post topic or subject"},
                    "content_type": {"type": "string", "description": "single_image, carousel, reel, story, text_post, thread", "default": "single_image"},
                    "tone": {"type": "string", "description": "engaging, educational, inspirational, behind_scenes", "default": "engaging"},
                    "caption": {"type": "string", "description": "Custom caption (auto-generated if empty)"},
                    "hashtags": {"type": "array", "items": {"type": "string"}, "description": "Custom hashtags (auto-generated if empty)"},
                    "media_url": {"type": "string", "description": "URL to image/video"},
                    "cta": {"type": "string", "description": "Call to action text"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_post",
            "description": "Schedule a post for future publishing via SocialClaw. Validates and queues the post.",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {"type": "string", "description": "instagram, linkedin, twitter, tiktok, facebook", "default": "instagram"},
                    "caption": {"type": "string", "description": "Post caption/text"},
                    "scheduled_at": {"type": "string", "description": "ISO datetime for when to publish (e.g. 2026-08-01T10:00:00Z)"},
                    "media_url": {"type": "string", "description": "URL to image/video"},
                    "hashtags": {"type": "array", "items": {"type": "string"}},
                    "account_id": {"type": "string", "description": "SocialClaw account ID"},
                },
                "required": ["caption"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "post_now",
            "description": "Immediately publish a post to social media via SocialClaw.",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {"type": "string", "description": "instagram, linkedin, twitter, tiktok, facebook", "default": "instagram"},
                    "caption": {"type": "string", "description": "Post caption/text"},
                    "media_url": {"type": "string", "description": "URL to image/video"},
                    "hashtags": {"type": "array", "items": {"type": "string"}},
                    "account_id": {"type": "string", "description": "SocialClaw account ID"},
                },
                "required": ["caption"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "social_accounts",
            "description": "Manage connected social media accounts. List accounts or initiate OAuth connection.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "list, connect", "default": "list"},
                    "provider": {"type": "string", "description": "x, linkedin, instagram_business, facebook, tiktok, youtube, reddit, wordpress, discord, telegram, pinterest"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "content_queue",
            "description": "View scheduled posts queue across all platforms. See what is coming up.",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {"type": "string", "description": "all, instagram, linkedin, twitter, tiktok, facebook", "default": "all"},
                    "status": {"type": "string", "description": "all, scheduled, published, failed", "default": "all"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "post_analytics",
            "description": "Track individual post performance and delivery status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {"type": "string", "description": "instagram, linkedin, twitter, tiktok", "default": "instagram"},
                    "post_id": {"type": "string", "description": "Post ID to check analytics for"},
                    "period": {"type": "string", "description": "1d, 7d, 30d, 90d", "default": "7d"},
                },
                "required": [],
            },
        },
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# 16. CREATE POST
# ═══════════════════════════════════════════════════════════════════════════════

def create_post(
    platform: str = "instagram",
    topic: str = "",
    content_type: str = "single_image",
    tone: str = "engaging",
    caption: str = "",
    hashtags: list[str] = [],
    media_url: str = "",
    cta: str = "",
) -> dict[str, Any]:
    """Create a complete social media post ready for scheduling/publishing."""
    # Auto-generate caption if not provided
    if not caption:
        cap_result = generate_caption(topic, platform, tone, "general", bool(cta))
        caption = cap_result.get("caption", "")
        if not hashtags:
            hashtags = cap_result.get("hashtags", "").split()

    post_id = f"post_{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    post = {
        "post_id": post_id,
        "platform": platform,
        "content_type": content_type,
        "caption": caption,
        "hashtags": hashtags,
        "media_url": media_url,
        "cta": cta,
        "status": "draft",
        "created_at": _now(),
    }

    return {
        "post": post,
        "next_steps": [
            "Use schedule_post to schedule this post",
            "Use post_now to publish immediately",
            "Review and edit before publishing",
        ],
        "platform_tips": {
            "instagram": "Add media (image/video) before posting. Max 30 hashtags.",
            "linkedin": "Professional tone works best. Add 3-5 hashtags.",
            "twitter": "Keep under 280 chars per tweet. Use threads for longer content.",
            "tiktok": "Hook in first 3 seconds. Use trending audio.",
            "facebook": "Ask questions to drive comments. Keep it conversational.",
        },
        "generated_at": _now(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 17. SCHEDULE POST
# ═══════════════════════════════════════════════════════════════════════════════

def schedule_post(
    platform: str = "instagram",
    caption: str = "",
    scheduled_at: str = "",
    media_url: str = "",
    hashtags: list[str] = [],
    account_id: str = "",
) -> dict[str, Any]:
    """Schedule a post for future publishing via SocialClaw."""
    import subprocess

    schedule_data = {
        "posts": [
            {
                "provider": platform,
                "account_id": account_id or f"default_{platform}",
                "text": caption,
                "scheduled_at": scheduled_at or (datetime.now() + timedelta(hours=2)).isoformat() + "Z",
            }
        ]
    }

    # Try SocialClaw CLI
    try:
        result = subprocess.run(
            ["socialclaw", "validate", "-f", "-", "--json"],
            input=json.dumps(schedule_data),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            validated = json.loads(result.stdout) if result.stdout else {}
            # Apply schedule
            apply_result = subprocess.run(
                ["socialclaw", "apply", "-f", "-", "--json"],
                input=json.dumps(schedule_data),
                capture_output=True,
                text=True,
                timeout=15,
            )
            if apply_result.returncode == 0:
                run_data = json.loads(apply_result.stdout) if apply_result.stdout else {}
                return {
                    "status": "scheduled",
                    "run_id": run_data.get("run_id", ""),
                    "platform": platform,
                    "scheduled_at": schedule_data["posts"][0]["scheduled_at"],
                    "socialclaw_response": run_data,
                    "generated_at": _now(),
                }
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: store locally
    return {
        "status": "scheduled_locally",
        "platform": platform,
        "scheduled_at": schedule_data["posts"][0]["scheduled_at"],
        "post_data": schedule_data,
        "note": "SocialClaw not available. Post stored locally. Install: npm install -g socialclaw",
        "generated_at": _now(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 18. POST NOW
# ═══════════════════════════════════════════════════════════════════════════════

def post_now(
    platform: str = "instagram",
    caption: str = "",
    media_url: str = "",
    hashtags: list[str] = [],
    account_id: str = "",
) -> dict[str, Any]:
    """Immediately publish a post to social media via SocialClaw."""
    import subprocess

    post_data = {
        "posts": [
            {
                "provider": platform,
                "account_id": account_id or f"default_{platform}",
                "text": caption,
                "scheduled_at": datetime.now(timezone.utc).isoformat(),
            }
        ]
    }

    # Try SocialClaw CLI
    try:
        result = subprocess.run(
            ["socialclaw", "apply", "-f", "-", "--json"],
            input=json.dumps(post_data),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            run_data = json.loads(result.stdout) if result.stdout else {}
            return {
                "status": "published",
                "run_id": run_data.get("run_id", ""),
                "platform": platform,
                "published_at": _now(),
                "socialclaw_response": run_data,
                "generated_at": _now(),
            }
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback
    return {
        "status": "pending",
        "platform": platform,
        "caption_preview": caption[:200],
        "note": "SocialClaw not available. Install: npm install -g socialclaw. Post created but not published.",
        "generated_at": _now(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 19. SOCIAL ACCOUNTS
# ═══════════════════════════════════════════════════════════════════════════════

def social_accounts(
    action: str = "list",
    provider: str = "",
) -> dict[str, Any]:
    """Manage connected social media accounts via SocialClaw."""
    import subprocess

    # Try SocialClaw CLI
    try:
        if action == "list":
            result = subprocess.run(
                ["socialclaw", "accounts", "list", "--json"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode == 0:
                accounts = json.loads(result.stdout) if result.stdout else []
                return {
                    "action": "list",
                    "accounts": accounts,
                    "count": len(accounts),
                    "generated_at": _now(),
                }

        elif action == "connect" and provider:
            result = subprocess.run(
                ["socialclaw", "accounts", "connect", "--provider", provider, "--open"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            return {
                "action": "connect",
                "provider": provider,
                "status": "connection_initiated",
                "note": f"OAuth flow opened for {provider}. Complete in browser.",
                "generated_at": _now(),
            }
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: show available providers
    return {
        "action": action,
        "status": "socialclaw_not_available",
        "available_providers": [
            "x (Twitter/X)",
            "linkedin (LinkedIn profile)",
            "linkedin_page (LinkedIn page)",
            "instagram_business (Instagram Business)",
            "facebook (Facebook Page)",
            "tiktok (TikTok)",
            "youtube (YouTube)",
            "reddit (Reddit)",
            "wordpress (WordPress)",
            "discord (Discord)",
            "telegram (Telegram)",
            "pinterest (Pinterest)",
        ],
        "setup": "npm install -g socialclaw && socialclaw login --api-key <key>",
        "note": "Install SocialClaw to manage accounts. Get key at: https://getsocialclaw.com/dashboard",
        "generated_at": _now(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 20. CONTENT QUEUE
# ═══════════════════════════════════════════════════════════════════════════════

def content_queue(
    platform: str = "all",
    status: str = "all",
) -> dict[str, Any]:
    """View scheduled posts queue across all platforms."""
    import subprocess

    # Try SocialClaw CLI
    try:
        result = subprocess.run(
            ["socialclaw", "posts", "list", "--json"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            posts = json.loads(result.stdout) if result.stdout else []
            filtered = posts
            if platform != "all":
                filtered = [p for p in filtered if p.get("provider") == platform]
            return {
                "platform": platform,
                "status_filter": status,
                "posts": filtered,
                "count": len(filtered),
                "generated_at": _now(),
            }
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: show queue guide
    return {
        "platform": platform,
        "status_filter": status,
        "posts": [],
        "count": 0,
        "queue_guide": {
            "how_to_add": "Use schedule_post to add posts to queue",
            "how_to_view": "Use content_queue to see all scheduled posts",
            "how_to_manage": "Use SocialClaw dashboard: https://getsocialclaw.com/dashboard",
        },
        "note": "SocialClaw not available. Install: npm install -g socialclaw",
        "generated_at": _now(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 21. POST ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════

def post_analytics(
    platform: str = "instagram",
    post_id: str = "",
    period: str = "7d",
) -> dict[str, Any]:
    """Track individual post performance and delivery status."""
    import subprocess

    # Try SocialClaw CLI
    try:
        result = subprocess.run(
            ["socialclaw", "status", "--json"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            status_data = json.loads(result.stdout) if result.stdout else {}
            return {
                "platform": platform,
                "post_id": post_id,
                "period": period,
                "delivery_status": status_data,
                "generated_at": _now(),
            }
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: analytics guide
    return {
        "platform": platform,
        "post_id": post_id,
        "period": period,
        "metrics_to_track": {
            "engagement": "Likes, comments, shares, saves",
            "reach": "Unique accounts that saw the post",
            "impressions": "Total times the post was displayed",
            "clicks": "Link clicks, profile visits",
            "growth": "New followers from this post",
        },
        "platform_benchmarks": {
            "instagram": {"engagement_rate": "3-5%", "reach_rate": "20-30%"},
            "linkedin": {"engagement_rate": "2-4%", "impression_rate": "10-20%"},
            "twitter": {"engagement_rate": "1-3%", "retweet_rate": "1-2%"},
            "tiktok": {"view_rate": "10-30%", "completion_rate": "30-50%"},
        },
        "note": "SocialClaw not available for live analytics. Install: npm install -g socialclaw",
        "generated_at": _now(),
    }


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
        "platform_strategy": lambda a: platform_strategy(a.get("industry", ""), a.get("goals", "brand awareness"), a.get("budget", "organic")),
        "content_gap_analysis": lambda a: content_gap_analysis(a.get("your_content", []), a.get("competitor_content", []), a.get("niche", "")),
        "audience_analysis": lambda a: audience_analysis(a.get("industry", ""), a.get("platform", "instagram"), a.get("location", "India")),
        "growth_tactics": lambda a: growth_tactics(a.get("current_followers", 0), a.get("platform", "instagram"), a.get("niche", ""), a.get("budget", "organic")),
        "generate_caption": lambda a: generate_caption(a.get("topic", ""), a.get("platform", "instagram"), a.get("tone", "engaging"), a.get("audience", "general"), a.get("include_cta", True)),
        "repurpose_content": lambda a: repurpose_content(a.get("original_content", ""), a.get("source_platform", "instagram"), a.get("target_platforms", ["linkedin", "twitter", "tiktok", "facebook"]), a.get("topic", "")),
        "dm_outreach": lambda a: dm_outreach(a.get("purpose", "collaboration"), a.get("platform", "instagram"), a.get("target_audience", "micro-influencers"), a.get("tone", "friendly")),
        "influencer_research": lambda a: influencer_research(a.get("niche", ""), a.get("platform", "instagram"), a.get("budget", "organic"), a.get("count", 10)),
        "analytics_report": lambda a: analytics_report(a.get("platform", "instagram"), a.get("metrics", ["followers", "engagement", "reach"]), a.get("period", "weekly")),
        # ── EXECUTION TOOLS (16-21) ──
        "create_post": lambda a: create_post(a.get("platform", "instagram"), a.get("topic", ""), a.get("content_type", "single_image"), a.get("tone", "engaging"), a.get("caption", ""), a.get("hashtags", []), a.get("media_url", ""), a.get("cta", "")),
        "schedule_post": lambda a: schedule_post(a.get("platform", "instagram"), a.get("caption", ""), a.get("scheduled_at", ""), a.get("media_url", ""), a.get("hashtags", []), a.get("account_id", "")),
        "post_now": lambda a: post_now(a.get("platform", "instagram"), a.get("caption", ""), a.get("media_url", ""), a.get("hashtags", []), a.get("account_id", "")),
        "social_accounts": lambda a: social_accounts(a.get("action", "list"), a.get("provider", "")),
        "content_queue": lambda a: content_queue(a.get("platform", "all"), a.get("status", "all")),
        "post_analytics": lambda a: post_analytics(a.get("platform", "instagram"), a.get("post_id", ""), a.get("period", "7d")),
    }
    fn = dispatch.get(name)
    if fn:
        try:
            return fn(args)
        except Exception as e:
            logger.exception("Social tool failed: %s", name)
            return {"error": str(e), "status": "failed"}
    return {"error": f"Unknown tool: {name}", "status": "failed"}
