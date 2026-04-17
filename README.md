# 🎬 OpenStudio

**The first open-source, end-to-end AI creative production platform.**

OpenStudio merges two powerful open-source systems into a unified pipeline:

- **[Open Generative AI](https://github.com/Anil-matcha/Open-Generative-AI)** — 200+ AI models for image/video/lipsync generation (the _asset factory_)
- **[OpenMontage](https://github.com/calesthio/OpenMontage)** — Agentic video production system with 11 pipelines, 49 tools, 400+ skills (the _production engine_)

Together: describe what you want → AI generates every asset → agents assemble a finished, polished video. One command, end-to-end.

```
"Make a 60-second product ad for AquaPulse smart bottle"
         ↓
OpenStudio Asset Engine (Open Generative AI)
  → Generates hero images (Flux/SDXL/Midjourney)
  → Generates video clips (Kling/Veo/Wan)
  → Syncs lip animations (LTX/Infinite Talk)
         ↓
OpenStudio Production Engine (OpenMontage)
  → Researches topic + writes script
  → Narrates with TTS
  → Composes with Remotion
  → Burns subtitles, color grades, exports
         ↓
  Final video — YouTube / TikTok / LinkedIn ready
```

---

## ✨ What's New in OpenStudio (vs using either repo separately)

| Feature | Open Generative AI alone | OpenMontage alone | **OpenStudio** |
|---|---|---|---|
| AI asset generation | ✅ Studio UI | ❌ API-only | ✅ Studio UI + programmatic |
| Agentic production pipelines | ❌ | ✅ 11 pipelines | ✅ 11 pipelines |
| Lip sync in pipelines | ❌ | Limited | ✅ 9 models, integrated |
| 200+ model access | ✅ | ❌ ~12 video providers | ✅ All 200+ via unified selector |
| Unified web UI | ✅ | ❌ CLI/agent only | ✅ Single dashboard |
| Agent-driven asset selection | ❌ | ❌ | ✅ Agent picks best model for scene |
| Multi-image inputs in pipeline | ❌ | ❌ | ✅ Up to 14 reference images per shot |
| Budget governance | ❌ | ✅ | ✅ Covers all 200+ models |

---

## 🏗️ Architecture

```
OpenStudio/
├── frontend/                    # Next.js unified dashboard (from Open Generative AI)
│   ├── app/
│   ├── components/
│   │   ├── StandaloneShell.js   # Studio tabs (Image, Video, Lip Sync, Cinema)
│   │   └── PipelinePanel.js     # NEW: Pipeline launcher UI
│   └── packages/studio/         # 200+ model library
│
├── engine/                      # Production engine (from OpenMontage)
│   ├── tools/                   # 49 Python tools (video, audio, graphics, etc.)
│   ├── pipeline_defs/           # 11 YAML pipeline manifests
│   ├── skills/                  # 400+ agent skill files
│   ├── schemas/                 # JSON Schema contracts
│   ├── styles/                  # Visual style playbooks
│   └── remotion-composer/       # React/Remotion composition engine
│
├── bridge/                      # NEW: Integration layer
│   ├── asset_router.py          # Routes pipeline asset requests → best model
│   ├── model_registry.py        # Unified model registry (200+ models)
│   ├── muapi_tool.py            # OpenMontage tool wrapping Muapi.ai API
│   ├── lipsync_tool.py          # Lip sync as a first-class pipeline stage
│   └── budget_tracker.py        # Extended to cover Muapi model costs
│
├── CLAUDE.md                    # Claude Code agent instructions
├── AGENT_GUIDE.md               # Unified agent contract
├── config.yaml                  # Unified configuration
└── .env.example                 # All API keys in one place
```

### The Bridge Layer (what makes it work)

The `bridge/` layer is the key innovation of OpenStudio. It exposes Open Generative AI's 200+ models as native OpenMontage tools, so agentic pipelines can call them transparently:

```python
# In any OpenMontage pipeline, the agent can now call:
generate_image(
    prompt="hero shot of smart water bottle, studio lighting",
    model="flux-kontext-pro",          # any of 200+ models
    reference_images=["./bottle.jpg"],  # multi-image support
    style_playbook="clean-professional"
)

generate_video(
    prompt="product reveal with dramatic camera pan",
    model="kling-v3",
    duration=5,
    aspect_ratio="16:9"
)

lipsync(
    portrait="./presenter.jpg",
    audio="./narration.mp3",
    model="ltx-2.3-lipsync"
)
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- FFmpeg (`brew install ffmpeg` / `sudo apt install ffmpeg`)
- An AI coding assistant — Claude Code, Cursor, Copilot, Windsurf, or Codex
- A [Muapi.ai](https://muapi.ai) API key (free tier available — covers 200+ models)

### Install

```bash
git clone https://github.com/YOUR_USERNAME/OpenStudio.git
cd OpenStudio
make setup
```

### Add API Keys

```bash
cp .env.example .env
# Edit .env — minimum: MUAPI_KEY=your-key
```

### Run

**Option A — Web Studio (visual interface)**
```bash
make studio
# Open http://localhost:3000
```

**Option B — Agentic pipeline (via Claude Code or Cursor)**
```bash
# Open the project in Claude Code and tell it:
"Make a 45-second explainer about how transformer models work"
```

**Option C — Demo (no API keys needed)**
```bash
make demo
```

---

## 📋 Pipeline Examples

These prompts work out of the box in your AI coding assistant:

### Zero API keys
```
"Create a 30-second animated explainer about compound interest"
```

### With Muapi key (~$0.50–$1.50)
```
"Make a product launch video for a fictional AI SaaS tool called 'Clarix' — 
 generate the logo, hero shots, and a 60-second explainer"
```

### Full setup (~$1–$3)
```
"Create a cinematic brand trailer for an architecture firm. 
 Use AI-generated building visuals, dramatic music, and a professional voiceover"
```

### Lip sync pipeline (new in OpenStudio)
```
"Take this portrait photo of a presenter and this script, 
 generate a professional talking head video with lipsync"
```

See the full **[Prompt Gallery](./docs/PROMPT_GALLERY.md)** for tested prompts with costs.

---

## 🎛️ Web Studio Tabs

The unified dashboard gives you both worlds in one interface:

| Tab | Source | What it does |
|---|---|---|
| **Image Studio** | Open Generative AI | Generate/edit images with 100+ models |
| **Video Studio** | Open Generative AI | Generate videos with 100+ models |
| **Lip Sync Studio** | Open Generative AI | Animate portraits, sync lips to audio |
| **Cinema Studio** | Open Generative AI | Pro camera controls for cinematic shots |
| **Pipelines** | OpenMontage (new) | Launch full production pipelines from the UI |
| **History** | Both | All past generations and pipeline outputs |

---

## 🤖 Supported AI Assistants

| Platform | Config File |
|---|---|
| **Claude Code** | `CLAUDE.md` |
| **Cursor** | `CURSOR.md` + `.cursor/rules/` |
| **GitHub Copilot** | `COPILOT.md` |
| **Codex** | `CODEX.md` |
| **Windsurf** | `.windsurfrules` |

---

## 🔑 API Keys

```bash
# .env

# REQUIRED — covers 200+ image, video, and lipsync models:
MUAPI_KEY=your-key              # muapi.ai — unified API for all generative models

# OPTIONAL — additional providers:
FAL_KEY=your-key                # FLUX, Google Veo, Kling, MiniMax
ELEVENLABS_API_KEY=your-key     # Premium TTS + music + sound effects
OPENAI_API_KEY=your-key         # OpenAI TTS, DALL-E 3
GOOGLE_API_KEY=your-key         # Google Imagen, Google TTS (700+ voices)
SUNO_API_KEY=your-key           # Full music generation
PEXELS_API_KEY=your-key         # Free stock footage (free to get)
PIXABAY_API_KEY=your-key        # Free stock footage (free to get)
RUNWAY_API_KEY=your-key         # Runway Gen-4 direct
```

**GPU users** — unlock free local video generation:
```bash
make install-gpu
# Adds: WAN 2.1, Hunyuan, CogVideo, LTX-Video
```

---

## 💰 Budget Governance

OpenStudio extends OpenMontage's cost tracker to cover all Muapi models:

- **Estimate before execution** — see what the full pipeline will cost
- **Per-action approval** — pause for confirmation above threshold (default: $0.50)
- **Hard cap** — default $10, fully configurable
- **Modes**: `observe` / `warn` / `cap`

---

## 📦 Pipelines

11 production pipelines inherited from OpenMontage, all extended with 200+ model access:

| Pipeline | Description |
|---|---|
| Animated Explainer | Research + script + narration + AI visuals + music |
| Cinematic | Trailer/teaser with AI-generated shots |
| Talking Head | Presenter video with optional AI lipsync |
| Avatar Spokesperson | Full avatar-driven video |
| Clip Factory | Long content → short social clips |
| Screen Demo | Software walkthrough with polish |
| Podcast Repurpose | Podcast highlights → video |
| Localization & Dub | Translate + dub in 50+ languages |
| Animation | Motion graphics, kinetic typography |
| Hybrid | Real footage + AI support visuals |
| **Lipsync Presenter** *(new)* | Portrait + script → talking head with lipsync |

---

## 🏛️ Credits & Licenses

OpenStudio is built on the shoulders of two excellent open-source projects:

- **[OpenMontage](https://github.com/calesthio/OpenMontage)** by [@calesthio](https://github.com/calesthio) — AGPL-3.0
- **[Open Generative AI](https://github.com/Anil-matcha/Open-Generative-AI)** by [@Anil-matcha](https://github.com/Anil-matcha) — MIT

OpenStudio itself is licensed under **AGPL-3.0** (the more restrictive of the two, as required when combining AGPL-3.0 components).

The bridge layer (`bridge/`) is original work, MIT licensed.

---

## 🤝 Contributing

The two most valuable contributions:

**1. New bridge tools** — wrap a new Muapi model as a native OpenMontage tool in `bridge/`  
**2. New pipelines** — add a YAML manifest in `engine/pipeline_defs/` with matching skill files

See `docs/CONTRIBUTING.md` for the full guide.

---

*OpenStudio — From prompt to polished video, end to end.*
