#!/usr/bin/env python3
"""Materialize the exact vendored Foundation CUE schema snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "release/foundation-contracts"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


def fetch(output: Path) -> list[Path]:
    release = json.loads((ROOT / "release/release-input.json").read_text(encoding="utf-8"))
    binding = release["foundationContract"]
    if binding["repository"] != "https://github.com/ADASK-B/platform-foundation":
        raise ValueError("Foundation contract repository is not approved")
    commit = binding["commit"]
    if COMMIT.fullmatch(commit) is None:
        raise ValueError("Foundation contract commit must be immutable")
    schemas = binding["schemas"]
    if set(schemas) != {
        "application-contract.schema.cue",
        "application-delivery-package.schema.cue",
    } or any(SHA256.fullmatch(value) is None for value in schemas.values()):
        raise ValueError("Foundation schema inventory is not the closed two-file contract")
    if not SNAPSHOT.is_dir() or SNAPSHOT.is_symlink():
        raise ValueError("vendored Foundation schema snapshot is missing or unsafe")
    if {path.name for path in SNAPSHOT.iterdir()} != set(schemas):
        raise ValueError("vendored Foundation schema snapshot contains unexpected files")
    verified: list[tuple[str, bytes]] = []
    for name, expected in sorted(schemas.items()):
        source = SNAPSHOT / name
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"vendored Foundation schema is missing or unsafe: {name}")
        content = source.read_bytes()
        observed = hashlib.sha256(content).hexdigest()
        if observed != expected:
            raise ValueError(f"vendored Foundation schema digest mismatch: {name}")
        verified.append((name, content))

    output.mkdir(parents=True, exist_ok=False)
    written: list[Path] = []
    for name, content in verified:
        path = output / name
        path.write_bytes(content)
        written.append(path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        written = fetch(args.output)
    except (FileExistsError, KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: materialized and verified {len(written)} immutable Foundation schemas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
