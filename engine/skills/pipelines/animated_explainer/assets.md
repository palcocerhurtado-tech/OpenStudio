# Stage: assets
# Pipeline: animated_explainer

## Objective
Generate all production assets: scene images, voiceover narration, and background music.
Estimate total cost before any paid API call. Pause if any single call exceeds
`BUDGET_APPROVAL_THRESHOLD_USD`.

## Step 1 — Cost Estimation

Before generating anything, calculate:
```
image_cost = len(scenes) × estimate_cost("image", selected_model)
tts_cost   = estimate_cost("tts", selected_voice, char_count)
total_est  = image_cost + tts_cost
```
Present the breakdown and get approval if `total_est > BUDGET_APPROVAL_THRESHOLD_USD`.

## Step 2 — Image Generation

For each scene in `02_scene_plan.json`:
```python
result = generate_image(
    prompt=scene["image_prompt"],
    model="auto",
    style=scene["style"],
    aspect_ratio=scene["aspect_ratio"],
    resolution="2K",
    output_path=f"output/{job_id}/images/{scene['asset_id']}.png"
)
```
Save result URL and model_used to asset manifest.

## Step 3 — Voiceover Narration

Recommended voice selection for Spanish (Castilian), professional male tone:

| Priority | Provider     | Voice ID                | Notes                        |
|----------|--------------|-------------------------|------------------------------|
| 1        | ElevenLabs   | `pNInz6obpgDQGcFmaJgB`  | Adam — deep, authoritative   |
| 2        | ElevenLabs   | `ErXwobaYiN019PkySvjV`  | Antoni — clear, warm Spanish |
| 3        | OpenAI       | `onyx`                  | Deep, professional           |
| 4        | Piper (free) | `es_ES-mls-medium`      | Local fallback, no cost      |

Generate narration:
```python
result = tts(
    text=script["full_narration"],
    voice_id=selected_voice,
    language="es",
    output_path=f"output/{job_id}/audio/narration.mp3",
    word_timestamps=True   # required for word-level subtitle sync
)
```

## Step 4 — Background Music

Search royalty-free music: ambient corporate, 60–70 BPM, instrumental.
Preferred sources (free): Pixabay, ccMixter, Free Music Archive.
Target track: ~90 seconds (loop if needed), fade-out at 55s.

```python
music = search_royalty_free_music(
    tags=["corporate", "ambient", "instrumental"],
    bpm_range=(60, 80),
    duration_min=60
)
```

## Output Schema

```json
{
  "job_id": "archon_promo_001",
  "cost_estimate_usd": 0.22,
  "cost_actual_usd": null,
  "images": [
    {
      "asset_id": "scene_01_problem",
      "url": "...",
      "local_path": "output/archon_promo_001/images/scene_01_problem.png",
      "model_used": "flux-kontext-pro",
      "cost_usd": 0.05
    }
  ],
  "narration": {
    "url": "...",
    "local_path": "output/archon_promo_001/audio/narration.mp3",
    "voice_id": "...",
    "provider": "elevenlabs",
    "word_timestamps": [],
    "cost_usd": 0.024
  },
  "music": {
    "url": "...",
    "local_path": "output/archon_promo_001/audio/bg_music.mp3",
    "source": "pixabay",
    "license": "royalty-free",
    "cost_usd": 0.00
  }
}
```

## Checkpoint
Save output as `.checkpoints/{job_id}/03_assets_manifest.json`
**Voice selection requires human approval before TTS generation.**
