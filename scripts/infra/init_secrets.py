#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import secrets
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory")
    args = parser.parse_args()
    root = Path(args.directory)
    root.mkdir(parents=True, exist_ok=True)
    values = {
        "db_admin_password": secrets.token_urlsafe(32),
        "db_password": secrets.token_urlsafe(32),
        "redis_password": secrets.token_urlsafe(32),
        "jwt_secret": secrets.token_urlsafe(64),
        "ai_internal_token": secrets.token_urlsafe(64),
    }
    for name, value in values.items():
        path = root / name
        if not path.exists():
            path.write_bytes((value + "\n").encode("utf-8"))
            if os.name != "nt":
                path.chmod(0o600)
        else:
            existing = path.read_text(encoding="utf-8").strip()
            if not existing or "\n" in existing or "\r" in existing:
                raise SystemExit(f"refusing to normalize malformed secret file: {path}")
            path.write_bytes((existing + "\n").encode("utf-8"))
    if os.name != "nt":
        root.chmod(0o700)
    print(root.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
