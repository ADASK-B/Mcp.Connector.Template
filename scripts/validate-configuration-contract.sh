#!/usr/bin/env bash
set -euo pipefail

chart='charts/mcp-connector'
values='release/trivy-chart-values.yaml'
invalid_values="$(mktemp)"
trap 'rm -f "$invalid_values"' EXIT

expect_rejected() {
  local description="$1"
  if helm template platform-test-app "$chart" --values "$values" \
    --values "$invalid_values" >/dev/null 2>&1; then
    echo "Chart accepted $description." >&2
    exit 1
  fi
}

rendered="$(helm template platform-test-app "$chart" --values "$values")"

grep -Fq 'kind: ConfigMap' <<<"$rendered"
grep -Fq 'platform.adask-b.io/platform-test-configuration/v1alpha1' <<<"$rendered"
grep -Fq '"message":"synthetic-release-scan-message"' <<<"$rendered"
grep -Fq 'mountPath: /etc/adask/platform-test/configuration.json' <<<"$rendered"
grep -Fq 'checksum/application-configuration:' <<<"$rendered"
grep -Fq 'serviceAccountName: platform-test-app-service' <<<"$rendered"
grep -Fq 'platform.adask-b.io/application-id: platform-test-app' <<<"$rendered"
grep -Fq 'platform.adask-b.io/trust-zone: vendor-apps' <<<"$rendered"
grep -Fq 'app: platform-test-app' <<<"$rendered"
grep -Fq 'team: vendor-apps' <<<"$rendered"
grep -Fq 'environment: release-rehearsal' <<<"$rendered"
grep -Fq 'readOnlyRootFilesystem: true' <<<"$rendered"
grep -Fq 'drop:' <<<"$rendered"
grep -Fq -- '- ALL' <<<"$rendered"

for forbidden in 'kind: NetworkPolicy' 'kind: ServiceAccount' 'kind: HTTPRoute' 'APPLICATION_MESSAGE'; do
  if grep -Fq "$forbidden" <<<"$rendered"; then
    echo "Chart rendered forbidden App-local configuration: $forbidden" >&2
    exit 1
  fi
done

printf 'application:\n  message: ""\n' >"$invalid_values"
expect_rejected 'missing generated application.message'

printf 'application:\n  message: 42\n' >"$invalid_values"
expect_rejected 'non-string generated application.message'

printf 'application:\n  message: "%s"\n' "$(printf '😀%.0s' {1..129})" >"$invalid_values"
expect_rejected 'generated application.message over 128 Unicode characters'

printf 'platformRuntime: null\n' >"$invalid_values"
expect_rejected 'missing canonical platformRuntime'

cat >"$invalid_values" <<'YAML'
platformRuntime:
  apiVersion: unsupported/v1
YAML
expect_rejected 'unsupported platformRuntime API'

cat >"$invalid_values" <<'YAML'
platformRuntime:
  application:
    id: another-app
YAML
expect_rejected 'runtime values for another Application identity'

cat >"$invalid_values" <<'YAML'
platformRuntime:
  application:
    releaseVersion: 9.9.9
YAML
expect_rejected 'runtime values for another release'

cat >"$invalid_values" <<'YAML'
platformRuntime:
  application:
    trustZone: customer-apps
YAML
expect_rejected 'runtime values for another trust zone'

cat >"$invalid_values" <<'YAML'
platformRuntime:
  application:
    standardLabels:
      app: another-app
YAML
expect_rejected 'divergent standard Application label'

cat >"$invalid_values" <<'YAML'
platformRuntime:
  workloads:
    service:
      hostNamespaces:
        network: true
YAML
expect_rejected 'forbidden host-network access'

cat >"$invalid_values" <<'YAML'
image:
  digest: latest
YAML
expect_rejected 'mutable image identity'

echo 'PASS: chart consumes only the closed generated Application runtime contract'
