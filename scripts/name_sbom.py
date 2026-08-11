#!/usr/bin/env python3
"""Bind an SPDX document to the exact published artifact it describes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SUBJECT = re.compile(r"^[^@\s]+@sha256:[0-9a-f]{64}$")
VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def bind(document: dict, subject: str, version: str, license_expression: str) -> dict:
    packages = document.get("packages")
    if not isinstance(packages, list) or not packages:
        raise ValueError("SBOM lists no packages, so it describes nothing")
    if SUBJECT.fullmatch(subject) is None or VERSION.fullmatch(version) is None:
        raise ValueError("SBOM subject or version is not immutable")
    if license_expression not in {"MIT", "NOASSERTION"}:
        raise ValueError("released-artifact license must be MIT or NOASSERTION")
    released_id = "SPDXRef-ReleasedArtifact"
    if any(package.get("SPDXID") == released_id for package in packages if isinstance(package, dict)):
        raise ValueError(f"{released_id} is already present")
    packages.append(
        {
            "SPDXID": released_id,
            "name": subject,
            "versionInfo": version,
            "downloadLocation": "NOASSERTION",
            "licenseDeclared": license_expression,
            "licenseConcluded": license_expression,
            "copyrightText": "Copyright (c) 2026 ADASK-B",
        }
    )
    document["name"] = subject
    document["documentDescribes"] = [released_id]
    return document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sbom", type=Path, required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--license", required=True, dest="license_expression")
    args = parser.parse_args()
    try:
        document = json.loads(args.sbom.read_text(encoding="utf-8"))
        bind(document, args.subject, args.version, args.license_expression)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    args.sbom.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"WROTE: {args.sbom} now names {args.subject}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
