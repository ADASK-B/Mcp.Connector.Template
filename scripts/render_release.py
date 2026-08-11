#!/usr/bin/env python3
"""Render one immutable ApplicationContract and availability-only Zarf package."""

from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RELEASE_INPUT = ROOT / "release/release-input.json"
CONTRACT_TEMPLATE = ROOT / "release/application-contract.template.json"
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


class RenderError(ValueError):
    """The release inputs cannot produce the closed delivery contract."""


def require_digest(value: str, label: str) -> str:
    if SHA256.fullmatch(value) is None:
        raise RenderError(f"{label} must be an exact sha256 digest")
    return value


def render(image_digest: str, chart_digest: str) -> tuple[dict, dict, dict]:
    image_digest = require_digest(image_digest, "image digest")
    chart_digest = require_digest(chart_digest, "chart digest")
    if image_digest == chart_digest:
        raise RenderError("image and chart digests must identify different artifacts")

    release_input = json.loads(RELEASE_INPUT.read_text(encoding="utf-8"))
    contract = deepcopy(json.loads(CONTRACT_TEMPLATE.read_text(encoding="utf-8")))
    if contract["apiVersion"] != release_input["applicationContractVersion"]:
        raise RenderError("contract version differs from release input")
    if contract["metadata"]["name"] != release_input["name"]:
        raise RenderError("contract Application identity differs from release input")
    release = contract["release"]
    if release["version"] != release_input["version"]:
        raise RenderError("contract release version differs from release input")
    if release["delivery"]["repository"] != release_input["publisher"]["packageRepository"]:
        raise RenderError("contract package repository differs from release input")
    if release["evidencePolicyRef"] != release_input["policies"]["evidencePolicyRef"]:
        raise RenderError("contract evidence policy differs from release input")
    if release["publisher"] != {
        "applicationClass": release_input["applicationClass"],
        "artifactClass": release_input["artifactClass"],
        "policyRef": release_input["policies"]["publisherPolicyRef"],
    }:
        raise RenderError("contract publisher binding differs from release input")

    release["artifacts"]["service-image"]["digest"] = image_digest
    release["artifacts"]["chart"]["digest"] = chart_digest
    images = [
        f"{artifact['repository']}@{artifact['digest']}"
        for _, artifact in sorted(release["artifacts"].items())
    ]
    package = {
        "apiVersion": "zarf.dev/v1alpha1",
        "kind": "ZarfPackageConfig",
        "metadata": {
            "name": f"application-{release_input['name']}",
            "version": release_input["version"],
            "description": (
                "Availability-only ADASK application release; activation requires "
                "setup.yaml and GitOps."
            ),
            "architecture": "amd64",
            "authors": "ADASK-B Platform Test App maintainers",
            "source": release_input["publisher"]["repository"],
        },
        "components": [
            {
                "name": "release-artifacts",
                "description": "Immutable OCI artifacts mirrored without application activation.",
                "required": True,
                "images": images,
            }
        ],
        "documentation": {"application-contract": "application-contract.yaml"},
    }
    return contract, package, {"application": contract, "package": package}


def write_release(
    output: Path,
    binding_output: Path,
    image_digest: str,
    chart_digest: str,
) -> None:
    contract, package, binding = render(image_digest, chart_digest)
    resolved_output = output.resolve()
    resolved_binding = binding_output.resolve()
    if resolved_binding == resolved_output or resolved_output in resolved_binding.parents:
        raise RenderError("CUE binding output must remain outside the Zarf package source")
    if binding_output.exists():
        raise FileExistsError(binding_output)
    output.mkdir(parents=True, exist_ok=False)
    for name, document in (
        ("application-contract.yaml", contract),
        ("zarf.yaml", package),
    ):
        (output / name).write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    binding_output.parent.mkdir(parents=True, exist_ok=True)
    binding_output.write_text(
        json.dumps(binding, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-digest", required=True)
    parser.add_argument("--chart-digest", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--binding-output", type=Path, required=True)
    args = parser.parse_args()
    try:
        write_release(
            args.output,
            args.binding_output,
            args.image_digest,
            args.chart_digest,
        )
    except (FileExistsError, KeyError, TypeError, json.JSONDecodeError, RenderError) as exc:
        parser.error(str(exc))
    print(f"WROTE: immutable application contract and Zarf definition to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
