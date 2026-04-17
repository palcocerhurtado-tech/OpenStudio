.PHONY: setup studio demo test install-gpu help

help:
	@echo ""
	@echo "OpenStudio — AI Creative Production Platform"
	@echo "─────────────────────────────────────────────"
	@echo "  make setup        Install all dependencies (Python + Node.js)"
	@echo "  make studio       Start the web studio at http://localhost:3000"
	@echo "  make demo         Render zero-key demo videos"
	@echo "  make test         Run contract tests (no API keys needed)"
	@echo "  make install-gpu  Install local GPU video generation models"
	@echo ""

setup:
	@echo "→ Installing Python dependencies..."
	pip install -r engine/requirements.txt
	pip install piper-tts
	@echo "→ Installing Node.js dependencies (frontend)..."
	cd frontend && npm install
	@echo "→ Installing Node.js dependencies (Remotion composer)..."
	cd engine/remotion-composer && npm install
	@echo "→ Copying .env template..."
	@test -f .env || cp .env.example .env
	@echo ""
	@echo "✅ Setup complete!"
	@echo "   1. Edit .env and add your API keys (MUAPI_KEY is the main one)"
	@echo "   2. Run 'make studio' for the visual interface"
	@echo "   3. Or open in Claude Code / Cursor and start prompting"
	@echo ""

studio:
	@echo "→ Starting OpenStudio web interface..."
	cd frontend && npm run dev

demo:
	@echo "→ Running zero-key demo pipeline..."
	cd engine && python -m tools.demo_runner

test:
	@echo "→ Running contract tests..."
	cd engine && make test-contracts

install-gpu:
	@echo "→ Installing GPU video generation dependencies..."
	pip install -r engine/requirements-gpu.txt
	@echo "✅ GPU setup complete. Set VIDEO_GEN_LOCAL_ENABLED=true in .env"
