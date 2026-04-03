#!/usr/bin/env bash
set -euo pipefail

# Prereqs:
#   export TOKEN=$(oc whoami -t)
#   export TRUSTY_ROUTE=https://$(oc get route/trustyai-service --template='{{.spec.host}}')
#   export MODEL_URL=https://diabetes-myproj1.apps.ocp4.example.com
#
# Optional:
#   export MODEL_NAME=diabetes
#   export DATA_TAG=TRAINING

MODEL_NAME="${MODEL_NAME:-diabetes}"
DATA_TAG="${DATA_TAG:-TRAINING}"

if [[ -z "${TOKEN:-}" ]]; then
  echo "ERROR: TOKEN is not set."
  exit 1
fi

if [[ -z "${TRUSTY_ROUTE:-}" ]]; then
  echo "ERROR: TRUSTY_ROUTE is not set."
  exit 1
fi

if [[ -z "${MODEL_URL:-}" ]]; then
  echo "ERROR: MODEL_URL is not set."
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq is required."
  exit 1
fi

INFER_URL="${MODEL_URL}/v2/models/${MODEL_NAME}/infer"
workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

# Demo rows:
# [Pregnancies, Glucose, BloodPressure, SkinThickness, Insulin, BMI, DiabetesPedigreeFunction, AgeOver50]
readarray -t ROWS <<'EOF'
0.0,92.0,68.0,18.0,80.0,23.5,0.18,0.0
1.0,100.0,70.0,20.0,85.0,24.8,0.22,0.0
1.0,108.0,72.0,20.0,90.0,25.5,0.25,0.0
2.0,118.0,74.0,22.0,105.0,27.2,0.30,0.0
2.0,128.0,76.0,24.0,120.0,29.0,0.36,0.0
2.0,136.0,78.0,24.0,135.0,30.2,0.40,0.0
2.0,140.0,80.0,25.0,150.0,31.5,0.45,0.0
3.0,145.0,82.0,26.0,165.0,32.8,0.50,0.0
3.0,150.0,84.0,28.0,175.0,34.0,0.56,0.0
4.0,158.0,86.0,30.0,190.0,35.5,0.63,0.0
5.0,168.0,88.0,32.0,210.0,37.2,0.72,0.0
6.0,178.0,92.0,35.0,235.0,39.8,0.86,0.0
0.0,92.0,68.0,18.0,80.0,23.5,0.18,1.0
1.0,100.0,70.0,20.0,85.0,24.8,0.22,1.0
1.0,108.0,72.0,20.0,90.0,25.5,0.25,1.0
2.0,118.0,74.0,22.0,105.0,27.2,0.30,1.0
2.0,128.0,76.0,24.0,120.0,29.0,0.36,1.0
2.0,136.0,78.0,24.0,135.0,30.2,0.40,1.0
2.0,140.0,80.0,25.0,150.0,31.5,0.45,1.0
3.0,145.0,82.0,26.0,165.0,32.8,0.50,1.0
3.0,150.0,84.0,28.0,175.0,34.0,0.56,1.0
4.0,158.0,86.0,30.0,190.0,35.5,0.63,1.0
5.0,168.0,88.0,32.0,210.0,37.2,0.72,1.0
6.0,178.0,92.0,35.0,235.0,39.8,0.86,1.0
EOF

count=0

for row in "${ROWS[@]}"; do
  req="${workdir}/req.json"
  resp="${workdir}/resp.json"
  joint="${workdir}/joint.json"

  cat > "${req}" <<EOF
{
  "inputs": [
    {
      "name": "dense_input",
      "shape": [1, 8],
      "datatype": "FP32",
      "data": [${row}]
    }
  ]
}
EOF

  curl -sk \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    "${INFER_URL}" \
    -d @"${req}" > "${resp}"

  jq -n \
    --arg model_name "${MODEL_NAME}" \
    --arg data_tag "${DATA_TAG}" \
    --slurpfile req "${req}" \
    --slurpfile resp "${resp}" \
    '{
      model_name: $model_name,
      data_tag: $data_tag,
      request: $req[0],
      response: $resp[0]
    }' > "${joint}"

  curl -sk \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    "${TRUSTY_ROUTE}/data/upload" \
    -d @"${joint}" >/dev/null

  count=$((count + 1))
  echo "Uploaded row ${count}"
done

echo
echo "Done. Uploaded ${count} datapoints."
echo "Verify with:"
echo "curl -sk -H \"Authorization: Bearer \$TOKEN\" \"${TRUSTY_ROUTE}/info\" | jq"
