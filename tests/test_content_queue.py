"""Tests for Content Job Queue — on-demand GPU management."""
import pytest
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from admin.tools.content_queue import (
    ContentBrief,
    ContentJobQueue,
    JobStatus,
    enhance_brief,
    get_queue,
    PLATFORM_SIZES,
    STYLE_MAP,
)


# ── ContentBrief Tests ────────────────────────────────────────────────────────


class TestContentBrief:
    def test_create_brief(self):
        brief = ContentBrief(
            workspace_id="ws_1",
            from_agent="social",
            content_type="social_post",
            platform="instagram",
            style="bold",
            quantity=5,
            topic="Summer Sale",
            description="5 Instagram posts for summer sale campaign",
            text_overlay="SUMMER SALE - 50% OFF",
            cta="Shop Now",
        )
        assert brief.workspace_id == "ws_1"
        assert brief.from_agent == "social"
        assert brief.quantity == 5
        assert brief.priority == "normal"
        assert brief.status == "pending"
        assert brief.retry_count == 0
        assert brief.max_retries == 2
        assert brief.output_files == []

    def test_brief_defaults(self):
        brief = ContentBrief()
        assert brief.platform == "instagram"
        assert brief.style == "professional"
        assert brief.quantity == 1
        assert brief.width == 1080
        assert brief.height == 1080
        assert brief.steps == 20
        assert brief.frames == 49

    def test_brief_from_different_agents(self):
        for agent in ["social", "ads", "website", "seo"]:
            brief = ContentBrief(from_agent=agent)
            assert brief.from_agent == agent


# ── JobQueue Tests ────────────────────────────────────────────────────────────


class TestContentJobQueue:
    def setup_method(self):
        self.queue = ContentJobQueue("ws_test")

    def test_submit_job(self):
        brief = ContentBrief(
            from_agent="social",
            content_type="image",
            platform="instagram",
            topic="Test post",
        )
        job_id = self.queue.submit(brief)
        assert job_id.startswith("job_")
        assert len(self.queue.jobs) == 1
        assert self.queue._queue == [job_id]

    def test_get_next_job(self):
        brief = ContentBrief(from_agent="social", content_type="image", topic="A")
        job_id = self.queue.submit(brief)
        job = self.queue.get_next()
        assert job is not None
        assert job.job_id == job_id
        assert job.status == JobStatus.RUNNING
        assert job.started_at != ""
        assert self.queue._running_job == job_id

    def test_get_next_busy_gpu(self):
        b1 = ContentBrief(from_agent="social", content_type="image", topic="A")
        b2 = ContentBrief(from_agent="ads", content_type="image", topic="B")
        self.queue.submit(b1)
        self.queue.submit(b2)

        # First job picked up
        job1 = self.queue.get_next()
        assert job1 is not None
        assert job1.status == JobStatus.RUNNING

        # GPU busy, second call returns None
        job2 = self.queue.get_next()
        assert job2 is None

    def test_complete_job(self):
        brief = ContentBrief(from_agent="social", content_type="image", topic="A")
        job_id = self.queue.submit(brief)
        self.queue.get_next()
        self.queue.complete(job_id, ["/output/img.png"], "/output/")

        job = self.queue.jobs[job_id]
        assert job.status == JobStatus.COMPLETED
        assert job.output_files == ["/output/img.png"]
        assert job.output_url == "/output/"
        assert job.completed_at != ""

        # Now GPU free, can pick next
        b2 = ContentBrief(from_agent="ads", content_type="image", topic="B")
        self.queue.submit(b2)
        job2 = self.queue.get_next()
        assert job2 is not None

    def test_fail_and_retry(self):
        brief = ContentBrief(from_agent="social", content_type="image", topic="A")
        job_id = self.queue.submit(brief)
        self.queue.get_next()

        # First failure — should retry
        will_retry = self.queue.fail(job_id, "GPU OOM")
        assert will_retry is True
        job = self.queue.jobs[job_id]
        assert job.status == JobStatus.RETRYING
        assert job.retry_count == 1

        # Re-queued, pick it up again
        job = self.queue.get_next()
        assert job is not None
        assert job.job_id == job_id

        # Second failure — should retry again
        will_retry = self.queue.fail(job_id, "GPU OOM again")
        assert will_retry is True
        assert self.queue.jobs[job_id].retry_count == 2

        # Third failure — permanently failed
        self.queue.get_next()
        will_retry = self.queue.fail(job_id, "GPU OOM third time")
        assert will_retry is False
        assert self.queue.jobs[job_id].status == JobStatus.FAILED

    def test_priority_ordering(self):
        # Submit in normal order
        for priority in ["low", "normal", "high", "urgent", "low"]:
            brief = ContentBrief(from_agent="social", content_type="image", topic=priority, priority=priority)
            self.queue.submit(brief)

        # Should process: urgent, high, normal, low, low
        order = []
        while True:
            job = self.queue.get_next()
            if not job:
                break
            order.append(job.topic)
            self.queue.complete(job.job_id, [])

        assert order == ["urgent", "high", "normal", "low", "low"]

    def test_get_status(self):
        brief = ContentBrief(from_agent="social", content_type="image", topic="A")
        job_id = self.queue.submit(brief)
        status = self.queue.get_status(job_id)
        assert status is not None
        assert status["job_id"] == job_id
        assert status["status"] == "pending"
        assert status["content_type"] == "image"
        assert status["platform"] == "instagram"

    def test_get_status_unknown_job(self):
        assert self.queue.get_status("unknown_job") is None

    def test_queue_status(self):
        for i in range(3):
            brief = ContentBrief(from_agent="social", content_type="image", topic=f"Job {i}")
            self.queue.submit(brief)

        self.queue.get_next()  # Pick one

        status = self.queue.get_queue_status()
        assert status["workspace_id"] == "ws_test"
        assert status["total_jobs"] == 3
        assert status["pending"] == 2
        assert status["running"] == 1
        assert status["gpu_busy"] is True
        assert status["queue_depth"] == 2

    def test_list_recent(self):
        for i in range(15):
            brief = ContentBrief(from_agent="social", content_type="image", topic=f"Job {i}")
            self.queue.submit(brief)

        recent = self.queue.list_recent(limit=5)
        assert len(recent) == 5
        assert all("job_id" in j for j in recent)

    def test_empty_queue(self):
        assert self.queue.get_next() is None
        assert self.queue.get_queue_status()["total_jobs"] == 0

    def test_multiple_agents_share_queue(self):
        """Verify all agents in workspace share the same queue."""
        social_brief = ContentBrief(from_agent="social", content_type="image", topic="Social")
        ads_brief = ContentBrief(from_agent="ads", content_type="image", topic="Ads")
        website_brief = ContentBrief(from_agent="website", content_type="image", topic="Website")

        q = self.queue
        q.submit(social_brief)
        q.submit(ads_brief)
        q.submit(website_brief)

        assert len(q.jobs) == 3
        agents = {j.from_agent for j in q.jobs.values()}
        assert agents == {"social", "ads", "website"}


# ── Enhance Brief Intelligence Tests ──────────────────────────────────────────


class TestEnhanceBrief:
    def test_instagram_post_dimensions(self):
        brief = ContentBrief(
            content_type="social_post",
            platform="instagram",
            topic="Summer Sale",
        )
        enhanced = enhance_brief(brief)
        assert enhanced.width == 1080
        assert enhanced.height == 1080

    def test_instagram_story_dimensions(self):
        brief = ContentBrief(
            content_type="social_post",
            platform="instagram",
            style="modern",
            topic="Behind the scenes",
        )
        enhanced = enhance_brief(brief)
        # Default to instagram_post
        assert enhanced.width == 1080
        assert enhanced.height == 1080

    def test_facebook_ad_dimensions(self):
        brief = ContentBrief(
            content_type="ad_creative",
            platform="facebook",
            topic="Sale offer",
        )
        enhanced = enhance_brief(brief)
        assert enhanced.width == 1200
        assert enhanced.height == 628

    def test_youtube_thumbnail_dimensions(self):
        brief = ContentBrief(
            content_type="thumbnail",
            platform="youtube",
            topic="New video",
        )
        enhanced = enhance_brief(brief)
        assert enhanced.width == 1280
        assert enhanced.height == 720

    def test_website_hero_dimensions(self):
        brief = ContentBrief(
            content_type="hero_banner",
            platform="website",
            topic="Landing page hero",
        )
        enhanced = enhance_brief(brief)
        assert enhanced.width == 1920
        assert enhanced.height == 1080

    def test_brand_colors_applied(self):
        brief = ContentBrief(
            content_type="social_post",
            platform="instagram",
            topic="Brand post",
        )
        client = {"brand_colors": ["#FF6B35", "#004E89", "#1A1A2E"]}
        enhanced = enhance_brief(brief, client)
        assert enhanced.brand_colors_used == ["#FF6B35", "#004E89", "#1A1A2E"]
        assert "#FF6B35" in enhanced.enhanced_prompt

    def test_industry_context(self):
        brief = ContentBrief(
            content_type="social_post",
            platform="instagram",
            topic="Listing post",
        )
        client = {"industry": "real_estate"}
        enhanced = enhance_brief(brief, client)
        assert "architectural" in enhanced.enhanced_prompt or "property" in enhanced.enhanced_prompt

    def test_target_audience_tone(self):
        brief = ContentBrief(
            content_type="social_post",
            platform="instagram",
            topic="New product",
        )
        client = {"target_audience": "young millennials"}
        enhanced = enhance_brief(brief, client)
        assert "trendy" in enhanced.enhanced_prompt or "youthful" in enhanced.enhanced_prompt

    def test_luxury_style(self):
        brief = ContentBrief(
            content_type="social_post",
            platform="instagram",
            style="luxury",
            topic="Premium product",
        )
        enhanced = enhance_brief(brief)
        assert "luxury" in enhanced.enhanced_prompt
        assert "premium" in enhanced.enhanced_prompt

    def test_bold_style(self):
        brief = ContentBrief(
            content_type="social_post",
            platform="instagram",
            style="bold",
            topic="Flash sale",
        )
        enhanced = enhance_brief(brief)
        assert "bold" in enhanced.enhanced_prompt
        assert "vibrant" in enhanced.enhanced_prompt

    def test_video_params(self):
        brief = ContentBrief(
            content_type="video",
            platform="instagram",
            topic="Product demo",
        )
        enhanced = enhance_brief(brief)
        assert enhanced.frames == 49  # Default

    def test_video_high_priority(self):
        brief = ContentBrief(
            content_type="video",
            platform="youtube",
            style="professional",
            topic="Brand video",
            priority="high",
        )
        enhanced = enhance_brief(brief)
        assert enhanced.frames == 81

    def test_image_high_priority_more_steps(self):
        brief = ContentBrief(
            content_type="social_post",
            platform="instagram",
            topic="Hero post",
            priority="high",
        )
        enhanced = enhance_brief(brief)
        assert enhanced.steps == 30

    def test_text_overlay_in_prompt(self):
        brief = ContentBrief(
            content_type="social_post",
            platform="instagram",
            topic="Sale",
            text_overlay="50% OFF",
        )
        enhanced = enhance_brief(brief)
        assert "50% OFF" in enhanced.enhanced_prompt

    def test_cta_in_prompt(self):
        brief = ContentBrief(
            content_type="social_post",
            platform="instagram",
            topic="Sale",
            cta="Buy Now",
        )
        enhanced = enhance_brief(brief)
        assert "Buy Now" in enhanced.enhanced_prompt

    def test_ai_reasoning_populated(self):
        brief = ContentBrief(
            content_type="social_post",
            platform="instagram",
            style="bold",
            topic="Test",
        )
        client = {"brand_colors": ["#FF0000"], "industry": "food", "target_audience": "families"}
        enhanced = enhance_brief(brief, client)
        assert enhanced.ai_reasoning != ""
        assert "instagram" in enhanced.ai_reasoning.lower() or "1080" in enhanced.ai_reasoning

    def test_style_enhancement_populated(self):
        brief = ContentBrief(
            content_type="social_post",
            platform="instagram",
            style="modern",
            topic="Test",
        )
        enhanced = enhance_brief(brief)
        assert enhanced.style_enhancement != ""

    def test_empty_client_context(self):
        brief = ContentBrief(
            content_type="social_post",
            platform="instagram",
            topic="Test",
        )
        enhanced = enhance_brief(brief, {})
        assert enhanced.enhanced_prompt != ""

    def test_no_client_context(self):
        brief = ContentBrief(
            content_type="social_post",
            platform="instagram",
            topic="Test",
        )
        enhanced = enhance_brief(brief)
        assert enhanced.enhanced_prompt != ""

    def test_full_enhancement_flow(self):
        """Complete flow: brief → enhance → queue → get → complete."""
        queue = ContentJobQueue("ws_integration")

        brief = ContentBrief(
            from_agent="social",
            content_type="social_post",
            platform="instagram",
            style="bold",
            quantity=3,
            topic="Summer Sale",
            description="Vibrant summer sale posts for Instagram",
            text_overlay="SUMMER SALE",
            cta="Shop Now",
        )

        # Enhance
        client = {
            "brand_colors": ["#FF6B35", "#004E89"],
            "industry": "ecommerce",
            "target_audience": "young millennials",
        }
        brief = enhance_brief(brief, client)
        assert brief.enhanced_prompt != ""
        assert brief.width == 1080
        assert brief.height == 1080

        # Queue
        job_id = queue.submit(brief)
        assert job_id.startswith("job_")

        # Process
        job = queue.get_next()
        assert job is not None
        assert job.enhanced_prompt != ""

        # Complete
        queue.complete(job_id, ["/output/img1.png"])
        status = queue.get_status(job_id)
        assert status["status"] == "completed"


# ── Queue Registry Tests ──────────────────────────────────────────────────────


class TestQueueRegistry:
    def test_same_queue_same_workspace(self):
        q1 = get_queue("ws_abc")
        q2 = get_queue("ws_abc")
        assert q1 is q2

    def test_different_queue_different_workspace(self):
        q1 = get_queue("ws_abc")
        q2 = get_queue("ws_xyz")
        assert q1 is not q2

    def test_workspace_isolation(self):
        q1 = get_queue("ws_1")
        q2 = get_queue("ws_2")

        brief1 = ContentBrief(from_agent="social", content_type="image", topic="A")
        brief2 = ContentBrief(from_agent="ads", content_type="image", topic="B")

        q1.submit(brief1)
        q2.submit(brief2)

        assert len(q1.jobs) == 1
        assert len(q2.jobs) == 1

        job1 = q1.get_next()
        assert job1.topic == "A"

        job2 = q2.get_next()
        assert job2.topic == "B"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
