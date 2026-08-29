"""Master Production Orchestrator & Resumable Execution Engine.

Coordinates end-to-end production runs across ANALYSIS, ADAPTATION, NARRATION, SUBTITLES,
VISUALS, RENDER, and QA stages. Supports single chapter and full novel batching with strict
chapter folder isolation (chapters/NNN/) and stage-level resume/retry.
"""

import json
import logging
from pathlib import Path
from typing import Callable, List, Optional, Tuple
from src.config.settings import AppSettings
from src.domain.ai_models import AIMode, AdaptationStatus
from src.domain.models import (
    Asset,
    AssetType,
    Chapter,
    Job,
    JobStatus,
    JobType,
    ProductionRun,
    ProductionRunStatus,
    Project,
    StageName,
)
from src.domain.render_models import QAReport, RenderSpec
from src.domain.subtitle_models import SubtitleStyleProfile
from src.domain.tts_models import TTSProviderType
from src.domain.visual_models import OutputProfile, ScalingMode, VisualMode
from src.repositories.adaptation_repo import AdaptationRepository
from src.repositories.analysis_repo import AnalysisRepository
from src.repositories.asset_repo import AssetRepository
from src.repositories.chapter_repo import ChapterRepository
from src.repositories.job_repo import JobRepository
from src.repositories.production_run_repo import ProductionRunRepository
from src.repositories.project_repo import ProjectRepository
from src.repositories.source_repo import SourceRepository
from src.services.ai_director import AIDirector
from src.services.diagnostic_bundle import DiagnosticBundleExporter
from src.services.narration_engine import NarrationEngine
from src.services.preflight_checker import PreflightChecker
from src.services.render_pipeline import RenderPipeline
from src.services.subtitle_engine import SubtitleEngine
from src.services.visual_planner import VisualPlanner
from src.utilities.exceptions import StudioAIError, ValidationError
from src.utilities.logging import get_logger

logger = get_logger()


class ProductionOrchestrator:
    """Master Production Orchestrator coordinating all pipeline stages with durable resume support."""

    def __init__(
        self,
        settings: AppSettings,
        project_repo: ProjectRepository,
        source_repo: SourceRepository,
        chapter_repo: ChapterRepository,
        analysis_repo: AnalysisRepository,
        adaptation_repo: AdaptationRepository,
        asset_repo: AssetRepository,
        job_repo: JobRepository,
        production_run_repo: ProductionRunRepository,
    ):
        if not isinstance(settings, AppSettings):
            actual_type = type(settings).__name__
            raise TypeError(
                f"ProductionOrchestrator constructor error: 'settings' argument must be an AppSettings instance, "
                f"got '{actual_type}'. Please check constructor parameter order."
            )
        if not isinstance(project_repo, ProjectRepository):
            raise TypeError(
                f"ProductionOrchestrator constructor error: 'project_repo' must be a ProjectRepository instance, got '{type(project_repo).__name__}'."
            )

        self.settings = settings
        self.project_repo = project_repo
        self.source_repo = source_repo
        self.chapter_repo = chapter_repo
        self.analysis_repo = analysis_repo
        self.adaptation_repo = adaptation_repo
        self.asset_repo = asset_repo
        self.job_repo = job_repo
        self.run_repo = production_run_repo

        # Service Instances
        self.preflight = PreflightChecker(settings, chapter_repo, source_repo)
        self.ai_director = AIDirector(analysis_repo, adaptation_repo, settings)
        self.narration_engine = NarrationEngine(settings)
        self.subtitle_engine = SubtitleEngine(settings)
        self.visual_planner = VisualPlanner(settings)
        self.render_pipeline = RenderPipeline(settings, asset_repo)
        self.bundle_exporter = DiagnosticBundleExporter(settings)

    def run_chapter_production(
        self,
        project_id: str,
        chapter_id: str,
        ai_mode: AIMode = AIMode.AI_FULL,
        voice_id: str = "af_heart",
        visual_mode: VisualMode = VisualMode.STATIC_IMAGE,
        profile: OutputProfile = OutputProfile.LANDSCAPE_16_9,
        subtitle_style: SubtitleStyleProfile = SubtitleStyleProfile.DEFAULT,
        force_rerun: bool = False,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> Tuple[ProductionRun, Path, QAReport]:
        """Run production pipeline for a single explicitly requested chapter with durable resume support."""
        project = self.project_repo.get_by_id(project_id)
        chapter = self.chapter_repo.get_by_id(chapter_id)

        # 1. Preflight Check
        is_ok, errors = self.preflight.check_preflight(
            project, [chapter_id], ai_mode=ai_mode, voice_id=voice_id
        )
        if not is_ok:
            raise ValidationError(f"Preflight validation failed: {'; '.join(errors)}")

        # Create or resume ProductionRun
        run = ProductionRun(
            project_id=project_id,
            status=ProductionRunStatus.RUNNING,
            current_stage=StageName.ANALYSIS,
            progress=0.0,
        )
        self.run_repo.save(run)

        try:
            # Stage 1: ANALYSIS (Resume check: reuse existing analysis if available)
            run.current_stage = StageName.ANALYSIS
            self.run_repo.save(run)
            if progress_callback:
                progress_callback("ANALYSIS", 0.1)

            existing_analysis = self.analysis_repo.get_by_chapter(chapter_id) if not force_rerun else None
            if existing_analysis:
                logger.info(f"RESUME: Reusing existing analysis for chapter {chapter_id}")
                analysis = existing_analysis
            else:
                analysis, _ = self.ai_director.analyze_chapter(
                    project_id=project_id,
                    chapter_id=chapter_id,
                    chapter_text=chapter.cleaned_text or chapter.original_text,
                    source_text_hash=chapter.content_hash,
                    mode=ai_mode,
                )

            # Stage 2: ADAPTATION (Resume check: reuse accepted adaptation)
            run.current_stage = StageName.ADAPTATION
            self.run_repo.save(run)
            if progress_callback:
                progress_callback("ADAPTATION", 0.25)

            accepted_adapt = self.adaptation_repo.get_accepted_by_chapter(chapter_id)
            if accepted_adapt and not force_rerun:
                logger.info(f"RESUME: Reusing accepted adaptation for chapter {chapter_id}")
                narration_text = accepted_adapt.adapted_text
            else:
                adapt, _ = self.ai_director.adapt_chapter_script(
                    project_id=project_id,
                    chapter_id=chapter_id,
                    chapter_text=chapter.cleaned_text or chapter.original_text,
                    source_text_hash=chapter.content_hash,
                    mode=ai_mode,
                )
                narration_text = adapt.adapted_text

            # Stage 3: NARRATION
            run.current_stage = StageName.NARRATION
            self.run_repo.save(run)
            if progress_callback:
                progress_callback("NARRATION", 0.4)

            audio_timeline = self.narration_engine.generate_narration_timeline(
                project_id=project_id,
                chapter_id=chapter_id,
                text=narration_text,
                voice_id=voice_id,
            )

            # Stage 4: SUBTITLES
            run.current_stage = StageName.SUBTITLES
            self.run_repo.save(run)
            if progress_callback:
                progress_callback("SUBTITLES", 0.55)

            ass_path, srt_path, _ = self.subtitle_engine.generate_subtitles_from_audio_timeline(
                timeline=audio_timeline,
                style_profile=subtitle_style,
            )

            # Stage 5: VISUALS
            run.current_stage = StageName.VISUALS
            self.run_repo.save(run)
            if progress_callback:
                progress_callback("VISUALS", 0.7)

            visual_spec = self.visual_planner.create_visual_plan(
                project_id=project_id,
                chapter_id=chapter_id,
                mode=visual_mode,
                profile=profile,
            )

            # Stage 6 & 7: RENDER & QA
            run.current_stage = StageName.RENDER
            self.run_repo.save(run)
            if progress_callback:
                progress_callback("RENDER", 0.85)

            # Isolated chapter output path: chapters/001/render/chapter_output.mp4
            pdir = self.settings.get_project_dir(project_id)
            cnum_str = f"{chapter.sequence_index + 1:03d}"
            output_dir = pdir / "chapters" / cnum_str / "render"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_mp4 = output_dir / f"chapter_{cnum_str}_render.mp4"

            render_spec = RenderSpec(
                project_id=project_id,
                chapter_id=chapter_id,
                output_path=str(output_mp4),
                narration_audio_path=audio_timeline.assembled_audio_path,
                target_duration_seconds=audio_timeline.total_duration_seconds,
                width=visual_spec.width,
                height=visual_spec.height,
                fps=30,
                visual_mode=visual_mode,
                subtitle_ass_path=str(ass_path),
                title_card=visual_spec.title_card,
            )

            out_file, qa_report = self.render_pipeline.execute_render_pipeline(render_spec)

            run.status = ProductionRunStatus.COMPLETED
            run.current_stage = StageName.QA
            run.progress = 1.0
            self.run_repo.save(run)

            if progress_callback:
                progress_callback("COMPLETED", 1.0)

            return run, out_file, qa_report

        except Exception as e:
            run.status = ProductionRunStatus.FAILED
            run.failure_reason = str(e)
            self.run_repo.save(run)

            # Export diagnostic bundle on failure
            self.bundle_exporter.export_bundle(
                production_run=run,
                project=project,
                chapter=chapter,
                exception=e,
            )
            raise

    def run_novel_production(
        self,
        project_id: str,
        ai_mode: AIMode = AIMode.AI_FULL,
        voice_id: str = "af_heart",
        visual_mode: VisualMode = VisualMode.STATIC_IMAGE,
        profile: OutputProfile = OutputProfile.LANDSCAPE_16_9,
        progress_callback: Optional[Callable[[str, int, float], None]] = None,
    ) -> List[Tuple[ProductionRun, Path, QAReport]]:
        """Run production sequentially across every chapter in a novel."""
        chapters = self.chapter_repo.list_by_project(project_id)
        if not chapters:
            raise ValidationError(f"Novel production failed: project '{project_id}' has no chapters.")

        results: List[Tuple[ProductionRun, Path, QAReport]] = []

        for idx, ch in enumerate(chapters):
            logger.info(f"Processing Novel Chapter #{ch.sequence_index + 1} ({ch.title})...")

            def _chapter_progress(stage: str, prog: float):
                if progress_callback:
                    progress_callback(stage, idx, prog)

            res = self.run_chapter_production(
                project_id=project_id,
                chapter_id=ch.id,
                ai_mode=ai_mode,
                voice_id=voice_id,
                visual_mode=visual_mode,
                profile=profile,
                progress_callback=_chapter_progress,
            )
            results.append(res)

        return results
