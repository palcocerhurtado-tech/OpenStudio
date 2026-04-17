"""
bridge/asset_router.py

The heart of OpenStudio's integration. Routes asset generation requests
from OpenMontage pipelines to the best available model in Open Generative AI's
200+ model library.

Usage in pipelines:
    from bridge.asset_router import generate_image, generate_video, lipsync
"""

import os
import json
import time
import requests
from pathlib import Path
from typing import Optional

# ─── Configuration ────────────────────────────────────────────────────────────

MUAPI_BASE = "https://api.muapi.ai/api/v1"
MUAPI_KEY = os.getenv("MUAPI_KEY", "")

# Model preference tiers — used when model="auto"
IMAGE_TIERS = {
    "cinematic":    ["flux-kontext-pro", "flux-dev", "dall-e-3", "sdxl"],
    "product":      ["nano-banana-2", "flux-kontext-pro", "ideogram-v3"],
    "illustration": ["midjourney-v7", "flux-dev", "sdxl"],
    "diagram":      ["sdxl", "flux-dev"],
    "budget":       ["sdxl", "flux-schnell"],
}

VIDEO_TIERS = {
    "cinematic":    ["kling-v3", "veo-3", "runway-gen4", "wan2.6"],
    "product":      ["kling-v2.1", "seedance-2.0", "minimax"],
    "social":       ["seedance-2.0", "kling-v2.1", "hailuo-2.3"],
    "budget":       ["wan2.6", "seedance-2.0", "cogvideo-5b-local"],
}

LIPSYNC_TIERS = {
    "portrait":     ["ltx-2.3-lipsync", "infinite-talk", "wan2.2-speech-to-video"],
    "video":        ["sync-lipsync", "latentsync", "creatify-lipsync"],
}

# ─── Availability Check ───────────────────────────────────────────────────────

def _has_muapi() -> bool:
    return bool(MUAPI_KEY)

def _has_fal() -> bool:
    return bool(os.getenv("FAL_KEY"))

def _has_openai() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))

def _has_local_gpu() -> bool:
    return os.getenv("VIDEO_GEN_LOCAL_ENABLED", "false").lower() == "true"


# ─── Core API Client ─────────────────────────────────────────────────────────

def _muapi_submit(endpoint: str, payload: dict) -> Optional[str]:
    """Submit a generation job to Muapi and return request_id."""
    if not _has_muapi():
        raise RuntimeError("MUAPI_KEY not set. Get a free key at https://muapi.ai")
    
    r = requests.post(
        f"{MUAPI_BASE}/{endpoint}",
        headers={"x-api-key": MUAPI_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("request_id") or data.get("id")


def _muapi_poll(request_id: str, timeout: int = 300) -> dict:
    """Poll Muapi until job completes. Returns result dict."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = requests.get(
            f"{MUAPI_BASE}/predictions/{request_id}/result",
            headers={"x-api-key": MUAPI_KEY},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        status = data.get("status", "")
        if status == "completed":
            return data
        if status in ("failed", "error"):
            raise RuntimeError(f"Generation failed: {data.get('error', 'unknown')}")
        time.sleep(3)
    raise TimeoutError(f"Generation timed out after {timeout}s")


def _muapi_upload(file_path: str) -> str:
    """Upload a local file to Muapi and return hosted URL."""
    with open(file_path, "rb") as f:
        r = requests.post(
            f"{MUAPI_BASE}/upload_file",
            headers={"x-api-key": MUAPI_KEY},
            files={"file": f},
            timeout=60,
        )
    r.raise_for_status()
    return r.json()["url"]


# ─── Model Selection ─────────────────────────────────────────────────────────

def _select_model(tier_map: dict, style: str, model: str) -> str:
    """Select the best available model given style and explicit override."""
    if model and model != "auto":
        return model
    
    candidates = tier_map.get(style, tier_map.get("budget", []))
    
    # Return first candidate (in production: check API key availability)
    for candidate in candidates:
        if "local" in candidate and not _has_local_gpu():
            continue
        return candidate
    
    return candidates[0] if candidates else "sdxl"


# ─── Public API ──────────────────────────────────────────────────────────────

def generate_image(
    prompt: str,
    model: str = "auto",
    style: str = "cinematic",
    reference_images: list[str] = None,
    aspect_ratio: str = "16:9",
    resolution: str = "1K",
    output_path: Optional[str] = None,
) -> dict:
    """
    Generate an image using the best available model.
    
    Args:
        prompt: Text description of the image
        model: Model name or "auto" to select automatically
        style: cinematic | product | illustration | diagram | budget
        reference_images: Local file paths or URLs for image-to-image
        aspect_ratio: e.g. "16:9", "9:16", "1:1"
        resolution: "1K", "2K", "4K"
        output_path: Where to save the result (optional)
    
    Returns:
        dict with keys: url, local_path, model_used, cost_estimate
    """
    selected = _select_model(IMAGE_TIERS, style, model)
    
    payload = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
    }
    
    # Handle reference images
    if reference_images:
        uploaded = []
        for img in reference_images:
            if img.startswith("http"):
                uploaded.append(img)
            else:
                uploaded.append(_muapi_upload(img))
        
        if len(uploaded) == 1:
            payload["image_url"] = uploaded[0]
        else:
            payload["images_list"] = uploaded
        
        endpoint = f"{selected}-i2i"
    else:
        endpoint = selected
    
    request_id = _muapi_submit(endpoint, payload)
    result = _muapi_poll(request_id)
    
    output_url = result.get("output", [None])[0] or result.get("image_url")
    
    # Optionally save locally
    local_path = None
    if output_path and output_url:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        img_data = requests.get(output_url, timeout=30).content
        with open(output_path, "wb") as f:
            f.write(img_data)
        local_path = output_path
    
    return {
        "url": output_url,
        "local_path": local_path,
        "model_used": selected,
        "request_id": request_id,
    }


def generate_video(
    prompt: str,
    model: str = "auto",
    style: str = "cinematic",
    duration: int = 5,
    aspect_ratio: str = "16:9",
    start_frame: Optional[str] = None,
    output_path: Optional[str] = None,
) -> dict:
    """
    Generate a video clip using the best available model.
    
    Args:
        prompt: Text description of the video
        model: Model name or "auto"
        style: cinematic | product | social | budget
        duration: Duration in seconds (5, 10, 15)
        aspect_ratio: "16:9", "9:16", "1:1"
        start_frame: Local path or URL of starting frame image
        output_path: Where to save the result
    
    Returns:
        dict with keys: url, local_path, model_used, duration
    """
    selected = _select_model(VIDEO_TIERS, style, model)
    
    payload = {
        "prompt": prompt,
        "duration": duration,
        "aspect_ratio": aspect_ratio,
    }
    
    if start_frame:
        frame_url = start_frame if start_frame.startswith("http") else _muapi_upload(start_frame)
        payload["image_url"] = frame_url
        endpoint = f"{selected}-i2v"
    else:
        endpoint = selected
    
    request_id = _muapi_submit(endpoint, payload)
    result = _muapi_poll(request_id, timeout=600)  # Video takes longer
    
    output_url = result.get("output", [None])[0] or result.get("video_url")
    
    local_path = None
    if output_path and output_url:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        video_data = requests.get(output_url, timeout=120).content
        with open(output_path, "wb") as f:
            f.write(video_data)
        local_path = output_path
    
    return {
        "url": output_url,
        "local_path": local_path,
        "model_used": selected,
        "duration": duration,
        "request_id": request_id,
    }


def lipsync(
    portrait_path: str,
    audio_path: str,
    model: str = "auto",
    mode: str = "portrait",
    resolution: str = "720p",
    prompt: Optional[str] = None,
    output_path: Optional[str] = None,
) -> dict:
    """
    Generate a lip-synced talking video.
    
    Args:
        portrait_path: Local path or URL to portrait image (or video if mode="video")
        audio_path: Local path or URL to audio file
        model: Model name or "auto"
        mode: "portrait" (image+audio→video) or "video" (video+audio→lipsync)
        resolution: "480p", "720p", "1080p"
        prompt: Optional motion style guidance
        output_path: Where to save the result
    
    Returns:
        dict with keys: url, local_path, model_used
    """
    selected = _select_model(LIPSYNC_TIERS, mode, model)
    
    # Upload assets
    portrait_url = portrait_path if portrait_path.startswith("http") else _muapi_upload(portrait_path)
    audio_url = audio_path if audio_path.startswith("http") else _muapi_upload(audio_path)
    
    payload = {
        "resolution": resolution,
    }
    
    if mode == "portrait":
        payload["image_url"] = portrait_url
        payload["audio_url"] = audio_url
    else:
        payload["video_url"] = portrait_url
        payload["audio_url"] = audio_url
    
    if prompt:
        payload["prompt"] = prompt
    
    request_id = _muapi_submit(selected, payload)
    result = _muapi_poll(request_id, timeout=600)
    
    output_url = result.get("output", [None])[0] or result.get("video_url")
    
    local_path = None
    if output_path and output_url:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        video_data = requests.get(output_url, timeout=120).content
        with open(output_path, "wb") as f:
            f.write(video_data)
        local_path = output_path
    
    return {
        "url": output_url,
        "local_path": local_path,
        "model_used": selected,
        "request_id": request_id,
    }


# ─── Cost Estimation ──────────────────────────────────────────────────────────

# Approximate costs in USD (Muapi pricing, may vary)
COST_ESTIMATES = {
    "image": {
        "flux-kontext-pro": 0.05,
        "flux-dev": 0.03,
        "dall-e-3": 0.04,
        "midjourney-v7": 0.06,
        "sdxl": 0.01,
        "nano-banana-2": 0.04,
        "default": 0.03,
    },
    "video": {
        "kling-v3": 0.35,
        "veo-3": 0.50,
        "runway-gen4": 0.40,
        "seedance-2.0": 0.20,
        "wan2.6": 0.15,
        "default": 0.25,
    },
    "lipsync": {
        "ltx-2.3-lipsync": 0.10,
        "infinite-talk": 0.08,
        "sync-lipsync": 0.12,
        "default": 0.10,
    },
}


def estimate_cost(asset_type: str, model: str, count: int = 1) -> float:
    """Estimate cost in USD before executing generation."""
    tier = COST_ESTIMATES.get(asset_type, {})
    per_unit = tier.get(model, tier.get("default", 0.05))
    return round(per_unit * count, 4)
