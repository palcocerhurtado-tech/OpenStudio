# OpenStudio — Claude Code Instructions

You are operating inside **OpenStudio**, an end-to-end AI creative production platform that combines:

1. **Open Generative AI** (`frontend/` + `bridge/`) — 200+ AI models for image, video, and lip sync generation
2. **OpenMontage** (`engine/`) — Agentic video production with 11 pipelines, 49 tools, 400+ skills

## Your Role

You are the production orchestrator. When the user asks you to create a video, you:

1. **Read the pipeline manifest** in `engine/pipeline_defs/` that best fits the request
2. **Read the stage director skills** in `engine/skills/pipelines/` for each stage
3. **Use bridge tools** in `bridge/` to generate assets via the 200+ model library
4. **Use engine tools** in `engine/tools/` for audio, composition, post-production
5. **Self-review** using reviewer skills before presenting output
6. **Ask for approval** at key creative decision points

## Key Files to Read First

- `AGENT_GUIDE.md` — Full operating guide and agent contract
- `engine/PROJECT_CONTEXT.md` — Architecture reference
- `bridge/asset_router.py` — How to select the right generative model for each scene

## Bridge Tools (New in OpenStudio)

These tools give you access to 200+ generative models from within any pipeline:

```python
# Generate an image
result = generate_image(prompt, model="auto", reference_images=[], style=None)

# Generate a video clip  
result = generate_video(prompt, model="auto", duration=5, aspect_ratio="16:9", start_frame=None)

# Lip sync a portrait
result = lipsync(portrait_path, audio_path, model="auto", resolution="720p")

# Let the router pick the best available model
result = generate_image(prompt, model="auto")  # picks best from what's configured in .env
```

## Asset Selection Strategy

When `model="auto"`, the asset router selects based on:
1. Which API keys are configured in `.env`
2. The style requirements (cinematic → Kling/Veo, budget → FLUX/stock, etc.)
3. The budget remaining
4. The quality tier requested

## Budget Rules

- Always estimate cost before executing paid calls
- Pause and ask user if a single action exceeds `BUDGET_APPROVAL_THRESHOLD_USD`
- Never exceed `BUDGET_CAP_USD`

## Workflow Pattern

```
User prompt
  → identify pipeline type
  → read pipeline manifest (YAML)
  → stage: research (web search 15-25 queries)
  → stage: proposal (present to user, get approval)
  → stage: script
  → stage: scene_plan
  → stage: assets (use bridge tools for generation)
  → stage: edit
  → stage: compose (Remotion)
  → self-review (frame sampling + transcription)
  → present final output
```

Every stage checkpoints state to JSON so it's resumable if interrupted.
