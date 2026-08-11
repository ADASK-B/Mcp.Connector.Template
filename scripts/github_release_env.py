#!/usr/bin/env python3
"""Project the closed release input into GitHub Actions environment entries."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TAG = re.compile(r"^v([0-9]+\.[0-9]+\.[0-9]+)$")


def entries(tag: str) -> dict[str, str]:
    match = TAG.fullmatch(tag)
    if match is None:
        raise ValueError("release tag must be stable SemVer")
    release = json.loads((ROOT / "release/release-input.json").read_text(encoding="utf-8"))
    if release["version"] != match.group(1):
        raise ValueError("release tag differs from release-input version")
    namespace = release["publisher"]["f1Namespace"]
    zarf = release["toolchain"]["zarf"]["linuxAmd64"]
    cue = release["toolchain"]["cue"]["linuxAmd64"]
    projected = {
        "RELEASE_VERSION": release["version"],
        "IMAGE_REPOSITORY": namespace,
        "CHART_REPOSITORY": f"{namespace}/charts/{release['name']}",
        "PACKAGE_REPOSITORY": release["publisher"]["packageRepository"],
        "RUNTIME_BASE_IMAGE": release["materials"]["runtimeBaseImage"],
        "SDK_BASE_IMAGE": release["materials"]["sdkBaseImage"],
        "PYTHON_VERSION": release["toolchain"]["python"]["version"],
        "DOTNET_VERSION": release["toolchain"]["dotnet"]["version"],
        "HELM_VERSION": release["toolchain"]["helm"]["version"],
        "COSIGN_VERSION": release["toolchain"]["cosign"]["version"],
        "TRIVY_VERSION": release["toolchain"]["trivy"]["version"],
        "SYFT_VERSION": release["toolchain"]["syft"]["version"],
        "CUE_SOURCE": cue["source"],
        "CUE_SHA256": cue["sha256"],
        "ZARF_SOURCE": zarf["source"],
        "ZARF_SHA256": zarf["sha256"],
    }
    if any("\n" in value or "\r" in value for value in projected.values()):
        raise ValueError("release input cannot contain multiline environment values")
    return projected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    try:
        projected = entries(args.tag)
    except (KeyError, TypeError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    with args.output.open("a", encoding="utf-8", newline="\n") as handle:
        for key, value in sorted(projected.items()):
            handle.write(f"{key}={value}\n")
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8", newline="\n") as handle:
            for key, value in sorted(projected.items()):
                handle.write(f"{key}={value}\n")
    print("PASS: release input projected into the publisher environment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
