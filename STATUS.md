# Studio-AI — Project Status

**Repository:** `MossabHamoumi/Studio-AI`
**Current Phase:** Blocking Startup Dependency Repair & Windows Readiness
**Phase Status:** COMPLETED
**Next Phase Readiness:** YES
**Last Updated:** Startup Dependency Repair Baseline

---

## 1. Executive Summary

Studio-AI is undergoing a clean, ground-up rebuild as a **local-first AI story and media production studio** targeting desktop environments (Windows / Ryzen 5 PRO 5650U / 16 GB RAM).

A blocking startup repair was executed on the desktop GUI application. The constructor dependency ordering mismatch in `ProductionOrchestrator` (`AppSettings` replaced by `ProjectRepository`) was resolved by enforcing explicit keyword arguments across `MainWindow` and `ProductionView` instantiations, and adding runtime `isinstance(settings, AppSettings)` type validation. All 50 unit and integration tests compile cleanly and pass without errors.

---

## 2. Startup Dependency Fix Report

### Root Cause
`ProductionOrchestrator.__init__` expects `settings: AppSettings` as its first argument. In `src/ui/main_window.py`, arguments were passed positionally in the wrong order (`project_repo` passed first, `settings` passed last), causing `self.settings` to hold a `ProjectRepository` object. When `PreflightChecker` initialized `FallbackTTSManager(settings)`, `setup_tts_logger` attempted to read `settings.logs_dir` and raised `AttributeError: 'ProjectRepository' object has no attribute 'logs_dir'`.

### Fix Applied
1. Updated `MainWindow` (`src/ui/main_window.py`) and `ProductionView` (`src/ui/production_view.py`) to use explicit keyword arguments when instantiating `ProductionOrchestrator` and all child views (`DashboardView`, `ProjectsView`, `CreateWizardView`, `WorkspaceView`, `AIView`, `SubtitleView`, `VisualView`, `ProductionView`, `LibraryView`).
2. Added runtime type checks in `ProductionOrchestrator.__init__` ensuring `isinstance(settings, AppSettings)` and `isinstance(project_repo, ProjectRepository)`, raising a clear `TypeError` if invalid objects are passed.
3. Added `test_startup_dependency_graph_regression` in `tests/test_gui.py` to assert that passing `ProjectRepository` as `settings` raises a `TypeError`, and passing valid `AppSettings` initializes `ProductionOrchestrator` successfully.

### Status Matrix

| Component / Verification | Status | Evidence / Result |
|---|---|---|
| `ProductionOrchestrator` Constructor | **PASS** | `isinstance(settings, AppSettings)` validation enforced |
| `MainWindow` Instantiation | **PASS** | Initializes all 10 views without `TypeError` or `AttributeError` |
| `SystemDoctor` CLI (`--doctor`) | **PASS** | Runs independently, reports status without constructing GUI graph |
| GUI Application Launch (`src.main`) | **PASS** | Launches `MainWindow` cleanly without traceback |
| Offscreen GUI Test Suite (`QT_QPA_PLATFORM=offscreen`) | **PASS** | 50 collected, 49 passed, 1 skipped (missing FFmpeg CLI in sandbox) |
| Kokoro ONNX Model Probing | **NOT READY** | Probes path `C:\Users\hp\.studio-ai\models\kokoro\kokoro-v0_19.onnx` (missing) |
| Piper TTS Model Probing | **NOT READY** | Probes path `C:\Users\hp\.studio-ai\models\piper` (missing) |

---

## 3. Global Ground Rules (Strict Enforcement)

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

## 4. Phase Roadmap & Progress

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
| **Phase 8** | Production Orchestrator & Full System Acceptance | **COMPLETED** | ProductionOrchestrator, PreflightChecker, DiagnosticBundleExporter, 20 Regressions Test, `PHASE_8_FULL_SYSTEM_ACCEPTANCE.md` |
| **Startup Fix** | Blocking Desktop GUI Startup Repair | **COMPLETED** | Explicit keyword arguments, `isinstance` checks, `test_startup_dependency_graph_regression` |
| **Phase 9** | Creative Desktop UI | PLANNED | PySide6 Studio UI (Dashboard, Projects, Create, Workspace, Production, Library, Settings) |
| **Phase 10** | Mandatory Windows Hardware Acceptance | PLANNED | Ryzen 5 PRO 5650U Execution Acceptance & Resource Profiling |
| **Phase 11** | SearXNG + Docker + Story Discovery | PLANNED | Rights-Aware Story Discovery Ingestion |
| **Phase 12** | Metadata + Publishing + Analytics | PLANNED | Packaging, Export, Analytics |

---

## 5. Command Reference for Windows Execution

To run System Doctor CLI:
```powershell
.\.venv\Scripts\python.exe -m src.main --doctor
```

To launch PySide6 Desktop GUI application:
```powershell
.\.venv\Scripts\python.exe -m src.main
```

To run test suite in offscreen mode:
```powershell
$env:QT_QPA_PLATFORM="offscreen"
.\.venv\Scripts\python.exe -m pytest -v
```
