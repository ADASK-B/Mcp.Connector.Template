#!/usr/bin/env python3
"""Create reviewed MIT evidence for one release-owned Test App component.

This predicate intentionally does not claim complete dependency obligation
coverage. The SBOM retains the broader inventory and release-input.json keeps
that production blocker explicit.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


DIGEST_REFERENCE = re.compile(r"^[^@\s]+@(sha256:[0-9a-f]{64})$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
UTC = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
SCHEMA = "platform.adask-b.io/application-license-evidence/v1alpha1"
COMPONENTS = {"platform-test-app-image", "platform-test-app-chart"}


def build(
    artifact: str,
    component: str,
    version: str,
    source_commit: str,
    reviewed_at: str,
    license_text: str,
) -> dict:
    match = DIGEST_REFERENCE.fullmatch(artifact)
    if match is None:
        raise ValueError("artifact must be an exact repository@sha256 digest")
    if component not in COMPONENTS:
        raise ValueError("component is not a release-owned Platform Test App artifact")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("version must be stable SemVer")
    if COMMIT.fullmatch(source_commit) is None:
        raise ValueError("source commit must be an exact SHA-1")
    if UTC.fullmatch(reviewed_at) is None:
        raise ValueError("reviewed-at must be an RFC3339 UTC second")
    if not license_text or license_text.startswith("/") or ".." in license_text.split("/"):
        raise ValueError("license-text must be a safe artifact-relative reference")
    return {
        "schemaVersion": SCHEMA,
        "artifactDigest": match.group(1),
        "components": [
            {
                "name": component,
                "version": version,
                "sourceOrigin": (
                    "https://github.com/ADASK-B/Mcp.Connector.Template/tree/" + source_commit
                ),
                "licenseExpression": "MIT",
                "modificationStatus": "unmodified",
                "licenseTexts": [license_text],
                "redistributionObligations": ["retain-license-text"],
                "notices": {"required": False, "artifacts": []},
                "sourceObligation": {"status": "not-required", "evidenceRefs": []},
            }
        ],
        "distributionDecision": "approved",
        "review": {
            "owner": "ADASK-B Platform Test App maintainers",
            "reviewedAt": reviewed_at,
            "evidenceRef": "review/platform-test-app-release-owned-mit-v1",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--component", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--reviewed-at", required=True)
    parser.add_argument("--license-text", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        predicate = build(
            args.artifact, args.component, args.version, args.source_commit,
            args.reviewed_at, args.license_text,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    args.output.write_text(json.dumps(predicate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"WROTE: reviewed release-owned MIT evidence for {args.artifact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
