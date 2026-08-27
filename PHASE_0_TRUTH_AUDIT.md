# Studio-AI — Phase 0 Truth Audit & Engineering Architecture Contract

**Repository:** `MossabHamoumi/Studio-AI`
**Phase:** Phase 0 — Product Requirements & Architecture Baseline
**Phase Status:** COMPLETED
**Phase 1 Ready:** YES

---

## 1. Repository State Audit

### 1.1 Baseline Truth
- The workspace repository (`MossabHamoumi/Studio-AI`) was initialized as a **clean empty repository** (`Initial commit`).
- No legacy code or broken historical branches have been imported.
- All product requirements and architectural contracts established in this audit serve as the binding engineering specification for all subsequent rebuild phases (Phases 1 through 12).

### 1.2 Global Ground Rules Compliance Matrix
| Rule | Principle | Implementation Contract |
|---|---|---|
| **Rule 1** | One Phase at a Time | Inspect → plan → implement → test → prove → stop. No multi-phase scope creep. |
| **Rule 2** | No Fake Success | Zero mock TTS, synthetic tone generators, or fake MP4 text files. Fail loudly on missing tools. |
| **Rule 3** | No Silent Fallback | Fallback events (e.g., Kokoro failure -> Piper attempt) must be explicitly logged and surfaced in UI. |
| **Rule 4** | Real System Doctor | System Doctor probes actual engine execution (e.g., test audio synthesis, FFmpeg run), not mere config presence. |
| **Rule 5** | Authoritative User Choices | AI provides creative suggestions but never overrides explicit user selections. |
| **Rule 6** | Immutable Source Data | Raw imported input text/files are preserved untouched; derived versions are strictly separated. |
| **Rule 7** | Durable State | SQLite in WAL mode is the single source of truth; filesystem holds media artifacts referenced by DB. |
| **Rule 8** | Resumable Operations | Pipeline stages support pause/resume/retry/cancel and reuse valid existing artifacts. |
| **Rule 9** | CPU-First Bounded Workloads | Bounded concurrency (default=1) and streaming/chunked processing for Ryzen 5 PRO 5650U / 16GB RAM. |
| **Rule 10** | Real Verification | Automated tests + actual execution + visual/audio inspection required to complete every phase. |

---

## 2. Product Vision & Requirements

Studio-AI is a **local-first desktop AI story and media production studio**.

### 2.1 Inputs
- TXT files (short stories to full-length novels up to 100,000+ words without silent truncation)
- Pasted text / ideas
- Existing project files
- Web story discovery (Phase 11 SearXNG integration)

### 2.2 Content Types
- `NOVEL`
- `SHORT_STORY`
- `ORIGINAL_STORY`
- `HORROR_STORY`
- `PHONE_CALL`
- `DIALOGUE`
- `REDDIT_STYLE`
- `PODCAST`
- `GAMEPLAY_STORY`
- `CUSTOM`

*All content types share a unified internal core domain model.*

### 2.3 Output Format Profiles
- `LONG_VIDEO`: Default 16:9 aspect ratio (1920x1080)
- `SHORT_REEL`: Default 9:16 aspect ratio (1080x1920)
- `AUDIO_ONLY`: MP3 / WAV audio export
- Custom presets for 1:1 square formats

### 2.4 Visual Modes
- `STATIC_IMAGE`: Single background image rendered across narration duration.
- `MULTI_IMAGE`: Scene/timeline-based image transitions.
- `GAMEPLAY`: Local background video clips (gameplay audio muted by default; narration is primary).
- `MIXED`: Combination of gameplay background and static/multi-image overlays.
- `NONE`: Pure audio production.

---

## 3. Hardware Strategy & Target System

- **Processor:** AMD Ryzen 5 PRO 5650U (6 cores / 12 threads)
- **RAM:** 16 GB DDR4
- **Graphics:** AMD Radeon Vega Integrated Graphics
- **Concurrency Strategy:** Heavy pipeline workloads (Ollama inference, ONNX TTS synthesis, FFmpeg rendering) run at a maximum concurrency of **1**.
- **Memory Bounding:** Large text files are streamed; TTS audio is synthesized in small sentence/paragraph chunks; FFmpeg renders directly to disk.

---

## 4. Local Technology Stack

| Layer | Component | Specification |
|---|---|---|
| **AI LLM** | Ollama | Local REST API (`http://localhost:11434`), model `qwen3:8b` |
| **TTS Engine** | Kokoro-ONNX | Primary local neural TTS engine |
| **TTS Fallback** | Piper TTS | Local ONNX/executable fallback TTS engine |
| **Media Processing** | FFmpeg & FFprobe | System-installed binaries for filtergraph construction & QA validation |
| **Database** | SQLite3 | WAL (Write-Ahead Logging) mode, explicit foreign keys & transactions |
| **GUI Framework** | PySide6 | Desktop UI (Qt 6 bindings for Python) |
| **Discovery (Future)** | SearXNG | Docker containerized search endpoint |

---

## 5. Master Pipeline Architecture

```
SOURCE DATA
   │
   ▼
[ 1. IMPORT & INTEGRITY CHECK ] (Byte, Char, Word, Paragraph count validation)
   │
   ▼
[ 2. STRUCTURE & SPLIT ] (Chapter & Section Segmentation with character offset tracking)
   │
   ▼
[ 3. STORY ANALYSIS ] (Characters, Tone, Mood, Events, Visual Opportunities via Ollama)
   │
   ▼
[ 4. OPTIONAL ADAPTATION ] (Scripting, Dialogue Extraction, Pace Adjustment)
   │
   ▼
[ 5. NARRATION PLAN ] (Voice Assignment, Speed, Chunking)
   │
   ▼
[ 6. REAL TTS SYNTHESIS ] (Kokoro primary -> Piper fallback; Audio Chunk Cache)
   │
   ▼
[ 7. AUDIO VALIDATION & TIMELINE ] (FFprobe duration check, Audio Concatenation)
   │
   ▼
[ 8. SUBTITLE GENERATION ] (ASS \an5 Subtitles with timing aligned to real audio duration)
   │
   ▼
[ 9. VISUAL PLANNER ] (Gameplay selection, Static image scaling, Scene timing)
   │
   ▼
[ 10. RENDER SPEC & FFMPEG ] (Complex FilterGraph generation, H.264/AAC encoding)
   │
   ▼
[ 11. FINAL QA VALIDATION ] (FFprobe stream checks: audio present, video present, duration match)
   │
   ▼
[ 12. PRODUCTION RUN COMPLETED ]
```

---

## 6. Domain Model Entities

The persistent domain entities stored in SQLite:

1. **`Project`**: Root container for production (`id`, `title`, `content_type`, `output_type`, `status`, `created_at`, `updated_at`).
2. **`Source`**: Original untouched input content (`id`, `project_id`, `raw_text`, `byte_count`, `char_count`, `word_count`, `paragraph_count`, `hash`).
3. **`Chapter`**: Sequential chapter unit (`id`, `project_id`, `chapter_number`, `sequence_index`, `title`, `start_offset`, `end_offset`, `cleaned_text`).
4. **`Section`**: Granular paragraph/scene unit (`id`, `chapter_id`, `sequence_index`, `text`, `character_speaker`).
5. **`Analysis`**: AI-extracted metadata (`id`, `project_id`, `chapter_id`, `summary`, `characters_json`, `locations_json`, `tone`, `mood`, `themes_json`, `visual_opportunities_json`).
6. **`Adaptation`**: Script modifications (`id`, `project_id`, `chapter_id`, `adapted_text`, `notes`).
7. **`ProductionPlan`**: High-level execution blueprint (`id`, `project_id`, `aspect_ratio`, `visual_mode`, `target_duration`).
8. **`NarrationPlan`**: TTS execution mapping (`id`, `production_plan_id`, `chapter_id`, `voice_id`, `speed`, `provider_preference`).
9. **`AudioAsset`**: Generated audio files (`id`, `narration_plan_id`, `file_path`, `duration_seconds`, `sample_rate`, `provider_used`, `status`).
10. **`SubtitleAsset`**: Subtitle files (`id`, `audio_asset_id`, `file_path`, `format`, `style_profile`).
11. **`VisualPlan`**: Visual timeline specification (`id`, `production_plan_id`, `mode`, `spec_json`).
12. **`Asset`**: General imported asset (image, graphic, audio track).
13. **`GameplayAsset`**: Local gameplay clip metadata (`id`, `file_path`, `filename`, `duration`, `resolution`, `fps`, `codec`, `hash`, `tags`, `category`).
14. **`Job`**: Background task tracking (`id`, `project_id`, `stage`, `status`, `progress_percentage`, `error_message`, `created_at`, `updated_at`).
15. **`ProductionRun`**: Complete render run tracking (`id`, `project_id`, `output_file_path`, `status`, `duration_seconds`, `qa_passed`).

---

## 7. Diagnostic System Contract

When an error occurs or a production run completes, a diagnostic bundle is written to disk:
`diagnostic_bundle_<run_id>.json`

**Contents:**
- `environment`: OS, Python version, CPU, RAM, FFmpeg version, Ollama connection status, Kokoro/Piper status.
- `project`: Project ID, title, content type, output type.
- `chapter_context`: Active chapter ID and sequence index.
- `stage`: Active pipeline stage name.
- `job`: Job ID, status, progress.
- `exception`: Exception type, message, formatted stack trace.
- `subprocess_info`: Command line execution strings, return codes, stdout/stderr tails.
- `artifacts`: List of generated file paths and verification status.

*No API keys or sensitive user credentials are included in diagnostic bundles.*

---

## 8. Creative Desktop UI Specification

Main navigation views in PySide6:
1. **Dashboard:** Active productions, recent projects, quick stats, system health indicators.
2. **Projects:** Searchable project list, creation, state restoration.
3. **Create:** Guided production wizard:
   - What am I making? (Content Type)
   - What am I using? (Input Text / File)
   - What will it produce? (Format Profile & Duration)
   - Voice Selection (Kokoro/Piper voices)
   - Visual Selection (Gameplay / Static / Multi-Image)
   - Subtitle Style (ASS \an5 presets)
   - AI Assistance Mode (`AI_FULL`, `AI_ASSISTED`, `LOCAL_ONLY`)
   - Review & Approve
4. **Workspace:** Chapter editing, script adaptation, story structure review.
5. **Production:** Active render progress, stage logs, System Doctor diagnostics.
6. **Library:** Gameplay video manager, image asset library, voice presets.
7. **Settings:** Provider configurations (Ollama URL/model, Kokoro voice models, FFmpeg paths).

---

## 9. Testing Strategy

1. **Unit Tests:** Verification of text splitters, integrity counters, database schemas, filtergraph command builders, ASS subtitle generators.
2. **Integration Tests:** Database transaction persistence, Ollama mock API schema validation, audio chunking, FFmpeg command syntax generation.
3. **Real Media Acceptance Tests:** Execution of FFmpeg renders, FFprobe stream inspections, real audio duration verifications.

---

## 10. Phase Roadmap

- **Phase 0:** Requirements & Architecture Baseline (Current)
- **Phase 1:** Durable Core + Project Memory
- **Phase 2:** Universal Content Engine
- **Phase 3:** Local AI Layer
- **Phase 4:** Real TTS + Narration
- **Phase 5:** Subtitle Engine
- **Phase 6:** Visual Engine
- **Phase 7:** Hardened FFmpeg Render Pipeline
- **Phase 8:** Production Orchestrator
- **Phase 9:** Creative Desktop UI
- **Phase 10:** Mandatory Windows Hardware Acceptance
- **Phase 11:** SearXNG + Docker + Story Discovery
- **Phase 12:** Metadata + Publishing + Analytics

---

## 11. Architectural Decision Records (ADRs)

- **ADR-001:** Single SQLite Database with WAL mode for absolute state durability.
- **ADR-002:** Strict CPU concurrency limit of 1 for heavy background jobs.
- **ADR-003:** Kokoro-ONNX as primary TTS with Piper ONNX as explicit fallback. Zero synthetic tone generation.
- **ADR-004:** Complex FFmpeg filtergraph rendering with explicit stream mapping (`[v]`, `[a]`).
- **ADR-005:** Standard ASS `\an5` (center-center) subtitles as default vertical anchor for mobile & reel videos.
- **ADR-006:** Complete isolation of chapter artifacts into `chapters/NNN/` directories.
- **ADR-007:** Strict schema enforcement on all Ollama AI outputs.

---

**PHASE 1 READY: YES**
