# Studio-AI — Project Status

**Repository:** `MossabHamoumi/Studio-AI`
**Current Phase:** Phase 4 — Real Local TTS + Narration Engine
**Phase Status:** COMPLETED
**Phase 5 Readiness:** YES
**Last Updated:** Phase 4 Completion

---

## 1. Executive Summary

Studio-AI is undergoing a clean, ground-up rebuild as a **local-first AI story and media production studio** targeting desktop environments (Windows / Ryzen 5 PRO 5650U / 16 GB RAM).

Phase 4 has delivered the **Real Local TTS & Narration Engine**, featuring Kokoro primary (`kokoro-onnx`) and Piper fallback (`piper-tts`) neural TTS integrations, `Kokoro -> Piper -> FAILED` fallback chain, pure sine tone and silence audio validation (rejecting synthetic tones), natural paragraph/sentence chunking (~120–300 words), deterministic SHA-256 audio cache reuse, audio timeline assembly, `logs/tts.log` logging, System Doctor TTS engine probes, and the Voice Library desktop UI.

---

## 2. Global Ground Rules (Strict Enforcement)

1. **One Phase at a Time:** Inspect → plan → implement → test → prove → stop.
2. **No Fake Success:** Fail clearly if real engines/tools are unavailable. No dummy tones, fake MP4s, or hardcoded provider health.
3. **No Silent Fallbacks:** UI and logs explicitly state every fallback action (e.g., `Kokoro FAILED -> Piper SUCCESS`).
4. **Real System Doctor:** System Doctor probes real provider capabilities, not static config flags.
5. **Authoritative User Choices:** AI recommends; AI never overrides explicit user settings.
6. **Immutable Source Data:** Original imported input is preserved untouched.
7. **Durable State:** SQLite (WAL mode) is the single source of truth for application state; filesystem holds artifacts.
8. **Resumable Operations:** Long operations support pause/resume/retry/cancel and reuse valid artifacts.
9. **CPU-First Bounded Processing:** Optimized for Ryzen 5 PRO 5650U with memory-bounded single-concurrency heavy tasks.
10. **Real Verification:** Automated tests + real execution + inspected artifacts required before declaring completion.

---

## 3. Phase Roadmap & Progress

| Phase | Description | Status | Deliverables / Notes |
|---|---|---|---|
| **Phase 0** | Product Requirements & Architecture Baseline | **COMPLETED** | `PHASE_0_TRUTH_AUDIT.md`, `PHASE_0_TRUTH_AUDIT.json`, `STATUS.md`, `ARCHITECTURE.md`, `README.md` |
| **Phase 1** | Durable Core + Project Memory | **COMPLETED** | SQLite WAL Engine, Migrations, Models, Repositories, GUI Shell, `PHASE_1_RESULT.md`, `SETUP.md` |
| **Phase 2** | Universal Content Engine | **COMPLETED** | Text Importer, Chapter Detector, Cleaner, Section Splitter, Workspace View, 9k Word Test, `PHASE_2_RESULT.md` |
| **Phase 3** | Local AI Layer | **COMPLETED** | Ollama Client (`qwen3:8b`), AI Modes, Enum Safety, Timeout Banners, Adaptation Review, `PHASE_3_RESULT.md` |
| **Phase 4** | Real TTS + Narration | **COMPLETED** | Kokoro Primary + Piper Fallback, Audio Validator, Chunker, Cache, Timeline, Voice Library, `PHASE_4_RESULT.md` |
| **Phase 5** | Subtitle Engine | PLANNED | ASS/SRT Timing Alignment from Audio Duration, ASS \an5 Presets |
| **Phase 6** | Visual Engine | PLANNED | Static Image, Gameplay Library Muted Audio, Multi-Image Scene Timeline |
| **Phase 7** | Hardened FFmpeg Render Pipeline | PLANNED | RenderSpec, FilterGraph, FFmpegCommand, Media QA |
| **Phase 8** | Production Orchestrator | PLANNED | Stage Pipeline, Resume/Retry Engine, Chapter Isolation |
| **Phase 9** | Creative Desktop UI | PLANNED | PySide6 Studio UI (Dashboard, Projects, Create, Workspace, Production, Library, Settings) |
| **Phase 10** | Mandatory Windows Hardware Acceptance | PLANNED | Ryzen 5 PRO 5650U Execution Acceptance & Resource Profiling |
| **Phase 11** | SearXNG + Docker + Story Discovery | PLANNED | Rights-Aware Story Discovery Ingestion |
| **Phase 12** | Metadata + Publishing + Analytics | PLANNED | Packaging, Export, Analytics |

---

## 4. Current Repository State

- **Branch:** `rebuild/phase-4`
- **Source Code:** Core domain, database engine, repositories, workspace manager, system doctor, universal content engine, Ollama local AI layer, Kokoro/Piper TTS engine, Voice Library PySide6 UI, test suite.
- **Test Suite Status:** 28 passed, 0 failed (`python3 -m pytest -v`).
- **Next Action:** Await approval / start Phase 5 (Subtitle Engine).
