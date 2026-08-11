#!/usr/bin/env python3
"""Create the SLSA provenance v1 predicate shared by exact release subjects."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


COMMIT = re.compile(r"^[0-9a-f]{40}$")
TAG = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")
UTC = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
OCI_DIGEST = re.compile(r"^([A-Za-z0-9.-]+/[A-Za-z0-9._/:-]+)@(sha256:[0-9a-f]{64})$")
IDENTITY_PREFIX = "https://github.com/ADASK-B/Mcp.Connector.Template/.github/workflows/release.yml@refs/tags/"


def timestamp(value: str, label: str) -> datetime:
    if UTC.fullmatch(value) is None:
        raise ValueError(f"{label} must be an RFC3339 UTC second")
    return datetime.fromisoformat(value.removesuffix("Z") + "+00:00").astimezone(timezone.utc)


def build(
    source_commit: str,
    tag: str,
    base_images: list[str],
    workflow_identity: str,
    invocation_id: str,
    started_on: str,
    finished_on: str,
) -> dict:
    if COMMIT.fullmatch(source_commit) is None or TAG.fullmatch(tag) is None:
        raise ValueError("source commit or tag is not immutable")
    parsed_images = [OCI_DIGEST.fullmatch(image) for image in base_images]
    if len(base_images) != 2 or any(match is None for match in parsed_images):
        raise ValueError("both Docker base images must be exact OCI digest references")
    if not workflow_identity.startswith(IDENTITY_PREFIX):
        raise ValueError("workflow identity is outside the approved publisher")
    if not invocation_id.strip():
        raise ValueError("invocation ID must be non-empty")
    started = timestamp(started_on, "started-on")
    finished = timestamp(finished_on, "finished-on")
    if finished < started:
        raise ValueError("finished-on precedes started-on")
    dependencies = [
        {
            "uri": "git+https://github.com/ADASK-B/Mcp.Connector.Template",
            "digest": {"sha1": source_commit},
        }
    ]
    for match in parsed_images:
        assert match is not None
        dependencies.append(
            {
                "uri": "oci://" + match.group(1),
                "digest": {"sha256": match.group(2).removeprefix("sha256:")},
            }
        )
    return {
        "buildDefinition": {
            "buildType": "https://github.com/ADASK-B/Mcp.Connector.Template/release/v1",
            "externalParameters": {"tag": tag},
            "internalParameters": {},
            "resolvedDependencies": dependencies,
        },
        "runDetails": {
            "builder": {"id": workflow_identity},
            "metadata": {
                "invocationId": invocation_id,
                "startedOn": started_on,
                "finishedOn": finished_on,
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--base-image", action="append", required=True, dest="base_images")
    parser.add_argument("--workflow-identity", required=True)
    parser.add_argument("--invocation-id", required=True)
    parser.add_argument("--started-on", required=True)
    parser.add_argument("--finished-on", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        predicate = build(
            args.source_commit, args.tag, args.base_images, args.workflow_identity,
            args.invocation_id, args.started_on, args.finished_on,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    args.output.write_text(json.dumps(predicate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"WROTE: SLSA provenance v1 for {args.source_commit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
