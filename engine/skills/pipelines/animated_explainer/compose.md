# Stage: compose
# Pipeline: animated_explainer

## Objective
Assemble all assets into a final video using Remotion, then mux audio,
burn word-level subtitles, and produce both 16:9 and 9:16 exports.

## Remotion Composition

Load the composition template from:
`engine/remotion-composer/compositions/{job_id}/index.jsx`

Each scene component receives:
```js
{
  imagePath: string,       // Local path to scene image
  animation: string,       // ken_burns_in | ken_burns_out | parallax_left | parallax_right | static_hold
  durationFrames: number,  // scene duration × fps
  textOverlays: [],        // On-screen text blocks
  transition: string       // fade_through | cut | slide_left
}
```

## Subtitle Generation

Use word timestamps from TTS output to generate SRT:
```python
subtitles = generate_word_subtitles(
    word_timestamps=assets["narration"]["word_timestamps"],
    max_chars_per_line=42,
    language="es",
    style="lower-third"   # position: bottom 15% of frame
)
# Output: output/{job_id}/subtitles/narration.srt
```

## Audio Mixing

```
narration.mp3     → 0 dB (primary)
bg_music.mp3      → -18 dB (ambient bed)
bg_music fade-out → starts at 52s, reaches -∞ at 60s
```

FFmpeg mux command:
```
ffmpeg -i video_no_audio.mp4 \
       -i narration.mp3 \
       -i bg_music.mp3 \
       -filter_complex "[1:a]volume=1.0[narr];[2:a]volume=0.18,afade=t=out:st=52:d=8[music];[narr][music]amix=inputs=2[aout]" \
       -map 0:v -map "[aout]" \
       -c:v copy -c:a aac -b:a 192k \
       output/{job_id}/archon_promo_001_draft.mp4
```

## Subtitle Burn-In

```
ffmpeg -i archon_promo_001_draft.mp4 \
       -vf "subtitles=narration.srt:force_style='FontName=Inter,FontSize=28,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Bold=1,Alignment=2'" \
       -c:a copy \
       output/{job_id}/archon_promo_001_16x9.mp4
```

## 9:16 Instagram Reels Variant

Re-render the Remotion composition with:
- `width: 1080, height: 1920`
- Image crops: smart-center on subject (avoid edges)
- Text safe zone: top 10% and bottom 15% reserved for platform UI
- Same audio mix, same subtitles re-positioned

```
ffmpeg -i archon_promo_001_16x9.mp4 \
       -vf "crop=608:1080:656:0,scale=1080:1920,pad=1080:1920:0:420:black" \
       output/{job_id}/archon_promo_001_9x16.mp4
```

## Output Files

```
output/archon_promo_001/
├── archon_promo_001_16x9.mp4      # LinkedIn deliverable (1920×1080)
├── archon_promo_001_9x16.mp4      # Instagram Reels (1080×1920)
├── subtitles/narration.srt        # Word-level subtitles
└── assets_manifest.json           # Full production audit trail
```

## Checkpoint
Save compose log as `.checkpoints/{job_id}/04_compose.json`
