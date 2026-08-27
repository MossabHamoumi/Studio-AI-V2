"""Universal Content Processing Engine.

Orchestrates import, validation, cleaning, chapter detection, section splitting,
persistence into SQLite, manual overrides, and import reports.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from src.domain.models import Chapter, ChapterStatus, Project, Section, Source, SourceStatus
from src.repositories.chapter_repo import ChapterRepository
from src.repositories.section_repo import SectionRepository
from src.repositories.source_repo import SourceRepository
from src.services.chapter_detector import ChapterDetector, DetectedChapter
from src.services.section_splitter import SectionSplitter
from src.services.text_cleaner import CleaningService
from src.services.text_importer import TextImportResult, TextImporter


@dataclass
class ImportReport:
    """Structured report summarizing source import results."""

    file_or_uri: str
    encoding: str
    byte_count: int
    char_count: int
    word_count: int
    line_count: int
    paragraph_count: int
    chapter_count: int
    duplicates_count: int
    gaps_count: int
    front_matter_count: int
    back_matter_count: int
    validation_status: str


class ContentEngine:
    """Universal Content Engine coordinating ingestion, cleaning, chapters, sections, and overrides."""

    def __init__(
        self,
        source_repo: SourceRepository,
        chapter_repo: ChapterRepository,
        section_repo: SectionRepository,
    ):
        self.source_repo = source_repo
        self.chapter_repo = chapter_repo
        self.section_repo = section_repo

        self.importer = TextImporter()
        self.cleaner = CleaningService()
        self.detector = ChapterDetector()
        self.splitter = SectionSplitter()

    def process_file_source(
        self, project_id: str, file_path: Union[str, Path]
    ) -> Tuple[Source, ImportReport]:
        """Ingest, clean, structure, and persist a text file source."""
        import_res = self.importer.import_text_file(file_path)
        return self._process_text_import(project_id, str(file_path), import_res)

    def process_text_source(
        self, project_id: str, raw_text: str, uri_or_path: str = "pasted_text"
    ) -> Tuple[Source, ImportReport]:
        """Ingest, clean, structure, and persist raw pasted text."""
        import_res = self.importer.import_raw_string(raw_text)
        return self._process_text_import(project_id, uri_or_path, import_res)

    def apply_manual_chapter_override(
        self,
        chapter_id: str,
        new_chapter_number: Optional[int] = None,
        new_title: Optional[str] = None,
        new_cleaned_text: Optional[str] = None,
    ) -> Chapter:
        """Apply user manual corrections to a chapter and persist."""
        chapter = self.chapter_repo.get_by_id(chapter_id)
        if new_chapter_number is not None:
            chapter.chapter_number = new_chapter_number
        if new_title is not None:
            chapter.title = new_title
        if new_cleaned_text is not None:
            chapter.cleaned_text = new_cleaned_text
            clean_res = self.cleaner.clean_text(new_cleaned_text)
            chapter.content_hash = clean_res.cleaned_hash

        return self.chapter_repo.save(chapter)

    def _process_text_import(
        self, project_id: str, uri_or_path: str, import_res: TextImportResult
    ) -> Tuple[Source, ImportReport]:
        """Internal processing pipeline."""
        # 1. Create Source entity
        source = Source(
            project_id=project_id,
            uri_or_path=uri_or_path,
            content_hash=import_res.content_hash,
            metadata={
                "encoding": import_res.encoding_used,
                "byte_count": import_res.byte_count,
                "char_count": import_res.char_count,
                "word_count": import_res.word_count,
                "line_count": import_res.line_count,
                "paragraph_count": import_res.paragraph_count,
            },
            status=SourceStatus.PROCESSING,
        )
        self.source_repo.save(source)

        # 2. Detect Chapters
        detected_chapters = self.detector.detect_chapters(import_res.raw_text)

        dup_count = 0
        gap_count = 0
        fm_count = 0
        bm_count = 0

        # 3. Clean and persist each chapter & sections
        for dc in detected_chapters:
            if dc.metadata.get("DUPLICATE_SUSPECTED"):
                dup_count += 1
            if dc.metadata.get("GAP_AFTER_PREVIOUS"):
                gap_count += 1
            if dc.classification == "FRONT_MATTER":
                fm_count += 1
            elif dc.classification == "BACK_MATTER":
                bm_count += 1

            clean_res = self.cleaner.clean_text(dc.text)

            chapter = Chapter(
                project_id=project_id,
                source_id=source.id,
                chapter_number=dc.chapter_number,
                sequence_index=dc.sequence_index,
                title=dc.title,
                start_offset=dc.start_offset,
                end_offset=dc.end_offset,
                original_text=dc.text,
                cleaned_text=clean_res.cleaned_text,
                content_hash=clean_res.cleaned_hash,
                status=ChapterStatus.CLEANED,
            )
            self.chapter_repo.save(chapter)

            # Split chapter into sections
            sections = self.splitter.split_chapter_to_sections(clean_res.cleaned_text)
            for sec in sections:
                sec_entity = Section(
                    chapter_id=chapter.id,
                    sequence_index=sec.sequence_index,
                    section_type=sec.section_type,
                    start_offset=sec.start_offset,
                    end_offset=sec.end_offset,
                    text=sec.text,
                    metadata=sec.metadata,
                )
                self.section_repo.save(sec_entity)

        source.status = SourceStatus.PROCESSED
        self.source_repo.save(source)

        import_report = ImportReport(
            file_or_uri=uri_or_path,
            encoding=import_res.encoding_used,
            byte_count=import_res.byte_count,
            char_count=import_res.char_count,
            word_count=import_res.word_count,
            line_count=import_res.line_count,
            paragraph_count=import_res.paragraph_count,
            chapter_count=len(detected_chapters),
            duplicates_count=dup_count,
            gaps_count=gap_count,
            front_matter_count=fm_count,
            back_matter_count=bm_count,
            validation_status="VALIDATED",
        )

        return source, import_report
