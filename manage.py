#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import asyncio
import os
import sys
from pathlib import Path


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def _ensure_postgres_bin_on_path() -> None:
    """Make libpq available on Windows when PostgreSQL is locally installed."""
    if sys.platform != "win32":
        return

    current_path = os.environ.get("PATH", "")
    candidates = []

    postgres_bin = os.environ.get("POSTGRES_BIN")
    if postgres_bin:
        candidates.append(Path(postgres_bin))

    candidates.append(Path(r"C:\Postgres\bin"))

    program_files = Path(r"C:\Program Files\PostgreSQL")
    if program_files.exists():
        candidates.extend(sorted(program_files.glob(r"*\bin"), reverse=True))

    for candidate in candidates:
        if not candidate.exists():
            continue
        candidate_str = str(candidate)
        if candidate_str.lower() in current_path.lower():
            return
        if (candidate / "libpq.dll").exists() or (candidate / "psql.exe").exists():
            os.environ["PATH"] = candidate_str + os.pathsep + current_path
            return


def main() -> None:
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    _ensure_postgres_bin_on_path()
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
