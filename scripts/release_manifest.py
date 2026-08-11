#!/usr/bin/env python3
"""Create immutable publisher evidence after every declared release gate ran."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


def require_digest(value: str, label: str) -> str:
    if DIGEST.fullmatch(value) is None:
        raise ValueError(f"{label} must be an exact sha256 digest")
    return value


def build(
    image_digest: str,
    chart_digest: str,
    package_digest: str,
    source_commit: str,
    contract_path: Path,
    run_id: str,
    run_attempt: str,
) -> dict:
    for value, label in (
        (image_digest, "image digest"),
        (chart_digest, "chart digest"),
        (package_digest, "package digest"),
    ):
        require_digest(value, label)
    if len({image_digest, chart_digest, package_digest}) != 3:
        raise ValueError("image, chart and package identities must be distinct")
    if COMMIT.fullmatch(source_commit) is None:
        raise ValueError("source commit must be an exact SHA-1")
    if not run_id.isdigit() or not run_attempt.isdigit():
        raise ValueError("GitHub run identity is malformed")
    contract_bytes = contract_path.read_bytes()
    contract = json.loads(contract_bytes)
    release = json.loads((ROOT / "release/release-input.json").read_text(encoding="utf-8"))
    if contract["metadata"]["name"] != release["name"] or contract["release"]["version"] != release["version"]:
        raise ValueError("rendered contract identity differs from release input")
    contract_release = contract["release"]
    if contract_release["artifacts"]["service-image"]["digest"] != image_digest:
        raise ValueError("rendered contract image digest differs from published image")
    if contract_release["artifacts"]["chart"]["digest"] != chart_digest:
        raise ValueError("rendered contract chart digest differs from published chart")
    if contract_release["delivery"]["repository"] != release["publisher"]["packageRepository"]:
        raise ValueError("rendered contract package repository differs from release input")
    namespace = release["publisher"]["f1Namespace"]
    admitted_toolchain = {
        name: release["toolchain"][name]
        for name in ("cosign", "helm", "python", "syft", "trivy", "zarf")
    }
    identity = (
        "https://github.com/ADASK-B/Mcp.Connector.Template/"
        f".github/workflows/release.yml@refs/tags/v{release['version']}"
    )
    return {
        "schemaVersion": "platform.adask-b.io/publisher-release/v1alpha2",
        "applicationClass": release["applicationClass"],
        "artifactClass": release["artifactClass"],
        "name": release["name"],
        "version": release["version"],
        "source": {"repository": "ADASK-B/Mcp.Connector.Template", "commit": source_commit},
        "package": {
            "reference": release["publisher"]["packageRepository"],
            "digest": package_digest,
            "contractDigest": "sha256:" + hashlib.sha256(contract_bytes).hexdigest(),
        },
        "image": {
            "reference": namespace,
            "digest": image_digest,
            "valuesPath": release["imageValuesPath"],
        },
        "chart": {"reference": f"{namespace}/charts/{release['name']}", "digest": chart_digest},
        "signer": {"mode": "keyless", "identity": identity, "issuer": release["publisher"]["issuer"]},
        "policies": release["policies"],
        "toolchain": admitted_toolchain,
        "evidence": sorted(release["requiredEvidence"]),
        "gateExecution": {
            "provider": "github-actions",
            "runId": run_id,
            "runAttempt": run_attempt,
            "sourceCommit": source_commit,
            "gates": [{"id": gate_id, "status": "PASS"} for gate_id in release["requiredGates"]],
        },
        "license": {
            "expression": release["license"]["expression"],
            "coverage": "release-owned-components-only",
            "completeDistributionCompliance": False,
        },
        "productionEligible": False,
        "blockers": release["blockers"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-digest", required=True)
    parser.add_argument("--chart-digest", required=True)
    parser.add_argument("--package-digest", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--run-attempt", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = build(
            args.image_digest, args.chart_digest, args.package_digest,
            args.source_commit, args.contract, args.run_id, args.run_attempt,
        )
    except (OSError, KeyError, TypeError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"WROTE: non-production publisher evidence to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
