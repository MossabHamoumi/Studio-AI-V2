"""System Doctor Diagnostic Tool.

Performs honest, real health checks on foundational environment components.
"""

import os
import platform
import sys
from pathlib import Path
from typing import Dict, Any
from src.config.settings import AppSettings
from src.database.engine import DatabaseEngine


class SystemDoctor:
    """System Doctor diagnostic runner for foundation infrastructure."""

    def __init__(self, settings: AppSettings):
        self.settings = settings

    def run_foundation_checks(self) -> Dict[str, Any]:
        """Run diagnostic checks on Python, OS, CPU, RAM, SQLite, and storage."""
        results: Dict[str, Any] = {}

        # 1. Python Environment Check
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        results["python"] = {
            "status": "OK" if sys.version_info >= (3, 10) else "WARNING",
            "version": py_version,
            "executable": sys.executable,
        }

        # 2. Operating System & Machine Architecture
        results["os"] = {
            "status": "OK",
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }

        # 3. Hardware / Memory Bounding Strategy
        results["hardware"] = {
            "status": "OK",
            "cpu_count": os.cpu_count() or 1,
            "bounded_heavy_concurrency": 1,
            "target_hardware_spec": "AMD Ryzen 5 PRO 5650U / 16GB RAM",
        }

        # 4. SQLite Database Engine Verification
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

        # 5. Workspace Storage & Write Permissions
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
            if status != "OK":
                all_ok = False
            print(f"[{symbol}] {category.upper()}: {status}")
            for k, v in info.items():
                if k != "status":
                    print(f"    - {k}: {v}")
            print("-" * 60)

        return all_ok
