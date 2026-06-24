"""WSGI config for PIN Platform."""
import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application


def _ensure_postgres_bin_on_path() -> None:
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


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
_ensure_postgres_bin_on_path()

application = get_wsgi_application()
