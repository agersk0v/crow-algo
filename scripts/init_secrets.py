"""Generate local Compose credentials once; never overwrite existing passwords."""

import secrets
from pathlib import Path


def initialize(directory: Path) -> None:
    if directory.is_symlink():
        raise ValueError("secret directory must not be a symlink")
    directory.mkdir(mode=0o700, exist_ok=True)
    directory.chmod(0o700)
    files = [
        directory / (name + ".txt") for name in ("postgres", "migration", "runtime")
    ]
    if any(path.exists() for path in files):
        raise ValueError(
            "credentials already exist; reuse them instead of regenerating"
        )
    for path in files:
        with path.open("x") as stream:
            stream.write(secrets.token_hex(32) + "\n")
        # Compose file-backed secrets preserve host permissions. The private parent
        # directory protects the files on the host; non-root containers need read.
        path.chmod(0o444)


if __name__ == "__main__":
    try:
        initialize(Path(".secrets"))
    except (OSError, ValueError) as exc:
        raise SystemExit(str(exc)) from None
    print("Local credentials created in .secrets; no passwords printed.")
