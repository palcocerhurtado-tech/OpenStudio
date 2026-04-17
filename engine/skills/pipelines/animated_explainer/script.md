# Stage: script
# Pipeline: animated_explainer

## Objective
Write a timed, scene-annotated voiceover script in the target language that fits
exactly within `{duration_seconds}` seconds.

## Pacing Guidelines

| Language | Wpm (professional narration) |
|----------|------------------------------|
| Spanish  | 125–135                      |
| English  | 140–155                      |
| French   | 130–140                      |

Calculate target word count: `duration_seconds / 60 * wpm`

## Script Structure (60-second template)

| Segment        | Duration | Purpose                                    |
|----------------|----------|--------------------------------------------|
| Hook / Problem | 0–12s    | Grab attention with audience pain point    |
| Opportunity    | 12–22s   | Reframe — something has changed            |
| Brand intro    | 22–32s   | Who we are, what we do, where we operate   |
| Use cases ×3   | 32–50s   | Concrete proof: 3 use cases ~6s each       |
| Trust signal   | 50–56s   | Differentiator / why us                    |
| CTA close      | 56–60s   | URL + tagline, clean out                   |

## Script Format

Write the script as:
- Plain prose paragraphs (no stage directions in the narration)
- Scene boundary markers: `[SCENE N — label — Xs–Xs]`
- Inline timing estimates per line (words ÷ wpm)
- Total word count and estimated duration at the bottom

## Quality Checks

- Hook must name the audience's pain within the first 8 words
- Brand name first appears before the 35-second mark
- URL is spoken aloud exactly once, at the very end
- No filler words: "básicamente", "en definitiva", "por supuesto"
- Tone: `{tone}` — enforce throughout

## Output Schema

```json
{
  "language": "es",
  "duration_estimate_seconds": 60,
  "word_count": 130,
  "scenes": [
    {
      "scene_id": 1,
      "label": "El problema",
      "start_s": 0,
      "end_s": 12,
      "narration": "...",
      "word_count": 26
    }
  ],
  "full_narration": "...",
  "approved": false
}
```

## Checkpoint
Save output as `.checkpoints/{job_id}/01_script.json`
**Requires human approval before proceeding.**
