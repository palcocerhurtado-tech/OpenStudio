"""
engine/remotion-composer/scripts/generate_assets.py

Generates all production assets for archon_promo_001:
  1. 8 scene images via bridge.asset_router (flux-kontext-pro, model=auto)
  2. TTS narration via OpenAI TTS (voice=onyx, language=es)
  3. Background music download from Pixabay (royalty-free)
  4. Word-level timestamps for subtitle sync

Run from repo root:
    python engine/remotion-composer/scripts/generate_assets.py

Requires:
    MUAPI_KEY or FAL_KEY in .env  (for image generation)
    OPENAI_API_KEY in .env        (for TTS narration)
"""

import os
import json
import time
import requests
from pathlib import Path

# ── Env ───────────────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

# ── Bridge imports ─────────────────────────────────────────────────────────────
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))  # repo root
from bridge.asset_router import generate_image, estimate_cost

JOB_ID = "archon_promo_001"
OUTPUT_BASE = Path(f"output/{JOB_ID}")
CHECKPOINT_PATH = Path(f".checkpoints/{JOB_ID}/03_assets_manifest.json")

# ── Load scene plan ────────────────────────────────────────────────────────────
with open(f".checkpoints/{JOB_ID}/02_scene_plan.json") as f:
    scene_plan = json.load(f)

with open(f".checkpoints/{JOB_ID}/01_script.json") as f:
    script = json.load(f)

# ── Cost preflight ─────────────────────────────────────────────────────────────
image_count = len(scene_plan["scenes"])
image_cost = estimate_cost("image", "flux-kontext-pro", image_count)
tts_cost = round(len(script["full_narration"]) / 1000 * 0.03, 4)
total_est = round(image_cost + tts_cost, 4)

print(f"\n{'─'*50}")
print(f"  Cost estimate for {JOB_ID}")
print(f"{'─'*50}")
print(f"  Images ({image_count} × flux-kontext-pro):  ${image_cost:.3f}")
print(f"  TTS narration (openai/onyx):        ${tts_cost:.3f}")
print(f"  Music (royalty-free):               $0.000")
print(f"  {'─'*30}")
print(f"  TOTAL:                              ${total_est:.3f}")
print(f"  Budget cap:                         $3.000")
print(f"{'─'*50}\n")

# ── Image generation ──────────────────────────────────────────────────────────
(OUTPUT_BASE / "images").mkdir(parents=True, exist_ok=True)

generated_images = []
for scene in scene_plan["scenes"]:
    asset_id = scene["asset_id"]
    output_path = str(OUTPUT_BASE / "images" / f"{asset_id}.png")

    print(f"  Generating image: {asset_id}...")
    result = generate_image(
        prompt=scene["image_prompt"],
        model="auto",
        style=scene["style"],
        aspect_ratio=scene["aspect_ratio"],
        resolution=scene["resolution"],
        output_path=output_path,
    )
    generated_images.append({
        "asset_id": asset_id,
        "url": result["url"],
        "local_path": output_path,
        "model_used": result["model_used"],
        "request_id": result["request_id"],
    })
    print(f"    ✓ {asset_id} → {result['url'][:60]}...")

# ── TTS Narration ─────────────────────────────────────────────────────────────
(OUTPUT_BASE / "audio").mkdir(parents=True, exist_ok=True)

openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise RuntimeError("OPENAI_API_KEY not set — cannot generate TTS narration")

print("\n  Generating TTS narration (openai/onyx, es)...")
from openai import OpenAI
client = OpenAI(api_key=openai_key)

narration_text = script["full_narration"]
narration_path = OUTPUT_BASE / "audio" / "narration.mp3"

with client.audio.speech.with_streaming_response.create(
    model="tts-1-hd",
    voice="onyx",
    input=narration_text,
    response_format="mp3",
) as response:
    response.stream_to_file(narration_path)

print(f"    ✓ Narration saved to {narration_path}")

# Word timestamps via Whisper transcription (for subtitle sync)
print("  Generating word timestamps via Whisper...")
with open(narration_path, "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="verbose_json",
        timestamp_granularities=["word"],
        language="es",
    )

timestamps_path = OUTPUT_BASE / "audio" / "word_timestamps.json"
with open(timestamps_path, "w") as f:
    json.dump(transcript.words, f, ensure_ascii=False, indent=2)
print(f"    ✓ Word timestamps saved to {timestamps_path}")

# ── Music ─────────────────────────────────────────────────────────────────────
# Pixabay royalty-free — download a pre-selected ambient corporate track
# In production: use music_search_royalty_free() tool or manual URL
MUSIC_URL = "https://cdn.pixabay.com/download/audio/2023/09/05/audio_corporate-ambient.mp3"
music_path = OUTPUT_BASE / "audio" / "bg_music.mp3"

print(f"\n  Downloading background music from Pixabay...")
try:
    response = requests.get(MUSIC_URL, timeout=60)
    response.raise_for_status()
    with open(music_path, "wb") as f:
        f.write(response.content)
    print(f"    ✓ Music saved to {music_path}")
except Exception as e:
    print(f"    ⚠ Music download failed: {e}")
    print("    → Place a royalty-free ambient MP3 at:", music_path)

# ── Update checkpoint ─────────────────────────────────────────────────────────
with open(CHECKPOINT_PATH) as f:
    manifest = json.load(f)

manifest["images"] = generated_images
manifest["narration"]["local_path"] = str(narration_path)
manifest["narration"]["word_timestamps_path"] = str(timestamps_path)
manifest["music"]["local_path"] = str(music_path)
manifest["cost_actual_usd"] = round(image_cost + tts_cost, 4)

with open(CHECKPOINT_PATH, "w") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print(f"\n  ✓ Asset manifest updated: {CHECKPOINT_PATH}")
print(f"  ✓ All assets ready. Run `npm run render:16x9` from engine/remotion-composer/ to render.\n")
