# Contributing to OpenStudio

Thanks for your interest! OpenStudio is built on two excellent open-source projects and welcomes contributions that improve the integration between them.

## Most Valuable Contributions

### 1. New Bridge Tools (`bridge/`)
Wrap a new Muapi model category as a native OpenMontage tool.

```python
# Example: bridge/upscale_tool.py
from .asset_router import _muapi_submit, _muapi_poll

def upscale_image(image_path: str, scale: int = 4, output_path: str = None) -> dict:
    """Upscale an image using AI upscaling models."""
    ...
```

### 2. New Pipelines (`engine/pipeline_defs/`)
Add a YAML manifest + matching skill files in `engine/skills/pipelines/`.

See `engine/pipeline_defs/lipsync_presenter.yaml` for a template.

### 3. Frontend Pipeline Panel (`frontend/components/PipelinePanel.js`)
Improve the UI for launching and monitoring production pipelines.

### 4. Model Registry Updates (`bridge/asset_router.py`)
Add new models to the `IMAGE_TIERS`, `VIDEO_TIERS`, or `LIPSYNC_TIERS` dicts as Muapi adds support for them.

## Development Setup

```bash
git clone https://github.com/YOUR_USERNAME/OpenStudio.git
cd OpenStudio
make setup
cp .env.example .env
# Add API keys to .env
```

## Testing

```bash
make test          # contract tests (no API keys needed)
```

## Code Style

- Python: follow existing patterns in `engine/tools/` and `bridge/`
- JS/React: follow patterns in `frontend/packages/studio/src/`
- YAML pipelines: follow `engine/pipeline_defs/lipsync_presenter.yaml` as template
- Markdown skills: follow `engine/skills/` conventions

## Licenses

- Contributions to `bridge/` are MIT licensed
- Contributions to `engine/` fall under AGPL-3.0 (inherited from OpenMontage)
- Contributions to `frontend/` fall under MIT (inherited from Open Generative AI)

By contributing you agree your work can be licensed under these terms.

## Credits

When adding a new model or pipeline, please credit the underlying service/model in comments or documentation.
