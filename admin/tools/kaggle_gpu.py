"""Kaggle GPU — On-demand visual content generation (v2).

GPU: T4x2 (enforced via accelerator metadata)
Image: FLUX.1-schnell (bfloat16, 4 steps, guidance 3.5, text-in-image)
Video: CogVideoX-2b (float16, on-demand only)

Flow:
  1. generate_visual(content_type, prompt, ...)
  2. Creates Kaggle notebook with FLUX/CogVideoX code
  3. Submits to T4x2 GPU via Kaggle API
  4. Polls until complete
  5. Downloads output to data/outputs/
  6. Returns local file path
  7. Memory cleanup after each task
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

FLUX_CODE = '''# TAGS Content Agent — FLUX.1-schnell Image Generation (T4x2)
# On-demand: model loaded ONLY during generation, cleaned after
import subprocess, sys, json, os, gc, traceback, time

_start = time.time()
print("=== FLUX.1-schnell Image Generation ===")
print(f"PyTorch: {__import__('torch').__version__}")

import torch
from diffusers import FluxPipeline
from PIL import Image

# ── GPU validation (must be sm_70+ for bfloat16) ──
if not torch.cuda.is_available():
    print(json.dumps({{"status": "error", "reason": "No CUDA GPU — T4x2 required"}}))
    sys.exit(1)

cap = torch.cuda.get_device_capability(0)
gpu_name = torch.cuda.get_device_name(0)
vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
print(f"GPU: {{gpu_name}} | sm_{{cap[0]}}{{cap[1]}} | {{vram:.1f}}GB VRAM")

if cap[0] < 7:
    print(json.dumps({{"status": "error", "reason": f"GPU sm_{{cap[0]}}{{cap[1]}} too old — need sm_70+ (T4)"}}))
    sys.exit(1)

DTYPE = torch.bfloat16
print(f"Using dtype: {{DTYPE}}")

# ── Load FLUX.1-schnell (ON-DEMAND — loaded only for this task) ──
HF_TOKEN = os.environ.get("HF_TOKEN") or os.environ.get("HF_TOKEN_READ", "")
print(f"HF_TOKEN: {'set' if HF_TOKEN else 'not set — using SDXL fallback'}")

if HF_TOKEN:
    MODEL_NAME = "black-forest-labs/FLUX.1-schnell"
    print(f"Loading {{MODEL_NAME}}...")
else:
    MODEL_NAME = "stabilityai/stable-diffusion-xl-base-1.0"
    print(f"No HF_TOKEN — loading {{MODEL_NAME}} (free, no auth)...")

sys.stdout.flush()
try:
    if HF_TOKEN:
        pipe = FluxPipeline.from_pretrained(
            MODEL_NAME, torch_dtype=DTYPE, token=HF_TOKEN,
        )
    else:
        from diffusers import DiffusionPipeline
        pipe = DiffusionPipeline.from_pretrained(
            MODEL_NAME, torch_dtype=DTYPE,
        )
    pipe.enable_model_cpu_offload()
    print("Model loaded into VRAM")
    sys.stdout.flush()
except Exception as e:
    print(f"MODEL LOAD ERROR: {{e}}")
    traceback.print_exc()
    sys.exit(1)

# ── Generate ──
PROMPT = "{prompt}"
WIDTH = {width}
HEIGHT = {height}

# FLUX.1-schnell: optimized for 4 steps, guidance 3.5
# Supports text-in-image for ad banners/posters
print(f"Generating: {{PROMPT[:120]}}")
print(f"Params: {{WIDTH}}x{{HEIGHT}}, steps=4, guidance=3.5")
sys.stdout.flush()
try:
    image = pipe(
        PROMPT,
        width=WIDTH,
        height=HEIGHT,
        num_inference_steps=4,
        guidance_scale=3.5,
    ).images[0]
    image.save("output.png")
    sz = os.path.getsize("output.png")
    elapsed = round(time.time() - _start, 1)
    print(json.dumps({{
        "status": "success",
        "file": "output.png",
        "size_bytes": sz,
        "gpu": gpu_name,
        "sm": f"sm_{{cap[0]}}{{cap[1]}}",
        "dtype": str(DTYPE),
        "model": "{model}",
        "steps": 4,
        "guidance": 3.5,
        "elapsed_seconds": elapsed
    }}))
except torch.cuda.OutOfMemoryError:
    print(json.dumps({"status": "error", "error": "VRAM_OOM", "reason": "CUDA out of memory - try smaller resolution", "gpu": gpu_name, "vram_gb": round(vram, 1)}))
    sys.exit(1)
except Exception as e:
    print(f"GENERATION ERROR: {{e}}")
    traceback.print_exc()
    sys.exit(1)
finally:
    # ── MEMORY CLEANUP (on-demand: free VRAM after task) ──
    try:
        del pipe
        gc.collect()
        torch.cuda.empty_cache()
        print("VRAM cleaned up")
    except Exception:
        pass
'''


COGVIDEO_CODE = '''# TAGS Content Agent — CogVideoX-2b Video Generation (T4x2)
# Triggered ONLY when video prompt is explicitly provided
# On-demand: model loaded ONLY during generation, cleaned after
import subprocess, sys, json, os, gc, traceback, time

_start = time.time()
print("=== CogVideoX-2b Video Generation ===")
print(f"PyTorch: {__import__('torch').__version__}")

import torch
from diffusers import CogVideoXPipeline
import imageio

# ── GPU validation (needs sm_70+ for float16) ──
if not torch.cuda.is_available():
    print(json.dumps({{"status": "error", "reason": "No CUDA GPU — T4x2 required"}}))
    sys.exit(1)

cap = torch.cuda.get_device_capability(0)
gpu_name = torch.cuda.get_device_name(0)
vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
print(f"GPU: {{gpu_name}} | sm_{{cap[0]}}{{cap[1]}} | {{vram:.1f}}GB VRAM")

if cap[0] < 7:
    print(json.dumps({{"status": "error", "reason": f"GPU sm_{{cap[0]}}{{cap[1]}} too old — need sm_70+ (T4)"}}))
    sys.exit(1)

DTYPE = torch.bfloat16 if cap[0] >= 8 else torch.float16
print(f"Using dtype: {{DTYPE}}")

# ── Load CogVideoX-2b (ON-DEMAND — loaded only for this task) ──
print("Loading THUDM/CogVideoX-2b (~5GB)...")
sys.stdout.flush()
try:
    pipe = CogVideoXPipeline.from_pretrained("THUDM/CogVideoX-2b", torch_dtype=DTYPE)
    pipe.enable_model_cpu_offload()
    print("Model loaded into VRAM")
    sys.stdout.flush()
except torch.cuda.OutOfMemoryError:
    print(json.dumps({"status": "error", "error": "VRAM_OOM", "reason": "CUDA OOM during model load - CogVideoX needs ~8GB"}))
    sys.exit(1)
except Exception as e:
    print(f"MODEL LOAD ERROR: {{e}}")
    traceback.print_exc()
    sys.exit(1)

# ── Generate video ──
PROMPT = "{prompt}"
NUM_FRAMES = {frames}

print(f"Generating video: {{PROMPT[:120]}}")
print(f"Params: {{NUM_FRAMES}} frames, 50 steps, guidance 6.0")
sys.stdout.flush()
try:
    video = pipe(
        PROMPT,
        num_videos_per_prompt=1,
        num_inference_steps=50,
        num_frames=NUM_FRAMES,
        guidance_scale=6.0,
    ).videos[0]
    imageio.mimsave("output.mp4", video, fps=8)
    sz = os.path.getsize("output.mp4")
    elapsed = round(time.time() - _start, 1)
    print(json.dumps({{
        "status": "success",
        "file": "output.mp4",
        "size_bytes": sz,
        "frames": NUM_FRAMES,
        "duration_seconds": round(NUM_FRAMES / 8, 1),
        "gpu": gpu_name,
        "sm": f"sm_{{cap[0]}}{{cap[1]}}",
        "dtype": str(DTYPE),
        "elapsed_seconds": elapsed
    }}))
except torch.cuda.OutOfMemoryError:
    reduced_frames = max(16, NUM_FRAMES // 2)
    print(f"OOM at {NUM_FRAMES} frames - retrying with {reduced_frames} frames")
    torch.cuda.empty_cache()
    gc.collect()
    try:
        video = pipe(PROMPT, num_videos_per_prompt=1, num_inference_steps=50, num_frames=reduced_frames, guidance_scale=6.0).videos[0]
        imageio.mimsave("output.mp4", video, fps=8)
        sz = os.path.getsize("output.mp4")
        elapsed = round(time.time() - _start, 1)
        print(json.dumps({"status": "success", "file": "output.mp4", "size_bytes": sz, "frames": reduced_frames, "duration_seconds": round(reduced_frames / 8, 1), "gpu": gpu_name, "sm": f"sm_{cap[0]}{cap[1]}", "dtype": str(DTYPE), "elapsed_seconds": elapsed, "warning": f"Reduced from {NUM_FRAMES} to {reduced_frames} frames due to VRAM limit"}))
    except Exception as e2:
        print(json.dumps({"status": "error", "error": "VRAM_OOM", "reason": f"OOM even at {reduced_frames} frames: {e2}", "gpu": gpu_name, "vram_gb": round(vram, 1)}))
        sys.exit(1)
except Exception as e:
    print(f"VIDEO ERROR: {{e}}")
    traceback.print_exc()
    sys.exit(1)
finally:
    # ── MEMORY CLEANUP (on-demand: free VRAM after task) ──
    try:
        del pipe
        gc.collect()
        torch.cuda.empty_cache()
        print("VRAM cleaned up")
    except Exception:
        pass
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
    "ad_banner": (1200, 628),
    "ad_poster": (1080, 1350),
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
    """Build Kaggle-format notebook JSON with T4x2 GPU enforcement."""
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kaggle": {
                "accelerator": "gpuT4x2",
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
    """Build kernel-metadata.json for Kaggle CLI — T4x2 GPU enforced."""
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
        "accelerator": "gpuT4x2",
    }


def _submit_notebook(code_source: str, title: str) -> dict[str, Any]:
    """Notebook banao aur Kaggle pe submit karo. Returns kernel_slug."""
    username = _get_username()
    if not username:
        return {"status": "error", "error": "Kaggle credentials not found. Set KAGGLE_USERNAME in env or ~/.kaggle/kaggle.json"}

    kernel_dir = tempfile.mkdtemp(prefix=f"kaggle_{title}_")

    try:
        notebook = _build_notebook(code_source)
        with open(os.path.join(kernel_dir, "notebook.ipynb"), "w") as f:
            json.dump(notebook, f, indent=2)

        metadata = _build_metadata(username, title)
        with open(os.path.join(kernel_dir, "kernel-metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)

        kernel_slug = metadata["id"]

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
    return "running"


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
    steps: int = 4,
    frames: int = 49,
    timeout: int = 600,
) -> dict[str, Any]:
    """Visual content generate karo — on-demand T4x2 GPU.

    Args:
        content_type: "image" or "video"
        prompt: AI prompt for generation (supports text-in-image for ads)
        platform: Target platform (for size auto-detection)
        width/height: Override platform size (0 = auto from platform)
        steps: Ignored — FLUX.1-schnell always uses 4 steps
        frames: CogVideoX frames (49=~6s, 60=~7.5s, 81=~10s)
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
            width=width, height=height,
            model="FLUX.1-schnell",
        )
        title = "flux-schnell"
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

def generate_image(prompt: str, platform: str = "instagram", width: int = 0, height: int = 0, steps: int = 4) -> dict[str, Any]:
    """Image generate karo — FLUX.1-schnell (4 steps, text-in-image support)."""
    return generate_visual("image", prompt, platform, width, height, steps=steps)


def generate_video(prompt: str, platform: str = "instagram", frames: int = 49) -> dict[str, Any]:
    """Video generate karo — CogVideoX-2b (triggered only when video prompt provided)."""
    return generate_visual("video", prompt, platform, frames=frames)


def generate_ad_image(product: str, platform: str = "facebook", style: str = "professional") -> dict[str, Any]:
    """Ad creative image generate karo — supports text-in-image for banners/posters."""
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
    steps: int = 4,
    content_type: str = "image",
    frames: int = 49,
) -> dict[str, Any]:
    """Try generate_visual; on failure simplify prompt and retry (max 3 attempts)."""
    _ADJECTIVE_WORDS = {
        "beautiful", "stunning", "amazing", "gorgeous", "elegant",
        "vibrant", "mesmerizing", "breathtaking", "captivating",
        "exquisite", "luminous", "radiant", "glorious", "magnificent",
        "fantastic", "brilliant", "wonderful", "spectacular", "fabulous",
        "luxurious", "premium", "high-quality", "ultra", "professional",
    }

    def _simplify_prompt(original: str) -> str:
        words = original.split()
        simplified = [w for w in words if w.lower().strip(",.!?;:") not in _ADJECTIVE_WORDS]
        return " ".join(simplified) if simplified else original

    last_error = ""

    for attempt in range(1, 4):
        current_prompt = prompt
        current_type = content_type

        if attempt == 2:
            current_prompt = _simplify_prompt(prompt)
            logger.info("Fallback attempt 2: simplified prompt '%s'", current_prompt[:80])
        elif attempt == 3:
            current_type = "image"
            current_prompt = _simplify_prompt(prompt)
            width = width or 1024
            height = height or 1024
            logger.info("Fallback attempt 3: force image mode with simplified prompt")

        result = generate_visual(
            content_type=current_type,
            prompt=current_prompt,
            platform=platform,
            width=width,
            height=height,
            steps=steps,
            frames=frames,
        )

        if result.get("status") == "success":
            result["attempts"] = attempt
            if attempt > 1:
                result["fallback_used"] = True
                result["fallback_reason"] = f"Attempt {attempt}: {'simplified prompt' if attempt == 2 else 'forced image mode'}"
            return result

        last_error = result.get("error", f"Attempt {attempt} failed")
        logger.warning("generate_with_fallback attempt %d failed: %s", attempt, last_error)

    return {
        "status": "error",
        "error": f"All 3 attempts failed. Last error: {last_error}",
        "attempts": 3,
        "fallback_used": True,
    }


def batch_generate(prompts: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate visuals for a list of prompt dicts sequentially."""
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
            steps=item.get("steps", 4),
            content_type=item.get("content_type", "image"),
            frames=item.get("frames", 49),
        )

        result["index"] = i
        results.append(result)

        if result.get("status") == "success":
            success_count += 1
        else:
            failure_count += 1

        if i < len(prompts) - 1:
            time.sleep(5)

    return {
        "status": "completed",
        "results": results,
        "success_count": success_count,
        "failure_count": failure_count,
        "total": len(prompts),
    }
