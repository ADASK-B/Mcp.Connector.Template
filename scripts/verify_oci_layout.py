#!/usr/bin/env python3
"""Verify the exact single-platform Buildx OCI layout before publication."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections.abc import Mapping
from pathlib import Path


SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
REVISION = re.compile(r"^[0-9a-f]{40}$")
VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
OCI_INDEX = "application/vnd.oci.image.index.v1+json"
OCI_MANIFEST = "application/vnd.oci.image.manifest.v1+json"
OCI_CONFIG = "application/vnd.oci.image.config.v1+json"
OCI_LAYER_PREFIX = "application/vnd.oci.image.layer.v1.tar"


class LayoutError(ValueError):
    """The OCI layout is not the closed Buildx release output."""


def exact_digest(value: object, label: str) -> str:
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        raise LayoutError(f"{label} must be an exact sha256 digest")
    return value


def document(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LayoutError(f"{label} is unavailable or malformed") from exc
    if not isinstance(value, dict):
        raise LayoutError(f"{label} must be an object")
    return value


def blob(layout: Path, descriptor: object, label: str) -> bytes:
    if not isinstance(descriptor, Mapping):
        raise LayoutError(f"{label} descriptor must be an object")
    identity = exact_digest(descriptor.get("digest"), f"{label} digest")
    size = descriptor.get("size")
    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
        raise LayoutError(f"{label} size must be a positive integer")
    path = layout / "blobs" / "sha256" / identity.removeprefix("sha256:")
    if path.is_symlink() or not path.is_file():
        raise LayoutError(f"{label} blob is missing or unsafe")
    content = path.read_bytes()
    if len(content) != size or "sha256:" + hashlib.sha256(content).hexdigest() != identity:
        raise LayoutError(f"{label} blob differs from its descriptor")
    return content


def json_blob(layout: Path, descriptor: object, label: str) -> dict:
    try:
        value = json.loads(blob(layout, descriptor, label))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LayoutError(f"{label} blob is not JSON") from exc
    if not isinstance(value, dict):
        raise LayoutError(f"{label} blob must be an object")
    return value


def verify(
    layout: Path,
    build_metadata: object,
    *,
    manifest_digest: str,
    revision: str,
    version: str,
) -> None:
    manifest_digest = exact_digest(manifest_digest, "Buildx manifest digest")
    if REVISION.fullmatch(revision) is None or VERSION.fullmatch(version) is None:
        raise LayoutError("source revision or version is not immutable")
    if not isinstance(build_metadata, Mapping):
        raise LayoutError("Buildx metadata must be an object")
    if exact_digest(build_metadata.get("containerimage.digest"), "Buildx metadata digest") != manifest_digest:
        raise LayoutError("Buildx digest output differs from its metadata")
    metadata_descriptor = build_metadata.get("containerimage.descriptor")
    if not isinstance(metadata_descriptor, Mapping):
        raise LayoutError("Buildx metadata contains no manifest descriptor")
    if document(layout / "oci-layout", "OCI layout marker") != {"imageLayoutVersion": "1.0.0"}:
        raise LayoutError("OCI layout marker is not v1.0.0")
    index = document(layout / "index.json", "OCI index")
    manifests = index.get("manifests")
    if index.get("schemaVersion") != 2 or index.get("mediaType") != OCI_INDEX or not isinstance(manifests, list) or len(manifests) != 1:
        raise LayoutError("OCI index must contain exactly one supported manifest")
    descriptor = manifests[0]
    if not isinstance(descriptor, Mapping) or descriptor.get("mediaType") != OCI_MANIFEST:
        raise LayoutError("OCI index does not select an OCI image manifest")
    if descriptor.get("digest") != manifest_digest or descriptor.get("platform") != {"architecture": "amd64", "os": "linux"}:
        raise LayoutError("OCI index digest or platform differs from the release")
    for field in ("digest", "mediaType", "size", "platform"):
        if metadata_descriptor.get(field) != descriptor.get(field):
            raise LayoutError(f"OCI index {field} differs from Buildx metadata")
    manifest = json_blob(layout, descriptor, "image manifest")
    config_descriptor = manifest.get("config")
    if manifest.get("schemaVersion") != 2 or manifest.get("mediaType") != OCI_MANIFEST:
        raise LayoutError("image manifest schema or media type is unsupported")
    if not isinstance(config_descriptor, Mapping) or config_descriptor.get("mediaType") != OCI_CONFIG:
        raise LayoutError("image config descriptor is unsupported")
    if config_descriptor.get("digest") != build_metadata.get("containerimage.config.digest"):
        raise LayoutError("image config differs from Buildx metadata")
    config = json_blob(layout, config_descriptor, "image config")
    if config.get("architecture") != "amd64" or config.get("os") != "linux":
        raise LayoutError("image config platform must be linux/amd64")
    runtime = config.get("config")
    labels = runtime.get("Labels") if isinstance(runtime, Mapping) else None
    if not isinstance(labels, Mapping):
        raise LayoutError("image config has no release labels")
    if labels.get("org.opencontainers.image.revision") != revision or labels.get("org.opencontainers.image.version") != version:
        raise LayoutError("image release labels differ from source identity")
    if labels.get("org.opencontainers.image.licenses") != "NOASSERTION":
        raise LayoutError("aggregate image license must remain NOASSERTION")
    layers = manifest.get("layers")
    if not isinstance(layers, list) or not layers:
        raise LayoutError("image manifest must contain layers")
    referenced = {manifest_digest, exact_digest(config_descriptor.get("digest"), "config digest")}
    for position, layer in enumerate(layers):
        if not isinstance(layer, Mapping) or not str(layer.get("mediaType", "")).startswith(OCI_LAYER_PREFIX):
            raise LayoutError(f"image layer {position} media type is unsupported")
        blob(layout, layer, f"image layer {position}")
        referenced.add(exact_digest(layer.get("digest"), f"image layer {position} digest"))
    blob_root = layout / "blobs" / "sha256"
    entries = list(blob_root.iterdir())
    if any(path.is_symlink() or not path.is_file() or re.fullmatch(r"[0-9a-f]{64}", path.name) is None for path in entries):
        raise LayoutError("OCI blob directory contains an unsafe entry")
    if {"sha256:" + path.name for path in entries} != referenced:
        raise LayoutError("OCI layout contains missing or unreferenced blobs")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layout", type=Path, required=True)
    parser.add_argument("--manifest-digest", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    try:
        metadata = json.loads(os.environ.get("LOCAL_IMAGE_METADATA", ""))
        verify(args.layout, metadata, manifest_digest=args.manifest_digest, revision=args.revision, version=args.version)
    except (LayoutError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("PASS: OCI layout is the exact Buildx release output")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
