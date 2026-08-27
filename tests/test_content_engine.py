"""Tests for Universal Content Engine (Phase 2)."""

from pathlib import Path
import pytest
from src.database.engine import DatabaseEngine
from src.database.migrations import MigrationRunner
from src.domain.models import Project, ProjectType
from src.repositories.chapter_repo import ChapterRepository
from src.repositories.project_repo import ProjectRepository
from src.repositories.section_repo import SectionRepository
from src.repositories.source_repo import SourceRepository
from src.services.content_engine import ContentEngine
from src.services.text_importer import TextImporter


@pytest.fixture
def test_db(tmp_path: Path):
    db_file = tmp_path / "test_content.db"
    engine = DatabaseEngine(db_file)
    migrator = MigrationRunner(engine)
    migrator.apply_migrations()
    yield engine
    engine.close()


def test_9000_word_non_truncation_regression(test_db: DatabaseEngine, tmp_path: Path):
    """PERMANENT REGRESSION: Ingest a 9,000+ word document and verify 100% full preservation."""
    source_repo = SourceRepository(test_db)
    chap_repo = ChapterRepository(test_db)
    sec_repo = SectionRepository(test_db)
    proj_repo = ProjectRepository(test_db)

    project = proj_repo.save(Project(title="9,000 Word Novel", project_type=ProjectType.NOVEL))

    # Generate a 9,500 word document with 10 chapters
    words_list = ["word" + str(i) for i in range(9500)]
    # Split into 10 chapters
    chapter_blocks = []
    chunk_size = 950
    for c in range(10):
        c_words = words_list[c * chunk_size : (c + 1) * chunk_size]
        body = " ".join(c_words)
        chapter_blocks.append(f"CHAPTER {c + 1}\n\n{body}\n\n")

    full_text = "\n".join(chapter_blocks)

    file_path = tmp_path / "large_novel_9000_words.txt"
    file_path.write_text(full_text, encoding="utf-8")

    engine = ContentEngine(source_repo, chap_repo, sec_repo)
    source, report = engine.process_file_source(project.id, file_path)

    # 1. Non-truncation verifications
    assert report.word_count >= 9500
    assert report.char_count == len(full_text)
    assert report.byte_count == len(full_text.encode("utf-8"))

    # 2. Check stored chapters
    chapters = chap_repo.list_by_project(project.id)
    assert len(chapters) == 10

    # Reconstruct total text from stored chapters and verify character match
    reconstructed = "".join([c.original_text for c in chapters])
    assert reconstructed == full_text


def test_encodings_bom_and_windows_lines(tmp_path: Path):
    importer = TextImporter()

    # UTF-8 with BOM
    bom_file = tmp_path / "bom.txt"
    bom_file.write_bytes(b"\xef\xbb\xbfChapter 1\nHello World!")
    res_bom = importer.import_text_file(bom_file)
    assert res_bom.encoding_used == "utf-8-sig"
    assert "Hello World!" in res_bom.raw_text

    # Windows CRLF Line Endings
    crlf_file = tmp_path / "crlf.txt"
    crlf_file.write_bytes(b"Line 1\r\nLine 2\r\nLine 3")
    res_crlf = importer.import_text_file(crlf_file)
    assert res_crlf.line_count == 3
    assert "\r" not in res_crlf.raw_text


def test_chapter_detection_roman_words_and_duplicates(test_db: DatabaseEngine):
    source_repo = SourceRepository(test_db)
    chap_repo = ChapterRepository(test_db)
    sec_repo = SectionRepository(test_db)
    proj_repo = ProjectRepository(test_db)

    project = proj_repo.save(Project(title="Roman & Duplicates"))

    sample_text = (
        "PROLOGUE\nThis is front matter.\n\n"
        "CHAPTER I\nFirst chapter content.\n\n"
        "CHAPTER IV\nFourth chapter content.\n\n"
        "Chapter IV\nDuplicate fourth chapter.\n\n"
        "EPILOGUE\nBack matter content."
    )

    engine = ContentEngine(source_repo, chap_repo, sec_repo)
    source, report = engine.process_text_source(project.id, sample_text)

    chapters = chap_repo.list_by_project(project.id)
    assert len(chapters) == 5

    # Check Sequence Indices vs Chapter Numbers
    assert chapters[0].title == "Prologue"
    assert chapters[0].chapter_number == 0

    assert chapters[1].chapter_number == 1  # CHAPTER I
    assert chapters[2].chapter_number == 4  # CHAPTER IV

    assert report.duplicates_count >= 1  # Chapter IV repeated
    assert report.gaps_count >= 1        # Skip from 1 to 4


def test_phone_call_dialogue_sections(test_db: DatabaseEngine):
    source_repo = SourceRepository(test_db)
    chap_repo = ChapterRepository(test_db)
    sec_repo = SectionRepository(test_db)
    proj_repo = ProjectRepository(test_db)

    project = proj_repo.save(Project(title="Phone Call"))

    script_text = (
        "CHAPTER 1\n\n"
        "OPERATOR: [Ringing]\n\n"
        "DETECTIVE: Hello, who is this?\n\n"
        "CALLER: I have the evidence."
    )

    engine = ContentEngine(source_repo, chap_repo, sec_repo)
    engine.process_text_source(project.id, script_text)

    chapters = chap_repo.list_by_project(project.id)
    sections = sec_repo.list_by_chapter(chapters[0].id)

    assert len(sections) == 4
    assert sections[1].metadata["speaker"] == "OPERATOR"
    assert sections[1].metadata["role"] == "SOUND_CUE"
    assert sections[2].metadata["speaker"] == "DETECTIVE"
    assert sections[3].metadata["speaker"] == "CALLER"


def test_manual_chapter_overrides(test_db: DatabaseEngine):
    source_repo = SourceRepository(test_db)
    chap_repo = ChapterRepository(test_db)
    sec_repo = SectionRepository(test_db)
    proj_repo = ProjectRepository(test_db)

    project = proj_repo.save(Project(title="Override Test"))
    text = "CHAPTER 1\nOriginal content."

    engine = ContentEngine(source_repo, chap_repo, sec_repo)
    engine.process_text_source(project.id, text)

    chapters = chap_repo.list_by_project(project.id)
    ch = chapters[0]

    # Apply manual override
    updated = engine.apply_manual_chapter_override(
        ch.id,
        new_chapter_number=10,
        new_title="Manually Corrected Title",
        new_cleaned_text="Manually updated cleaned text.",
    )

    assert updated.chapter_number == 10
    assert updated.title == "Manually Corrected Title"
    assert updated.cleaned_text == "Manually updated cleaned text."
    # Original text remains untouched!
    assert updated.original_text == text
