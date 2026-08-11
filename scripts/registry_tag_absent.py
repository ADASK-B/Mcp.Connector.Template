#!/usr/bin/env python3
"""Require an authenticated Registry-v2 404 before publishing an immutable tag."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
from collections.abc import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


REFERENCE = re.compile(r"^ghcr\.io/([a-z0-9._-]+(?:/[a-z0-9._-]+)+)$")
TAG = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
ACCEPT = ", ".join(
    (
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
    )
)


class RegistryProbeError(RuntimeError):
    """The Registry did not authoritatively establish tag absence."""


OpenRequest = Callable[..., object]


def request(
    open_request: OpenRequest,
    url: str,
    *,
    method: str = "GET",
    headers: Mapping[str, str] | None = None,
) -> tuple[int, Mapping[str, str], bytes]:
    try:
        response = open_request(Request(url, method=method, headers=dict(headers or {})), timeout=30)
        return response.status, response.headers, response.read()
    except HTTPError as exc:
        return exc.code, exc.headers, exc.read()
    except (OSError, URLError) as exc:
        raise RegistryProbeError(f"Registry request failed: {exc}") from exc


def bearer_parameters(header: str) -> dict[str, str]:
    if not header.startswith("Bearer "):
        raise RegistryProbeError("Registry did not return a Bearer challenge")
    parameters = dict(re.findall(r'([a-z]+)="([^"]+)"', header[7:]))
    if set(parameters) < {"realm", "service", "scope"}:
        raise RegistryProbeError("Registry Bearer challenge is incomplete")
    realm = urlparse(parameters["realm"])
    if realm.scheme != "https" or realm.hostname != "ghcr.io":
        raise RegistryProbeError("Registry Bearer realm is outside ghcr.io HTTPS")
    return parameters


def is_absent(
    repository: str,
    tag: str,
    username: str,
    token: str,
    *,
    open_request: OpenRequest = urlopen,
) -> bool:
    match = REFERENCE.fullmatch(repository)
    if match is None:
        raise RegistryProbeError("repository must be an exact ghcr.io path")
    if TAG.fullmatch(tag) is None:
        raise RegistryProbeError("tag must be stable SemVer")
    if not username or not token:
        raise RegistryProbeError("Registry credentials are unavailable")
    manifest_url = f"https://ghcr.io/v2/{match.group(1)}/manifests/{tag}"
    status, headers, _ = request(open_request, manifest_url, method="HEAD", headers={"Accept": ACCEPT})
    if status == 200:
        return False
    if status != 401:
        raise RegistryProbeError(f"anonymous Registry probe returned unexpected HTTP {status}")
    challenge = bearer_parameters(str(headers.get("WWW-Authenticate", "")))
    credentials = base64.b64encode(f"{username}:{token}".encode()).decode("ascii")
    token_url = challenge["realm"] + "?" + urlencode(
        {"service": challenge["service"], "scope": challenge["scope"]}
    )
    status, _, body = request(
        open_request, token_url, headers={"Authorization": f"Basic {credentials}"}
    )
    if status != 200:
        raise RegistryProbeError(f"Registry token exchange returned HTTP {status}")
    try:
        token_document = json.loads(body)
        bearer = token_document.get("token") or token_document.get("access_token")
    except (AttributeError, json.JSONDecodeError) as exc:
        raise RegistryProbeError("Registry token response is malformed") from exc
    if not isinstance(bearer, str) or not bearer:
        raise RegistryProbeError("Registry token response contains no token")
    status, _, _ = request(
        open_request, manifest_url, method="HEAD",
        headers={"Accept": ACCEPT, "Authorization": f"Bearer {bearer}"},
    )
    if status == 404:
        return True
    if status == 200:
        return False
    raise RegistryProbeError(f"authenticated Registry probe returned unexpected HTTP {status}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--token-env", default="REGISTRY_TOKEN")
    args = parser.parse_args()
    try:
        absent = is_absent(args.repository, args.tag, args.username, os.environ.get(args.token_env, ""))
    except RegistryProbeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if not absent:
        print(f"ERROR: immutable Registry tag already exists: {args.repository}:{args.tag}", file=sys.stderr)
        return 1
    print(f"PASS: immutable Registry tag is absent: {args.repository}:{args.tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
