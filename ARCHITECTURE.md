# Studio-AI — Architecture Baseline

This document defines the systemic engineering architecture for Studio-AI.

## 1. System Overview

Studio-AI is a local-first desktop application for transforming story text (TXT, story ideas, imported documents) into narrated videos and reels.

```
+-----------------------------------------------------------------------+
|                          PySide6 Desktop UI                            |
| (Dashboard, Projects, Create Wizard, Workspace, Production, Library)  |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                       Production Orchestrator                          |
|             (Job Runner, Resumable Pipeline Stages, QA)                |
+-----------------------------------------------------------------------+
        |                  |                    |                  |
        v                  v                    v                  v
+---------------+  +---------------+  +---------------+  +---------------+
|  SQLite WAL   |  | Local Ollama  |  | Kokoro/Piper  |  | FFmpeg Render |
| State Storage |  | AI (qwen3:8b) |  |   TTS Engine  |  |  Pipeline     |
+---------------+  +---------------+  +---------------+  +---------------+
```

## 2. Master Pipeline Stages

1. **Source Ingestion & Integrity Check:** Hashes raw input, counts bytes/chars/words/paragraphs.
2. **Structure & Segmentation:** Splits novel into chapters and sections with character offset ranges.
3. **AI Story Analysis:** Extracts summary, characters, scenes, tone, mood via Ollama `qwen3:8b`.
4. **Narration Planning & TTS:** Assigns voices, synthesizes WAV/MP3 via Kokoro (primary) or Piper (fallback).
5. **Subtitle Generation:** Creates ASS subtitles (`\an5` center-center anchor) synchronized to actual audio segment timings.
6. **Visual Selection & Timeline:** Maps background video (gameplay) or static/multi-image overlays.
7. **FFmpeg Complex Filter Graph:** Generates and executes exact FFmpeg commands with explicit audio/video stream maps.
8. **Final QA Inspection:** Probes output MP4 with FFprobe to verify video/audio streams and duration integrity.

## 3. Database Schema Strategy

- SQLite WAL Mode enabled on connection.
- Foreign keys enabled (`PRAGMA foreign_keys = ON;`).
- Migrations managed via sequential SQL script runner.
- Single database file: `~/.studio-ai/studio_ai.db`.
