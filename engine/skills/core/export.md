# Stage: export
# Pipeline: all

## Objective
Encode and deliver all final output files in platform-optimized formats.

## LinkedIn 16:9 Export

```
ffmpeg -i {draft_mp4} \
  -c:v libx264 -preset slow -crf 18 \
  -profile:v high -level 4.0 \
  -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 \
  -movflags +faststart \
  -s 1920x1080 \
  output/{job_id}/final/{job_id}_linkedin_1080p.mp4
```

## Instagram Reels 9:16 Export

```
ffmpeg -i {draft_9x16_mp4} \
  -c:v libx264 -preset slow -crf 20 \
  -profile:v high -level 4.0 \
  -pix_fmt yuv420p \
  -c:a aac -b:a 128k -ar 48000 \
  -movflags +faststart \
  -s 1080x1920 \
  output/{job_id}/final/{job_id}_instagram_reels_1080x1920.mp4
```

## Deliverables Manifest

```json
{
  "job_id": "...",
  "completed_at": "...",
  "files": [
    {"label": "LinkedIn 16:9", "path": "...", "resolution": "1920x1080", "size_mb": null},
    {"label": "Instagram Reels 9:16", "path": "...", "resolution": "1080x1920", "size_mb": null},
    {"label": "Subtitles SRT", "path": "...", "format": "srt"}
  ],
  "total_cost_usd": null,
  "models_used": []
}
```
