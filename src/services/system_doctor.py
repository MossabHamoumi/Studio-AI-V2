"""System Doctor Diagnostic Tool.

Performs honest, real health checks on foundational environment, venv, PySide6, FFmpeg/FFprobe,
Ollama AI, and Kokoro/Piper TTS components.
"""

import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Dict, Any
from src.config.settings import AppSettings
from src.database.engine import DatabaseEngine
from src.domain.ai_models import AIStatus
from src.providers.tts_kokoro import KokoroTTSProvider
from src.providers.tts_piper import PiperTTSProvider
from src.services.ai_provider import OllamaProvider


class SystemDoctor:
    """System Doctor diagnostic runner for environment, AI, and TTS infrastructure."""

    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.ollama_provider = OllamaProvider()
        self.kokoro_provider = KokoroTTSProvider()
        self.piper_provider = PiperTTSProvider()

    def run_foundation_checks(self) -> Dict[str, Any]:
        """Run diagnostic checks on Python, venv, PySide6, OS, CPU, RAM, SQLite, storage, FFmpeg, Ollama, and TTS."""
        results: Dict[str, Any] = {}

        # 1. Python Environment Check
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        results["python"] = {
            "status": "OK" if (3, 10) <= sys.version_info < (3, 13) else "WARNING",
            "version": py_version,
            "executable": sys.executable,
        }

        # 2. Virtual Environment Check
        is_venv = sys.prefix != sys.base_prefix
        results["venv"] = {
            "status": "OK" if is_venv else "WARNING",
            "active": is_venv,
            "prefix_path": sys.prefix,
            "message": "Project virtual environment is ACTIVE" if is_venv else "Running in global Python (Recommend: .\\.venv\\Scripts\\python.exe)",
        }

        # 3. PySide6 GUI Framework Check
        try:
            import PySide6
            from PySide6.QtCore import __version__ as qt_version
            results["pyside6"] = {
                "status": "OK",
                "installed": True,
                "version": PySide6.__version__,
                "qt_version": qt_version,
            }
        except ImportError as e:
            results["pyside6"] = {
                "status": "ERROR",
                "installed": False,
                "error": str(e),
                "install_command": ".\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt",
            }

        # 4. Operating System & Machine Architecture
        results["os"] = {
            "status": "OK",
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }

        # 5. Hardware / Memory Bounding Strategy
        results["hardware"] = {
            "status": "OK",
            "cpu_count": os.cpu_count() or 1,
            "bounded_heavy_concurrency": 1,
            "target_hardware_spec": "AMD Ryzen 5 PRO 5650U / 16GB RAM",
        }

        # 6. SQLite Database Engine Verification
        try:
            db_path = self.settings.workspace_dir / "doctor_probe.db"
            engine = DatabaseEngine(db_path)
            conn = engine.get_connection()
            cursor = conn.execute("PRAGMA journal_mode;")
            mode = cursor.fetchone()[0]
            engine.close()
            if db_path.exists():
                db_path.unlink()

            results["sqlite"] = {
                "status": "OK" if mode.lower() == "wal" else "WARNING",
                "journal_mode": mode,
            }
        except Exception as e:
            results["sqlite"] = {
                "status": "ERROR",
                "message": str(e),
            }

        # 7. Workspace Storage & Write Permissions
        try:
            test_file = self.settings.workspace_dir / "doctor_write_test.tmp"
            test_file.write_text("write_permission_check", encoding="utf-8")
            test_file.unlink()
            results["storage"] = {
                "status": "OK",
                "workspace_path": str(self.settings.workspace_dir),
                "write_permission": True,
            }
        except Exception as e:
            results["storage"] = {
                "status": "ERROR",
                "workspace_path": str(self.settings.workspace_dir),
                "write_permission": False,
                "error": str(e),
            }

        # 8. FFmpeg & FFprobe Binary Checks
        ffmpeg_bin = shutil.which("ffmpeg")
        ffprobe_bin = shutil.which("ffprobe")
        results["ffmpeg"] = {
            "status": "OK" if ffmpeg_bin else "WARNING",
            "ffmpeg_installed": ffmpeg_bin is not None,
            "ffmpeg_path": ffmpeg_bin or "NOT FOUND in PATH",
        }
        results["ffprobe"] = {
            "status": "OK" if ffprobe_bin else "WARNING",
            "ffprobe_installed": ffprobe_bin is not None,
            "ffprobe_path": ffprobe_bin or "NOT FOUND in PATH",
        }

        # 9. Real Ollama AI Health Verification
        ollama_status = self.ollama_provider.check_health()
        results["ollama_ai"] = {
            "status": "OK" if ollama_status == AIStatus.AVAILABLE else "WARNING",
            "ollama_status": ollama_status.value,
            "endpoint": self.ollama_provider.base_url,
            "default_model": self.ollama_provider.model,
        }

        # 10. Real Kokoro TTS Engine Verification
        kokoro_avail = self.kokoro_provider.is_available()
        results["kokoro_tts"] = {
            "status": "OK" if kokoro_avail else "WARNING",
            "installed_and_models_present": kokoro_avail,
            "engine": "kokoro-onnx",
            "model_path": str(self.kokoro_provider.model_path),
            "voices_count": len(self.kokoro_provider.list_voices()),
        }

        # 11. Real Piper TTS Engine Verification
        piper_avail = self.piper_provider.is_available()
        results["piper_tts"] = {
            "status": "OK" if piper_avail else "WARNING",
            "installed_and_models_present": piper_avail,
            "engine": "piper-tts",
            "model_dir": str(self.piper_provider.model_dir),
            "voices_count": len(self.piper_provider.list_voices()),
        }

        return results

    def print_doctor_report(self) -> bool:
        """Print human-readable System Doctor report to stdout."""
        checks = self.run_foundation_checks()
        print("=" * 60)
        print("            STUDIO-AI SYSTEM DOCTOR REPORT")
        print("=" * 60)
        all_ok = True

        for category, info in checks.items():
            status = info.get("status", "UNKNOWN")
            symbol = "✓" if status == "OK" else "✗"
            if status == "ERROR":
                all_ok = False
            print(f"[{symbol}] {category.upper()}: {status}")
            for k, v in info.items():
                if k != "status":
                    print(f"    - {k}: {v}")
            print("-" * 60)

        return all_ok
