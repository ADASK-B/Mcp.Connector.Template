#!/usr/bin/env python3
"""Convert a non-empty clean Trivy report into typed release evidence."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SCHEMA = "platform.adask-b.io/application-vulnerability-evidence/v1alpha1"
PUBLISHED_REFERENCE = re.compile(r"^[^@\s]+@sha256:[0-9a-f]{64}$")
UTC = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")


def examined_targets(report: dict) -> list[str]:
    return sorted({str(result.get("Target", "")) for result in report.get("Results") or [] if result.get("Target")})


def findings(report: dict) -> list[dict[str, str]]:
    collected: list[dict[str, str]] = []
    for result in report.get("Results") or []:
        target = result.get("Target", "")
        for item in result.get("Vulnerabilities") or []:
            collected.append({"id": item["VulnerabilityID"], "severity": item.get("Severity", "UNKNOWN"), "target": target})
        for item in result.get("Misconfigurations") or []:
            collected.append({"id": item["ID"], "severity": item.get("Severity", "UNKNOWN"), "target": target})
    return sorted(collected, key=lambda item: (item["target"], item["id"]))


def rfc3339_second(value: object) -> str | None:
    rendered = str(value or "")
    if "." in rendered:
        rendered = rendered.split(".", 1)[0] + "Z"
    return rendered if UTC.fullmatch(rendered) else None


def build(report: dict, artifact_name: str, gated: set[str], database_updated_at: str) -> dict:
    for field in ("ArtifactName", "ArtifactType"):
        if not report.get(field):
            raise ValueError(f"Trivy report names no {field}")
    if PUBLISHED_REFERENCE.fullmatch(artifact_name) is None:
        raise ValueError("artifact name must be an exact repository@sha256 digest")
    if UTC.fullmatch(database_updated_at) is None:
        raise ValueError("database-updated-at must be an RFC3339 UTC second")
    scanned = str(report["ArtifactName"])
    if PUBLISHED_REFERENCE.fullmatch(scanned) and scanned != artifact_name:
        raise ValueError(f"report scanned {scanned}, not {artifact_name}")
    if not examined_targets(report):
        raise ValueError("scan examined no targets")
    unresolved = [item for item in findings(report) if item["severity"] in gated]
    if unresolved:
        raise ValueError(f"{len(unresolved)} unresolved gated finding(s) remain")
    scanner_version = (report.get("Trivy") or {}).get("Version")
    scanned_at = rfc3339_second(report.get("CreatedAt"))
    if not scanner_version or scanned_at is None:
        raise ValueError("Trivy report has no exact scanner version/scanned time")
    return {
        "schemaVersion": SCHEMA,
        "artifactDigest": artifact_name.rsplit("@", 1)[1],
        "scanner": {"name": "trivy", "version": scanner_version, "databaseUpdatedAt": database_updated_at},
        "scannedAt": scanned_at,
        "findings": [],
        "releaseDecision": "pass",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--artifact-name", required=True)
    parser.add_argument("--severities", required=True)
    parser.add_argument("--database-updated-at", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        predicate = build(
            report, args.artifact_name,
            {item.strip() for item in args.severities.split(",") if item.strip()},
            args.database_updated_at,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    args.output.write_text(json.dumps(predicate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"WROTE: typed clean scan evidence to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
