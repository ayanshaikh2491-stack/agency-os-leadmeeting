"""Tests for Structured Brief System + Workspace Integration."""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from admin.workspace.briefs import (
    SocialVisualBrief,
    AdsVisualBrief,
    SEOVisualBrief,
    WebsiteVisualBrief,
    BRIEF_TYPES,
    create_brief,
    brief_to_dict,
    brief_to_content_agent_input,
)
from admin.workspace.manager import _build_knowledge_context


# ── Social Brief Tests ────────────────────────────────────────────────────────


class TestSocialBrief:
    def test_create_social_brief(self):
        brief = SocialVisualBrief(
            day="Monday",
            post_type="listing",
            title="3BHK Luxury Flat in Bandra",
            description="Spacious living room with floor-to-ceiling windows, sea link view, premium marble flooring",
            mood="Premium, aspirational, luxurious",
            text_overlay="Your Dream Home Awaits — ₹2.5 Cr*",
            cta="Book a Site Visit",
            why_this_works="Monday listings get highest saves on Instagram",
            platform="instagram",
            target_audience="25-45 age home buyers, premium segment",
            performance_expectation="High saves and profile visits",
        )
        assert brief.day == "Monday"
        assert brief.post_type == "listing"
        assert brief.mood == "Premium, aspirational, luxurious"
        assert brief.platform == "instagram"
        assert brief.brief_id.startswith("sb_")

    def test_social_brief_to_text(self):
        brief = SocialVisualBrief(
            day="Tuesday",
            post_type="testimonial",
            title="Happy Customer — Sharma Family",
            description="Couple standing in their new living room",
            mood="Warm, emotional, trustworthy",
            text_overlay="We finally found our dream home",
            cta="Start Your Journey",
            why_this_works="Testimonials build trust",
            platform="instagram",
            target_audience="Home buyers",
        )
        text = brief_to_content_agent_input(brief)
        assert "Social Media Visual Brief" in text
        assert "Tuesday" in text
        assert "testimonial" in text
        assert "Happy Customer" in text
        assert "Warm, emotional" in text
        assert "Sharma" in text
        assert "creative intelligence" in text.lower()

    def test_social_brief_all_fields(self):
        brief = SocialVisualBrief(
            day="Friday",
            post_type="event",
            title="Weekend Open House",
            description="Model flat entrance, evening lights",
            mood="Inviting, exclusive",
            text_overlay="Open House This Weekend",
            cta="Register Now",
            hashtags="#OpenHouse #LuxuryLiving",
            why_this_works="Friday event posts get bookings",
            platform="facebook",
            post_time="6 PM IST",
            content_mix_category="engagement",
            target_audience="Local home buyers",
            competitor_reference="DLF uses similar approach",
            performance_expectation="200+ registrations",
        )
        assert brief.hashtags == "#OpenHouse #LuxuryLiving"
        assert brief.post_time == "6 PM IST"
        assert brief.competitor_reference == "DLF uses similar approach"


# ── Ads Brief Tests ───────────────────────────────────────────────────────────


class TestAdsBrief:
    def test_create_ads_brief(self):
        brief = AdsVisualBrief(
            campaign_name="Summer Sale Campaign",
            ad_type="carousel",
            platform="facebook",
            objective="conversions",
            headline="Find Your Dream Home",
            primary_text="Luxury apartments in Bandra starting at ₹2.5 Cr",
            cta="Learn More",
            visual_style="lifestyle",
            mood="Premium, aspirational",
            target_audience="25-45, urban professionals",
        )
        assert brief.campaign_name == "Summer Sale Campaign"
        assert brief.ad_type == "carousel"
        assert brief.objective == "conversions"
        assert brief.brief_id.startswith("ab_")

    def test_ads_brief_to_text(self):
        brief = AdsVisualBrief(
            campaign_name="Brand Awareness",
            ad_type="single_image",
            platform="instagram",
            objective="awareness",
            headline="Premium Living",
            primary_text="Experience luxury in Bandra",
            cta="Sign Up",
            visual_style="product_focused",
            mood="Professional",
            target_audience="Home buyers",
            a_b_test_note="Test product vs lifestyle images",
        )
        text = brief_to_content_agent_input(brief)
        assert "Ad Creative Brief" in text
        assert "Brand Awareness" in text
        assert "single_image" in text
        assert "product_focused" in text
        assert "A/B Test" in text


# ── SEO Brief Tests ───────────────────────────────────────────────────────────


class TestSEOBrief:
    def test_create_seo_brief(self):
        brief = SEOVisualBrief(
            blog_title="Top 10 Reasons to Buy in Bandra in 2025",
            keywords=["bandra flats", "mumbai real estate", "buy property bandra"],
            content_type="featured_image",
            topic_summary="Why Bandra is the best investment in Mumbai",
            mood="Authoritative, informative",
            target_audience="Property investors",
        )
        assert brief.blog_title == "Top 10 Reasons to Buy in Bandra in 2025"
        assert len(brief.keywords) == 3
        assert brief.brief_id.startswith("seob_")

    def test_seo_brief_to_text(self):
        brief = SEOVisualBrief(
            blog_title="Best Schools in Mumbai",
            keywords=["schools mumbai", "education"],
            content_type="blog_image",
            topic_summary="Guide to best schools",
            mood="Educational, friendly",
            target_audience="Parents",
        )
        text = brief_to_content_agent_input(brief)
        assert "SEO Visual Brief" in text
        assert "Best Schools" in text
        assert "schools mumbai" in text


# ── Website Brief Tests ───────────────────────────────────────────────────────


class TestWebsiteBrief:
    def test_create_website_brief(self):
        brief = WebsiteVisualBrief(
            page="home",
            section="hero",
            asset_type="hero_banner",
            purpose="First impression, brand impact",
            mood="Professional, innovative",
            dimensions_needed="1920x1080",
            style_reference="Like Apple's homepage",
            cta_context="Schedule a Visit button below",
        )
        assert brief.page == "home"
        assert brief.section == "hero"
        assert brief.brief_id.startswith("wb_")

    def test_website_brief_to_text(self):
        brief = WebsiteVisualBrief(
            page="about",
            section="team",
            asset_type="team_photo",
            purpose="Trust building",
            mood="Warm, approachable",
        )
        text = brief_to_content_agent_input(brief)
        assert "Website Visual Brief" in text
        assert "about" in text
        assert "team" in text


# ── Brief Registry Tests ──────────────────────────────────────────────────────


class TestBriefRegistry:
    def test_all_agents_have_briefs(self):
        for agent_type in ["social", "ads", "seo", "website"]:
            assert agent_type in BRIEF_TYPES

    def test_create_brief_social(self):
        brief = create_brief("social", day="Monday", post_type="listing", title="Test")
        assert isinstance(brief, SocialVisualBrief)
        assert brief.day == "Monday"

    def test_create_brief_ads(self):
        brief = create_brief("ads", campaign_name="Test Campaign", ad_type="carousel")
        assert isinstance(brief, AdsVisualBrief)

    def test_create_brief_seo(self):
        brief = create_brief("seo", blog_title="Test Blog")
        assert isinstance(brief, SEOVisualBrief)

    def test_create_brief_website(self):
        brief = create_brief("website", page="home", section="hero")
        assert isinstance(brief, WebsiteVisualBrief)

    def test_create_brief_unknown_agent(self):
        with pytest.raises(ValueError, match="No brief type for agent"):
            create_brief("analytics")

    def test_brief_to_dict(self):
        brief = SocialVisualBrief(day="Monday", title="Test")
        d = brief_to_dict(brief)
        assert d["day"] == "Monday"
        assert d["title"] == "Test"
        assert "brief_id" in d


# ── Knowledge Context Builder Tests ───────────────────────────────────────────


class TestKnowledgeContext:
    def test_empty_knowledge(self):
        result = _build_knowledge_context({})
        assert result == ""

    def test_with_patterns(self):
        knowledge = {
            "prompt_patterns": [
                {
                    "visual_type": "social_post",
                    "platform": "instagram",
                    "prompt_template": "Professional real estate photograph",
                    "success_count": 15,
                },
            ],
            "brand_insights": [],
            "platform_tips": [],
        }
        result = _build_knowledge_context(knowledge)
        assert "CROSS-PROJECT KNOWLEDGE" in result
        assert "Professional real estate" in result
        assert "15 times" in result

    def test_with_insights(self):
        knowledge = {
            "prompt_patterns": [],
            "brand_insights": [
                {"type": "color_trend", "insight": "Warm gold tones work for real estate"},
            ],
            "platform_tips": [],
        }
        result = _build_knowledge_context(knowledge)
        assert "Brand/Visual Insights" in result
        assert "Warm gold" in result

    def test_with_tips(self):
        knowledge = {
            "prompt_patterns": [],
            "brand_insights": [],
            "platform_tips": [
                {"total_jobs": 50, "avg_gpu_minutes": 2.5, "common_visual_types": {"image": 40}},
            ],
        }
        result = _build_knowledge_context(knowledge)
        assert "Platform Tips" in result
        assert "50 jobs" in result
        assert "2.5 min" in result

    def test_full_knowledge(self):
        knowledge = {
            "prompt_patterns": [
                {"visual_type": "image", "platform": "instagram", "prompt_template": "Luxury interior", "success_count": 10},
            ],
            "brand_insights": [
                {"type": "style", "insight": "Minimalist works for SaaS"},
            ],
            "platform_tips": [
                {"total_jobs": 20, "avg_gpu_minutes": 3.0, "common_visual_types": {}},
            ],
        }
        result = _build_knowledge_context(knowledge)
        assert "Prompt Patterns" in result
        assert "Brand/Visual Insights" in result
        assert "Platform Tips" in result
        assert "learnings" in result.lower()


# ── Integration: Full Flow ────────────────────────────────────────────────────


class TestFullBriefFlow:
    def test_social_agent_to_content_agent_flow(self):
        """Simulate: Social Agent creates brief → Content Agent receives it."""
        # 1. Social Agent creates structured brief
        brief = SocialVisualBrief(
            day="Monday",
            post_type="listing",
            title="Luxury 3BHK in Bandra West",
            description="Spacious living room with sea link view, premium marble flooring, modular kitchen",
            mood="Premium, aspirational, luxurious",
            text_overlay="Your Dream Home Awaits — ₹2.5 Cr*",
            cta="Book a Site Visit",
            why_this_works="Monday listings get highest saves",
            platform="instagram",
            target_audience="25-45 home buyers, premium segment",
        )

        # 2. Convert to Content Agent input
        content_input = brief_to_content_agent_input(brief)

        # 3. Content Agent receives and enhances
        assert "Luxury 3BHK" in content_input
        assert "Premium, aspirational" in content_input
        assert "instagram" in content_input
        assert "creative intelligence" in content_input.lower()

        # 4. Verify Content Agent can enhance with brand context
        # (Content Agent adds: brand colors, dimensions, AI prompt)

    def test_ads_agent_to_content_agent_flow(self):
        """Simulate: Ads Agent creates brief → Content Agent receives it."""
        brief = AdsVisualBrief(
            campaign_name="Q1 Lead Gen",
            ad_type="carousel",
            platform="facebook",
            objective="leads",
            headline="Find Your Dream Home",
            primary_text="Luxury apartments starting at ₹2.5 Cr",
            cta="Sign Up",
            visual_style="lifestyle",
            mood="Premium",
            target_audience="Home buyers",
        )

        content_input = brief_to_content_agent_input(brief)
        assert "Q1 Lead Gen" in content_input
        assert "carousel" in content_input
        assert "facebook" in content_input

    def test_multiple_briefs_for_content_agent(self):
        """Simulate: Social Agent creates weekly plan with 5 briefs."""
        briefs = [
            SocialVisualBrief(day="Monday", post_type="listing", title="3BHK Bandra", mood="Premium", platform="instagram", description="Interior shot"),
            SocialVisualBrief(day="Tuesday", post_type="testimonial", title="Happy Family", mood="Warm", platform="instagram", description="Family photo"),
            SocialVisualBrief(day="Wednesday", post_type="behind_scenes", title="Construction Update", mood="Professional", platform="instagram", description="Building site"),
            SocialVisualBrief(day="Thursday", post_type="education", title="Why Bandra?", mood="Authoritative", platform="instagram", description="Skyline view"),
            SocialVisualBrief(day="Friday", post_type="event", title="Open House", mood="Inviting", platform="instagram", description="Model flat"),
        ]

        for brief in briefs:
            content_input = brief_to_content_agent_input(brief)
            assert brief.title in content_input
            assert brief.mood in content_input
            assert brief.day in content_input


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
