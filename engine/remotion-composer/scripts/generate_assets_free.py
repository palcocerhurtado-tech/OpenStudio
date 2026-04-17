"""
engine/remotion-composer/scripts/generate_assets_free.py

Zero-cost asset pipeline for archon_promo_001:
  Images  — Pexels stock search (PEXELS_API_KEY required)
            Falls back to an FFmpeg colored placeholder per scene if the
            query returns no results or the key is absent.
  Music   — Pixabay audio search (only when PIXABAY_API_KEY is set)
            Completely skipped + a silent WAV is written when the key is empty.
  TTS     — skipped in this variant (free run, no API keys required)

Run from repo root:
    python engine/remotion-composer/scripts/generate_assets_free.py
"""

import json
import os
import subprocess
import sys
import wave
import struct
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
JOB_ID = "archon_promo_001"
REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_BASE = REPO_ROOT / "output" / JOB_ID
CHECKPOINT_DIR = REPO_ROOT / ".checkpoints" / JOB_ID

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "")

PEXELS_SEARCH = "https://api.pexels.com/v1/search"
PIXABAY_AUDIO = "https://pixabay.com/api/"

# Per-scene Pexels search query (short, literal terms work best with stock search)
SCENE_QUERIES = {
    "scene_01_problem":    "office paperwork documents desk",
    "scene_02_gap":        "technology digital transformation",
    "scene_03_archon":     "Zaragoza Spain city skyline",
    "scene_04_documents":  "digital document management files",
    "scene_05_onboarding": "business meeting handshake onboarding",
    "scene_06_reporting":  "data analytics dashboard business",
    "scene_07_trust":      "architecture precision structure abstract",
    "scene_08_cta":        "corporate navy blue office abstract",
}

# Fallback placeholder color per scene (brand palette variants)
SCENE_COLORS = {
    "scene_01_problem":    "0x2C1A10",
    "scene_02_gap":        "0x0A2463",
    "scene_03_archon":     "0x051E46",
    "scene_04_documents":  "0x0A3A2A",
    "scene_05_onboarding": "0x1A0A3A",
    "scene_06_reporting":  "0x071E3A",
    "scene_07_trust":      "0x3A1A0A",
    "scene_08_cta":        "0x05152E",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _pexels_search(query: str) -> str | None:
    """Return the URL of the first landscape photo or None."""
    if not PEXELS_API_KEY:
        return None
    try:
        r = requests.get(
            PEXELS_SEARCH,
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": 1, "orientation": "landscape"},
            timeout=15,
        )
        r.raise_for_status()
        photos = r.json().get("photos", [])
        if not photos:
            return None
        return photos[0]["src"]["large2x"]
    except Exception as e:
        print(f"    ⚠ Pexels error for '{query}': {e}")
        return None


def _download(url: str, dest: Path) -> bool:
    """Download url to dest. Returns True on success."""
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        dest.write_bytes(r.content)
        return True
    except Exception as e:
        print(f"    ⚠ Download failed ({url[:60]}): {e}")
        return False


def _ffmpeg_placeholder(dest: Path, color: str, width: int = 1920, height: int = 1080) -> None:
    """Generate a solid-color PNG with FFmpeg."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c={color}:size={width}x{height}:rate=1",
        "-vframes", "1",
        str(dest),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def _silent_wav(dest: Path, duration_s: int = 65, sample_rate: int = 44100) -> None:
    """Write a silent stereo WAV file using only stdlib."""
    n_samples = duration_s * sample_rate
    with wave.open(str(dest), "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)          # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00\x00\x00" * n_samples)   # L+R silence


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    (OUTPUT_BASE / "images").mkdir(parents=True, exist_ok=True)
    (OUTPUT_BASE / "audio").mkdir(parents=True, exist_ok=True)

    print(f"\n{'─'*54}")
    print(f"  generate_assets_free — {JOB_ID}")
    print(f"  Pexels key : {'set ✓' if PEXELS_API_KEY else 'NOT SET — placeholders only'}")
    print(f"  Pixabay key: {'set ✓' if PIXABAY_API_KEY else 'NOT SET — music skipped'}")
    print(f"{'─'*54}\n")

    # ── Images ────────────────────────────────────────────────────────────────
    generated_images = []
    for asset_id, query in SCENE_QUERIES.items():
        dest = OUTPUT_BASE / "images" / f"{asset_id}.png"
        if dest.exists():
            print(f"  [skip] {asset_id} already exists")
            generated_images.append({"asset_id": asset_id, "local_path": str(dest), "source": "cached"})
            continue

        print(f"  {asset_id}  query='{query}'")
        photo_url = _pexels_search(query)

        if photo_url:
            ok = _download(photo_url, dest)
            if ok:
                print(f"    ✓ Pexels photo → {dest.name}")
                generated_images.append({"asset_id": asset_id, "local_path": str(dest), "source": "pexels", "url": photo_url})
                continue
            print("    ↳ download failed, falling back to placeholder")

        # No results or download failed — generate FFmpeg placeholder
        color = SCENE_COLORS[asset_id]
        _ffmpeg_placeholder(dest, color)
        print(f"    ✓ FFmpeg placeholder ({color}) → {dest.name}")
        generated_images.append({"asset_id": asset_id, "local_path": str(dest), "source": "ffmpeg_placeholder", "color": color})

    # ── Music ─────────────────────────────────────────────────────────────────
    music_path = OUTPUT_BASE / "audio" / "bg_music.wav"
    music_info: dict

    if not PIXABAY_API_KEY:
        print("\n  Music: PIXABAY_API_KEY is empty — skipping Pixabay, writing silent track")
        _silent_wav(music_path)
        print(f"    ✓ Silent WAV → {music_path.name}  ({music_path.stat().st_size // 1024} KB)")
        music_info = {"source": "silent_fallback", "local_path": str(music_path)}
    else:
        print("\n  Music: searching Pixabay audio...")
        try:
            r = requests.get(
                PIXABAY_AUDIO,
                params={
                    "key": PIXABAY_API_KEY,
                    "q": "corporate ambient",
                    "media_type": "music",
                    "per_page": 3,
                },
                timeout=15,
            )
            r.raise_for_status()
            hits = r.json().get("hits", [])
            if hits:
                mp3_url = hits[0].get("audio", hits[0].get("url"))
                mp3_path = OUTPUT_BASE / "audio" / "bg_music.mp3"
                ok = _download(mp3_url, mp3_path)
                if ok:
                    print(f"    ✓ Pixabay track → {mp3_path.name}")
                    music_info = {"source": "pixabay", "local_path": str(mp3_path), "url": mp3_url}
                else:
                    raise RuntimeError("download failed")
            else:
                raise RuntimeError("no hits returned")
        except Exception as e:
            print(f"    ⚠ Pixabay search failed: {e} — writing silent track")
            _silent_wav(music_path)
            music_info = {"source": "silent_fallback", "local_path": str(music_path)}

    # ── Summary ───────────────────────────────────────────────────────────────
    pexels_count = sum(1 for i in generated_images if i["source"] == "pexels")
    placeholder_count = sum(1 for i in generated_images if i["source"] == "ffmpeg_placeholder")
    cached_count = sum(1 for i in generated_images if i["source"] == "cached")

    print(f"\n{'─'*54}")
    print(f"  Images:  {pexels_count} Pexels  |  {placeholder_count} placeholders  |  {cached_count} cached")
    print(f"  Music:   {music_info['source']}")
    print(f"  Cost:    $0.00")
    print(f"{'─'*54}")

    # ── Update checkpoint ─────────────────────────────────────────────────────
    manifest_path = CHECKPOINT_DIR / "03_assets_manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)
        manifest["images"] = generated_images
        manifest["music"]["local_path"] = music_info["local_path"]
        manifest["music"]["source"] = music_info["source"]
        manifest["cost_actual_usd"] = 0.00
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        print(f"\n  ✓ Checkpoint updated: {manifest_path}")

    print(f"  ✓ Done. Assets in: output/{JOB_ID}/\n")


if __name__ == "__main__":
    main()
