# Studio-AI — Project Status

**Repository:** `MossabHamoumi/Studio-AI`
**Current Phase:** GUI Startup Contract Repair & Constructor Audit
**Phase Status:** COMPLETED
**Next Phase Readiness:** YES
**Last Updated:** GUI Startup Contract Repair Baseline

---

## 1. Executive Summary

Studio-AI is undergoing a clean, ground-up rebuild as a **local-first AI story and media production studio** targeting desktop environments (Windows / Ryzen 5 PRO 5650U / 16 GB RAM).

A constructor contract audit was performed across all application views and core services. The parameter mismatch in `ProjectsView` (`on_project_activated` keyword vs `on_project_selected` parameter) was resolved. All 10 views (`DashboardView`, `ProjectsView`, `CreateWizardView`, `WorkspaceView`, `AIView`, `SubtitleView`, `VisualView`, `ProductionView`, `LibraryView`, `Settings`) and core services (`ProductionOrchestrator`, `PreflightChecker`, `FallbackTTSManager`, etc.) were audited and verified to pass explicit keyword arguments cleanly.

---

## 2. GUI Startup Contract Audit Matrix

| Class / Component | Expected Constructor Parameters | MainWindow Instantiation Status | Verification Result |
|---|---|---|---|
| `MainWindow` | `settings, db_engine, project_repo, source_repo, chapter_repo, section_repo, analysis_repo, adaptation_repo, asset_repo, job_repo, production_run_repo, workspace_mgr` | **PASS** | Instantiates without errors |
| `DashboardView` | `project_repo` | **PASS** | Validated in offscreen smoke test |
| `ProjectsView` | `project_repo, workspace_mgr, on_project_selected` | **PASS** | Fixed keyword mismatch (`on_project_selected=self.on_project_activated`) |
| `CreateWizardView` | `session_ctx, project_repo, source_repo, chapter_repo, section_repo, workspace_mgr, orchestrator, settings, on_navigate_stage` | **PASS** | Validated in offscreen smoke test |
| `WorkspaceView` | `source_repo, chapter_repo, section_repo, session_ctx, on_navigate_stage` | **PASS** | Validated in offscreen smoke test |
| `AIView` | `analysis_repo, adaptation_repo, chapter_repo, settings` | **PASS** | Validated in offscreen smoke test |
| `SubtitleView` | `chapter_repo, settings` | **PASS** | Validated in offscreen smoke test |
| `VisualView` | `asset_repo, chapter_repo, settings` | **PASS** | Validated in offscreen smoke test |
| `ProductionView` | `project_repo, source_repo, chapter_repo, analysis_repo, adaptation_repo, asset_repo, job_repo, production_run_repo, settings` | **PASS** | Validated in offscreen smoke test |
| `LibraryView` | `settings` | **PASS** | Validated in offscreen smoke test |
| `ProductionOrchestrator` | `settings, project_repo, source_repo, chapter_repo, analysis_repo, adaptation_repo, asset_repo, job_repo, production_run_repo` | **PASS** | Enforces `isinstance(settings, AppSettings)` type validation |

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
| **Contract Repair** | GUI Startup Contract Repair & Constructor Audit | **COMPLETED** | Explicit keyword arguments, `on_project_selected` callback alignment, view construction smoke tests |
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
