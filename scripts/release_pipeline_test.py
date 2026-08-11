#!/usr/bin/env python3
"""Deterministic positive and fail-closed tests for the App release helpers."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import github_release_env  # noqa: E402
import license_predicate  # noqa: E402
import name_sbom  # noqa: E402
import provenance_predicate  # noqa: E402
import registry_tag_absent  # noqa: E402
import release_manifest  # noqa: E402
import render_artifact_values  # noqa: E402
import render_release  # noqa: E402
import scan_predicate  # noqa: E402
import trivy_database_time  # noqa: E402
import validate_repo  # noqa: E402
import verify_oci_layout  # noqa: E402


DIGEST_A = "sha256:" + ("a" * 64)
DIGEST_B = "sha256:" + ("b" * 64)
DIGEST_C = "sha256:" + ("c" * 64)
COMMIT = "d" * 40
SUBJECT = f"ghcr.io/adask-b/platform-test-app@{DIGEST_A}"


def descriptor(content: bytes, media_type: str, **extra: object) -> dict:
    return {
        "mediaType": media_type,
        "digest": "sha256:" + hashlib.sha256(content).hexdigest(),
        "size": len(content),
        **extra,
    }


class Response:
    def __init__(self, status: int, headers: dict[str, str] | None = None, body: bytes = b""):
        self.status = status
        self.headers = headers or {}
        self._body = body

    def read(self) -> bytes:
        return self._body


class ReleaseContractTests(unittest.TestCase):
    def test_repository_contract_is_closed(self) -> None:
        self.assertEqual([], validate_repo.collect_errors())

        release_path = ROOT / "release/release-input.json"
        original = release_path.read_text(encoding="utf-8")
        try:
            candidate = json.loads(original)
            candidate["toolchain"]["unexpected"] = {"version": "latest"}
            release_path.write_text(json.dumps(candidate), encoding="utf-8")
            self.assertIn(
                "release toolchain inventory must be exact",
                validate_repo.collect_errors(),
            )
        finally:
            release_path.write_text(original, encoding="utf-8", newline="\n")

    def test_release_environment_accepts_only_exact_release_tag(self) -> None:
        entries = github_release_env.entries("v1.1.0")
        self.assertEqual("1.1.0", entries["RELEASE_VERSION"])
        self.assertEqual("10.0.400", entries["DOTNET_VERSION"])
        self.assertEqual("ghcr.io/adask-b/platform-test-app", entries["IMAGE_REPOSITORY"])
        with self.assertRaises(ValueError):
            github_release_env.entries("v1.1.1")
        with self.assertRaises(ValueError):
            github_release_env.entries("latest")

    def test_rendered_contract_and_package_bind_exact_distinct_artifacts(self) -> None:
        contract, package, binding = render_release.render(DIGEST_A, DIGEST_B)
        release = contract["release"]
        self.assertEqual(DIGEST_A, release["artifacts"]["service-image"]["digest"])
        self.assertEqual(DIGEST_B, release["artifacts"]["chart"]["digest"])
        self.assertEqual("application-platform-test-app", package["metadata"]["name"])
        self.assertNotIn("actions", json.dumps(package).lower())
        self.assertEqual(contract, binding["application"])
        with self.assertRaises(render_release.RenderError):
            render_release.render(DIGEST_A, DIGEST_A)
        with self.assertRaises(render_release.RenderError):
            render_release.render("latest", DIGEST_B)

    def test_zarf_source_contains_only_package_definition_and_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "zarf-source"
            binding = root / "application-package-binding.json"
            render_release.write_release(source, binding, DIGEST_A, DIGEST_B)
            self.assertEqual(
                {"application-contract.yaml", "zarf.yaml"},
                {path.name for path in source.iterdir()},
            )
            self.assertTrue(binding.is_file())
            with self.assertRaises(render_release.RenderError):
                render_release.write_release(
                    root / "another-source",
                    root / "another-source" / "binding.json",
                    DIGEST_A,
                    DIGEST_B,
                )

    def test_manifest_binds_all_gates_after_exact_contract(self) -> None:
        contract, _, _ = render_release.render(DIGEST_A, DIGEST_B)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contract.json"
            path.write_text(json.dumps(contract), encoding="utf-8")
            manifest = release_manifest.build(
                DIGEST_A, DIGEST_B, DIGEST_C, COMMIT, path, "1234", "2"
            )
        self.assertFalse(manifest["productionEligible"])
        self.assertTrue(manifest["blockers"])
        self.assertEqual(
            {"cosign", "helm", "python", "syft", "trivy", "zarf"},
            set(manifest["toolchain"]),
        )
        self.assertTrue(manifest["gateExecution"]["gates"])
        self.assertEqual(
            {"PASS"}, {gate["status"] for gate in manifest["gateExecution"]["gates"]}
        )
        with self.assertRaises(ValueError):
            release_manifest.build(DIGEST_A, DIGEST_A, DIGEST_C, COMMIT, path, "1", "1")


class EvidenceTests(unittest.TestCase):
    def test_license_evidence_is_narrow_and_release_owned(self) -> None:
        evidence = license_predicate.build(
            SUBJECT,
            "platform-test-app-image",
            "1.1.0",
            COMMIT,
            "2026-08-12T00:00:00Z",
            "LICENSE",
        )
        self.assertEqual("approved", evidence["distributionDecision"])
        self.assertEqual("MIT", evidence["components"][0]["licenseExpression"])
        with self.assertRaises(ValueError):
            license_predicate.build(
                SUBJECT, "dependency", "1.1.0", COMMIT,
                "2026-08-12T00:00:00Z", "LICENSE"
            )

    def test_provenance_binds_source_two_base_images_and_keyless_identity(self) -> None:
        identity = (
            "https://github.com/ADASK-B/Mcp.Connector.Template/"
            ".github/workflows/release.yml@refs/tags/v1.1.0"
        )
        evidence = provenance_predicate.build(
            COMMIT,
            "v1.1.0",
            [f"mcr.microsoft.com/dotnet/aspnet@{DIGEST_A}", f"mcr.microsoft.com/dotnet/sdk@{DIGEST_B}"],
            identity,
            "https://github.com/ADASK-B/Mcp.Connector.Template/actions/runs/1/attempts/1",
            "2026-08-12T00:00:00Z",
            "2026-08-12T00:01:00Z",
        )
        self.assertEqual(3, len(evidence["buildDefinition"]["resolvedDependencies"]))
        with self.assertRaises(ValueError):
            provenance_predicate.build(
                COMMIT, "v1.1.0", [f"example.invalid/base@{DIGEST_A}"], identity,
                "run", "2026-08-12T00:00:00Z", "2026-08-12T00:01:00Z"
            )
        with self.assertRaises(ValueError):
            provenance_predicate.build(
                COMMIT,
                "v1.1.0",
                [f"example.invalid/a@{DIGEST_A}", f"example.invalid/b@{DIGEST_B}"],
                "https://github.com/other/repository/release.yml@refs/tags/v1.1.0",
                "run",
                "2026-08-12T00:00:00Z",
                "2026-08-12T00:01:00Z",
            )

    def test_scan_evidence_rejects_empty_or_gated_reports(self) -> None:
        report = {
            "ArtifactName": "oci-dir:release-image",
            "ArtifactType": "container_image",
            "CreatedAt": "2026-08-12T00:01:02Z",
            "Trivy": {"Version": "0.69.3"},
            "Results": [{"Target": "release-image", "Vulnerabilities": []}],
        }
        evidence = scan_predicate.build(
            report, SUBJECT, {"HIGH", "CRITICAL"}, "2026-08-12T00:00:00Z"
        )
        self.assertEqual("pass", evidence["releaseDecision"])
        with self.assertRaises(ValueError):
            scan_predicate.build(
                {**report, "Results": []}, SUBJECT, {"HIGH"}, "2026-08-12T00:00:00Z"
            )
        report["Results"][0]["Vulnerabilities"] = [
            {"VulnerabilityID": "CVE-TEST", "Severity": "HIGH"}
        ]
        with self.assertRaises(ValueError):
            scan_predicate.build(report, SUBJECT, {"HIGH"}, "2026-08-12T00:00:00Z")

    def test_sbom_and_build_local_values_require_immutable_subjects(self) -> None:
        sbom = name_sbom.bind({"packages": [{"SPDXID": "SPDXRef-Package"}]}, SUBJECT, "1.1.0", "MIT")
        self.assertEqual(["SPDXRef-ReleasedArtifact"], sbom["documentDescribes"])
        self.assertEqual(
            {"image": {"repository": "ghcr.io/adask-b/platform-test-app", "digest": DIGEST_A}},
            render_artifact_values.render("ghcr.io/adask-b/platform-test-app", DIGEST_A),
        )
        with self.assertRaises(ValueError):
            name_sbom.bind({"packages": []}, SUBJECT, "1.1.0", "MIT")
        with self.assertRaises(ValueError):
            render_artifact_values.render("ghcr.io/adask-b/platform-test-app:latest", DIGEST_A)

    def test_trivy_database_identity_requires_utc(self) -> None:
        self.assertEqual(
            "2026-08-12T00:00:00Z",
            trivy_database_time.read_updated_at(
                {"VulnerabilityDB": {"UpdatedAt": "2026-08-12T00:00:00.123Z"}}
            ),
        )
        with self.assertRaises(ValueError):
            trivy_database_time.read_updated_at(
                {"VulnerabilityDB": {"UpdatedAt": "2026-08-12T01:00:00+01:00"}}
            )


class RegistryTests(unittest.TestCase):
    def test_authenticated_404_is_required_for_tag_absence(self) -> None:
        calls: list[object] = []

        def open_request(request: object, timeout: int) -> Response:
            calls.append(request)
            authorization = getattr(request, "headers", {}).get("Authorization", "")
            if len(calls) == 1:
                return Response(
                    401,
                    {"WWW-Authenticate": (
                        'Bearer realm="https://ghcr.io/token",service="ghcr.io",'
                        'scope="repository:adask-b/platform-test-app:pull"'
                    )},
                )
            if authorization.startswith("Basic "):
                return Response(200, body=b'{"token":"registry-bearer"}')
            if authorization == "Bearer registry-bearer":
                return Response(404)
            return Response(500)

        self.assertTrue(
            registry_tag_absent.is_absent(
                "ghcr.io/adask-b/platform-test-app", "1.1.0", "publisher", "token",
                open_request=open_request,
            )
        )
        self.assertEqual(3, len(calls))

    def test_anonymous_404_or_missing_credentials_do_not_prove_absence(self) -> None:
        with self.assertRaises(registry_tag_absent.RegistryProbeError):
            registry_tag_absent.is_absent(
                "ghcr.io/adask-b/platform-test-app", "1.1.0", "publisher", "token",
                open_request=lambda request, timeout: Response(404),
            )
        with self.assertRaises(registry_tag_absent.RegistryProbeError):
            registry_tag_absent.is_absent(
                "ghcr.io/adask-b/platform-test-app", "1.1.0", "", "",
                open_request=lambda request, timeout: Response(404),
            )


class OciLayoutTests(unittest.TestCase):
    def create_layout(self, root: Path) -> tuple[dict, str]:
        blobs = root / "blobs" / "sha256"
        blobs.mkdir(parents=True)
        (root / "oci-layout").write_text('{"imageLayoutVersion":"1.0.0"}', encoding="utf-8")

        config = json.dumps(
            {
                "architecture": "amd64",
                "os": "linux",
                "config": {
                    "Labels": {
                        "org.opencontainers.image.revision": COMMIT,
                        "org.opencontainers.image.version": "1.1.0",
                        "org.opencontainers.image.licenses": "NOASSERTION",
                    }
                },
            },
            separators=(",", ":"),
        ).encode()
        layer = b"release-layer"
        config_descriptor = descriptor(config, verify_oci_layout.OCI_CONFIG)
        layer_descriptor = descriptor(layer, verify_oci_layout.OCI_LAYER_PREFIX + "+gzip")
        manifest = json.dumps(
            {
                "schemaVersion": 2,
                "mediaType": verify_oci_layout.OCI_MANIFEST,
                "config": config_descriptor,
                "layers": [layer_descriptor],
            },
            separators=(",", ":"),
        ).encode()
        manifest_descriptor = descriptor(
            manifest,
            verify_oci_layout.OCI_MANIFEST,
            platform={"architecture": "amd64", "os": "linux"},
        )
        for content, item in ((config, config_descriptor), (layer, layer_descriptor), (manifest, manifest_descriptor)):
            (blobs / item["digest"].removeprefix("sha256:")).write_bytes(content)
        (root / "index.json").write_text(
            json.dumps(
                {
                    "schemaVersion": 2,
                    "mediaType": verify_oci_layout.OCI_INDEX,
                    "manifests": [manifest_descriptor],
                }
            ),
            encoding="utf-8",
        )
        metadata = {
            "containerimage.digest": manifest_descriptor["digest"],
            "containerimage.config.digest": config_descriptor["digest"],
            "containerimage.descriptor": manifest_descriptor,
        }
        return metadata, manifest_descriptor["digest"]

    def test_exact_single_linux_amd64_layout_passes_and_orphan_blob_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            metadata, manifest_digest = self.create_layout(root)
            verify_oci_layout.verify(
                root,
                metadata,
                manifest_digest=manifest_digest,
                revision=COMMIT,
                version="1.1.0",
            )
            orphan = root / "blobs" / "sha256" / ("f" * 64)
            orphan.write_bytes(b"orphan")
            with self.assertRaises(verify_oci_layout.LayoutError):
                verify_oci_layout.verify(
                    root,
                    metadata,
                    manifest_digest=manifest_digest,
                    revision=COMMIT,
                    version="1.1.0",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
