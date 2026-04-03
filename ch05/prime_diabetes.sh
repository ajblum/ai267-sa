#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   export TOKEN=$(oc whoami -t)
#   export TRUSTY_ROUTE=https://$(oc get route/trustyai-service --template={{.spec.host}})
#   ./upload_trustyai_training_data.sh training_data.json
#
# Optional:
#   MODEL_ID=diabetes ./upload_trustyai_training_data.sh training_data.json

MODEL_ID="${MODEL_ID:-diabetes}"

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <training_data.json>"
  exit 1
fi

DATA_FILE="$1"

if [[ -z "${TOKEN:-}" ]]; then
  echo "ERROR: TOKEN is not set."
  echo 'Run: export TOKEN=$(oc whoami -t)'
  exit 1
fi

if [[ -z "${TRUSTY_ROUTE:-}" ]]; then
  echo "ERROR: TRUSTY_ROUTE is not set."
  echo 'Run: export TRUSTY_ROUTE=https://$(oc get route/trustyai-service --template={{.spec.host}})'
  exit 1
fi

if [[ ! -f "$DATA_FILE" ]]; then
  echo "ERROR: File not found: $DATA_FILE"
  exit 1
fi

echo "Uploading training data from: $DATA_FILE"
echo "TrustyAI route: $TRUSTY_ROUTE"
echo

curl -sk "${TRUSTY_ROUTE}/data/upload" \
  --header "Authorization: Bearer ${TOKEN}" \
  --header "Content-Type: application/json" \
  -d @"${DATA_FILE}"

echo
echo
echo "Current TrustyAI model info:"
curl -sk -H "Authorization: Bearer ${TOKEN}" \
  "${TRUSTY_ROUTE}/info" | jq

echo
echo "Tip: after upload, the observation count for ${MODEL_ID} should increase."
