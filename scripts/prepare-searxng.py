#!/usr/bin/env python3
"""Create private runtime configuration; never overwrite an existing install."""
from pathlib import Path
import secrets
import os
root = Path(__file__).resolve().parents[1]
target = Path.home() / "searxng/config/settings.yml"
target.parent.mkdir(parents=True, exist_ok=True)
text = (root / "configs/searxng/settings.yml.example").read_text()
text = text.replace("<GENERATE_LOCALLY>", secrets.token_hex(32))
fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "w") as out:
    out.write(text)
print("Created private runtime settings; do not commit this file.")
