#!/usr/bin/env python3
"""Read the exact vulnerability DB update time from `trivy version` JSON."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def read_updated_at(document: dict) -> str:
    raw = (document.get("VulnerabilityDB") or {}).get("UpdatedAt")
    if not isinstance(raw, str) or not raw:
        raise ValueError("Trivy version evidence has no VulnerabilityDB.UpdatedAt")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Trivy vulnerability DB time is not RFC3339") from exc
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("Trivy vulnerability DB time is not UTC")
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version-json", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(read_updated_at(json.loads(args.version_json.read_text(encoding="utf-8"))))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
