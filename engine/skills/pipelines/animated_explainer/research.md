# Stage: research
# Pipeline: animated_explainer

## Objective
Gather competitive intelligence, audience context, and content hooks before scripting.

## Instructions

1. **Brand research** — Search for `{brand_name}` to find:
   - Positioning statement and key services
   - Target audience descriptors
   - Geographic market context
   - Any existing taglines or values language

2. **Market context** — Search for relevant statistics (use 3–5 per script):
   - Automation adoption rate for the target segment
   - Pain points most cited in industry reports
   - Competitor landscape at a headline level

3. **Platform norms** — Check current best practices for `{output_platform}`:
   - Optimal video length and hook structure
   - Caption / subtitle conventions
   - Aspect ratio and safe zones

4. **Content angle** — Based on research, identify:
   - The single strongest problem statement (opening hook)
   - The clearest proof point (middle)
   - The most motivating CTA framing (close)

## Output Schema

```json
{
  "brand_facts": ["..."],
  "market_stats": [{"stat": "...", "source": "..."}],
  "pain_points": ["..."],
  "content_angle": {
    "hook": "...",
    "proof_point": "...",
    "cta_frame": "..."
  },
  "platform_norms": { "hook_window_seconds": 3, "cta_placement": "last_5s" }
}
```

## Checkpoint
Save output as `.checkpoints/{job_id}/00_research.json`
