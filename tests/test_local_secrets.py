"""Local credentials must not be replaced accidentally on a second setup."""

import subprocess
import sys
from pathlib import Path


def test_secret_initialization_does_not_print_or_overwrite_passwords(
    tmp_path: Path,
) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "init_secrets.py"
    first = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    directory = tmp_path / ".secrets"
    before = {path.name: path.read_bytes() for path in directory.iterdir()}
    assert len(before) == 3
    assert directory.stat().st_mode & 0o777 == 0o700
    assert all(
        value.decode().strip() not in first.stdout + first.stderr
        for value in before.values()
    )
    repeated = subprocess.run(
        [sys.executable, str(script)], cwd=tmp_path, capture_output=True, text=True
    )
    assert repeated.returncode != 0
    assert before == {path.name: path.read_bytes() for path in directory.iterdir()}
