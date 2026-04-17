# Stage: scene_plan
# Pipeline: animated_explainer

## Objective
Translate the approved script into a shot-by-shot visual plan with image prompts
and animation directives for each scene.

## Instructions

For each scene defined in `01_script.json`:

1. **Visual concept** — Describe the key visual for this moment (1-2 sentences)
2. **Image generation prompt** — Write the exact prompt for `generate_image()`:
   - Include style keywords: `{style}` playbook tokens
   - Include technical specs: aspect ratio, mood, color palette
   - Avoid text in generated images (handled separately as overlays)
3. **Animation directive** — One of:
   - `ken_burns_in` — slow zoom in
   - `ken_burns_out` — slow zoom out
   - `parallax_left` / `parallax_right` — lateral drift
   - `fade_through` — cross-dissolve to next scene
   - `static_hold` — no motion
4. **Text overlays** — Any on-screen text (separate from narration subtitles):
   - Label, font size class (h1/h2/body), position, timing within scene
5. **Transition** — How this scene exits to the next

## Image Prompt Engineering Rules

- Start with the subject, then environment, then lighting, then style
- For "clean-professional" style: `corporate, minimal, clean lines, desaturated with blue accent, flat depth of field`
- For AI/tech scenes: `subtle data visualization overlay, geometric network nodes, soft glow`
- Always specify: `photorealistic` or `flat illustration` or `3D render`
- Never mention brand names in image prompts

## Output Schema

```json
{
  "total_scenes": 8,
  "scenes": [
    {
      "scene_id": 1,
      "label": "El problema",
      "start_s": 0,
      "end_s": 12,
      "visual_concept": "...",
      "image_prompt": "...",
      "style": "clean-professional",
      "aspect_ratio": "16:9",
      "animation": "ken_burns_in",
      "text_overlays": [],
      "transition": "fade_through",
      "asset_id": "scene_01_problem"
    }
  ]
}
```

## Checkpoint
Save output as `.checkpoints/{job_id}/02_scene_plan.json`
