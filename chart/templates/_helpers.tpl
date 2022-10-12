# {{/* vim: set filetype=mustache: */}}
# {{/*
# Expand the name of the chart.
# */}}
# {{- define "imageswap.name" -}}
# {{- default .Chart.Name | trunc 63 | trimSuffix "-" -}}
# {{- end -}}

# {{/*
# Create a default fully qualified app name.
# We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
# If release name contains chart name it will be used as a full name.
# */}}
# {{- define "imageswap.fullname" -}}
# {{- $name := default .Chart.Name -}}
# {{- if contains $name .Release.Name -}}
# {{- .Release.Name | trunc 63 | trimSuffix "-" -}}
# {{- else -}}
# {{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
# {{- end -}}
# {{- end -}}
