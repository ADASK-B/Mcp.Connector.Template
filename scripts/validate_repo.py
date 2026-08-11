#!/usr/bin/env python3
"""Fail-closed source validation for the independent Platform Test App release."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SHA256 = re.compile(r"^[0-9a-f]{64}$")
OCI_DIGEST = re.compile(r"^[^@\s]+@sha256:[0-9a-f]{64}$")
ACTION_PIN = re.compile(r"\buses:\s*[^\s@]+@[0-9a-f]{40}(?:\s*#.*)?$")


def image_values_path_selects_a_pinned_image(path: str) -> bool:
    lines = (ROOT / "charts/mcp-connector/values.yaml").read_text(encoding="utf-8").splitlines()
    depth = 0
    for key in path.split("."):
        for index, line in enumerate(lines):
            if line == f"{'  ' * depth}{key}:":
                lines, depth = lines[index + 1 :], depth + 1
                break
        else:
            return False
    indent = "  " * depth
    leaf: list[str] = []
    for line in lines:
        if line.strip() and not line.startswith(indent):
            break
        leaf.append(line.strip().split(":")[0])
    return "repository" in leaf and "digest" in leaf


def collect_errors() -> list[str]:
    errors: list[str] = []
    release = json.loads((ROOT / "release/release-input.json").read_text(encoding="utf-8"))
    expected_release_keys = {
        "schemaVersion", "applicationContractVersion", "artifactClass",
        "applicationClass", "name", "version", "imageValuesPath", "publisher",
        "policies", "requiredEvidence", "requiredGates", "materials",
        "foundationContract", "toolchain", "license", "productionEligible", "blockers",
    }
    if set(release) != expected_release_keys:
        errors.append("release input must use the closed v1alpha2 shape")
    if release.get("schemaVersion") != "platform.adask-b.io/app-release-input/v1alpha2":
        errors.append("release input must use v1alpha2")
    if release.get("applicationContractVersion") != "platform.adask-b.io/application-contract/v1alpha9":
        errors.append("release input must select ApplicationContract v1alpha9")
    if release.get("applicationClass") != "platform-test" or release.get("artifactClass") != "vendor-app":
        errors.append("release class must be platform-test/vendor-app")
    if release.get("name") != "platform-test-app" or release.get("version") != "1.1.1":
        errors.append("release stable identity/version differs from the reviewed 1.1.1 boundary")
    image_values_path = release.get("imageValuesPath")
    if not isinstance(image_values_path, str) or not image_values_path_selects_a_pinned_image(image_values_path):
        errors.append("imageValuesPath must select the chart repository/digest pair")
    if release.get("productionEligible") is not False:
        errors.append("Test App release must remain non-production")
    if set(release.get("requiredEvidence") or []) != {
        "signature", "sbom", "provenance", "vulnerability-scan", "license-attestation",
    }:
        errors.append("release input must require exactly five Application evidence types")
    if release.get("requiredGates") != [
        "source-contract-and-unit-tests", "immutable-image-scan", "rendered-chart-scan",
        "artifact-signature-and-evidence-verification", "zarf-package-create-sign-publish-verify",
    ]:
        errors.append("release input must define the ordered mandatory gate inventory")
    publisher = release.get("publisher") or {}
    if publisher != {
        "repository": "https://github.com/ADASK-B/Mcp.Connector.Template",
        "f1Namespace": "ghcr.io/adask-b/platform-test-app",
        "packageRepository": "ghcr.io/adask-b/platform-test-app/packages/application-platform-test-app",
        "signerIdentity": "https://github.com/ADASK-B/Mcp.Connector.Template/.github/workflows/release.yml@refs/tags/v*",
        "issuer": "https://token.actions.githubusercontent.com",
    }:
        errors.append("publisher boundary differs from the Foundation-approved platform-test policy")
    if "f2" in json.dumps(publisher).lower():
        errors.append("publisher input must not contain an F2 target")
    if release.get("policies") != {
        "publisherPolicyRef": "trust/adask-platform-test-app",
        "evidencePolicyRef": "release/application-platform-test-v1",
        "revocationPolicyRef": "revocation/adask-platform-test-app-v1",
    }:
        errors.append("release policy references must be exact")
    if release.get("blockers") != [
        "approved-delivery-to-f2b-not-yet-proven",
        "complete-oss-distribution-obligation-assessment-not-yet-proven",
        "customer-path-runtime-convergence-not-yet-proven",
        "production-gate-aggregation-not-yet-proven",
        "server-side-source-branch-protection-not-enforced",
    ]:
        errors.append("non-production blocker inventory must remain explicit")

    materials = release.get("materials") or {}
    if set(materials) != {"runtimeBaseImage", "sdkBaseImage"} or any(
        OCI_DIGEST.fullmatch(str(value)) is None for value in materials.values()
    ):
        errors.append("both Docker base images must be immutable release materials")
    dockerfile = (ROOT / "Mcp.Connector.Template/Dockerfile").read_text(encoding="utf-8")
    for material in materials.values():
        if f"FROM {material} AS " not in dockerfile:
            errors.append(f"Dockerfile does not consume exact release material {material}")

    foundation = release.get("foundationContract") or {}
    schemas = foundation.get("schemas") or {}
    if foundation.get("repository") != "https://github.com/ADASK-B/platform-foundation":
        errors.append("Foundation contract source repository is not approved")
    if not re.fullmatch(r"[0-9a-f]{40}", str(foundation.get("commit", ""))):
        errors.append("Foundation contract source must be an immutable commit")
    if set(schemas) != {"application-contract.schema.cue", "application-delivery-package.schema.cue"} or any(
        SHA256.fullmatch(str(value)) is None for value in schemas.values()
    ):
        errors.append("Foundation schema hash inventory must be exact")
    snapshot = ROOT / "release/foundation-contracts"
    if not snapshot.is_dir() or snapshot.is_symlink() or {
        path.name for path in snapshot.iterdir()
    } != set(schemas):
        errors.append("vendored Foundation schema snapshot must contain exactly the bound schemas")
    else:
        for name, expected in schemas.items():
            path = snapshot / name
            content = path.read_bytes() if path.is_file() and not path.is_symlink() else b""
            canonical = content.replace(b"\r\n", b"\n")
            if (
                not content
                or b"\r" in canonical
                or hashlib.sha256(canonical).hexdigest() != expected
            ):
                errors.append(f"vendored Foundation schema bytes differ from the bound commit: {name}")

    toolchain = release.get("toolchain") or {}
    expected_tools = {
        "python": {"version": "3.13.14"},
        "dotnet": {"version": "10.0.400"},
        "helm": {"version": "v4.1.3"},
        "cosign": {"version": "v3.0.3"},
        "trivy": {"version": "v0.69.3"},
        "syft": {"version": "v1.42.2"},
    }
    if set(toolchain) != {*expected_tools, "cue", "zarf"}:
        errors.append("release toolchain inventory must be exact")
    for name, value in expected_tools.items():
        if toolchain.get(name) != value:
            errors.append(f"{name} release tool differs from the reviewed pin")
    for name, version, source, digest in (
        (
            "cue", "v0.17.1",
            "https://github.com/cue-lang/cue/releases/download/v0.17.1/cue_v0.17.1_linux_amd64.tar.gz",
            "a39b0c97695069d95d276d99be0f5dbabb081d801bfdc9ba49b76efaf94e2369",
        ),
        (
            "zarf", "v0.81.1",
            "https://github.com/zarf-dev/zarf/releases/download/v0.81.1/zarf_v0.81.1_Linux_amd64",
            "eabd687b956b621a0e0f9e1889dc68f6b589baea7932c4ecb020da7fe81d13f6",
        ),
    ):
        value = toolchain.get(name) or {}
        if value.get("version") != version or value.get("linuxAmd64") != {"source": source, "sha256": digest}:
            errors.append(f"{name} source/version/digest differs from the Foundation pin")
    if (ROOT / ".python-version").read_text(encoding="utf-8").strip() != "3.13.14":
        errors.append("setup-python input must equal the release toolchain pin")
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    if "*.cue text eol=lf" not in attributes:
        errors.append("vendored CUE schema bytes must be checked out with LF endings")

    license_contract = release.get("license") or {}
    if license_contract.get("expression") != "MIT":
        errors.append("release-owned App license must remain MIT")
    license_path = ROOT / str(license_contract.get("text", ""))
    chart_license = ROOT / "charts/mcp-connector/LICENSE"
    if not license_path.is_file() or not chart_license.is_file() or (
        license_path.read_text(encoding="utf-8").splitlines()
        != chart_license.read_text(encoding="utf-8").splitlines()
    ):
        errors.append("root and chart MIT license texts must exist and match")

    contract = json.loads((ROOT / "release/application-contract.template.json").read_text(encoding="utf-8"))
    if contract.get("apiVersion") != release.get("applicationContractVersion"):
        errors.append("ApplicationContract template version differs from release input")
    if contract.get("metadata") != {"name": "platform-test-app"}:
        errors.append("ApplicationContract stable identity differs from release input")
    contract_release = contract.get("release") or {}
    if contract_release.get("version") != release.get("version"):
        errors.append("ApplicationContract release version differs from release input")
    if contract_release.get("publisher") != {
        "applicationClass": "platform-test", "artifactClass": "vendor-app",
        "policyRef": "trust/adask-platform-test-app",
    }:
        errors.append("ApplicationContract publisher binding differs from release policy")
    expected_artifacts = {
        "chart": {
            "role": "chart",
            "repository": "ghcr.io/adask-b/platform-test-app/charts/platform-test-app",
            "digest": "sha256:" + ("0" * 64),
            "mediaType": "application/vnd.cncf.helm.chart.content.v1.tar+gzip",
        },
        "service-image": {
            "role": "image",
            "repository": "ghcr.io/adask-b/platform-test-app",
            "digest": "sha256:" + ("1" * 64),
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
        },
    }
    if contract_release.get("artifacts") != expected_artifacts:
        errors.append("ApplicationContract artifact repositories or media types are not closed")
    if contract.get("compatibility", {}).get("profiles") != ["onprem-linux-vm-v1"] or (
        contract.get("compatibility", {}).get("architectures") != ["amd64"]
    ):
        errors.append("ApplicationContract must retain fixed on-prem/amd64 product eligibility")
    renderer = (contract.get("deployment") or {}).get("renderer")
    if renderer != {
        "apiVersion": "platform.adask-b.io/application-runtime-values/v1alpha2",
        "helmValuePath": "platformRuntime",
    }:
        errors.append("ApplicationContract must use the fixed v1alpha9 renderer boundary")
    features = (((contract.get("requirements") or {}).get("platform-runtime") or {}).get("api") or {}).get("features")
    if features != ["gitops-v1", "restricted-workload-v1", "standard-workload-labels-v1"]:
        errors.append("ApplicationContract must require the standard-label runtime feature")
    if contract.get("secrets") != {} or (contract.get("network") or {}).get("egress") != {}:
        errors.append("APP-050 contract must not claim unimplemented Secret or egress behavior")
    if (contract.get("network") or {}).get("defaultDeny") is not True:
        errors.append("ApplicationContract must require the generic default-deny boundary")
    if (contract.get("data") or {}).get("persistent") is not False:
        errors.append("APP-050 contract must remain stateless")

    values_text = (ROOT / "charts/mcp-connector/values.yaml").read_text(encoding="utf-8")
    for forbidden in ("labels:", "route:", "networkPolicy:", "serviceAccount:"):
        if forbidden in values_text:
            errors.append(f"chart reintroduces parallel desired-state surface: {forbidden}")
    for removed in ("serviceaccount.yaml", "networkpolicy.yaml", "httproute.yaml"):
        if (ROOT / "charts/mcp-connector/templates" / removed).exists():
            errors.append(f"App-local infrastructure template returned: {removed}")

    for workflow in sorted((ROOT / ".github/workflows").glob("*.yml")):
        uses_lines = [line.strip() for line in workflow.read_text(encoding="utf-8").splitlines() if "uses:" in line]
        if any(not ACTION_PIN.search(line) for line in uses_lines):
            errors.append(f"all actions must use full commit pins: {workflow.name}")
    release_workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    required_operations = (
        "scripts/registry_tag_absent.py", "scripts/verify_oci_layout.py",
        "scripts/fetch_foundation_contracts.py", "scripts/release_pipeline_test.py",
        "git merge-base --is-ancestor", "cue vet", "#ApplicationZarfPackage", "push: false",
        "provenance: false", "zarf tools registry push", "zarf tools registry digest",
        "zarf package create", "zarf package sign", "--keyless", "zarf package publish",
        "zarf package inspect digest", "--verify=always", "slsaprovenance1",
        "https://adask-b.io/attestations/license/v1", "cosign sign-blob", "cosign verify-blob",
    )
    for required in required_operations:
        if required not in release_workflow:
            errors.append(f"release workflow does not execute required operation: {required}")
    lowered = release_workflow.lower()
    for forbidden in (
        "oras ", "zarf package deploy", "--insecure", "--plain-http", "push: true",
        "workflow_dispatch", "rm -rf",
    ):
        if forbidden in lowered:
            errors.append(f"release workflow contains forbidden operation: {forbidden}")
    rehearsal_markers = (
        "Run source, contract, unit and chart gates", "Scan immutable image",
        "Scan the rendered chart", "Generate image SBOM", "Generate chart SBOM",
    )
    mutation_markers = ("zarf tools registry push", "helm push")
    positions = {marker: release_workflow.find(marker) for marker in rehearsal_markers + mutation_markers}
    if any(position < 0 for position in positions.values()) or max(
        positions[marker] for marker in rehearsal_markers
    ) > min(positions[marker] for marker in mutation_markers):
        errors.append("all content gates must execute before the first F1 mutation")
    if release_workflow.count("-d '#ApplicationZarfPackage'") != 2:
        errors.append("delivery package contract must run in rehearsal and against exact release bytes")
    if release_workflow.count("cosign sign --yes \"") != 2:
        errors.append("image and chart must be signed as separate exact subjects")
    package_position = release_workflow.find("zarf package publish")
    manifest_position = release_workflow.find("scripts/release_manifest.py")
    if package_position < 0 or manifest_position < package_position:
        errors.append("publisher manifest must be created only after signed package publication")
    mandatory_image_scan = re.search(
        r"- name: Scan immutable image\n(?P<body>.*?)(?=\n      - name:)",
        release_workflow,
        re.DOTALL,
    )
    if mandatory_image_scan is None or not all(
        marker in mandatory_image_scan.group("body")
        for marker in (
            "format: json", "output: trivy-image.json",
            "severity: CRITICAL,HIGH", "exit-code: '1'",
        )
    ):
        errors.append("mandatory image scan must be a severity-filtered JSON gate")
    if "Re-read the image scan as an attestable report" in release_workflow:
        errors.append("release must not substitute a second scan for the mandatory image gate result")
    sarif_mirror = re.search(
        r"- name: Generate full image SARIF mirror\n(?P<body>.*?)(?=\n      - name:)",
        release_workflow,
        re.DOTALL,
    )
    if sarif_mirror is None or not all(
        marker in sarif_mirror.group("body")
        for marker in ("format: sarif", "output: trivy-results.sarif", "exit-code: '0'")
    ) or "continue-on-error" in sarif_mirror.group("body"):
        errors.append("full SARIF evidence must be generated separately without defining the vulnerability gate")

    build_workflow = (ROOT / ".github/workflows/build-and-test.yml").read_text(encoding="utf-8")
    for required in (
        "scripts/validate_repo.py", "scripts/release_pipeline_test.py",
        "scripts/fetch_foundation_contracts.py", "#ApplicationZarfPackage",
        "scripts/validate-configuration-contract.sh",
    ):
        if required not in build_workflow:
            errors.append(f"PR Build/Test does not execute required gate: {required}")
    if "paths-ignore:" in build_workflow or "paths:" in build_workflow:
        errors.append("PR Build/Test must not be bypassed by path filters")
    exact_dotnet_projection = "dotnet-version: ${{ steps.release.outputs.DOTNET_VERSION }}"
    if exact_dotnet_projection not in build_workflow or exact_dotnet_projection not in release_workflow:
        errors.append("build and release workflows must consume the exact projected .NET SDK")
    codeql_workflow = (ROOT / ".github/workflows/codeql.yml").read_text(encoding="utf-8")
    if "dotnet-version: '10.0.400'" not in codeql_workflow:
        errors.append("CodeQL must use the exact admitted .NET SDK")
    if "dotnet-version: '10.0.x'" in codeql_workflow:
        errors.append("CodeQL must not use a mutable .NET SDK selector")
    return sorted(set(errors))


def main() -> int:
    try:
        errors = collect_errors()
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        errors = [f"source contract is unreadable: {exc}"]
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("PASS: Platform Test App source and release boundary are fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
