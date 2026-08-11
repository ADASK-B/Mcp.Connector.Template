#!/usr/bin/env python3
"""Render build-local Helm values for scanning one exact release image."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REPOSITORY = re.compile(r"^[A-Za-z0-9.-]+/[A-Za-z0-9._/-]+$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


def render(repository: str, digest: str) -> dict:
    if REPOSITORY.fullmatch(repository) is None or "@" in repository:
        raise ValueError("repository must be an untagged OCI repository")
    if DIGEST.fullmatch(digest) is None:
        raise ValueError("digest must be an exact sha256 digest")
    return {"image": {"repository": repository, "digest": digest}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--digest", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        values = render(args.repository, args.digest)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(values, sort_keys=True) + "\n", encoding="utf-8")
    print(f"WROTE: build-local exact image values to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
