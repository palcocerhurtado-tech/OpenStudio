# Stage: self_review
# Pipeline: all

## Objective
Independently verify the final video before presenting to the user for approval.

## Step 1 — Frame Sampling

Sample frames at key moments:
- 0s (first frame), 3s (hook), 10s (problem end), 22s (brand intro)
- Scene transition frames (every scene boundary ±0.5s)
- 55s (CTA), final frame

```python
frames = sample_frames(
    video_path=f"output/{job_id}/{job_id}_16x9.mp4",
    timestamps=[0, 3, 10, 22, 30, 38, 46, 54, 58, 60]
)
```

## Step 2 — Transcription Check

Transcribe the audio and compare against approved script:
```python
transcript = transcribe(audio_path=f"output/{job_id}/audio/narration.mp3", language="es")
wer = word_error_rate(transcript["text"], script["full_narration"])
# Flag if wer > 0.05 (5% error)
```

## Step 3 — Visual QA Checklist

For each sampled frame, verify:
- [ ] No garbled AI text/logos visible (images are text-free)
- [ ] Brand name spelled correctly in all text overlays
- [ ] URL readable and correctly spelled in CTA frame
- [ ] Subtitle timing aligned (±0.3s tolerance)
- [ ] Audio levels balanced (narration clearly audible over music)
- [ ] No black frames or visual glitches at transitions
- [ ] Safe zone respected (no key content in outer 5% of frame)
- [ ] 9:16 crop: subject not cut off

## Step 4 — Duration Check

Verify: `abs(actual_duration - target_duration) < 2.0` seconds

## Output Schema

```json
{
  "review_passed": true,
  "duration_actual_s": 60.4,
  "wer": 0.02,
  "frame_issues": [],
  "subtitle_sync_ok": true,
  "audio_levels_ok": true,
  "safe_zone_ok": true,
  "notes": "..."
}
```

Present sampled frames and review summary to user before final export.
