#!/usr/bin/env bash
set -euo pipefail

chart='charts/mcp-connector'
values='release/trivy-chart-values.yaml'
invalid_values="$(mktemp)"
trap 'rm -f "$invalid_values"' EXIT

rendered="$(helm template mcp-reference "$chart" --values "$values")"

grep -Fq 'kind: ConfigMap' <<<"$rendered"
grep -Fq 'platform.adask-b.io/platform-test-configuration/v1alpha1' <<<"$rendered"
grep -Fq '"message":"synthetic-release-scan-message"' <<<"$rendered"
grep -Fq 'mountPath: /etc/adask/platform-test/configuration.json' <<<"$rendered"
grep -Fq 'checksum/application-configuration:' <<<"$rendered"

if grep -Fq 'APPLICATION_MESSAGE' <<<"$rendered"; then
  echo 'Application message must not be transported through an environment variable.' >&2
  exit 1
fi

printf 'application:\n  message: ""\n' >"$invalid_values"
if helm template mcp-reference "$chart" --values "$values" \
  --values "$invalid_values" >/dev/null 2>&1; then
  echo 'Chart accepted missing generated application.message.' >&2
  exit 1
fi

printf 'application:\n  message: 42\n' >"$invalid_values"
if helm template mcp-reference "$chart" --values "$values" \
  --values "$invalid_values" >/dev/null 2>&1; then
  echo 'Chart accepted non-string generated application.message.' >&2
  exit 1
fi

printf 'application:\n  message: "%s"\n' "$(printf '😀%.0s' {1..129})" >"$invalid_values"
if helm template mcp-reference "$chart" --values "$values" \
  --values "$invalid_values" >/dev/null 2>&1; then
  echo 'Chart accepted generated application.message over 128 Unicode characters.' >&2
  exit 1
fi
