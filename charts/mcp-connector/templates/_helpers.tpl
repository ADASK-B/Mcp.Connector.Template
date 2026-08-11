{{- define "mcp-connector.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "mcp-connector.fullname" -}}
{{- printf "%s" (include "mcp-connector.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "mcp-connector.labels" -}}
{{- include "mcp-connector.validateRuntime" . -}}
app.kubernetes.io/name: {{ include "mcp-connector.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
platform.adask-b.io/application-id: {{ .Values.platformRuntime.application.id }}
platform.adask-b.io/trust-zone: {{ .Values.platformRuntime.application.trustZone }}
app: {{ .Values.platformRuntime.application.standardLabels.app }}
team: {{ .Values.platformRuntime.application.standardLabels.team }}
environment: {{ .Values.platformRuntime.application.standardLabels.environment }}
{{- end -}}

{{- define "mcp-connector.validateRuntime" -}}
{{- $runtime := required "platformRuntime is required from the canonical resolved setup model" .Values.platformRuntime -}}
{{- if ne $runtime.apiVersion "platform.adask-b.io/application-runtime-values/v1alpha2" -}}
{{- fail "platformRuntime.apiVersion must be application-runtime-values/v1alpha2" -}}
{{- end -}}
{{- if ne $runtime.application.id "platform-test-app" -}}
{{- fail "platformRuntime.application.id must equal the stable Application ID platform-test-app" -}}
{{- end -}}
{{- if ne $runtime.application.releaseVersion .Chart.AppVersion -}}
{{- fail "platformRuntime.application.releaseVersion must equal the immutable chart release" -}}
{{- end -}}
{{- if ne $runtime.application.trustZone "vendor-apps" -}}
{{- fail "platformRuntime.application.trustZone must equal the release-bound vendor-apps trust zone" -}}
{{- end -}}
{{- $labels := required "platformRuntime.application.standardLabels is required" $runtime.application.standardLabels -}}
{{- if ne $labels.app $runtime.application.id -}}
{{- fail "platformRuntime standard app label differs from the stable Application ID" -}}
{{- end -}}
{{- if ne $labels.team $runtime.application.trustZone -}}
{{- fail "platformRuntime standard team label differs from the release-bound trust zone" -}}
{{- end -}}
{{- $_ := required "platformRuntime standard environment label is required" $labels.environment -}}
{{- end -}}
