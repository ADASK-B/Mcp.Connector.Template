{{- define "mcp-connector.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "mcp-connector.fullname" -}}
{{- printf "%s" (include "mcp-connector.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "mcp-connector.labels" -}}
app.kubernetes.io/name: {{ include "mcp-connector.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
platform.adask-b.io/trust-zone: vendor-apps
app: {{ required "labels.app is required" .Values.labels.app }}
team: {{ required "labels.team is required" .Values.labels.team }}
environment: {{ required "labels.environment is required" .Values.labels.environment }}
{{- end -}}
