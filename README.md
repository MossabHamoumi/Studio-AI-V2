# Studio-AI — Local-First AI Story & Media Studio

Studio-AI is a desktop application designed to transform text (novels, short stories, Reddit-style stories, podcasts) into fully narrated short-form reels and long-form videos using local AI models, local neural TTS engines, and FFmpeg.

## Core Principles

- **Local-First & Private:** Runs completely offline using Ollama (`qwen3:8b`), Kokoro-ONNX / Piper TTS, and FFmpeg.
- **No Silent Fallbacks or Fake Output:** All capabilities fail loudly with actionable diagnostics if dependencies are missing.
- **CPU Bounded:** Optimized for desktop hardware (AMD Ryzen 5 PRO 5650U, 16 GB RAM).
- **Durable State:** All pipeline progress is stored in SQLite (WAL mode) and can be resumed across restarts.

## Quick Start

See `SETUP.md` for full environment and installation instructions.

```bash
# Install dependencies
pip install -r requirements.txt

# Run System Doctor diagnostics
python -m src.main --doctor

# Launch desktop GUI
python -m src.main

# Run automated test suite
python -m compileall -q src tests
python -m pytest -v
```

## Documentation

- `STATUS.md`: Current project status and phase progress.
- `SETUP.md`: Detailed installation and environment guide.
- `PHASE_0_TRUTH_AUDIT.md`: Binding engineering specifications and truth audit.
- `PHASE_1_RESULT.md`: Phase 1 implementation and test results.
- `PHASE_2_RESULT.md`: Phase 2 Universal Content Engine implementation and test results.
- `PHASE_3_RESULT.md`: Phase 3 Local AI Layer implementation and test results.
- `PHASE_4_RESULT.md`: Phase 4 Real Local TTS & Narration Engine implementation and test results.
- `ARCHITECTURE.md`: Master pipeline and system design.

## Rebuild Roadmap

1. **Phase 0:** Product Requirements & Architecture Baseline (COMPLETED)
2. **Phase 1:** Durable Core + Project Memory (COMPLETED)
3. **Phase 2:** Universal Content Engine (COMPLETED)
4. **Phase 3:** Local AI Layer (COMPLETED)
5. **Phase 4:** Real TTS + Narration (COMPLETED)
6. **Phase 5:** Subtitle Engine (PLANNED)
7. **Phase 6:** Visual Engine (PLANNED)
8. **Phase 7:** Hardened FFmpeg Render Pipeline (PLANNED)
9. **Phase 8:** Production Orchestrator (PLANNED)
10. **Phase 9:** Creative Desktop UI (PLANNED)
11. **Phase 10:** Mandatory Windows Hardware Acceptance (PLANNED)
12. **Phase 11:** SearXNG + Docker + Story Discovery (PLANNED)
13. **Phase 12:** Metadata + Publishing + Analytics (PLANNED)
