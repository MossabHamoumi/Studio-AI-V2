# Studio-AI — Project Status

**Repository:** `MossabHamoumi/Studio-AI`
**Current Phase:** Phase 8 — Production Orchestrator + Durable Execution
**Phase Status:** COMPLETED
**Phase 9 Readiness:** YES
**Last Updated:** Phase 8 Completion

---

## 1. Executive Summary

Studio-AI is undergoing a clean, ground-up rebuild as a **local-first AI story and media production studio** targeting desktop environments (Windows / Ryzen 5 PRO 5650U / 16 GB RAM).

Phase 8 has delivered the **Production Orchestrator & Durable Execution Engine**, connecting all verified engine layers into a unified pipeline (`ANALYSIS -> ADAPTATION -> NARRATION -> SUBTITLES -> VISUALS -> RENDER -> QA`). Features single requested chapter processing, full novel sequential processing, strict chapter directory isolation (`chapters/NNN/`), pre-flight dependency checking, stage-level resume/retry, diagnostic bundle generation (`diagnostic_bundle_<run_id>.json`), and the Production Orchestrator PySide6 desktop UI.

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
| **Phase 5** | Subtitle Engine | **COMPLETED** | Audio Timeline Subtitles, SubtitleValidator, ASS \an5 Presets, SRT, Line Wrapper, `PHASE_5_RESULT.md` |
| **Phase 6** | Visual Engine | **COMPLETED** | Visual Modes, FFprobe Inspector, Asset Library, Gameplay Looping, Image Prompts, Title Cards, `PHASE_6_RESULT.md` |
| **Phase 7** | Hardened FFmpeg Render Pipeline | **COMPLETED** | RenderSpec, FilterGraphBuilder, CommandBuilder, FFmpegRenderer, MediaQAValidator, `qa_report.json`, `PHASE_7_RESULT.md` |
| **Phase 8** | Production Orchestrator | **COMPLETED** | ProductionOrchestrator, PreflightChecker, DiagnosticBundleExporter, Chapter Isolation, `PHASE_8_RESULT.md` |
| **Phase 9** | Creative Desktop UI | PLANNED | PySide6 Studio UI (Dashboard, Projects, Create, Workspace, Production, Library, Settings) |
| **Phase 10** | Mandatory Windows Hardware Acceptance | PLANNED | Ryzen 5 PRO 5650U Execution Acceptance & Resource Profiling |
| **Phase 11** | SearXNG + Docker + Story Discovery | PLANNED | Rights-Aware Story Discovery Ingestion |
| **Phase 12** | Metadata + Publishing + Analytics | PLANNED | Packaging, Export, Analytics |

---

## 4. Current Repository State

- **Branch:** `rebuild/phase-8`
- **Source Code:** Complete core domain, SQLite database engine, repositories, workspace manager, system doctor, universal content engine, Ollama local AI layer, Kokoro/Piper TTS engine, audio-driven subtitle engine, visual engine & asset library, hardened FFmpeg render pipeline, production orchestrator, preflight checker, diagnostic exporter, PySide6 UI views, test suite.
- **Test Suite Status:** 44 passed, 1 skipped (`python3 -m pytest -v`).
- **Next Action:** Await approval / start Phase 9 (Creative Desktop UI).
