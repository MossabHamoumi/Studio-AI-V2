# Studio-AI — Local-First AI Story & Media Studio

Studio-AI is a desktop application designed to transform text (novels, short stories, Reddit-style stories, podcasts) into fully narrated short-form reels and long-form videos using local AI models, local neural TTS engines, and FFmpeg.

## Core Principles

- **Local-First & Private:** Runs completely offline using Ollama (`qwen3:8b`), Kokoro-ONNX / Piper TTS, and FFmpeg.
- **No Silent Fallbacks or Fake Output:** All capabilities fail loudly with actionable diagnostics if dependencies are missing.
- **CPU Bounded:** Optimized for desktop hardware (AMD Ryzen 5 PRO 5650U, 16 GB RAM).
- **Durable State:** All pipeline progress is stored in SQLite (WAL mode) and can be resumed across restarts.

## Documentation

- `STATUS.md`: Current project status and phase progress.
- `PHASE_0_TRUTH_AUDIT.md`: Binding engineering specifications and truth audit.
- `PHASE_0_TRUTH_AUDIT.json`: Structured machine-readable architecture specification.
- `ARCHITECTURE.md`: Master pipeline and system design.

## Rebuild Roadmap

1. **Phase 0:** Product Requirements & Architecture Baseline (COMPLETED)
2. **Phase 1:** Durable Core + Project Memory
3. **Phase 2:** Universal Content Engine
4. **Phase 3:** Local AI Layer
5. **Phase 4:** Real TTS + Narration
6. **Phase 5:** Subtitle Engine
7. **Phase 6:** Visual Engine
8. **Phase 7:** Hardened FFmpeg Render Pipeline
9. **Phase 8:** Production Orchestrator
10. **Phase 9:** Creative Desktop UI
11. **Phase 10:** Mandatory Windows Hardware Acceptance
12. **Phase 11:** SearXNG + Docker + Story Discovery
13. **Phase 12:** Metadata + Publishing + Analytics
