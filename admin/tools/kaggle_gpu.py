"""Kaggle GPU — On-demand visual content generation.

Submit notebook → T4 GPU run → download output.

Image: FLUX.1-dev (free, 30hrs/week)
Video: CogVideoX-2b (free, 30hrs/week)

Flow:
  1. generate_visual(content_type, prompt, ...) 
  2. Creates Kaggle notebook with FLUX/CogVideoX code
  3. Submits to GPU via Kaggle API
  4. Polls until complete
  5. Downloads output to data/outputs/
  6. Returns local file path
"""
from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_OUTPUT_DIR = Path(os.getenv("TAGS_OUTPUT_DIR", "data/outputs"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════════════════
# NOTEBOOK CODE TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

FLUX_CODE = '''# TAGS Content Agent — FLUX Image Generation
import subprocess, sys, json, os, traceback

# P100 check (Kaggle free tier)
P100_MODE = False
try:
    out = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=name,compute_cap", "--format=csv,noheader"],
        text=True, timeout=10
    ).strip().lower()
    print(f"GPU: {out}")
    if "p100" in out:
        P100_MODE = True
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        print("P100 detected — no sm_60 support, using CPU")
except Exception as e:
    print(f"GPU check: {e}")

import torch
from diffusers import DiffusionPipeline
from PIL import Image

DEVICE = "cpu"
DTYPE = torch.float32
if torch.cuda.is_available() and torch.cuda.device_count() > 0:
    try:
        cap = torch.cuda.get_device_capability(0)
        if cap[0] >= 7 and not P100_MODE:
            DEVICE = "cuda"
            DTYPE = torch.bfloat16
        elif cap[0] >= 6 and not P100_MODE:
            DEVICE = "cuda"
            DTYPE = torch.float16
    except Exception:
        pass

print(f"Device: {DEVICE}, dtype: {DTYPE}")

# Model selection
HF_TOKEN = os.environ.get("HF_TOKEN") or os.environ.get("HF_TOKEN_READ", "")
if HF_TOKEN:
    try:
        from diffusers import FluxPipeline
        MODEL_NAME = "black-forest-labs/FLUX.1-dev"
        PIPE_CLASS = FluxPipeline
        print("Using FLUX.1-dev")
    except ImportError:
        MODEL_NAME = "stabilityai/stable-diffusion-xl-base-1.0"
        PIPE_CLASS = DiffusionPipeline
        print("FluxPipeline not found, using SDXL")
else:
    MODEL_NAME = "stabilityai/stable-diffusion-xl-base-1.0"
    PIPE_CLASS = DiffusionPipeline
    print("No HF_TOKEN, using SDXL (free, no auth)")

print(f"Loading {MODEL_NAME}...")
sys.stdout.flush()
try:
    pipe = PIPE_CLASS.from_pretrained(
        MODEL_NAME, torch_dtype=DTYPE,
        token=HF_TOKEN or None,
        safety_checker=None, requires_safety_checker=False,
    )
    if DEVICE == "cuda":
        pipe.enable_model_cpu_offload()
    else:
        pipe = pipe.to("cpu")
    print("Model loaded")
    sys.stdout.flush()
except Exception as e:
    print(f"MODEL LOAD ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

# Generate
PROMPT = "{prompt}"
WIDTH = {width}
HEIGHT = {height}
STEPS = {steps}

print(f"Generating: {{PROMPT[:100]}} ({{WIDTH}}x{{HEIGHT}}, steps={{STEPS}})")
sys.stdout.flush()
try:
    image = pipe(PROMPT, width=WIDTH, height=HEIGHT, num_inference_steps=STEPS, guidance_scale=7.5).images[0]
    image.save("output.png")
    sz = os.path.getsize("output.png")
    print(json.dumps({{"status": "success", "file": "output.png", "size_bytes": sz}}))
except Exception as e:
    print(f"GENERATION ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)
'''

COGVIDEO_CODE = '''# TAGS Content Agent — CogVideoX Video Generation
import subprocess, sys, json, os, traceback

P100_MODE = False
try:
    out = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=name,compute_cap", "--format=csv,noheader"],
        text=True, timeout=10
    ).strip().lower()
    print(f"GPU: {out}")
    if "p100" in out:
        P100_MODE = True
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        print("P100 — CogVideo needs T4+. Skipping.")
except Exception as e:
    print(f"GPU check: {e}")

import torch
from diffusers import CogVideoXPipeline
import imageio

if P100_MODE or not torch.cuda.is_available():
    print(json.dumps({{"status": "skipped", "reason": "CogVideo needs T4+ GPU"}}))
    sys.exit(0)

cap = torch.cuda.get_device_capability(0)
if cap[0] < 7:
    print(json.dumps({{"status": "skipped", "reason": f"GPU sm_{cap[0]}{cap[1]} too old for CogVideo"}}))
    sys.exit(0)

DTYPE = torch.bfloat16 if cap[0] >= 7 else torch.float16
print(f"GPU: {{torch.cuda.get_device_name(0)}} (sm_{{cap[0]}}{{cap[1]}})")

print("Loading THUDM/CogVideoX-2b...")
sys.stdout.flush()
try:
    pipe = CogVideoXPipeline.from_pretrained("THUDM/CogVideoX-2b", torch_dtype=DTYPE)
    pipe.enable_model_cpu_offload()
    print("Model loaded")
    sys.stdout.flush()
except Exception as e:
    print(f"MODEL LOAD ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

PROMPT = "{prompt}"
NUM_FRAMES = {frames}

print(f"Generating video: {{PROMPT[:100]}} ({{NUM_FRAMES}} frames, ~5-10 min)")
sys.stdout.flush()
try:
    video = pipe(PROMPT, num_videos_per_prompt=1, num_inference_steps=50, num_frames=NUM_FRAMES, guidance_scale=6.0).videos[0]
    imageio.mimsave("output.mp4", video, fps=8)
    sz = os.path.getsize("output.mp4")
    print(json.dumps({{"status": "success", "file": "output.mp4", "size_bytes": sz, "frames": NUM_FRAMES}}))
except Exception as e:
    print(f"VIDEO ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)
'''


# ═══════════════════════════════════════════════════════════════════════════════
# PLATFORM SIZES
# ═══════════════════════════════════════════════════════════════════════════════

PLATFORM_SIZES: dict[str, tuple[int, int]] = {
    "instagram_square": (1080, 1080),
    "instagram_portrait": (1080, 1350),
    "instagram_story": (1080, 1920),
    "instagram_reel": (1080, 1920),
    "facebook_post": (1200, 630),
    "facebook_ad": (1080, 1080),
    "facebook_story": (1080, 1920),
    "linkedin_post": (1200, 627),
    "twitter_post": (1200, 675),
    "youtube_thumbnail": (1280, 720),
    "blog_hero": (1200, 600),
    "og_image": (1200, 630),
    "poster_a4": (2480, 3508),
    "square": (1024, 1024),
    "landscape": (1920, 1080),
    "portrait": (1080, 1920),
}


def get_platform_size(platform: str) -> tuple[int, int]:
    """Platform name se size nikaalo."""
    key = platform.lower().replace(" ", "_").replace("-", "_")
    if key in PLATFORM_SIZES:
        return PLATFORM_SIZES[key]
    for pkey, psize in PLATFORM_SIZES.items():
        if key in pkey or pkey in key:
            return psize
    return (1024, 1024)


# ═══════════════════════════════════════════════════════════════════════════════
# KAGGLE CLI HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _check_kaggle() -> bool:
    """Kaggle CLI installed hai ya nahi."""
    for cmd in [["kaggle", "--version"], [sys.executable, "-m", "kaggle", "--version"]]:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return False


def _get_username() -> str:
    """Kaggle username from env or kaggle.json."""
    username = os.getenv("KAGGLE_USERNAME", "")
    if username:
        return username
    kaggle_json = os.path.expanduser("~/.kaggle/kaggle.json")
    if os.path.exists(kaggle_json):
        with open(kaggle_json) as f:
            return json.load(f).get("username", "")
    return ""


def _run_kaggle(args: list[str], timeout: int = 30) -> dict[str, Any]:
    """Kaggle CLI command run karo."""
    for cmd in [["kaggle"] + args, [sys.executable, "-m", "kaggle"] + args]:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return {
                "success": r.returncode == 0,
                "stdout": r.stdout.strip(),
                "stderr": r.stderr.strip(),
            }
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "timeout"}
    return {"success": False, "error": "kaggle CLI not found"}


# ═══════════════════════════════════════════════════════════════════════════════
# NOTEBOOK BUILD + SUBMIT
# ═══════════════════════════════════════════════════════════════════════════════

def _source_to_lines(source: str) -> list[str]:
    """Convert source to Jupyter notebook cell format."""
    lines = source.split("\n")
    return [line + "\n" for line in lines[:-1]] + [lines[-1]]


def _build_notebook(code_source: str) -> dict[str, Any]:
    """Build Kaggle-format notebook JSON."""
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kaggle": {
                "accelerator": "gpu",
                "dataSources": [],
                "isGpuEnabled": True,
                "isInternetEnabled": True,
                "language": "python",
            },
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
        },
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": _source_to_lines(code_source),
            }
        ],
    }


def _build_metadata(username: str, title: str) -> dict[str, Any]:
    """Build kernel-metadata.json for Kaggle CLI."""
    unique = uuid.uuid4().hex[:8]
    full_title = f"TAGS {title} {unique}"
    slug = re.sub(r"[^a-z0-9\s-]", "", full_title.lower())
    slug = re.sub(r"[\s]+", "-", slug).strip("-")
    kernel_id = f"{username}/{slug}"

    return {
        "id": kernel_id,
        "title": full_title,
        "code_file": "notebook.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": False,
        "enable_gpu": True,
        "enable_internet": True,
        "kernel_sources": [],
        "dataset_sources": [],
    }


def _submit_notebook(code_source: str, title: str) -> dict[str, Any]:
    """Notebook banao aur Kaggle pe submit karo. Returns kernel_slug."""
    username = _get_username()
    if not username:
        return {"status": "error", "error": "Kaggle credentials not found. Set KAGGLE_USERNAME in env or ~/.kaggle/kaggle.json"}

    kernel_dir = tempfile.mkdtemp(prefix=f"kaggle_{title}_")

    try:
        # Write notebook
        notebook = _build_notebook(code_source)
        with open(os.path.join(kernel_dir, "notebook.ipynb"), "w") as f:
            json.dump(notebook, f, indent=2)

        # Write metadata
        metadata = _build_metadata(username, title)
        with open(os.path.join(kernel_dir, "kernel-metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)

        kernel_slug = metadata["id"]

        # Submit
        result = _run_kaggle(["kernels", "push", "-p", kernel_dir], timeout=60)
        if result["success"]:
            return {
                "status": "submitted",
                "kernel_slug": kernel_slug,
                "url": f"https://www.kaggle.com/code/{kernel_slug}",
            }
        else:
            return {
                "status": "error",
                "error": result.get("stderr", result.get("error", "Submit failed")),
            }
    finally:
        shutil.rmtree(kernel_dir, ignore_errors=True)


# ═══════════════════════════════════════════════════════════════════════════════
# POLL + DOWNLOAD
# ═══════════════════════════════════════════════════════════════════════════════

def poll_status(kernel_slug: str) -> str:
    """Notebook status check karo. Returns: queued/running/complete/error."""
    result = _run_kaggle(["kernels", "status", kernel_slug])
    if not result["success"]:
        return "error"

    output = result["stdout"].lower()
    if "complete" in output or "success" in output:
        return "complete"
    elif "running" in output or "loading" in output:
        return "running"
    elif "queued" in output or "waiting" in output:
        return "queued"
    elif "error" in output or "fail" in output:
        return "error"
    return "running"  # default: still going


def download_output(kernel_slug: str, dest_dir: str | Path | None = None) -> dict[str, Any]:
    """Completed notebook se output files download karo."""
    if dest_dir is None:
        dest_dir = _OUTPUT_DIR / kernel_slug.split("/")[-1]
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    result = _run_kaggle(
        ["kernels", "output", kernel_slug, "-p", str(dest_dir)],
        timeout=120,
    )

    if result["success"]:
        files = list(dest_dir.iterdir())
        return {
            "status": "downloaded",
            "dir": str(dest_dir),
            "files": [f.name for f in files],
        }
    return {
        "status": "error",
        "error": result.get("stderr", "Download failed"),
    }


def wait_for_completion(kernel_slug: str, timeout: int = 600, poll_interval: int = 15) -> dict[str, Any]:
    """Notebook complete hone tak wait karo (poll every N seconds)."""
    start = time.time()
    last_status = ""

    while time.time() - start < timeout:
        status = poll_status(kernel_slug)
        elapsed = int(time.time() - start)

        if status != last_status:
            logger.info("[%s] Status: %s (%ds elapsed)", kernel_slug, status, elapsed)
            last_status = status

        if status == "complete":
            return {"status": "complete", "elapsed_seconds": elapsed}
        elif status == "error":
            return {"status": "error", "elapsed_seconds": elapsed, "error": "Notebook failed on GPU"}

        time.sleep(poll_interval)

    return {"status": "timeout", "elapsed_seconds": timeout}


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API — MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def generate_visual(
    content_type: str,
    prompt: str,
    platform: str = "instagram",
    width: int = 0,
    height: int = 0,
    steps: int = 20,
    frames: int = 49,
    timeout: int = 600,
) -> dict[str, Any]:
    """Visual content generate karo — on-demand GPU.

    Args:
        content_type: "image" or "video"
        prompt: AI prompt for generation
        platform: Target platform (for size auto-detection)
        width/height: Override platform size (0 = auto from platform)
        steps: FLUX inference steps (images only)
        frames: CogVideoX frames (videos only, 49=~6s, 81=~10s)
        timeout: Max wait time in seconds

    Returns:
        {
            status: "success" | "error" | "submitted",
            file: "path/to/output.png" | "path/to/output.mp4",
            kernel_slug: "...",
            kaggle_url: "...",
            elapsed_seconds: 123,
        }
    """
    if not _check_kaggle():
        return {"status": "error", "error": "Kaggle CLI not installed. Run: pip install kaggle"}

    # Platform size auto-detect
    if width == 0 or height == 0:
        pw, ph = get_platform_size(platform)
        width = width or pw
        height = height or ph

    # Build code
    if content_type == "video":
        code = COGVIDEO_CODE.format(prompt=prompt.replace('"', '\\"'), frames=frames)
        title = "cogvideo"
        estimated = f"~{frames // 8} sec video"
    else:
        code = FLUX_CODE.format(
            prompt=prompt.replace('"', '\\"'),
            width=width, height=height, steps=steps,
        )
        title = "flux"
        estimated = f"{width}x{height}"

    logger.info("Generating %s: %s (%s)", content_type, prompt[:80], estimated)

    # Submit
    submit = _submit_notebook(code, title)
    if submit["status"] == "error":
        return submit

    kernel_slug = submit["kernel_slug"]

    # Poll until complete
    logger.info("Notebook submitted: %s — polling...", kernel_slug)
    wait_result = wait_for_completion(kernel_slug, timeout=timeout)

    if wait_result["status"] != "complete":
        return {
            "status": wait_result["status"],
            "kernel_slug": kernel_slug,
            "kaggle_url": submit["url"],
            "error": wait_result.get("error", "GPU generation did not complete"),
        }

    # Download output
    download = download_output(kernel_slug)
    if download["status"] == "error":
        return {
            "status": "download_error",
            "kernel_slug": kernel_slug,
            "kaggle_url": submit["url"],
            "error": download["error"],
        }

    # Find the output file
    output_files = download.get("files", [])
    output_file = ""
    for f in output_files:
        if f.endswith((".png", ".jpg", ".jpeg", ".mp4", ".webm")):
            output_file = os.path.join(download["dir"], f)
            break

    return {
        "status": "success",
        "content_type": content_type,
        "file": output_file,
        "output_dir": download["dir"],
        "all_files": output_files,
        "kernel_slug": kernel_slug,
        "kaggle_url": submit["url"],
        "elapsed_seconds": wait_result.get("elapsed_seconds", 0),
        "prompt": prompt,
        "platform": platform,
        "size": f"{width}x{height}" if content_type == "image" else f"{frames} frames",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS (for API routes + direct use)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_image(prompt: str, platform: str = "instagram", width: int = 0, height: int = 0, steps: int = 20) -> dict[str, Any]:
    """Image generate karo."""
    return generate_visual("image", prompt, platform, width, height, steps=steps)


def generate_video(prompt: str, platform: str = "instagram", frames: int = 49) -> dict[str, Any]:
    """Video generate karo."""
    return generate_visual("video", prompt, platform, frames=frames)


def generate_ad_image(product: str, platform: str = "facebook", style: str = "professional") -> dict[str, Any]:
    """Ad creative image generate karo."""
    style_desc = {
        "professional": "clean, professional, modern, corporate",
        "bold": "bold, vibrant, eye-catching, dynamic",
        "minimal": "minimalist, clean, white space, elegant",
        "creative": "creative, artistic, unique, memorable",
    }.get(style, "professional, modern")
    prompt = f"A professional {style} advertisement for {product}, {style_desc}, high quality marketing material"
    return generate_image(prompt, platform)


def generate_social_image(topic: str, platform: str = "instagram") -> dict[str, Any]:
    """Social media post image generate karo."""
    prompt = f"A beautiful, engaging social media post about {topic}, modern design, vibrant colors, professional quality"
    return generate_image(prompt, platform)


def generate_hero_image(topic: str, style: str = "modern") -> dict[str, Any]:
    """Hero/banner image generate karo."""
    prompt = f"A stunning hero banner image about {topic}, {style} design, wide format, professional quality"
    return generate_image(prompt, "blog_hero", width=1920, height=1080)


def check_status(kernel_slug: str) -> str:
    """Notebook status check karo."""
    return poll_status(kernel_slug)


# ═══════════════════════════════════════════════════════════════════════════════
# FALLBACK + BATCH + SMART RETRY
# ═══════════════════════════════════════════════════════════════════════════════


def generate_with_fallback(
    prompt: str,
    platform: str = "instagram",
    width: int = 0,
    height: int = 0,
    steps: int = 20,
    content_type: str = "image",
    frames: int = 49,
) -> dict[str, Any]:
    """Try generate_visual; on failure simplify prompt and retry (max 3 attempts).

    Attempt 1: Original prompt.
    Attempt 2: Remove adjectives (simplified prompt).
    Attempt 3: Switch content_type to "image" with SDXL model.
    """
    _ADJECTIVE_WORDS = {
        "beautiful", "stunning", "amazing", "gorgeous", "elegant",
        "gorgeous", "vibrant", "mesmerizing", "breathtaking", "captivating",
        "exquisite", "luminous", "radiant", "glorious", "magnificent",
        "fantastic", "brilliant", "wonderful", "spectacular", "fabulous",
        "luxurious", "premium", "high-quality", "ultra", "professional",
    }

    def _simplify_prompt(original: str) -> str:
        """Remove adjectives from prompt to reduce model confusion."""
        words = original.split()
        simplified = [w for w in words if w.lower().strip(",.!?;:") not in _ADJECTIVE_WORDS]
        return " ".join(simplified) if simplified else original

    last_error = ""

    for attempt in range(1, 4):
        current_prompt = prompt
        current_type = content_type
        current_steps = steps

        if attempt == 2:
            # Attempt 2: simplified prompt (adjectives removed)
            current_prompt = _simplify_prompt(prompt)
            logger.info("Fallback attempt 2: simplified prompt '%s'", current_prompt[:80])
        elif attempt == 3:
            # Attempt 3: force image with SDXL-compatible settings
            current_type = "image"
            current_prompt = _simplify_prompt(prompt)
            current_steps = 25
            width = width or 1024
            height = height or 1024
            logger.info("Fallback attempt 3: force image mode with simplified prompt")

        result = generate_visual(
            content_type=current_type,
            prompt=current_prompt,
            platform=platform,
            width=width,
            height=height,
            steps=current_steps,
            frames=frames,
        )

        if result.get("status") == "success":
            result["attempts"] = attempt
            if attempt > 1:
                result["fallback_used"] = True
                result["fallback_reason"] = f"Attempt {attempt}: {'simplified prompt' if attempt == 2 else 'forced image mode'}"
            return result

        last_error = result.get("error", f"Attempt {attempt} failed")
        logger.warning(
            "generate_with_fallback attempt %d failed: %s", attempt, last_error,
        )

    return {
        "status": "error",
        "error": f"All 3 attempts failed. Last error: {last_error}",
        "attempts": 3,
        "fallback_used": True,
    }


def batch_generate(prompts: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate visuals for a list of prompt dicts sequentially.

    Each dict should contain:
        prompt (str): The AI prompt.
        platform (str, optional): Target platform.
        width (int, optional): Image width.
        height (int, optional): Image height.
        steps (int, optional): Inference steps.
        content_type (str, optional): "image" or "video".
        frames (int, optional): Video frames.

    Returns:
        {status, results: [...], success_count, failure_count}

    Used for content calendars where multiple assets are needed.
    """
    results: list[dict[str, Any]] = []
    success_count = 0
    failure_count = 0

    for i, item in enumerate(prompts):
        prompt_text = item.get("prompt", "")
        if not prompt_text:
            results.append({"index": i, "status": "skipped", "error": "Empty prompt"})
            failure_count += 1
            continue

        logger.info("batch_generate [%d/%d]: %s", i + 1, len(prompts), prompt_text[:60])

        result = generate_with_fallback(
            prompt=prompt_text,
            platform=item.get("platform", "instagram"),
            width=item.get("width", 0),
            height=item.get("height", 0),
            steps=item.get("steps", 20),
            content_type=item.get("content_type", "image"),
            frames=item.get("frames", 49),
        )

        result["index"] = i
        results.append(result)

        if result.get("status") == "success":
            success_count += 1
        else:
            failure_count += 1

        # Small delay between submissions to avoid Kaggle rate limits
        if i < len(prompts) - 1:
            time.sleep(5)

    return {
        "status": "completed",
        "results": results,
        "success_count": success_count,
        "failure_count": failure_count,
        "total": len(prompts),
    }


def smart_retry(
    kernel_slug: str, max_retries: int = 2, timeout: int = 600
) -> dict[str, Any]:
    """If a notebook fails, resubmit with simplified code and check status.

    Args:
        kernel_slug: The original kernel slug that failed.
        max_retries: Maximum retry attempts (default 2).
        timeout: Max wait per attempt in seconds.

    Returns:
        {status, kernel_slug, retries_used, ...}
    """
    for attempt in range(1, max_retries + 1):
        logger.info("smart_retry attempt %d/%d for %s", attempt, max_retries, kernel_slug)

        # Check current status first
        status = poll_status(kernel_slug)
        if status == "complete":
            return {
                "status": "complete",
                "kernel_slug": kernel_slug,
                "retries_used": attempt - 1,
            }
        elif status != "error":
            # Still running or queued -- wait
            wait_result = wait_for_completion(kernel_slug, timeout=timeout)
            if wait_result["status"] == "complete":
                return {
                    "status": "complete",
                    "kernel_slug": kernel_slug,
                    "retries_used": attempt - 1,
                }

        # Notebook errored -- attempt resubmission with simplified code
        logger.warning(
            "Kernel %s failed (attempt %d). Resubmitting...", kernel_slug, attempt,
        )

        # Extract username and base slug to create a new submission
        username = _get_username()
        if not username:
            return {
                "status": "error",
                "error": "Kaggle credentials not found for retry",
                "retries_used": attempt,
            }

        # Build simplified notebook -- reduce steps, use smaller size
        simplified_code = FLUX_CODE.format(
            prompt="a simple clear photograph",
            width=512,
            height=512,
            steps=15,
        )
        title = f"retry-{attempt}"

        submit = _submit_notebook(simplified_code, title)
        if submit["status"] == "error":
            return {
                "status": "error",
                "error": f"Retry {attempt} submission failed: {submit.get('error', '')}",
                "retries_used": attempt,
            }

        kernel_slug = submit["kernel_slug"]
        logger.info("Retry %d submitted as %s", attempt, kernel_slug)

        # Wait for retry to complete
        wait_result = wait_for_completion(kernel_slug, timeout=timeout)
        if wait_result["status"] == "complete":
            # Download output
            download = download_output(kernel_slug)
            if download["status"] == "downloaded":
                output_files = download.get("files", [])
                output_file = ""
                for f in output_files:
                    if f.endswith((".png", ".jpg", ".jpeg", ".mp4", ".webm")):
                        output_file = os.path.join(download["dir"], f)
                        break
                return {
                    "status": "complete",
                    "kernel_slug": kernel_slug,
                    "file": output_file,
                    "retries_used": attempt,
                }

    return {
        "status": "error",
        "kernel_slug": kernel_slug,
        "error": f"All {max_retries} retries exhausted",
        "retries_used": max_retries,
    }
