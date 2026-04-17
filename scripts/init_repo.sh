#!/bin/bash
# init_repo.sh — Initialize OpenStudio as a git repo and prepare for GitHub push
# Run this once after cloning / setting up the project

set -e

echo ""
echo "🎬 OpenStudio — Git Repository Setup"
echo "────────────────────────────────────"
echo ""

# Check we're in the right directory
if [ ! -f "README.md" ] || ! grep -q "OpenStudio" README.md; then
  echo "❌ Run this script from the OpenStudio project root directory"
  exit 1
fi

# Initialize git
if [ ! -d ".git" ]; then
  echo "→ Initializing git repository..."
  git init
  git branch -M main
fi

# Initial commit
echo "→ Creating initial commit..."
git add .
git commit -m "feat: initial OpenStudio release

Integrates OpenMontage (agentic video production) with Open Generative AI
(200+ image/video/lipsync models) into a unified end-to-end platform.

- bridge/asset_router.py: routes pipeline asset requests to 200+ models
- engine/pipeline_defs/lipsync_presenter.yaml: new OpenStudio-original pipeline
- Unified .env, Makefile, CLAUDE.md for Claude Code
- Full README with architecture, quick start, and examples

Credits:
  OpenMontage by @calesthio (AGPL-3.0)
  Open Generative AI by @Anil-matcha (MIT)
"

echo ""
echo "✅ Git repository initialized!"
echo ""
echo "Next steps:"
echo "  1. Create a new repo on GitHub: https://github.com/new"
echo "     Name suggestion: OpenStudio"
echo "     Visibility: Public"
echo "     Do NOT initialize with README (we already have one)"
echo ""
echo "  2. Add the remote and push:"
echo "     git remote add origin https://github.com/YOUR_USERNAME/OpenStudio.git"
echo "     git push -u origin main"
echo ""
echo "  3. Add topics on GitHub for discoverability:"
echo "     video-production, generative-ai, ai-video, open-source,"
echo "     claude-code, agentic-ai, text-to-video, lipsync"
echo ""
