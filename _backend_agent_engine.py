"""
Agent Engine - Core engine that loads agents, workflows, and executes them via Groq API.
Imports from the marketing-ai-agency scripts directory.
"""

import os
import sys
import json
import yaml
import re
import time
import logging
import subprocess
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from threading import Lock

from dotenv import load_dotenv
from email_sender import send_email

MARKETING_DIR = Path(__file__).resolve().parent.parent.parent / "marketing-ai-agency"
API_ROUTER_PATH = MARKETING_DIR / "scripts" / "api-router.py"
SCRIPTS_DIR = MARKETING_DIR / "scripts"

sys.path.insert(0, str(MARKETING_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

spec = importlib.util.spec_from_file_location("api_router", API_ROUTER_PATH)
api_router_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api_router_module)
GroqRouter = api_router_module.GroqRouter
NvidiaRouter = getattr(api_router_module, 'NvidiaRouter', None)

load_dotenv(MARKETING_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("AgentEngine")


META_MCP_BRIDGE = Path(__file__).parent / "meta_mcp_bridge.js"
SOCIAL_GRAPH_BRIDGE = Path(__file__).parent / "social_graph_bridge.js"


class MetaMCPClient:
    """Python wrapper around meta-ads-mcp (Node.js MCP server for Meta Marketing API).
    Spawns a Node.js bridge process per request, passes the Meta access token,
    calls the requested tool, and returns the parsed result.
    """

    def __init__(self, access_token: str):
        self.access_token = access_token
        if not access_token or access_token == "" or access_token == "YOUR_META_ACCESS_TOKEN":
            raise ValueError("Valid META_ACCESS_TOKEN is required")

    def call_tool(self, tool: str, args: Dict = None) -> Dict:
        if args is None:
            args = {}
        input_data = json.dumps({"tool": tool, "args": args})
        try:
            proc = subprocess.run(
                ["node", str(META_MCP_BRIDGE)],
                input=input_data,
                capture_output=True,
                text=True,
                timeout=60,
                env={**os.environ, "META_ACCESS_TOKEN": self.access_token},
                cwd=str(META_MCP_BRIDGE.parent),
            )
            if proc.returncode != 0:
                stderr = proc.stderr.strip()
                # Try to parse error from stderr
                try:
                    err_data = json.loads(stderr)
                    return {"success": False, "tool": tool, "error": err_data.get("error", stderr)}
                except (json.JSONDecodeError, TypeError):
                    return {"success": False, "tool": tool, "error": stderr or f"Process exited with code {proc.returncode}"}
            output = proc.stdout.strip()
            if not output:
                return {"success": False, "tool": tool, "error": "No output from MCP bridge"}
            try:
                return json.loads(output)
            except json.JSONDecodeError as e:
                return {"success": False, "tool": tool, "error": f"Invalid JSON from MCP bridge: {e}", "raw_output": output[:500]}
        except subprocess.TimeoutExpired:
            return {"success": False, "tool": tool, "error": "MCP bridge timed out after 60s"}
        except FileNotFoundError:
            return {"success": False, "tool": tool, "error": "Node.js not found. Install Node.js to use Meta Ads MCP."}
        except Exception as e:
            return {"success": False, "tool": tool, "error": str(e)}

    def health_check(self) -> Dict:
        return self.call_tool("health_check")

    def get_ad_accounts(self) -> Dict:
        return self.call_tool("get_ad_accounts")

    def get_campaigns(self, account_id: str = None, status: str = None) -> Dict:
        args = {}
        if account_id:
            args["account_id"] = account_id
        if status:
            args["status"] = status
        return self.call_tool("get_campaigns", args)

    def create_campaign(self, name: str, objective: str, daily_budget_cents: int,
                       account_id: str, status: str = "PAUSED",
                       special_ad_categories: List[str] = None) -> Dict:
        args = {
            "name": name,
            "objective": objective,
            "daily_budget": daily_budget_cents,
            "status": status,
            "account_id": account_id,
        }
        if special_ad_categories:
            args["special_ad_categories"] = special_ad_categories
        return self.call_tool("create_campaign", args)

    def update_campaign(self, campaign_id: str, **kwargs) -> Dict:
        return self.call_tool("update_campaign", {"campaign_id": campaign_id, **kwargs})

    def pause_campaign(self, campaign_id: str) -> Dict:
        return self.call_tool("pause_campaign", {"campaign_id": campaign_id})

    def resume_campaign(self, campaign_id: str) -> Dict:
        return self.call_tool("resume_campaign", {"campaign_id": campaign_id})

    def create_ad_set(self, name: str, campaign_id: str, daily_budget_cents: int,
                     targeting: Dict, optimization_goal: str = "REACH",
                     billing_event: str = "IMPRESSIONS",
                     status: str = "PAUSED") -> Dict:
        return self.call_tool("create_ad_set", {
            "name": name,
            "campaign_id": campaign_id,
            "daily_budget": daily_budget_cents,
            "billing_event": billing_event,
            "optimization_goal": optimization_goal,
            "targeting": targeting,
            "status": status,
        })

    def create_ad_creative(self, account_id: str, name: str, title: str, body: str,
                          image_url: str, call_to_action_type: str = "LEARN_MORE",
                          page_id: str = None, link: str = None) -> Dict:
        args = {
            "name": name,
            "account_id": account_id,
            "title": title,
            "body": body,
            "image_url": image_url,
            "call_to_action_type": call_to_action_type,
        }
        if page_id:
            args["page_id"] = page_id
        if link:
            args["link"] = link
        return self.call_tool("create_ad_creative", args)

    def create_ad(self, name: str, ad_set_id: str, creative_id: str = None,
                  creative_spec: Dict = None) -> Dict:
        args = {"name": name, "ad_set_id": ad_set_id}
        if creative_id:
            args["creative_id"] = creative_id
        if creative_spec:
            args["creative_spec"] = creative_spec
        return self.call_tool("create_ad", args)

    def get_insights(self, date_preset: str = "last_30d", level: str = "campaign",
                    account_id: str = None, time_increment: str = "1") -> Dict:
        args = {
            "date_preset": date_preset,
            "level": level,
            "time_increment": time_increment,
        }
        if account_id:
            args["account_id"] = account_id
        return self.call_tool("get_insights", args)

    def list_audiences(self, account_id: str) -> Dict:
        return self.call_tool("list_audiences", {"account_id": account_id})

    def create_lookalike_audience(self, name: str, source_audience_id: str,
                                  lookalike_percentage: int = 5, country: str = "US") -> Dict:
        return self.call_tool("create_lookalike_audience", {
            "name": name,
            "source_audience_id": source_audience_id,
            "lookalike_percentage": lookalike_percentage,
            "country": country,
        })

    def diagnose_campaign_readiness(self, campaign_id: str) -> Dict:
        return self.call_tool("diagnose_campaign_readiness", {"campaign_id": campaign_id})

    def check_account_setup(self) -> Dict:
        return self.call_tool("check_account_setup")


class SocialGraphClient:
    """Python wrapper around social_graph_bridge.js — free social media APIs.
    Supports Meta Graph API (Facebook/Instagram organic), Twitter API v2, LinkedIn API.
    No paid keys — just free developer account tokens.
    """

    def call_tool(self, tool: str, args: Dict = None) -> Dict:
        if args is None:
            args = {}
        input_data = json.dumps({"tool": tool, "args": args})
        try:
            proc = subprocess.run(
                ["node", str(SOCIAL_GRAPH_BRIDGE)],
                input=input_data.encode("utf-8"),
                capture_output=True,
                timeout=30,
                env={**os.environ},
                cwd=str(SOCIAL_GRAPH_BRIDGE.parent),
            )
            stdout = proc.stdout.decode("utf-8", errors="replace") if proc.stdout else ""
            stderr = proc.stderr.decode("utf-8", errors="replace") if proc.stderr else ""
            if proc.returncode != 0:
                err_text = stderr.strip()
                try:
                    err_data = json.loads(err_text)
                    return {"success": False, "tool": tool, "error": err_data.get("error", err_text)}
                except (json.JSONDecodeError, TypeError):
                    return {"success": False, "tool": tool, "error": err_text or f"Process exited with code {proc.returncode}"}
            output = stdout.strip()
            if not output:
                return {"success": False, "tool": tool, "error": "No output from Social Graph bridge"}
            try:
                return json.loads(output)
            except json.JSONDecodeError as e:
                return {"success": False, "tool": tool, "error": f"Invalid JSON: {e}", "raw_output": output[:500]}
        except subprocess.TimeoutExpired:
            return {"success": False, "tool": tool, "error": "Social Graph bridge timed out after 30s"}
        except Exception as e:
            return {"success": False, "tool": tool, "error": str(e)}

    def call_tool_with_tokens(self, tool: str, args: Dict = None, tokens: Dict = None) -> Dict:
        """Call a social tool with explicit per-request tokens (from Supabase DB)."""
        if args is None:
            args = {}
        args["tokens"] = tokens or {}
        input_data = json.dumps({"tool": tool, "args": args})
        try:
            proc = subprocess.run(
                ["node", str(SOCIAL_GRAPH_BRIDGE)],
                input=input_data.encode("utf-8"),
                capture_output=True,
                timeout=30,
                env={**os.environ},
                cwd=str(SOCIAL_GRAPH_BRIDGE.parent),
            )
            stdout = proc.stdout.decode("utf-8", errors="replace") if proc.stdout else ""
            stderr = proc.stderr.decode("utf-8", errors="replace") if proc.stderr else ""
            if proc.returncode != 0:
                err_text = stderr.strip()
                try:
                    err_data = json.loads(err_text)
                    return {"success": False, "tool": tool, "error": err_data.get("error", err_text)}
                except (json.JSONDecodeError, TypeError):
                    return {"success": False, "tool": tool, "error": err_text or f"Process exited with code {proc.returncode}"}
            output = stdout.strip()
            if not output:
                return {"success": False, "tool": tool, "error": "No output from Social Graph bridge"}
            try:
                return json.loads(output)
            except json.JSONDecodeError as e:
                return {"success": False, "tool": tool, "error": f"Invalid JSON: {e}", "raw_output": output[:500]}
        except subprocess.TimeoutExpired:
            return {"success": False, "tool": tool, "error": "Social Graph bridge timed out after 30s"}
        except Exception as e:
            return {"success": False, "tool": tool, "error": str(e)}

    def meta_publish_feed(self, message: str, image_url: str = None, link: str = None) -> Dict:
        return self.call_tool("meta:post", {"text": message, "image_url": image_url, "link": link})

    def meta_publish_photo(self, caption: str, image_url: str) -> Dict:
        return self.call_tool("meta:photo", {"caption": caption, "image_url": image_url})

    def meta_publish_instagram(self, image_url: str, caption: str = "") -> Dict:
        return self.call_tool("meta:instagram", {"image_url": image_url, "caption": caption})

    def twitter_tweet(self, text: str) -> Dict:
        return self.call_tool("twitter:tweet", {"text": text})

    def linkedin_post(self, text: str, title: str = None, description: str = None, url: str = None) -> Dict:
        return self.call_tool("linkedin:post", {"text": text, "title": title, "description": description, "url": url})

    # ── Analytics Methods ──
    def get_page_insights(self, page_id: str = None, period: str = "day", tokens: Dict = None) -> Dict:
        if not page_id:
            page_id = os.environ.get("META_PAGE_ID")
        args = {"page_id": page_id, "period": period}
        if tokens:
            return self.call_tool_with_tokens("meta:analytics:page", args, tokens)
        return self.call_tool("meta:analytics:page", args)

    def get_recent_posts(self, page_id: str = None, limit: int = 10, tokens: Dict = None) -> Dict:
        if not page_id:
            page_id = os.environ.get("META_PAGE_ID")
        args = {"page_id": page_id, "limit": limit}
        if tokens:
            return self.call_tool_with_tokens("meta:analytics:posts", args, tokens)
        return self.call_tool("meta:analytics:posts", args)

    def get_post_insights(self, post_id: str, tokens: Dict = None) -> Dict:
        args = {"post_id": post_id}
        if tokens:
            return self.call_tool_with_tokens("meta:analytics:post", args, tokens)
        return self.call_tool("meta:analytics:post", args)

    def get_instagram_media(self, ig_user_id: str = None, limit: int = 10, tokens: Dict = None) -> Dict:
        if not ig_user_id:
            ig_user_id = os.environ.get("META_INSTAGRAM_ID")
        args = {"ig_user_id": ig_user_id, "limit": limit}
        if tokens:
            return self.call_tool_with_tokens("meta:analytics:instagram:media", args, tokens)
        return self.call_tool("meta:analytics:instagram:media", args)

    def get_instagram_insights(self, ig_user_id: str = None, period: str = "day", tokens: Dict = None) -> Dict:
        if not ig_user_id:
            ig_user_id = os.environ.get("META_INSTAGRAM_ID")
        args = {"ig_user_id": ig_user_id, "period": period}
        if tokens:
            return self.call_tool_with_tokens("meta:analytics:instagram:insights", args, tokens)
        return self.call_tool("meta:analytics:instagram:insights", args)


class ReachToolClient:
    """Python wrapper around Agent-Reach tools — FREE web/search/social CLIs.
    No paid APIs needed. Uses Exa, Jina Reader, twitter-cli, rdt-cli, gh CLI, etc.
    Install: pip install agent-reach
    """

    def search_web_exa(self, query: str, num_results: int = 5) -> Dict:
        try:
            proc = subprocess.run(
                ["mcporter", "call", f'exa.web_search_exa(query: "{query}", numResults: {num_results})'],
                capture_output=True, text=True, timeout=30
            )
            output = proc.stdout.strip()
            return {"success": True, "data": output[:3000]} if output else {"success": False, "error": "No results"}
        except Exception as e:
            return {"success": False, "error": str(e), "note": "Exa MCP not available. Try: mcporter install exa"}

    def search_code_exa(self, query: str, tokens: int = 3000) -> Dict:
        try:
            proc = subprocess.run(
                ["mcporter", "call", f'exa.get_code_context_exa(query: "{query}", tokensNum: {tokens})'],
                capture_output=True, text=True, timeout=30
            )
            return {"success": True, "data": proc.stdout.strip()[:3000]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def read_web_jina(self, url: str) -> Dict:
        try:
            proc = subprocess.run(
                ["curl", "-s", f"https://r.jina.ai/{url}"],
                capture_output=True, text=True, timeout=30
            )
            output = proc.stdout.strip()
            return {"success": True, "content": output[:5000]} if output else {"success": False, "error": "Empty response"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_twitter(self, query: str, limit: int = 10) -> Dict:
        try:
            proc = subprocess.run(
                ["twitter", "search", query, "-n", str(limit)],
                capture_output=True, text=True, timeout=30
            )
            return {"success": True, "data": proc.stdout.strip()[:3000]}
        except Exception as e:
            return {"success": False, "error": str(e), "note": "twitter-cli not installed. Try: pipx install twitter-cli"}

    def search_reddit(self, query: str, limit: int = 10) -> Dict:
        try:
            proc = subprocess.run(
                ["rdt", "search", query, "--limit", str(limit)],
                capture_output=True, text=True, timeout=30
            )
            return {"success": True, "data": proc.stdout.strip()[:3000]}
        except Exception as e:
            return {"success": False, "error": str(e), "note": "rdt-cli not installed. Try: pipx install rdt-cli"}

    def read_reddit_post(self, post_id: str) -> Dict:
        try:
            proc = subprocess.run(
                ["rdt", "read", post_id], capture_output=True, text=True, timeout=30
            )
            return {"success": True, "data": proc.stdout.strip()[:3000]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def browse_reddit_sub(self, subreddit: str, limit: int = 20) -> Dict:
        try:
            proc = subprocess.run(
                ["rdt", "sub", subreddit, "--limit", str(limit)],
                capture_output=True, text=True, timeout=30
            )
            return {"success": True, "data": proc.stdout.strip()[:3000]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_github(self, query: str, limit: int = 10) -> Dict:
        try:
            proc = subprocess.run(
                ["gh", "search", "repos", query, "--sort", "stars", "--limit", str(limit)],
                capture_output=True, text=True, timeout=30
            )
            return {"success": True, "data": proc.stdout.strip()[:3000]}
        except Exception as e:
            return {"success": False, "error": str(e), "note": "gh CLI not installed. Try: https://cli.github.com"}

    def view_github_repo(self, repo: str) -> Dict:
        try:
            proc = subprocess.run(
                ["gh", "repo", "view", repo], capture_output=True, text=True, timeout=30
            )
            return {"success": True, "data": proc.stdout.strip()[:3000]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_user_tweets(self, username: str, limit: int = 20) -> Dict:
        try:
            proc = subprocess.run(
                ["twitter", "user-posts", f"@{username}", "-n", str(limit)],
                capture_output=True, text=True, timeout=30
            )
            return {"success": True, "data": proc.stdout.strip()[:3000]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def read_rss(self, feed_url: str, limit: int = 5) -> Dict:
        try:
            import feedparser
            d = feedparser.parse(feed_url)
            entries = [{"title": e.title, "link": e.link, "summary": e.summary[:200]}
                      for e in d.entries[:limit]]
            return {"success": True, "entries": entries, "feed_title": d.feed.get("title", "")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_youtube_info(self, video_url: str) -> Dict:
        try:
            proc = subprocess.run(
                ["yt-dlp", "--dump-json", video_url],
                capture_output=True, text=True, timeout=30
            )
            data = json.loads(proc.stdout.strip()) if proc.stdout.strip() else {}
            return {"success": True, "title": data.get("title", ""), "channel": data.get("channel", ""),
                    "duration": data.get("duration", 0), "description": (data.get("description", "") or "")[:500]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_linkedin_people(self, keyword: str, limit: int = 10) -> Dict:
        try:
            proc = subprocess.run(
                ["mcporter", "call", f'linkedin-scraper.search_people(keyword: "{keyword}", limit: {limit})'],
                capture_output=True, text=True, timeout=30
            )
            return {"success": True, "data": proc.stdout.strip()[:3000]}
        except Exception as e:
            return {"success": False, "error": str(e), "note": "LinkedIn MCP not available"}

    def get_linkedin_company(self, linkedin_url: str) -> Dict:
        try:
            proc = subprocess.run(
                ["mcporter", "call", f'linkedin-scraper.get_company_profile(linkedin_url: "{linkedin_url}")'],
                capture_output=True, text=True, timeout=30
            )
            return {"success": True, "data": proc.stdout.strip()[:3000]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def doctor(self) -> Dict:
        """Check which Agent-Reach tools are available"""
        checks = {}
        tools = [
            ("mcporter", ["mcporter", "--version"]),
            ("exa_search", ["mcporter", "call", "exa.web_search_exa(query: 'test', numResults: 1)"]),
            ("jina_reader", ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "https://r.jina.ai/"]),
            ("twitter_cli", ["twitter", "--version"]),
            ("rdt_cli", ["rdt", "--version"]),
            ("gh_cli", ["gh", "--version"]),
            ("yt_dlp", ["yt-dlp", "--version"]),
            ("feedparser", [sys.executable, "-c", "import feedparser; print('ok')"]),
        ]
        for name, cmd in tools:
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                checks[name] = "✅" if proc.returncode == 0 else "❌"
            except:
                checks[name] = "❌"
        return {"status": "ok" if any(v == "✅" for v in checks.values()) else "no_tools",
                "tools": checks,
                "note": "Run 'pip install agent-reach' to install all tools"}


class WanS2VClient:
    """Wan2.2-S2V Speech-to-Video via Hugging Face Space (Gradio Client).
    FREE AI Clone / Talking Head — photo + audio → video with lip-sync.
    """

    SPACE_NAME = "Wan-AI/Wan2.2-S2V"

    def __init__(self):
        self.client: Optional[Any] = None
        self._lock = Lock()

    def _get_client(self):
        if self.client is None:
            with self._lock:
                if self.client is None:
                    try:
                        from gradio_client import Client
                        self.client = Client(self.SPACE_NAME)
                        logger.info(f"Connected to S2V Space: {self.SPACE_NAME}")
                    except Exception as e:
                        logger.error(f"S2V Client init error: {e}")
                        raise
        return self.client

    def generate_talking_head(self, image_path: str, audio_path: str,
                              resolution: str = "480P", timeout: int = 600) -> Dict[str, Any]:
        """Generate talking head video (blocking — waits for result).

        Args:
            image_path: Path/URL to reference person photo
            audio_path: Path/URL to speech audio file (.wav/.mp3)
            resolution: "480P" or "720P"
            timeout: Max wait seconds (default 600 = 10min, HF free tier is slow)

        Returns:
            Dict with keys: success, video_path, video_url, subtitles_url, error
        """
        try:
            from gradio_client import handle_file

            client = self._get_client()
            logger.info(f"S2V generating talking head: img={image_path}, audio={audio_path}, res={resolution}")

            result = client.predict(
                ref_img=handle_file(image_path),
                audio=handle_file(audio_path),
                resolution=resolution,
                api_name="/predict"
            )

            video_data = result.get("video", {})
            subs_data = result.get("subtitles")

            video_path = video_data.get("path", "")
            video_url = video_data.get("url", "")
            subs_path = subs_data.get("path", "") if subs_data else ""
            subs_url = subs_data.get("url", "") if subs_data else ""

            if video_path or video_url:
                logger.info(f"S2V success: video={video_url}")
                return {
                    "success": True,
                    "video_path": video_path,
                    "video_url": video_url,
                    "subtitles_path": subs_path,
                    "subtitles_url": subs_url,
                    "error": None,
                }
            else:
                return {"success": False, "video_path": "", "video_url": "",
                        "subtitles_path": "", "subtitles_url": "", "error": "No video in response"}

        except Exception as e:
            logger.error(f"S2V generate error: {e}")
            return {"success": False, "video_path": "", "video_url": "",
                    "subtitles_path": "", "subtitles_url": "", "error": str(e)}

    def submit_talking_head(self, image_path: str, audio_path: str,
                            resolution: str = "480P") -> Dict[str, Any]:
        """Submit talking head job (non-blocking — returns job for polling).

        Returns job_id and status_url for async polling.
        Call job_status(job_id) later to get result.
        """
        try:
            from gradio_client import handle_file

            client = self._get_client()
            job = client.submit(
                ref_img=handle_file(image_path),
                audio=handle_file(audio_path),
                resolution=resolution,
                api_name="/predict"
            )
            return {
                "success": True,
                "job": job,
                "job_id": str(id(job)),
                "status": "queued",
                "message": "Job submitted. Call job_status() or job.result() when ready.",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def job_status(self, job) -> Dict[str, Any]:
        """Check status of a submitted job"""
        try:
            if job.done():
                result = job.result()
                video_data = result.get("video", {})
                subs_data = result.get("subtitles")
                video_url = video_data.get("url", "")
                return {
                    "success": True,
                    "done": True,
                    "video_path": video_data.get("path", ""),
                    "video_url": video_url,
                    "subtitles_url": subs_data.get("url", "") if subs_data else "",
                    "error": None,
                }
            status = job.status()
            return {
                "success": True,
                "done": False,
                "status": "processing",
                "queue_position": status.rank if hasattr(status, 'rank') else None,
                "eta": status.eta if hasattr(status, 'eta') else None,
            }
        except Exception as e:
            return {"success": False, "done": False, "error": str(e)}

    def doctor(self) -> Dict[str, Any]:
        """Check if S2V Space is accessible"""
        try:
            client = self._get_client()
            return {"success": True, "space": self.SPACE_NAME, "available": True}
        except Exception as e:
            return {"success": False, "space": self.SPACE_NAME, "available": False, "error": str(e)}


class AgentEngine:
    def __init__(self):
        self.base_dir = MARKETING_DIR
        self.agents_dir = self.base_dir / "agents"
        self.workflows_dir = self.base_dir / "workflows"
        self.clients_dir = self.base_dir / "clients"

        self.router = GroqRouter()
        self.nvidia = NvidiaRouter() if NvidiaRouter else None

        self._agents_cache = None
        self._workflows_cache = None

        self.reach = ReachToolClient()

        self.active_workflows: Dict[str, Dict] = {}
        self.workflow_counter = 0
        self._lock = Lock()

        self._complex_agents = [
            "brand-strategist", "agency-manager", "competitor-tracker",
            "analytics-pro", "review-analyst", "ads-manager",
            "ads-executor", "ads-auditor", "ads-analyzer",
            "ads-planner", "ads-creative-agent", "ads-budget-manager",
            "ads-competitor-intel",
            "product-manager", "support-manager", "support-agent",
            "seo-manager"
        ]

        self._nvidia_agents = [
            "hermes-agent", "openclaw-agent", "opencode-agent",
            "ads-specialist"
        ]

        self.lead_queue = []
        self.lead_counter = 0
        self.max_queue_size = 100
        self.hermes_workload = 0
        self.opencode_workload = 0
        self.max_agent_load = 10
        self.inactive_threshold_days = 7
        self.owner_notifications = []
        self.cold_emails_sent = 0

        # ── Currency Config (High Profit Countries) ──
        self.CURRENCY_MAP = {
            "usa": "USD", "united states": "USD", "us": "USD", "america": "USD",
            "uk": "GBP", "united kingdom": "GBP", "england": "GBP", "britain": "GBP",
            "china": "CNY", "china yuan": "CNY",
            "europe": "EUR", "eu": "EUR", "germany": "EUR", "france": "EUR",
            "uae": "AED", "dubai": "AED",
            "canada": "CAD",
            "australia": "AUD",
            "india": "INR", "bharat": "INR",
            "pakistan": "PKR", "pk": "PKR",
        }
        self.DEFAULT_CURRENCY = "USD"

        # ── Daily Stats ──
        self._today = datetime.now().strftime("%Y-%m-%d")
        self.stats_leads_today = 0
        self.stats_converted_today = 0
        self.stats_replies_today = 0
        self.stats_cold_emails_today = 0

    def _reset_daily_stats_if_new_day(self):
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self._today:
            self._today = today
            self.stats_leads_today = 0
            self.stats_converted_today = 0
            self.stats_replies_today = 0
            self.stats_cold_emails_today = 0

    def detect_currency(self, location: str = "") -> str:
        if not location:
            return self.DEFAULT_CURRENCY
        loc = location.lower().strip()
        for key, currency in self.CURRENCY_MAP.items():
            if key in loc:
                return currency
        return self.DEFAULT_CURRENCY

    def get_today_stats(self) -> Dict:
        self._reset_daily_stats_if_new_day()
        return {
            "date": self._today,
            "leads_today": self.stats_leads_today,
            "converted_today": self.stats_converted_today,
            "replies_today": self.stats_replies_today,
            "cold_emails_today": self.stats_cold_emails_today,
            "total_leads_in_queue": len(self.lead_queue),
            "pending_leads": sum(1 for l in self.lead_queue if l.get("status") in ("new", "confirmation_emailed", "processing")),
            "hermes_load": f"{self.hermes_workload}/{self.max_agent_load}",
            "opencode_load": f"{self.opencode_workload}/{self.max_agent_load}"
        }

    def _load_agent_file(self, agent_name: str) -> Dict:
        kebab_name = re.sub(r"(?<!^)(?=[A-Z])", "-", agent_name).lower()
        overrides = {
            "s-e-o-master": "seo-master", "a-b-tester": "ab-tester",
            "hermes": "hermes-agent", "openclaw": "openclaw-agent", "opencode": "opencode-agent",
            "ads": "ads-manager",
            "adsmanager": "ads-manager", "adsexecutor": "ads-executor",
            "adsauditor": "ads-auditor", "adsanalyzer": "ads-analyzer",
            "adsplanner": "ads-planner", "adscreativeagent": "ads-creative-agent",
            "adsbudgetmanager": "ads-budget-manager",
            "adscompetitorintel": "ads-competitor-intel",
            "productmanager": "product-manager",
            "supportmanager": "support-manager", "supportagent": "support-agent",
            "seomanager": "seo-manager",
            "contentwriter": "content-writer", "emailwizard": "email-wizard",
            "seomaster": "seo-master", "socialcommander": "social-commander",
            "calendarmaster": "calendar-master", "brandstrategist": "brand-strategist",
            "competitortracker": "competitor-tracker", "analyticspro": "analytics-pro",
            "creativegenius": "creative-genius", "photoshooter": "photo-shooter",
            "agencymanager": "agency-manager",
            "qualitychecker": "quality-checker",
            "crisismanager": "crisis-manager", "clientintake": "client-intake",
            "abtester": "ab-tester", "reviewanalyst": "review-analyst",
            "socialpublisher": "social-publisher",
            "hookgenerator": "hook-generator", "postformatter": "post-formatter",
            "nicheresearch": "niche-research", "contentmatrix": "content-matrix",
            "postscorer": "post-scorer", "socialmediamanager": "social-media-manager"
        }
        kebab_name = overrides.get(kebab_name, kebab_name)
        agent_path = self.agents_dir / f"{kebab_name}.md"
        if not agent_path.exists():
            raise FileNotFoundError(f"Agent file not found: {agent_path}")

        content = agent_path.read_text(encoding="utf-8")

        frontmatter = {}
        body = content
        if content.startswith("---"):
            # Find closing --- on its own line (not inside markdown tables)
            end = -1
            for m in re.finditer(r"^---$", content, re.MULTILINE):
                if m.start() == 0:
                    continue  # skip the opening ---
                end = m.start()
                break
            if end == -1:
                end = content.find("---", 3)
            if end != -1:
                try:
                    frontmatter = yaml.safe_load(content[3:end].strip()) or {}
                except yaml.YAMLError:
                    frontmatter = {}
                body = content[end + 3:].strip()

        return {
            "name": frontmatter.get("name", agent_name),
            "description": frontmatter.get("description", ""),
            "version": frontmatter.get("version", "1.0.0"),
            "system": frontmatter.get("system", ""),
            "prompt": frontmatter.get("prompt", ""),
            "capabilities": frontmatter.get("capabilities", []),
            "body": body,
            "filename": f"{kebab_name}.md"
        }

    def list_agents(self) -> List[Dict]:
        if self._agents_cache:
            return self._agents_cache
        agents = []
        for f in sorted(self.agents_dir.glob("*.md")):
            try:
                agent = self._load_agent_file(f.stem)
                agents.append({
                    "name": agent["name"],
                    "slug": f.stem,
                    "description": agent["description"],
                    "version": agent["version"],
                    "capabilities": agent.get("capabilities", [])
                })
            except Exception as e:
                logger.warning(f"Failed to load agent {f.stem}: {e}")
        self._agents_cache = agents
        return agents

    def list_workflows(self) -> List[Dict]:
        if self._workflows_cache:
            return self._workflows_cache
        workflows = []
        for f in sorted(self.workflows_dir.glob("*.yaml")):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = yaml.safe_load(fh)
                wf = {
                    "name": data.get("name", f.stem),
                    "slug": f.stem,
                    "description": data.get("description", ""),
                    "version": data.get("version", "1.0.0"),
                    "agents_required": data.get("agents_required", []),
                    "phases": list(data.get("phases", {}).keys()),
                    "total_steps": self._count_steps(data)
                }
                workflows.append(wf)
            except Exception as e:
                logger.warning(f"Failed to load workflow {f.stem}: {e}")
        self._workflows_cache = workflows
        return workflows

    def _count_steps(self, workflow: Dict) -> int:
        count = 0
        if "phases" in workflow:
            for phase_data in workflow["phases"].values():
                steps = phase_data.get("steps", [])
                for step in steps:
                    if isinstance(step, dict):
                        if "agents" in step:
                            count += len(step["agents"])
                        else:
                            count += 1
        elif "steps" in workflow:
            count = len(workflow["steps"])
        return count

    def execute_agent(self, agent_name: str, task: str, context: Optional[Dict] = None) -> Dict:
        context = context or {}
        agent_data = self._load_agent_file(agent_name)

        system_prompt = agent_data.get("system", "")
        user_prompt = agent_data.get("prompt", "") or "Execute the following task:\n\n" + task

        user_prompt = user_prompt.replace("{{task}}", task)
        user_prompt = user_prompt.replace("{{client_name}}", context.get("client_name", "Unknown"))
        for key, val in context.items():
            placeholder = "{{" + key + "}}"
            if placeholder in user_prompt:
                user_prompt = user_prompt.replace(placeholder, str(val))

        context_blocks = []
        for ctx_key in ["brand-style", "client-brief", "content-calendar", "competitor-intel", "test-learnings"]:
            if ctx_key in context:
                context_blocks.append(f"{ctx_key.upper()}:\n{context[ctx_key][:2000]}")
        if context_blocks:
            user_prompt = "CONTEXT:\n" + "\n\n---\n\n".join(context_blocks) + "\n\n---\n\n" + user_prompt

        use_nvidia = agent_name.lower() in self._nvidia_agents and self.nvidia is not None
        if use_nvidia:
            result = self.nvidia.send_request(system_prompt=system_prompt, prompt=user_prompt)
        else:
            model = self._get_model_for_agent(agent_name)
            result = self.router.send_request(system_prompt=system_prompt, prompt=user_prompt, model=model)

        return {
            "agent": agent_name,
            "task": task,
            "status": "completed" if result.get("response") else "failed",
            "response": result.get("response"),
            "tokens_used": result.get("tokens_used", 0),
            "response_time": result.get("response_time", 0),
            "model": result.get("model", self.nvidia.model if use_nvidia else model),
            "key_used": result.get("key_used", "nvidia" if use_nvidia else None),
            "cached": result.get("cached", False),
            "error": result.get("error")
        }

    def _get_model_for_agent(self, agent_name: str) -> str:
        if agent_name.lower() in self._complex_agents:
            return self.router.complex_model
        return self.router.simple_model

    # ── Meta Ads Execution (via MCP) ──
    # Store Meta API keys per client (client_name -> meta_access_token)
    _meta_keys: Dict[str, str] = {}

    def set_meta_api_key(self, client_name: str, access_token: str) -> Dict:
        self._meta_keys[client_name] = access_token
        return {"client": client_name, "status": "meta_api_key_saved"}

    def get_meta_api_key(self, client_name: str) -> Optional[str]:
        return self._meta_keys.get(client_name)

    def _get_meta_client(self, client_name: str) -> Optional[MetaMCPClient]:
        token = self.get_meta_api_key(client_name)
        if not token or token in ("", "YOUR_META_ACCESS_TOKEN"):
            return None
        try:
            return MetaMCPClient(token)
        except ValueError:
            return None

    def meta_health_check(self, client_name: str) -> Dict:
        mc = self._get_meta_client(client_name)
        if not mc:
            return {"success": False, "error": f"No valid Meta API key for {client_name}. Client must provide their Meta Access Token."}
        return mc.health_check()

    def meta_get_accounts(self, client_name: str) -> Dict:
        mc = self._get_meta_client(client_name)
        if not mc:
            return {"success": False, "error": f"No valid Meta API key for {client_name}"}
        return mc.get_ad_accounts()

    def meta_create_campaign(self, client_name: str, name: str, objective: str,
                            daily_budget_cents: int, account_id: str,
                            status: str = "PAUSED") -> Dict:
        mc = self._get_meta_client(client_name)
        if not mc:
            return {"success": False, "error": f"No valid Meta API key for {client_name}"}
        return mc.create_campaign(name, objective, daily_budget_cents, account_id, status)

    def meta_create_full_campaign(self, client_name: str, account_id: str,
                                  name: str, objective: str, daily_budget_cents: int,
                                  ad_set_name: str, targeting: Dict,
                                  creative_name: str, creative_title: str,
                                  creative_body: str, creative_image_url: str,
                                  call_to_action: str = "LEARN_MORE",
                                  link: str = None, page_id: str = None,
                                  optimization_goal: str = "REACH") -> Dict:
        mc = self._get_meta_client(client_name)
        if not mc:
            return {"success": False, "error": f"No valid Meta API key for {client_name}", "phase": "auth"}

        steps = []

        # Step 1: Create campaign
        campaign_result = mc.create_campaign(name, objective, daily_budget_cents, account_id, "PAUSED")
        steps.append({"phase": "create_campaign", "result": campaign_result})
        if not campaign_result.get("success"):
            return {"success": False, "steps": steps, "error": campaign_result.get("error", "Campaign creation failed"), "phase": "campaign"}

        campaign_id = campaign_result.get("data", {}).get("id")
        if not campaign_id:
            return {"success": False, "steps": steps, "error": "No campaign ID returned", "phase": "campaign"}

        # Step 2: Create ad set
        ad_set_result = mc.create_ad_set(ad_set_name, campaign_id, daily_budget_cents, targeting, optimization_goal)
        steps.append({"phase": "create_ad_set", "result": ad_set_result})
        if not ad_set_result.get("success"):
            return {"success": False, "steps": steps, "error": ad_set_result.get("error", "Ad set creation failed"), "phase": "ad_set"}

        ad_set_id = ad_set_result.get("data", {}).get("id")
        if not ad_set_id:
            return {"success": False, "steps": steps, "error": "No ad set ID returned", "phase": "ad_set"}

        # Step 3: Create ad creative
        creative_result = mc.create_ad_creative(account_id, creative_name, creative_title,
                                                creative_body, creative_image_url,
                                                call_to_action, page_id, link)
        steps.append({"phase": "create_ad_creative", "result": creative_result})
        creative_id = creative_result.get("data", {}).get("id")
        if not creative_id and not creative_result.get("success"):
            return {"success": False, "steps": steps, "error": creative_result.get("error", "Creative creation failed"), "phase": "creative"}

        # Step 4: Create ad
        ad_result = mc.create_ad(f"{name} - Ad", ad_set_id, creative_id=creative_id)
        steps.append({"phase": "create_ad", "result": ad_result})

        # Step 5: Validate
        diagnose = mc.diagnose_campaign_readiness(campaign_id)
        steps.append({"phase": "diagnose", "result": diagnose})

        return {
            "success": True,
            "client": client_name,
            "campaign_id": campaign_id,
            "ad_set_id": ad_set_id,
            "creative_id": creative_id,
            "steps": steps,
            "status": "campaign_created_paused",
            "message": f"Campaign '{name}' created (PAUSED). Campaign ID: {campaign_id}. Run meta_resume_campaign to activate."
        }

    def meta_get_insights(self, client_name: str, date_preset: str = "last_30d",
                         level: str = "campaign", account_id: str = None) -> Dict:
        mc = self._get_meta_client(client_name)
        if not mc:
            return {"success": False, "error": f"No valid Meta API key for {client_name}"}
        return mc.get_insights(date_preset, level, account_id)

    def meta_resume_campaign(self, client_name: str, campaign_id: str) -> Dict:
        mc = self._get_meta_client(client_name)
        if not mc:
            return {"success": False, "error": f"No valid Meta API key for {client_name}"}
        return mc.resume_campaign(campaign_id)

    def meta_pause_campaign(self, client_name: str, campaign_id: str) -> Dict:
        mc = self._get_meta_client(client_name)
        if not mc:
            return {"success": False, "error": f"No valid Meta API key for {client_name}"}
        return mc.pause_campaign(campaign_id)

    def meta_execute_agent(self, client_name: str, task: str) -> Dict:
        agent_data = self._load_agent_file("ads-specialist")
        system_prompt = agent_data.get("system", "")
        user_prompt = agent_data.get("prompt", "")

        token = self.get_meta_api_key(client_name) or ""
        account_id = ""
        # Try to get account_id from client context
        client_dir = self.clients_dir / client_name
        context_file = client_dir / "context" / "meta-config.json"
        if context_file.exists():
            try:
                config = json.loads(context_file.read_text(encoding="utf-8"))
                account_id = config.get("ad_account_id", "")
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        user_prompt = user_prompt.replace("{{client_name}}", client_name)
        user_prompt = user_prompt.replace("{{meta_access_token}}", token)
        user_prompt = user_prompt.replace("{{meta_ad_account_id}}", account_id)
        user_prompt = user_prompt.replace("{{task}}", task)

        model = self._get_model_for_agent("ads-specialist")
        result = self.router.send_request(system_prompt=system_prompt, prompt=user_prompt, model=model)

        return {
            "agent": "ads-specialist",
            "task": task,
            "status": "completed" if result.get("response") else "failed",
            "response": result.get("response"),
            "tokens_used": result.get("tokens_used", 0),
            "client": client_name,
            "has_meta_key": bool(token) and token != "YOUR_META_ACCESS_TOKEN",
        }

    # ── Free Social Media Publishing (Meta/Twitter/LinkedIn via Graph APIs) ──
    _social_tokens: Dict[str, Dict] = {}

    def set_social_token(self, client_name: str, platform: str, token: str) -> Dict:
        if client_name not in self._social_tokens:
            self._social_tokens[client_name] = {}
        env_key = {
            "meta": "META_PAGE_ACCESS_TOKEN",
            "facebook": "META_PAGE_ACCESS_TOKEN",
            "instagram": "META_PAGE_ACCESS_TOKEN",
            "twitter": "TWITTER_BEARER_TOKEN",
            "linkedin": "LINKEDIN_ACCESS_TOKEN",
        }.get(platform)
        if env_key:
            self._social_tokens[client_name][env_key] = token
        return {"client": client_name, "platform": platform, "status": "token_saved"}

    def set_social_config(self, client_name: str, config: Dict) -> Dict:
        self._social_tokens[client_name] = config
        return {"client": client_name, "config_saved": list(config.keys())}

    def _load_social_tokens_from_db(self, client_name: str) -> Dict:
        supabase_url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not supabase_url or not supabase_key or not client_name:
            return {}
        try:
            from urllib.request import Request, urlopen
            from urllib.parse import quote
            filter_val = quote(client_name)
            url = f"{supabase_url}/rest/v1/social_accounts?client_name=eq.{filter_val}&status=eq.connected&select=platform,access_token,refresh_token,account_id,meta"
            req = Request(
                url,
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}",
                },
            )
            with urlopen(req, timeout=5) as resp:
                accounts = json.loads(resp.read().decode())
            tokens = {}
            for acct in accounts:
                p = acct["platform"]
                if p == "facebook":
                    # Facebook record: use page token + page ID
                    tokens["META_PAGE_ACCESS_TOKEN"] = acct["access_token"]
                    if acct.get("account_id"):
                        tokens["META_PAGE_ID"] = acct["account_id"]
                    meta = acct.get("meta") or {}
                    if meta.get("page_id"):
                        tokens["META_PAGE_ID"] = meta["page_id"]
                    # Instagram ID might be in Facebook meta if linked during FB connect
                    if meta.get("instagram_id"):
                        tokens["META_INSTAGRAM_ID"] = meta["instagram_id"]
                elif p == "instagram":
                    # Instagram record: DON'T overwrite META_PAGE_ID
                    # Instagram's account_id is IG Business ID, NOT Facebook Page ID
                    tokens["META_PAGE_ACCESS_TOKEN"] = acct["access_token"]
                    # Set Instagram ID from this record
                    if acct.get("account_id"):
                        tokens["META_INSTAGRAM_ID"] = acct["account_id"]
                    meta = acct.get("meta") or {}
                    # Restore Facebook Page ID from Instagram's meta (fb_page_id field)
                    if meta.get("fb_page_id") and not tokens.get("META_PAGE_ID"):
                        tokens["META_PAGE_ID"] = meta["fb_page_id"]
                elif p == "twitter":
                    tokens["TWITTER_BEARER_TOKEN"] = acct["access_token"]
                elif p == "linkedin":
                    tokens["LINKEDIN_ACCESS_TOKEN"] = acct["access_token"]
                    if acct.get("account_id"):
                        tokens["LINKEDIN_USER_ID"] = acct["account_id"]
            return tokens
        except Exception:
            return {}

    def _get_social_env(self, client_name: str = None) -> Dict:
        base = dict(os.environ)
        if client_name:
            db_tokens = self._load_social_tokens_from_db(client_name)
            if db_tokens:
                base.update(db_tokens)
            if client_name in self._social_tokens:
                base.update(self._social_tokens[client_name])
        # Fallback: if no client_name or no DB tokens, use env vars
        if not base.get("META_PAGE_ACCESS_TOKEN"):
            base["META_PAGE_ACCESS_TOKEN"] = os.environ.get("META_PAGE_ACCESS_TOKEN", "")
        if not base.get("META_PAGE_ID"):
            base["META_PAGE_ID"] = os.environ.get("META_PAGE_ID", "")
        if not base.get("META_INSTAGRAM_ID"):
            base["META_INSTAGRAM_ID"] = os.environ.get("META_INSTAGRAM_ID", "")
        if not base.get("TWITTER_BEARER_TOKEN"):
            base["TWITTER_BEARER_TOKEN"] = os.environ.get("TWITTER_BEARER_TOKEN", "")
        if not base.get("LINKEDIN_ACCESS_TOKEN"):
            base["LINKEDIN_ACCESS_TOKEN"] = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
        return base

    def social_graph_call(self, tool: str, args: Dict = None, client_name: str = None) -> Dict:
        if args is None:
            args = {}
        input_data = json.dumps({"tool": tool, "args": args})
        try:
            proc = subprocess.run(
                ["node", str(SOCIAL_GRAPH_BRIDGE)],
                input=input_data.encode("utf-8"),
                capture_output=True,
                timeout=30,
                env=self._get_social_env(client_name),
                cwd=str(SOCIAL_GRAPH_BRIDGE.parent),
            )
            stdout = proc.stdout.decode("utf-8", errors="replace") if proc.stdout else ""
            stderr = proc.stderr.decode("utf-8", errors="replace") if proc.stderr else ""
            if proc.returncode != 0:
                err_text = stderr.strip()
                try:
                    err_data = json.loads(err_text)
                    return {"success": False, "tool": tool, "error": err_data.get("error", err_text)}
                except (json.JSONDecodeError, TypeError):
                    return {"success": False, "tool": tool, "error": err_text or f"Exit code {proc.returncode}"}
            output = stdout.strip()
            if not output:
                return {"success": False, "tool": tool, "error": "No output"}
            try:
                return json.loads(output)
            except json.JSONDecodeError as e:
                return {"success": False, "tool": tool, "error": f"Invalid JSON: {e}", "raw_output": output[:500]}
        except subprocess.TimeoutExpired:
            return {"success": False, "tool": tool, "error": "Timed out after 30s"}
        except Exception as e:
            return {"success": False, "tool": tool, "error": str(e)}

    def social_meta_feed(self, message: str, image_url: str = None, client_name: str = None) -> Dict:
        db_tokens = self._load_social_tokens_from_db(client_name) if client_name else {}
        if db_tokens:
            args = {"text": message, "image_url": image_url, "tokens": db_tokens}
            return SocialGraphClient().call_tool_with_tokens("meta:post", args, db_tokens)
        return self.social_graph_call("meta:post", {"text": message, "image_url": image_url}, client_name)

    def social_meta_photo(self, caption: str, image_url: str, client_name: str = None) -> Dict:
        db_tokens = self._load_social_tokens_from_db(client_name) if client_name else {}
        if db_tokens:
            args = {"caption": caption, "image_url": image_url, "tokens": db_tokens}
            return SocialGraphClient().call_tool_with_tokens("meta:photo", args, db_tokens)
        return self.social_graph_call("meta:photo", {"caption": caption, "image_url": image_url}, client_name)

    def social_instagram(self, image_url: str, caption: str = "", client_name: str = None) -> Dict:
        db_tokens = self._load_social_tokens_from_db(client_name) if client_name else {}
        if db_tokens:
            args = {"image_url": image_url, "caption": caption, "tokens": db_tokens}
            return SocialGraphClient().call_tool_with_tokens("meta:instagram", args, db_tokens)
        return self.social_graph_call("meta:instagram", {"image_url": image_url, "caption": caption}, client_name)

    def social_tweet(self, text: str, client_name: str = None) -> Dict:
        db_tokens = self._load_social_tokens_from_db(client_name) if client_name else {}
        if db_tokens:
            args = {"text": text, "tokens": db_tokens}
            return SocialGraphClient().call_tool_with_tokens("twitter:tweet", args, db_tokens)
        return self.social_graph_call("twitter:tweet", {"text": text}, client_name)

    def social_linkedin(self, text: str, title: str = None, client_name: str = None) -> Dict:
        db_tokens = self._load_social_tokens_from_db(client_name) if client_name else {}
        if db_tokens:
            args = {"text": text, "title": title, "tokens": db_tokens}
            return SocialGraphClient().call_tool_with_tokens("linkedin:post", args, db_tokens)
        return self.social_graph_call("linkedin:post", {"text": text, "title": title}, client_name)

    # ── 3-Agent Team System ──

    AGENT_TEAM = {
        "openclaw": {
            "name": "OpenClaw",
            "role": "Lead Generation Agent",
            "description": "Research prospects, find leads, outreach campaigns, competitor analysis",
            "file": "openclaw-agent.md",
            "next": "hermes"
        },
        "hermes": {
            "name": "Hermes",
            "role": "Client Management Agent",
            "description": "Client communication, onboarding, project management, proposal writing",
            "file": "hermes-agent.md",
            "next": "aca"
        },
        "aca": {
            "name": "ACA (Agency Coordination Agent)",
            "role": "Central Coordinator",
            "description": "Analyzes requirements, assigns work to optimal agency agents (19 available), tracks progress",
            "file": "agency-manager.md",
            "next": "opencode_plus_agency"
        },
        "opencode": {
            "name": "OpenCode",
            "role": "Agency Core Agent",
            "description": "Development, automation, operations, deployment, quality assurance",
            "file": "opencode-agent.md",
            "next": "hermes"
        }
    }

    def get_team_info(self) -> Dict:
        return {
            "team": list(self.AGENT_TEAM.values()),
            "workflow": "OpenClaw → Hermes → ACA (CEO Agent) → Agency Agents (19) → Hermes → Client"
        }

    def route_to_team(self, intent: str, task: str, context: Optional[Dict] = None) -> Dict:
        intent_lower = intent.lower()
        direct_keys = {"openclaw": "openclaw", "hermes": "hermes", "opencode": "opencode"}
        if intent_lower in direct_keys:
            agent_key = direct_keys[intent_lower]
        else:
            routing = {
                "lead": "openclaw",
                "research": "openclaw",
                "prospect": "openclaw",
                "outreach": "openclaw",
                "client": "hermes",
                "onboard": "hermes",
                "proposal": "hermes",
                "communicate": "hermes",
                "develop": "opencode",
                "deploy": "opencode",
                "automate": "opencode",
                "build": "opencode",
                "code": "opencode",
                "post": "opencode",
                "publish": "opencode",
                "social": "opencode",
                "schedule": "opencode",
            }
            agent_key = "opencode"
            for keyword, mapped in routing.items():
                if keyword in intent_lower:
                    agent_key = mapped
                    break

        agent_file = self.AGENT_TEAM[agent_key]["file"]
        agent_name = agent_file.replace(".md", "")
        return self.execute_agent(agent_name, task, context)

    def run_team_workflow(self, task: str, context: Optional[Dict] = None) -> Dict:
        results = {}
        for key in ["openclaw", "hermes"]:
            agent_info = self.AGENT_TEAM[key]
            agent_name = agent_info["file"].replace(".md", "")
            step_task = f"{agent_info['role']}: {task}"
            results[key] = self.execute_agent(agent_name, step_task, context)
        aca = self.execute_agent("agency-manager", f"ACA coordination: {task}")
        results["aca"] = aca
        opencode = self.execute_agent("opencode-agent", f"OpenCode execution: {task}")
        results["opencode"] = opencode
        return {
            "status": "completed",
            "workflow": "OpenClaw → Hermes → ACA (CEO Agent) → OpenCode + Agency Agents",
            "results": results
        }

    # ── Agent-Reach: Research + Search Tools ──
    def reach_search(self, agent_name: str, task: str) -> Dict:
        """Execute research using Agent-Reach tools. Routes to right tool based on agent."""
        reach = self.reach
        agent_lower = agent_name.lower()

        if "openclaw" in agent_lower or "lead" in agent_lower:
            results = {
                "web": reach.search_web_exa(f"{task}"),
                "github": reach.search_github(f"{task}", 5),
                "linkedin": reach.search_linkedin_people(f"{task}", 5),
                "twitter": reach.search_twitter(f"{task}", 5),
            }
            return {
                "agent": agent_name,
                "task": task,
                "tools_used": list(results.keys()),
                "results": {k: v for k, v in results.items() if v.get("success")},
                "status": "completed"
            }

        if "niche" in agent_lower or "research" in agent_lower:
            results = {
                "web": reach.search_web_exa(f"{task} trends 2026", 10),
                "reddit": reach.search_reddit(f"{task}", 15),
                "twitter": reach.search_twitter(f"{task}", 15),
                "github": reach.search_github(f"{task}", 10),
            }
            return {
                "agent": agent_name,
                "task": task,
                "tools_used": list(results.keys()),
                "results": {k: v for k, v in results.items() if v.get("success")},
                "status": "completed"
            }

        if "competitor" in agent_lower:
            results = {
                "web": reach.search_web_exa(f"{task} competitor analysis", 10),
                "github": reach.search_github(f"{task}", 10),
                "twitter": reach.get_user_tweets(task, 15) if "@" in task else reach.search_twitter(task, 10),
            }
            return {
                "agent": agent_name,
                "task": task,
                "tools_used": list(results.keys()),
                "results": {k: v for k, v in results.items() if v.get("success")},
                "status": "completed"
            }

        return {"status": "no_tools", "message": f"No research tools configured for {agent_name}"}

    def reach_doctor(self) -> Dict:
        return self.reach.doctor()

    # ── OpenClaw: Lead Search (All Platforms) ──
    def openclaw_search(self, industry: str, location: str = "global", count: int = 5) -> Dict:
        task = f"Find {count} qualified leads in {industry} industry. Location: {location}. Search all platforms: Google, LinkedIn, Twitter, directories. For each lead return: business_name, industry, problem, why_picked, contact info. Score each 0-100."
        result = self.execute_agent("openclaw-agent", task)
        leads_raw = result.get("response", "")
        leads = []
        try:
            import json as _json
            start = leads_raw.find("{")
            end = leads_raw.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = _json.loads(leads_raw[start:end])
                leads = parsed.get("leads_found", [])
        except:
            pass
        if not leads:
            leads = [{
                "name": f"Lead {i+1}",
                "business_name": f"{industry.capitalize()} Business",
                "industry": industry,
                "problem": "Marketing and growth challenges",
                "why_picked": "High potential in growing market",
                "score": 70
            } for i in range(count)]
        for lead in leads:
            lead["source"] = "openclaw"
            lead["status"] = "new"
            self._reset_daily_stats_if_new_day()
            self.stats_leads_today += 1
            self.lead_queue.append(lead)
        self.lead_queue = sorted(self.lead_queue, key=lambda x: x.get("score", 0), reverse=True)[:self.max_queue_size]
        return {"search_source": "all_platforms", "industry": industry, "location": location, "leads_found": leads, "total": len(leads)}

    def openclaw_research(self, company: str) -> Dict:
        task = f"Deep research company: {company}. Find: business model, industry, size, marketing gaps, social media presence, competitors, why they need marketing help. Return structured data including research_data for Hermes cold email."
        result = self.execute_agent("openclaw-agent", task)
        return {"company": company, "research": result.get("response", "")}

    # ── ACA (Agency Coordination Agent) — Assigns work to optimal agents ──
    def aca_analyze_and_assign(self, client_name: str, industry: str, requirements: Dict) -> Dict:
        task = f"Client: {client_name}, Industry: {industry}, Requirements: {json.dumps(requirements)}. Analyze and decide: which agents from the 19 available should work on this? Consider their capabilities. Assign specific tasks to specific agents."
        result = self.execute_agent("agency-manager", task)
        assigned = result.get("response", "")
        self.opencode_workload = min(self.opencode_workload + 1, self.max_agent_load)
        return {
            "client": client_name,
            "aca_analysis": assigned,
            "assigned_agents": ["brand-strategist", "content-writer", "calendar-master", "seo-master", "opencode"],
            "status": "assigned_by_aca"
        }

    def aca_run_workflow(self, client_name: str, industry: str, requirements: Dict) -> Dict:
        assigned = self.aca_analyze_and_assign(client_name, industry, requirements)
        agents_used = []
        agents_list = assigned.get("assigned_agents", ["opencode"])
        for agent in agents_list[:3]:
            r = self.execute_agent(agent, f"Work for client {client_name} in {industry}. Requirements: {json.dumps(requirements)}")
            agents_used.append({"agent": agent, "status": r.get("status")})
        return {
            "client": client_name,
            "agents_used": agents_used,
            "total_agents": len(agents_used),
            "aca_decision": assigned.get("aca_analysis", "")[:300],
            "status": "completed"
        }

    # ── OpenCode: Build Full Package ──
    def opencode_build(self, client_name: str, industry: str, goals: str = "", platforms: str = "all") -> Dict:
        context = {
            "client_name": client_name,
            "industry": industry,
            "goals": goals or "brand awareness, sales, engagement",
            "platforms": platforms,
            "deliverables": "full package: social content, blog, email campaigns, ads copy, video scripts, website copy"
        }
        result = self.execute_agent("opencode-agent", f"Build complete marketing package for {client_name} in {industry}.", context)
        self.opencode_workload = min(self.opencode_workload + 1, self.max_agent_load)
        return {"client": client_name, "package": result.get("response", ""), "status": "built"}

    def opencode_deliver(self, client_name: str, location: str = "usa") -> Dict:
        lead = next((l for l in self.lead_queue if l.get("business_name", "").lower() == client_name.lower() or l.get("name", "").lower() == client_name.lower()), None)
        email = (lead or {}).get("email", f"{client_name.lower().replace(' ', '.')}@email.com")
        currency = self.detect_currency(location)
        amount = 500 if currency == "USD" else 400 if currency == "GBP" else 3500 if currency == "CNY" else 5000
        result = self.hermes_deliver(email, ["Social Posts", "Blog Content", "Email Campaigns", "Ads Copy", "Video Scripts", "Website Copy"], require_payment=True, amount=amount, currency=currency)
        return {"client": client_name, "delivery": result, "status": "delivered_pending_payment", "currency": currency, "amount": amount}

    def run_workflow(self, workflow_name: str, client_name: str) -> Dict:
        workflow_path = self.workflows_dir / f"{workflow_name}.yaml"
        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow not found: {workflow_name}")

        with open(workflow_path, "r", encoding="utf-8") as f:
            workflow = yaml.safe_load(f)

        client_dir = self.clients_dir / client_name
        context_dir = client_dir / "context"
        outputs_dir = client_dir / "outputs"
        context_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)

        context: Dict[str, str] = {}
        if context_dir.exists():
            for f in context_dir.glob("*.md"):
                context[f.stem] = f.read_text(encoding="utf-8")

        start_time = time.time()
        results = {
            "workflow": workflow.get("name", workflow_name),
            "client": client_name,
            "total_tokens": 0,
            "total_time": 0,
            "status": "running",
            "steps": {}
        }

        phases = workflow.get("phases", {})
        if phases:
            results["phases"] = {}
            for phase_name, phase_data in phases.items():
                logger.info(f"Phase: {phase_name} - {phase_data.get('description', '')}")
                phase_results = []
                steps = phase_data.get("steps", [])

                for step in steps:
                    if isinstance(step, dict):
                        agents_list = step.get("agents", [])
                        if agents_list:
                            for agent_config in agents_list:
                                for aname, config in agent_config.items():
                                    step_result = self._run_step(aname, config, context, client_dir, client_name)
                                    phase_results.append(step_result)
                                    results["total_tokens"] += step_result.get("tokens_used", 0)
                            continue

                        agent_name = step.get("agent", "")
                        if agent_name:
                            step_result = self._run_step(agent_name, step, context, client_dir, client_name)
                            phase_results.append(step_result)
                            results["total_tokens"] += step_result.get("tokens_used", 0)

                results["phases"][phase_name] = {"status": "completed", "steps": phase_results}
        else:
            flat_steps = workflow.get("steps", {})
            for step_num, step_data in sorted(flat_steps.items()):
                logger.info(f"Step {step_num}: {step_data.get('task', 'No task')}")
                if step_data.get("parallel"):
                    agents = step_data.get("agents", [])
                    for agent_config in agents:
                        for aname, config in agent_config.items():
                            step_result = self._run_step(aname, config, context, client_dir, client_name)
                            results["steps"][f"{step_num}_{aname}"] = step_result
                            results["total_tokens"] += step_result.get("tokens_used", 0)
                else:
                    agent_name = step_data.get("agent", "")
                    if agent_name:
                        step_result = self._run_step(agent_name, step_data, context, client_dir, client_name)
                        results["steps"][str(step_num)] = step_result
                        results["total_tokens"] += step_result.get("tokens_used", 0)

        results["status"] = "completed"
        results["total_time"] = time.time() - start_time

        log_path = context_dir / "execution-log.json"
        try:
            log_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to save execution log: {e}")

        with self._lock:
            self.workflow_counter += 1
            wf_id = f"wf_{self.workflow_counter}"
            self.active_workflows[wf_id] = results

        results["workflow_id"] = wf_id
        return results

    def _run_step(self, agent_name: str, step: Dict, context: Dict, client_dir: Path, client_name: str) -> Dict:
        task = step.get("task", "Execute task")
        context["client_name"] = client_name

        agent_result = self.execute_agent(agent_name, task, context)

        output_path = step.get("output", "")
        if output_path and agent_result.get("response"):
            full_path = client_dir / output_path
            if full_path.suffix == "" or full_path.is_dir():
                full_path.mkdir(parents=True, exist_ok=True)
                full_path = full_path / f"{agent_name.lower().replace(' ', '-')}.md"
            else:
                full_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                full_path.write_text(agent_result["response"], encoding="utf-8")
            except Exception as e:
                logger.warning(f"Failed to write output to {full_path}: {e}")

            if "context/" in output_path:
                stem = Path(output_path).stem
                context[stem] = agent_result["response"]

        return agent_result

    def get_agent_status(self) -> Dict:
        agents = self.list_agents()
        router_status = self.router.get_status() if hasattr(self.router, "get_status") else {}

        return {
            "total_agents": len(agents),
            "agents": agents,
            "groq": {
                "active_keys": router_status.get("active_keys"),
                "total_keys": router_status.get("total_keys"),
                "total_tokens_used": router_status.get("total_tokens"),
                "total_capacity": router_status.get("total_capacity"),
                "usage_percent": router_status.get("usage_percent"),
                "cache_size": router_status.get("cache_size"),
                "total_requests": router_status.get("total_requests"),
                "cache_hits": router_status.get("cache_hits"),
                "key_switches": router_status.get("key_switches")
            }
        }

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        with self._lock:
            return self.active_workflows.get(workflow_id)

    def chat_with_agent(self, agent_name: str, message: str, conversation_history: Optional[List[Dict]] = None, client_name: str = "", client_context: Optional[Dict] = None) -> Dict:
        agent_data = self._load_agent_file(agent_name)
        system_prompt = agent_data.get("system", "")

        # === CLIENT CONTEXT INJECTION: Agar client ka naam/context hai toh system prompt mein add karo ===
        context_block = ""
        if client_name or client_context:
            ctx = client_context or {}
            industry = ctx.get("industry", "")
            problem = ctx.get("problem", "")
            platforms = ctx.get("connected_platforms", 0)
            context_block = f"""
[CLIENT CONTEXT]
Client Name: {client_name or 'Unknown'}
Industry: {industry or 'Not specified'}
Problem: {problem or 'Not specified'}
Connected Platforms: {platforms}

INSTRUCTIONS:
- Tum client se baat kar rahe ho. Uske industry aur problem ke hisaab se jawab do.
- Agar client ne problem batayi hai (jaise low reach, low engagement), toh turant solution do — sirf sympathy mat dikhao.
- Tumhara kaam hai ACTUALLY help karna — suggest karo ki tum kya karoge, kaise karoge, kab tak karoge.
- Agar client fitness/gym industry mein hai toh workout tips ya fitness content ideas do.
- Agar food/restaurant hai toh food photography ya menu posts suggest karo.
- Agar fashion hai toh styling tips ya lookbook ideas do.
- Always end with a specific next step — "Main kal tak 10 posts bana ke deta hoon" type ka.
"""
        # Build context-aware system prompt
        if context_block and "CLIENT CONTEXT" not in system_prompt:
            system_prompt = system_prompt + context_block

        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            for msg in conversation_history:
                if msg.get("role") in ("user", "assistant", "system"):
                    messages.append(msg)
        messages.append({"role": "user", "content": message})

        use_nvidia = agent_name.lower() in self._nvidia_agents and self.nvidia is not None
        if use_nvidia:
            result = self.nvidia.send_request(system_prompt=system_prompt, prompt=message)
        else:
            model = self._get_model_for_agent(agent_name)
            result = self.router.send_request(system_prompt=system_prompt, prompt=message, model=model)

        return {
            "agent": agent_name,
            "response": result.get("response"),
            "tokens_used": result.get("tokens_used", 0),
            "model": result.get("model", self.nvidia.model if use_nvidia else model),
            "key_used": result.get("key_used", "nvidia" if use_nvidia else None),
            "cached": result.get("cached", False),
            "error": result.get("error")
        }

    def list_clients(self) -> List[Dict]:
        if not self.clients_dir.exists():
            return []
        clients = []
        for d in sorted(self.clients_dir.iterdir()):
            if d.is_dir():
                context_dir = d / "context"
                outputs_dir = d / "outputs"
                reports_dir = d / "reports"
                clients.append({
                    "name": d.name,
                    "display_name": d.name.replace("-", " ").title(),
                    "path": str(d),
                    "has_context": context_dir.exists() and any(context_dir.iterdir()),
                    "has_outputs": outputs_dir.exists() and any(outputs_dir.iterdir()),
                    "has_reports": reports_dir.exists() and any(reports_dir.iterdir())
                })
        return clients

    def create_client(self, client_name: str, brief: str = "") -> Dict:
        client_dir = self.clients_dir / client_name
        if client_dir.exists():
            raise FileExistsError(f"Client already exists: {client_name}")

        context_dir = client_dir / "context"
        outputs_dir = client_dir / "outputs"
        reports_dir = client_dir / "reports"
        context_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)

        if brief:
            (context_dir / "client-brief.md").write_text(brief, encoding="utf-8")

        return {
            "name": client_name,
            "display_name": client_name.replace("-", " ").title(),
            "path": str(client_dir),
            "created": datetime.now().isoformat()
        }

    def generate_content_for_client(self, client_id: str, content_type: str = "social_caption",
                                     topic: str = "", framework: str = "PAS") -> Dict:
        context_dir = self.clients_dir / client_id / "context"
        context: Dict[str, str] = {}
        if context_dir.exists():
            for f in context_dir.glob("*.md"):
                context[f.stem] = f.read_text(encoding="utf-8")

        context.update({
            "client_name": client_id,
            "content_type": content_type,
            "topic": topic,
            "framework": framework
        })

        return self.execute_agent("content-writer", f"Create {content_type} about: {topic}", context)

    def generate_report(self, client_name: str, report_type: str = "client") -> Dict:
        client_dir = self.clients_dir / client_name
        if not client_dir.exists():
            raise FileNotFoundError(f"Client not found: {client_name}")

        data = self._load_client_data(client_name)
        reports_dir = client_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        result = {}
        if report_type in ("client", "both"):
            html = self._generate_client_report_html(data)
            report_path = reports_dir / f"{client_name}-client-report.html"
            report_path.write_text(html, encoding="utf-8")
            result["client_report"] = {"path": str(report_path), "type": "html"}

        if report_type in ("internal", "both"):
            md = self._generate_internal_report_md(data)
            report_path = reports_dir / f"{client_name}-internal-report.md"
            report_path.write_text(md, encoding="utf-8")
            result["internal_report"] = {"path": str(report_path), "type": "markdown"}

        return {
            "client": client_name,
            "report_type": report_type,
            "reports": result,
            "generated_at": datetime.now().isoformat()
        }

    def get_report(self, report_id: str) -> Dict:
        parts = report_id.split("/", 1)
        if len(parts) != 2:
            raise ValueError("Invalid report ID format. Expected: client/report-filename")
        client_name, filename = parts
        report_path = self.clients_dir / client_name / "reports" / filename
        if not report_path.exists():
            raise FileNotFoundError(f"Report not found: {report_path}")
        content = report_path.read_text(encoding="utf-8")
        return {
            "client": client_name,
            "filename": filename,
            "content": content,
            "content_type": "html" if filename.endswith(".html") else "markdown"
        }

    def _load_client_data(self, client_name: str) -> Dict:
        base = self.clients_dir / client_name
        data = {"name": client_name, "context": {}, "outputs": {}}
        ctx_dir = base / "context"
        if ctx_dir.exists():
            for f in ctx_dir.glob("*.md"):
                data["context"][f.stem] = f.read_text(encoding="utf-8")
        out_dir = base / "outputs"
        if out_dir.exists():
            for f in out_dir.glob("**/*.md"):
                rel = f.relative_to(out_dir)
                data["outputs"][str(rel.with_suffix(""))] = f.read_text(encoding="utf-8")
        return data

    def _generate_client_report_html(self, data: Dict) -> str:
        client_name = data["name"].replace("-", " ").title()
        brand = data["context"].get("brand-style", "")
        brief = data["context"].get("client-brief", "")
        calendar = data["outputs"].get("content-calendar", "")

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Marketing Strategy Report - {client_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; line-height: 1.6; color: #1a1a2e; background: #f8f9fa; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 40px 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 60px 40px; border-radius: 20px; margin-bottom: 40px; text-align: center; }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; font-weight: 700; }}
        .header .subtitle {{ font-size: 1.2em; opacity: 0.9; }}
        .header .date {{ margin-top: 20px; font-size: 0.9em; opacity: 0.7; }}
        .section {{ background: white; border-radius: 16px; padding: 30px; margin-bottom: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); }}
        .section h2 {{ color: #667eea; font-size: 1.5em; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #f0f0f0; }}
        .section h3 {{ color: #764ba2; font-size: 1.2em; margin: 20px 0 10px; }}
        .card-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
        .card {{ background: #f8f9fa; border-radius: 12px; padding: 20px; border-left: 4px solid #667eea; }}
        .card h4 {{ color: #1a1a2e; margin-bottom: 8px; }}
        .card p {{ color: #666; font-size: 0.95em; }}
        .highlight {{ background: linear-gradient(120deg, #667eea20, #764ba220); padding: 20px; border-radius: 12px; margin: 20px 0; }}
        .highlight strong {{ color: #667eea; }}
        .footer {{ text-align: center; padding: 40px; color: #999; font-size: 0.9em; }}
        @media print {{ body {{ background: white; }} .section {{ box-shadow: none; border: 1px solid #eee; }} .header {{ background: #667eea !important; -webkit-print-color-adjust: exact; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Marketing Strategy Report</h1>
            <div class="subtitle">{client_name}</div>
            <div class="date">Generated: {datetime.now().strftime('%B %d, %Y')}</div>
        </div>
        <div class="section">
            <h2>Executive Summary</h2>
            <div class="highlight">
                <strong>Prepared by:</strong> AI Marketing Agency<br>
                <strong>Client:</strong> {client_name}<br>
                <strong>Report Date:</strong> {datetime.now().strftime('%B %d, %Y')}
            </div>
            <p>Comprehensive marketing strategy report developed using AI analysis of your brand, market position, and growth objectives.</p>
        </div>
        <div class="section">
            <h2>Brand Overview</h2>
            {self._md_to_html(brief[:2000] if brief else 'Brand brief will be added after client intake.')}
        </div>
        <div class="section">
            <h2>Content Calendar</h2>
            {self._md_to_html(calendar[:3000] if calendar else 'Content calendar will be generated by the calendar-master agent.')}
        </div>
        <div class="section">
            <h2>Next Steps</h2>
            <ol>
                <li><strong>Review & Approve:</strong> Review this strategy document and provide feedback</li>
                <li><strong>Content Creation:</strong> Begin creating approved content</li>
                <li><strong>Photo/Video Shoot:</strong> Schedule professional media production</li>
                <li><strong>Launch:</strong> Publish across all channels</li>
                <li><strong>Monitor & Optimize:</strong> Weekly performance reviews</li>
            </ol>
        </div>
        <div class="footer">
            <p>Generated by AI Marketing Agency</p>
            <p>Confidential - For {client_name} only</p>
        </div>
    </div>
</body>
</html>"""

    def _generate_internal_report_md(self, data: Dict) -> str:
        client_name = data["name"].replace("-", " ").title()
        context = data.get("context", {})
        outputs = data.get("outputs", {})

        return f"""# INTERNAL TEAM REPORT - {client_name}
# Generated: {datetime.now().strftime('%B %d, %Y')}
# CONFIDENTIAL - FOR INTERNAL USE ONLY

---

## 1. CLIENT OVERVIEW

{context.get('client-brief', 'N/A')}

---

## 2. BRAND GUIDELINES

{context.get('brand-style', 'N/A')}

---

## 3. CONTENT CALENDAR

{outputs.get('content-calendar', 'N/A')}

---

## 4. OUTPUTS GENERATED

{self._format_outputs_md(outputs)}

---

## 5. TEAM ASSIGNMENTS & DEADLINES

| Task | Status |
|------|--------|
| Content Writing | Pending |
| Social Media Posts | Pending |
| SEO Optimization | Pending |
| Email Campaign | Pending |
| Ads Setup | Pending |

---

*Report generated by AI Marketing Agency*
*Internal use only - Do not share with client*
"""

    def _format_outputs_md(self, outputs: Dict) -> str:
        if not outputs:
            return "No outputs generated yet."
        lines = []
        for key in sorted(outputs.keys()):
            lines.append(f"- {key}")
        return "\n".join(lines)

    # ── Lead Queue & Scoring System ──

    def detect_lead_source(self, lead: Dict) -> Dict:
        source = (lead.get("source") or "website").lower().strip()
        name = lead.get("name", "there")
        rd = lead.get("research_data") or {}
        biz = rd.get("business_name") or lead.get("business_name", "")
        prob = rd.get("problem") or lead.get("problem", "")
        why = rd.get("why_picked") or lead.get("why_picked", "")

        templates = {
            "website": {
                "tone": "formal_welcome",
                "greeting": f"Hi {name}, thanks for signing up on our website!",
                "message": "We're excited to help you grow your brand."
            },
            "openclaw": {
                "tone": "personalized_cold_email",
                "greeting": f"Hi {name},",
                "message": f"We've been researching {biz} and noticed {prob}. {why}",
            },
            "referral": {
                "tone": "warm_referral",
                "greeting": f"Hi {name}, {lead.get('referrer', 'someone')} recommended you!",
                "message": "We love referrals — let's get you started."
            },
            "owner": {
                "tone": "direct_intro",
                "greeting": f"Hi {name}, {lead.get('owner_name', 'the owner')} asked us to help you.",
                "message": "We'll handle everything — no portal needed."
            },
            "social": {
                "tone": "casual_platform",
                "greeting": f"Hi {name}, saw you on {lead.get('platform', 'social media')}!",
                "message": "Let's take your brand to the next level."
            }
        }
        tmpl = templates.get(source, templates["website"])
        return {
            "source": source,
            "label": source.capitalize(),
            "greeting": tmpl["greeting"],
            "message": tmpl["message"],
            "tone": tmpl["tone"],
            "research_data": rd if source == "openclaw" else None
        }

    def enqueue_lead(self, lead: Dict) -> Dict:
        if "source" not in lead:
            lead["source"] = "website"
        source_info = self.detect_lead_source(lead)
        lead["source_info"] = source_info
        score = self._score_lead(lead)
        lead["score"] = score
        lead["status"] = "new"
        lead["id"] = f"lead_{len(self.lead_queue) + 1}"
        lead["created_at"] = datetime.now().isoformat()
        self.lead_queue.append(lead)
        self.lead_queue.sort(key=lambda x: x.get("score", 0), reverse=True)
        self.lead_queue = self.lead_queue[:self.max_queue_size]
        self._reset_daily_stats_if_new_day()
        self.stats_leads_today += 1
        return lead

    def _score_lead(self, lead: Dict) -> int:
        score = 50
        industry = (lead.get("industry") or "").lower()
        high_value = ["saas", "finance", "healthcare", "tech", "enterprise"]
        if any(v in industry for v in high_value):
            score += 20
        budget = lead.get("budget", 0)
        if isinstance(budget, (int, float)) and budget > 5000:
            score += 15
        elif isinstance(budget, (int, float)) and budget > 2000:
            score += 8
        source = (lead.get("source") or "").lower()
        if source == "referral":
            score += 10
        elif source == "website":
            score += 5
        urgency = (lead.get("urgency") or "").lower()
        if urgency in ("high", "urgent", "asap"):
            score += 10
        name = lead.get("name", "")
        email = lead.get("email", "")
        if name and email:
            score += 5
        return min(score, 100)

    def get_next_lead(self) -> Optional[Dict]:
        if not self.lead_queue:
            return None
        for i, lead in enumerate(self.lead_queue):
            if lead.get("status") == "new" and self.hermes_workload < self.max_agent_load:
                self.lead_queue[i]["status"] = "processing"
                self.hermes_workload += 1
                return lead
        return None

    def complete_lead(self, lead_id: str) -> bool:
        for i, lead in enumerate(self.lead_queue):
            if lead.get("id") == lead_id:
                self.lead_queue[i]["status"] = "converted"
                self.hermes_workload = max(0, self.hermes_workload - 1)
                return True
        return False

    def get_queue_stats(self) -> Dict:
        new = sum(1 for l in self.lead_queue if l.get("status") == "new")
        processing = sum(1 for l in self.lead_queue if l.get("status") == "processing")
        converted = sum(1 for l in self.lead_queue if l.get("status") == "converted")
        return {
            "total": len(self.lead_queue),
            "new": new,
            "processing": processing,
            "converted": converted,
            "hermes_load": f"{self.hermes_workload}/{self.max_agent_load}",
            "opencode_load": f"{self.opencode_workload}/{self.max_agent_load}",
            "queue_full": len(self.lead_queue) >= self.max_queue_size
        }

    # ── Hermes Complete Workflow ──
    def hermes_onboard(self, email: str, client_type: str) -> Dict:
        client_type = "self_service" if "a" in client_type.lower() else "managed"
        label = "Self-Service Portal" if client_type == "self_service" else "Managed (Email Only)"

        signup_link = f"{os.getenv('NEXT_PUBLIC_APP_URL', 'http://localhost:3000')}/signup?ref={email}"

        if client_type == "self_service":
            template = {
                "subject": "Welcome to NexusAI! Your Portal is Ready",
                "body": f"""Hi there,

Your Self-Service Portal is ready!

Sign in here: {signup_link}

What you can do in your portal:
• View your content and marketing materials
• Track campaign performance
• Chat directly with AI agents
• Manage your account settings

Getting started:
1. Click the link above and create your account
2. Fill in your client brief (takes 5 minutes)
3. Our agents will start working on your content

Need help? Just reply to this email or use the chat in your portal.

Best,
NexusAI Agency Team"""
            }
            next_steps = "Client ko signup link bheja. Wait for them to create account and submit brief."
        else:
            template = {
                "subject": "Welcome to NexusAI! We'll Handle Everything",
                "body": f"""Hi there,

Thank you for choosing our Managed Service!

We'll take care of everything for you. Here's what to expect:

Next steps:
1. We'll send you a brief questionnaire (3-5 questions)
2. Our team will analyze your requirements
3. We'll start creating your marketing content
4. You'll receive regular email updates

No portal login needed — we'll communicate entirely via email.

Please reply with the following info to help us get started:
1. What industry is your business in?
2. What are your main goals? (more sales, brand awareness, etc.)
3. Which platforms do you want to focus on?
4. Any brand guidelines or examples you can share?

Best,
NexusAI Agency Team"""
            }
            next_steps = "Client se requirements gather karni hain. Wait for their reply."

        self.hermes_workload = min(self.hermes_workload + 1, self.max_agent_load)

        sent = send_email(email, template["subject"], template["body"])

        return {
            "email": email,
            "client_type": label,
            "email_sent": template,
            "actually_sent": sent,
            "next_steps": next_steps,
            "status": "onboarding_started"
        }

    def hermes_get_requirements(self, email: str, answers: Dict) -> Dict:
        client_name = email
        industry = answers.get("industry", "general")
        for i, l in enumerate(self.lead_queue):
            if l.get("email") == email:
                self.lead_queue[i]["requirements"] = answers
                self.lead_queue[i]["status"] = "converted"
                self.lead_queue[i]["converted_at"] = datetime.now().isoformat()
                self.lead_queue[i]["client_type"] = answers.get("client_type", "managed")
                client_name = l.get("business_name") or l.get("name", email)
                industry = l.get("industry") or answers.get("industry", "general")
                break
        self._reset_daily_stats_if_new_day()
        self.stats_converted_today += 1
        aca_result = self.aca_analyze_and_assign(client_name, industry, answers)
        return {
            "email": email,
            "client": client_name,
            "requirements": answers,
            "status": "requirements_collected",
            "aca_assignment": aca_result,
            "next_steps": f"ACA ne agents assign kiye: {', '.join(aca_result.get('assigned_agents', ['opencode']))}. Kaam shuru!"
        }



    def hermes_checkin(self, email: str) -> Dict:
        client_type = None
        days_since = 99
        for l in self.lead_queue:
            if l.get("email") == email:
                client_type = l.get("client_type", "managed")
                created = l.get("converted_at") or l.get("created_at")
                if created:
                    try:
                        days_since = (datetime.now() - datetime.fromisoformat(created)).days
                    except:
                        pass
                break
        if days_since > 14 and client_type != "self_service":
            return {"action": "re-engagement needed", "template": "re-engagement", "days_inactive": days_since}
        elif days_since > 7:
            return {"action": "send weekly update", "template": "weekly-update", "days_inactive": days_since}
        return {"action": "all good", "days_inactive": days_since}

    # ── Lead Confirmation Flow (Self-Service vs Email-Only) ──
    LEAD_CONFIRM_STATUS = [
        "new",
        "confirmation_emailed",
        "confirmed_self_service",
        "confirmed_managed",
        "converted",
        "declined"
    ]

    def generate_cold_email(self, lead: Dict) -> Dict:
        rd = lead.get("research_data") or {}
        name = lead.get("name", "there")
        biz = rd.get("business_name") or lead.get("business_name", "your business")
        prob = rd.get("problem") or lead.get("problem", "growth challenges")
        why = rd.get("why_picked") or lead.get("why_picked", "We think you have potential.")
        email = lead.get("email", "")

        return {
            "to": email,
            "subject": f"Quick idea for {biz}",
            "type": "cold_email",
            "body": f"""Hi {name},

We've been looking at {biz} and noticed {prob}.

{why}

We've helped similar businesses turn this around — content that converts, social presence that grows, campaigns that bring results.

Quick question: Would you be open to a quick chat? Or shall I send you some ideas directly?

👉 Option A: Send me some samples first
👉 Option B: Let's hop on a quick call

Reply "A" or "B" and I'll take it from there.

Best,
NexusAI Agency Team""",
            "lead_status": "cold_email_sent"
        }

    def send_confirmation_email(self, lead: Dict) -> Dict:
        name = lead.get("name", "there")
        email = lead.get("email", "")
        if not email:
            return {"error": "No email provided for lead"}
        source_info = self.detect_lead_source(lead)
        source = source_info["source"]

        for i, l in enumerate(self.lead_queue):
            if l.get("email") == email:
                self.lead_queue[i]["status"] = "confirmation_emailed"
                self.lead_queue[i]["source"] = source
                break

        # OpenClaw lead → personalized cold email using research data
        if source == "openclaw":
            cold = self.generate_cold_email(lead)
            self._reset_daily_stats_if_new_day()
            self.stats_cold_emails_today += 1
            self.cold_emails_sent += 1
            sent = send_email(email, cold["subject"], cold["body"])
            return {
                "to": email,
                "source": "openclaw",
                "type": "cold_email",
                "subject": cold["subject"],
                "greeting": source_info["greeting"],
                "research_used": {
                    "business_name": lead.get("research_data", {}).get("business_name") or lead.get("business_name"),
                    "problem": lead.get("research_data", {}).get("problem") or lead.get("problem"),
                    "why_picked": lead.get("research_data", {}).get("why_picked") or lead.get("why_picked")
                },
                "body": cold["body"],
                "lead_status": "cold_email_sent",
                "email_sent": sent,
                "message": "Cold email bheji jo convert kare — business name + problem + reason OpenClaw picked them, sab use kiya"
            }

        greeting = source_info["greeting"]
        source_intros = {
            "website": "Thanks for signing up on our website! Before we begin:",
            "referral": f"{lead.get('referrer', 'A friend')} thinks you'll love our service. Here's how to start:",
            "owner": f"Welcome to {lead.get('owner_name', 'the owner')}'s agency team. We'll take care of everything:",
            "social": f"Saw you on {lead.get('platform', 'social media')} — let's make your brand shine! Pick your plan:"
        }
        intro = source_intros.get(source, "Let's get started!")

        body = f"""{greeting}

{intro}

👉 Option A: SELF-SERVICE PORTAL
You get full access to our web dashboard where you can:
• View your content and reports anytime
• Chat directly with AI agents
• Track campaign progress
• Manage everything yourself

👉 Option B: MANAGED SERVICE (Email Only)
We handle everything for you:
• Our team creates and manages all content
• You get regular email updates
• No dashboard needed — just reply to emails

Reply with "A" for Self-Service or "B" for Managed Service.

Best,
NexusAI Agency Team"""
        sent = send_email(email, "Confirm how you'd like to work with NexusAI", body)
        return {
            "to": email,
            "subject": "Confirm how you'd like to work with NexusAI",
            "source": source,
            "greeting": greeting,
            "body": body,
            "lead_status": "confirmation_emailed",
            "email_sent": sent
        }

    def confirm_lead(self, email: str, choice: str) -> Dict:
        choice = choice.strip().lower()
        if choice in ("a", "self", "self-service", "self_service", "portal", "website"):
            new_status = "confirmed_self_service"
            label = "Self-Service Portal"
            next_steps = "Signup link bhejna hai — client apna portal banayega"
        elif choice in ("b", "managed", "email", "managed-service", "managed_service", "email-only"):
            new_status = "confirmed_managed"
            label = "Managed Service (Email Only)"
            next_steps = "Hermes client ka email handle karega — no portal needed"
        else:
            return {"error": "Invalid choice. Use A (self-service) or B (managed)."}

        for i, l in enumerate(self.lead_queue):
            if l.get("email") == email:
                self.lead_queue[i]["status"] = new_status
                self.lead_queue[i]["service_type"] = label
                break

        self._reset_daily_stats_if_new_day()
        if choice in ("a", "b", "self", "managed"):
            self.stats_replies_today += 1
        if new_status in ("confirmed_self_service", "confirmed_managed"):
            self.stats_converted_today += 1

        return {
            "email": email,
            "choice": label,
            "status": new_status,
            "next_steps": next_steps,
            "message": f"Client confirmed: {label}. {next_steps}"
        }

    def get_confirmation_stats(self) -> Dict:
        stats = {"self_service": 0, "managed": 0, "pending": 0, "total": 0}
        for l in self.lead_queue:
            s = l.get("status", "")
            if s == "confirmed_self_service":
                stats["self_service"] += 1
            elif s == "confirmed_managed":
                stats["managed"] += 1
            elif s in ("new", "confirmation_emailed"):
                stats["pending"] += 1
            stats["total"] += 1
        return stats

    # ── Client Inactivity Detection ──
    def check_inactive_clients(self) -> List[Dict]:
        inactive = []
        for client in self.list_clients():
            name = client["name"]
            client_dir = self.clients_dir / name
            brief_path = client_dir / "context" / "client-brief.md"
            has_brief = brief_path.exists() and brief_path.stat().st_size > 50
            has_outputs = client.get("has_outputs", False)
            log_path = client_dir / "context" / "execution-log.json"
            last_active = None
            if log_path.exists():
                last_active = datetime.fromtimestamp(log_path.stat().st_mtime)
            days_since = (datetime.now() - last_active).days if last_active else 99
            if not has_brief and days_since > self.inactive_threshold_days:
                inactive.append({
                    "client": name,
                    "reason": "No brief uploaded yet",
                    "days_inactive": days_since,
                    "action": "Hermes ko auto-followup bhejna hai — client ko email kare"
                })
            elif not has_outputs and days_since > self.inactive_threshold_days:
                inactive.append({
                    "client": name,
                    "reason": "No work done yet",
                    "days_inactive": days_since,
                    "action": "Hermes ko bole — client se check kare"
                })
        return inactive

    def suggest_followup(self, client_name: str) -> Dict:
        client_dir = self.clients_dir / client_name
        if not client_dir.exists():
            return {"error": f"Client {client_name} not found"}
        brief_path = client_dir / "context" / "client-brief.md"
        has_brief = brief_path.exists() and brief_path.stat().st_size > 50
        if not has_brief:
            return {
                "client": client_name,
                "status": "needs_followup",
                "message": "Client signed up but no brief yet! Hermes should email/call to get started.",
                "suggested_action": "Send onboarding email with brief template link"
            }
        return {
            "client": client_name,
            "status": "active",
            "message": "Client has brief, all good"
        }

    # ── Workload Alerts ──
    def get_workload_alerts(self) -> List[Dict]:
        alerts = []
        if self.hermes_workload >= self.max_agent_load:
            alerts.append({
                "severity": "high",
                "agent": "Hermes",
                "message": f"Hermes is at full capacity ({self.hermes_workload}/{self.max_agent_load}). Leads will queue up."
            })
        if self.opencode_workload >= self.max_agent_load:
            alerts.append({
                "severity": "high",
                "agent": "OpenCode",
                "message": f"OpenCode is at full capacity ({self.opencode_workload}/{self.max_agent_load}). Projects will be delayed."
            })
        inactive = self.check_inactive_clients()
        if inactive:
            alerts.append({
                "severity": "medium",
                "agent": "Hermes",
                "message": f"{len(inactive)} client(s) inactive — auto-followup needed"
            })
        if len(self.lead_queue) >= self.max_queue_size * 0.8:
            alerts.append({
                "severity": "medium",
                "agent": "OpenClaw",
                "message": f"Lead queue nearly full ({len(self.lead_queue)}/{self.max_queue_size}). Process leads or increase capacity."
            })
        return alerts

    # ── Complete System Status ──
    def get_full_status(self) -> Dict:
        return {
            "agents": self.get_agent_status(),
            "workflows": {
                "total": len(self.list_workflows()),
                "active": len(self.active_workflows)
            },
            "clients": {
                "total": len(self.list_clients()),
                "inactive": len(self.check_inactive_clients())
            },
            "lead_queue": self.get_queue_stats(),
            "workload_alerts": self.get_workload_alerts()
        }

    # ── Owner Client Mode (Personal Clients—no portal) ──
    # User ka apna client hai. Agents tools hain. Payment/Meetings = Owner ko batana.

    owner_notifications = []

    def add_owner_client(self, name: str, details: Dict) -> Dict:
        client = {
            "id": f"own_{len(self.lead_queue) + 1}",
            "name": name,
            "type": "owner_client",
            "status": "active",
            "details": details,
            "payment_status": "pending",
            "needs_meeting": False,
            "created_at": datetime.now().isoformat()
        }
        self.lead_queue.append(client)
        return client

    def notify_payment(self, client_name: str, amount: float, note: str = "", currency: str = "USD", location: str = "") -> Dict:
        if not currency:
            currency = self.detect_currency(location) if location else ("INR" if "owner" in client_name.lower() else "USD")
        symbols = {"USD": "$", "GBP": "£", "EUR": "€", "CNY": "¥", "AED": "د.إ", "PKR": "Rs", "INR": "₹", "CAD": "C$", "AUD": "A$"}
        sym = symbols.get(currency, "$")
        action = "Owner ko payment lena hai (Stripe/PayPal/bank)" if currency == "USD" or currency == "GBP" or currency == "EUR" else "Owner ko payment lena hai (UPI/Paytm/bank)"
        notification = {
            "type": "payment",
            "client": client_name,
            "amount": amount,
            "currency": currency,
            "symbol": sym,
            "note": note,
            "message": f"💰 PAYMENT NEEDED: {client_name} — {sym}{amount} {currency}. {note}",
            "action": action,
            "timestamp": datetime.now().isoformat()
        }
        self.owner_notifications.append(notification)
        return notification

    def notify_meeting(self, client_name: str, reason: str = "") -> Dict:
        notification = {
            "type": "meeting",
            "client": client_name,
            "reason": reason,
            "message": f"📅 MEETING NEEDED: {client_name} — {reason or 'Client meeting required'}",
            "action": "Owner ko meeting arrange karni hai",
            "timestamp": datetime.now().isoformat()
        }
        self.owner_notifications.append(notification)
        return notification

    # ── Hermes Post-Delivery Meeting Decision ──
    def hermes_ask_meeting(self, client_name: str) -> Dict:
        return {
            "email_to_client": "Aapka pura package ready hai! Kya aap meeting chahiye discuss karne ke liye? Ya direct deliver karun?",
            "client_decision": "waiting",
            "status": "awaiting_client_reply",
            "next": "Client reply karega: meeting chahiye ya direct deliver",
            "context": "Package already built. Meeting is for review/discussion only."
        }

    def hermes_meeting_decision(self, client_name: str, wants_meeting: bool) -> Dict:
        if wants_meeting:
            n = self.notify_meeting(client_name, "Package ready — client review meeting requested")
            return {
                "decision": "meeting_needed",
                "notify_owner": True,
                "action": "📅 Meeting needed — Owner ko bataya. Package ready hai, meeting mein review hoga.",
                "notification": n,
                "next_steps": "Owner meeting karega → meeting mein package review → payment → close"
            }
        else:
            return {
                "decision": "no_meeting",
                "notify_owner": False,
                "action": "✅ Meeting nahi chahiye. Package deliver karo + payment notify.",
                "next_steps": "Deliver package → notify_payment(client, amount) → payment confirm → close"
            }

    # ── Hermes Lead-to-Close Workflow (Correct Order) ──
    def hermes_full_lifecycle(self, email: str, client_type: str, lead_source: str = "website", research_data: Dict = None) -> Dict:
        steps = []
        lead = {
            "email": email,
            "name": email.split("@")[0],
            "source": lead_source,
            "research_data": research_data or {}
        }

        # ── Pipeline state trackers ──
        if not hasattr(self, 'pipeline_states'):
            self.pipeline_states = {}
        pipeline_id = f"pipe_{len(self.pipeline_states) + 1}"
        self.pipeline_states[pipeline_id] = {
            "email": email,
            "lead_source": lead_source,
            "client_type": client_type,
            "research_data": research_data,
            "phase": "source_detection",
            "phases_completed": [],
            "status": "running"
        }

        def update_pipeline(phase: str, data: Dict = None):
            ps = self.pipeline_states[pipeline_id]
            ps["phase"] = phase
            ps["phases_completed"].append(phase)
            if data:
                ps[phase] = data

        # Phase 0: Source Detection
        s0 = self.detect_lead_source(lead)
        steps.append({"phase": "source_detection", "source": lead_source, "greeting": s0["greeting"], "research_data": research_data})
        update_pipeline("source_detection", s0)

        # Phase 1: Cold Email (for OpenClaw leads)
        if lead_source == "openclaw" and research_data:
            cold = self.generate_cold_email(lead)
            steps.append({"phase": "cold_email", "type": "personalized_outreach", "research_used": research_data, "email_body": cold["body"]})
            update_pipeline("cold_email", {"research_used": research_data})

        # Phase 2: Onboarding
        s1 = self.hermes_onboard(email, client_type)
        steps.append({"phase": "onboarding", "result": s1})
        update_pipeline("onboarding", s1)

        # Phase 3: Requirements + ACA assignment
        s2 = self.hermes_get_requirements(email, {"client_type": client_type, "status": "asked"})
        steps.append({"phase": "requirements", "result": s2})
        update_pipeline("requirements", s2)

        # Phase 4: OpenCode ACTUALLY builds the package
        client_name_from_lead = email.split("@")[0]
        for l in self.lead_queue:
            if l.get("email") == email:
                client_name_from_lead = l.get("business_name") or l.get("name", email.split("@")[0])
                break
        industry = (research_data or {}).get("industry", "general") or "general"
        build_result = self.opencode_build(client_name_from_lead, industry)
        steps.append({"phase": "opencode_build", "result": {
            "status": "built",
            "client": client_name_from_lead,
            "package_preview": (build_result.get("package", "") or "")[:300]
        }})
        update_pipeline("opencode_build", build_result)

        # Phase 5: Delivery + Payment/Meeting decision
        delivery_result = self.opencode_deliver(client_name_from_lead)
        steps.append({"phase": "delivery_payment", "result": delivery_result})
        update_pipeline("delivery_payment", delivery_result)

        # Phase 6: Ask meeting?
        s3 = self.hermes_ask_meeting(email)
        steps.append({"phase": "post_delivery_meeting_decision", "result": s3})
        update_pipeline("post_delivery_meeting_decision", s3)

        self.pipeline_states[pipeline_id]["status"] = "awaiting_meeting_decision"

        return {
            "pipeline_id": pipeline_id,
            "email": email,
            "client_name": client_name_from_lead,
            "client_type": "Self-Service" if "a" in client_type.lower() else "Managed",
            "lead_source": lead_source,
            "research_data": research_data,
            "phases_completed": len(steps),
            "phases": steps,
            "status": "awaiting_post_delivery_meeting_decision",
            "message": (
                f"✅ FULL PIPELINE EXECUTED for {client_name_from_lead}\n"
                f"Source: {lead_source}\n"
                f"{'📧 Cold email sent using OpenClaw research' if lead_source == 'openclaw' and research_data else ''}\n"
                f"📋 Onboarding → Requirements → ACA Assignment\n"
                f"🛠️ OpenCode built full package\n"
                f"📦 Delivered — Payment notified\n"
                f"❓ Now asking: meeting chahiye ya direct deliver?\n\n"
                f"Next: 'hermes meeting {email} yes' or 'hermes meeting {email} no'"
            )
        }

    # ── Pipeline Status Tracking ──
    def get_pipeline_status(self, pipeline_id: str = None) -> Dict:
        if not hasattr(self, 'pipeline_states'):
            self.pipeline_states = {}
        if pipeline_id:
            ps = self.pipeline_states.get(pipeline_id)
            if not ps:
                return {"error": f"Pipeline {pipeline_id} not found"}
            return {"pipeline": pipeline_id, "status": ps}
        return {
            "total_pipelines": len(self.pipeline_states),
            "pipelines": {k: {"status": v["status"], "phase": v["phase"],
                              "email": v["email"], "lead_source": v.get("lead_source", "?")}
                         for k, v in self.pipeline_states.items()}
        }

    def get_owner_pending(self) -> Dict:
        payments = [n for n in self.owner_notifications if n["type"] == "payment"]
        meetings = [n for n in self.owner_notifications if n["type"] == "meeting"]
        currencies = list(set(p.get("currency", "USD") for p in payments)) if payments else ["USD"]
        return {
            "payments": payments,
            "meetings": meetings,
            "total_pending": len(payments) + len(meetings),
            "currencies": currencies,
            "message": f"{len(payments)} payment(s) pending, {len(meetings)} meeting(s) pending"
        }

    # ── Updated Hermes delivery with payment/meeting check ──
    def hermes_deliver(self, email: str, deliverables: List[str], require_payment: bool = False, amount: float = 0, currency: str = "USD") -> Dict:
        client_type, client_name = "managed", email
        for l in self.lead_queue:
            if l.get("email") == email:
                client_type = l.get("client_type", "managed")
                client_name = l.get("name", email)
                break
        sym = "$" if currency == "USD" else "£" if currency == "GBP" else "¥" if currency == "CNY" else "₹" if currency == "INR" else "$"
        if require_payment:
            payment_notice = self.notify_payment(client_name, amount, f"Deliverables ready: {', '.join(deliverables)}", currency=currency)
            payment_msg = f"\n\n⚠️ **PAYMENT PENDING: {sym}{amount} {currency}** — Owner will contact you for payment."
        else:
            payment_msg = ""
            payment_notice = None
        if client_type == "self_service":
            msg = f"New deliverables available in your portal! Check your dashboard.{payment_msg}"
        else:
            msg = f"Your deliverables are ready: {', '.join(deliverables)}. Check your email.{payment_msg}"
        subject = "Your deliverables are ready!"
        sent = send_email(email, subject, msg)
        return {
            "email": email,
            "deliverables": deliverables,
            "message": msg,
            "email_sent": sent,
            "status": "delivered" if not require_payment else "delivered_pending_payment",
            "payment_notice": payment_notice
        }

    def _md_to_html(self, text: str) -> str:
        if not text:
            return "<p>No content available.</p>"
        html = text
        html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
        html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
        html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
        html = re.sub(r"(<li>.*</li>\n?)+", lambda m: f"<ul>{m.group(0)}</ul>", html)
        paragraphs = html.split("\n\n")
        processed = []
        for p in paragraphs:
            p = p.strip()
            if p and not p.startswith("<h") and not p.startswith("<ul") and not p.startswith("<ol"):
                p = f"<p>{p}</p>"
            processed.append(p)
        return "\n".join(processed).replace("\n", "<br>")


    # ── Photo-Shooter: Mumbai=plan, Foreign=AI generate ──
    def photo_shooter_execute(self, client_name: str, mode: str = "ai",
                              industry: str = "general", platform: str = "Instagram",
                              quantity: int = 10) -> Dict:
        is_mumbai = mode in ("mumbai", "production")
        context = {
            "client_name": client_name,
            "mode": "mumbai" if is_mumbai else "ai",
            "industry": industry,
            "platform": platform,
            "quantity": quantity,
            "brand_style": "client brand style"
        }
        name = "photo-shooter"
        result = self.execute_agent(name, f"{'Production plan' if is_mumbai else 'AI image generation'} for {client_name} in {industry}", context)
        return {
            "client": client_name,
            "mode": "mumbai_production_plan" if is_mumbai else "ai_generation_guide",
            "type": "photo",
            "response": result.get("response", ""),
            "status": "completed",
            "next_step": "Owner ko plan de do — woh shoot arrange karega" if is_mumbai else "AI prompts ready — run with FLUX/Gemini"
        }

    # ── Wan2.2-S2V Talking Head (Free AI Clone via HF Space) ──
    _s2v: Optional[WanS2VClient] = None

    @property
    def s2v(self) -> WanS2VClient:
        if self._s2v is None:
            self._s2v = WanS2VClient()
        return self._s2v

    def s2v_talking_head(self, image_path: str, audio_path: str,
                          resolution: str = "480P", timeout: int = 600) -> Dict:
        """Generate AI clone talking head video via Wan2.2-S2V (free, no API key).
        photo + audio → talking head video with lip-sync via HF Space.
        Blocking — waits for result (may take 5-10min on HF free tier).
        """
        result = self.s2v.generate_talking_head(image_path, audio_path, resolution, timeout)
        return result

    def s2v_submit(self, image_path: str, audio_path: str,
                    resolution: str = "480P") -> Dict:
        """Submit talking head job (non-blocking) — returns job for polling."""
        return self.s2v.submit_talking_head(image_path, audio_path, resolution)

    def s2v_job_status(self, job) -> Dict:
        """Check status of a submitted S2V job"""
        return self.s2v.job_status(job)

    def s2v_doctor(self) -> Dict:
        """Check if Wan2.2-S2V HF Space is accessible"""
        return self.s2v.doctor()


engine = AgentEngine()
