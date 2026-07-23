"""Tests for Workspace Content Store — per-workspace memory."""
import pytest
import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use temp dir for test data
_test_dir = tempfile.mkdtemp()
os.environ["TAGS_DATA_DIR"] = _test_dir

from admin.workspace.content_store import (
    ContentAgentMemory,
    WorkspaceContentStore,
    get_content_store,
)


class TestContentAgentMemory:
    def test_create_memory(self):
        mem = ContentAgentMemory(
            workspace_id="ws_test1",
            workspace_name="TestWorkspace",
            client_name="TestClient",
            industry="real_estate",
        )
        assert mem.workspace_id == "ws_test1"
        assert mem.total_jobs == 0
        assert mem.success_count == 0
        assert mem.failure_count == 0
        assert mem.mistakes_to_avoid == []

    def test_memory_to_dict(self):
        mem = ContentAgentMemory(workspace_id="ws_1", workspace_name="W1")
        d = mem.to_dict()
        assert d["workspace_id"] == "ws_1"
        assert "briefs_received" in d
        assert "successes" in d
        assert "failures" in d
        assert "mistakes_to_avoid" in d


class TestWorkspaceContentStore:
    def setup_method(self):
        self.store = WorkspaceContentStore()

    def test_get_or_create_new(self):
        mem = self.store.get_or_create(
            workspace_id="ws_new1",
            workspace_name="NewWorkspace",
            client_name="NewClient",
            industry="saas",
        )
        assert mem.workspace_id == "ws_new1"
        assert mem.workspace_name == "NewWorkspace"
        assert mem.client_name == "NewClient"
        assert mem.industry == "saas"

    def test_get_existing(self):
        mem1 = self.store.get_or_create(
            workspace_id="ws_exist1",
            workspace_name="W1",
            client_name="C1",
        )
        mem2 = self.store.get_or_create(workspace_id="ws_exist1")
        assert mem1 is mem2  # Same object
        assert mem2.workspace_name == "W1"

    def test_persistence(self):
        # Create
        self.store.get_or_create(
            workspace_id="ws_persist1",
            workspace_name="PersistWorkspace",
            client_name="PersistClient",
            industry="ecommerce",
        )

        # Create new store instance (simulates restart)
        store2 = WorkspaceContentStore()
        mem = store2.get_or_create(workspace_id="ws_persist1")
        assert mem.workspace_name == "PersistWorkspace"
        assert mem.client_name == "PersistClient"
        assert mem.industry == "ecommerce"

    def test_record_brief(self):
        self.store.get_or_create(
            workspace_id="ws_brief1",
            workspace_name="W1",
            client_name="C1",
        )
        self.store.record_brief_received(
            workspace_id="ws_brief1",
            brief={"title": "Test Brief", "post_type": "listing"},
        )
        mem = self.store.get_or_create(workspace_id="ws_brief1")
        assert len(mem.briefs_received) == 1
        assert mem.briefs_received[0]["title"] == "Test Brief"
        assert mem.total_jobs == 1

    def test_record_success(self):
        self.store.get_or_create(
            workspace_id="ws_succ1",
            workspace_name="W1",
            client_name="C1",
            industry="real_estate",
        )
        self.store.record_success(
            workspace_id="ws_succ1",
            job_id="job_1",
            brief_summary="5 Instagram listing images",
            deliverables=["img1.png", "img2.png"],
            prompts_used=["professional real estate photo"],
            platform="instagram",
            visual_type="listing_image",
            gpu_minutes=2.5,
            learnings=["Warm tones worked well for real estate"],
        )
        mem = self.store.get_or_create(workspace_id="ws_succ1")
        assert mem.success_count == 1
        assert len(mem.successes) == 1
        assert mem.successes[0]["job_id"] == "job_1"
        assert "Warm tones worked well for real estate" in mem.brand_learnings

    def test_record_failure(self):
        self.store.get_or_create(
            workspace_id="ws_fail1",
            workspace_name="W1",
            client_name="C1",
        )
        self.store.record_failure(
            workspace_id="ws_fail1",
            job_id="job_2",
            brief_summary="Video generation failed",
            error="GPU OOM",
            platform="instagram",
            visual_type="video",
            what_failed="CogVideoX OOM on 81 frames",
            avoid_next_time="Use 49 frames for Instagram videos",
        )
        mem = self.store.get_or_create(workspace_id="ws_fail1")
        assert mem.failure_count == 1
        assert len(mem.failures) == 1
        assert "Use 49 frames for Instagram videos" in mem.mistakes_to_avoid

    def test_platform_performance_tracking(self):
        self.store.get_or_create(
            workspace_id="ws_plat1",
            workspace_name="W1",
            client_name="C1",
        )
        # Success on instagram
        self.store.record_success(
            workspace_id="ws_plat1",
            job_id="j1",
            brief_summary="Post 1",
            deliverables=["img1.png"],
            prompts_used=["prompt1"],
            platform="instagram",
            visual_type="image",
            gpu_minutes=2.0,
        )
        # Another success
        self.store.record_success(
            workspace_id="ws_plat1",
            job_id="j2",
            brief_summary="Post 2",
            deliverables=["img2.png"],
            prompts_used=["prompt2"],
            platform="instagram",
            visual_type="listing",
            gpu_minutes=3.0,
        )
        # Failure on instagram
        self.store.record_failure(
            workspace_id="ws_plat1",
            job_id="j3",
            brief_summary="Video failed",
            error="Timeout",
            platform="instagram",
        )

        mem = self.store.get_or_create(workspace_id="ws_plat1")
        stats = mem.platform_performance["instagram"]
        assert stats["total_jobs"] == 3
        assert stats["successes"] == 2
        assert stats["failures"] == 1
        assert stats["avg_gpu_minutes"] == 2.5  # (2+3)/2

    def test_memory_summary(self):
        self.store.get_or_create(
            workspace_id="ws_sum1",
            workspace_name="W1",
            client_name="C1",
            industry="real_estate",
        )
        # Add some history
        self.store.record_success(
            workspace_id="ws_sum1",
            job_id="j1",
            brief_summary="Test",
            deliverables=[],
            prompts_used=["prompt1"],
            platform="instagram",
            visual_type="image",
            gpu_minutes=2.0,
            learnings=["Warm tones work for real estate"],
        )
        self.store.record_failure(
            workspace_id="ws_sum1",
            job_id="j2",
            brief_summary="Fail",
            error="OOM",
            avoid_next_time="Reduce video frames",
        )

        summary = self.store.get_memory_summary("ws_sum1")
        assert "Success rate" in summary
        assert "50%" in summary  # 1 success, 1 failure
        assert "Warm tones work" in summary
        assert "MISTAKES TO AVOID" in summary
        assert "Reduce video frames" in summary

    def test_empty_memory_summary(self):
        summary = self.store.get_memory_summary("nonexistent")
        assert summary == ""

    def test_stats(self):
        self.store.get_or_create(
            workspace_id="ws_stats1",
            workspace_name="W1",
            client_name="C1",
        )
        self.store.record_success(
            workspace_id="ws_stats1",
            job_id="j1",
            brief_summary="Test",
            deliverables=[],
            prompts_used=[],
            platform="instagram",
            visual_type="image",
            gpu_minutes=1.0,
        )
        stats = self.store.get_stats("ws_stats1")
        assert stats["success_count"] == 1
        assert stats["failure_count"] == 0
        assert stats["success_rate"] == 100.0

    def test_multiple_workspaces_isolation(self):
        self.store.get_or_create(
            workspace_id="ws_iso1",
            workspace_name="W1",
            client_name="C1",
        )
        self.store.get_or_create(
            workspace_id="ws_iso2",
            workspace_name="W2",
            client_name="C2",
        )

        self.store.record_success(
            workspace_id="ws_iso1",
            job_id="j1",
            brief_summary="W1 job",
            deliverables=[],
            prompts_used=[],
            platform="instagram",
            visual_type="image",
            gpu_minutes=1.0,
        )

        mem1 = self.store.get_or_create(workspace_id="ws_iso1")
        mem2 = self.store.get_or_create(workspace_id="ws_iso2")

        assert mem1.success_count == 1
        assert mem2.success_count == 0  # Isolated


class TestGlobalStore:
    def test_singleton(self):
        s1 = get_content_store()
        s2 = get_content_store()
        assert s1 is s2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
    shutil.rmtree(_test_dir, ignore_errors=True)
