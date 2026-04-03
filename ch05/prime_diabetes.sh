#!/usr/bin/env bash
set -euo pipefail

# Required:
#   export TOKEN=$(oc whoami -t)
#
# Optional:
#   export MODEL_URL="https://diabetes-myproj1.apps.ocp4.example.com"
#   export ITERATIONS=5

MODEL_URL="${MODEL_URL:-https://diabetes-myproj1.apps.ocp4.example.com}"
MODEL_NAME="${MODEL_NAME:-diabetes}"
ITERATIONS="${ITERATIONS:-5}"

if [[ -z "${TOKEN:-}" ]]; then
  echo "ERROR: TOKEN is not set."
  echo 'Run: export TOKEN=$(oc whoami -t)'
  exit 1
fi

INFER_URL="${MODEL_URL}/v2/models/${MODEL_NAME}/infer"

# Sample rows WITHOUT AgeOver50.
# The script will append 0.0 and 1.0 automatically.
# Format:
# Pregnancies,Glucose,BloodPressure,SkinThickness,Insulin,BMI,DiabetesPedigreeFunction
SAMPLES=(
  "0.0,92.0,68.0,18.0,80.0,23.5,0.18"
  "1.0,110.0,72.0,20.0,100.0,26.0,0.25"
  "2.0,125.0,76.0,22.0,120.0,28.0,0.30"
  "2.0,135.0,80.0,24.0,140.0,30.0,0.40"
  "2.0,140.0,80.0,25.0,150.0,31.5,0.45"
  "3.0,145.0,84.0,28.0,170.0,33.0,0.50"
  "4.0,155.0,88.0,30.0,200.0,36.0,0.65"
  "5.0,185.0,96.0,35.0,240.0,40.0,0.82"
)

total=0

echo "Sending demo traffic to ${INFER_URL}"
echo "Iterations per sample/group: ${ITERATIONS}"
echo

for ageflag in 0.0 1.0; do
  echo "Loading samples for AgeOver50=${ageflag}"
  for sample in "${SAMPLES[@]}"; do
    for ((i=1; i<=ITERATIONS; i++)); do
      payload=$(cat <<EOF
{
  "model_name": "${MODEL_NAME}",
  "inputs": [
    {
      "name": "dense_input",
      "shape": [1, 8],
      "datatype": "FP32",
      "data": [${sample}, ${ageflag}]
    }
  ]
}
EOF
)

      curl -sk \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        "${INFER_URL}" \
        -d "${payload}" >/dev/null

      total=$((total + 1))
    done
  done
done

echo
echo "Done."
echo "Total inference requests sent: ${total}"
echo
echo "Next checks:"
echo '  curl -sk -H "Authorization: Bearer ${TOKEN}" "${TRUSTY_ROUTE}/info" | jq'
echo
echo 'Then test SPD with:'
cat <<'EOF'
curl -sk -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -X POST "${TRUSTY_ROUTE}/metrics/group/fairness/spd" \
  -d '{
    "modelId": "diabetes",
    "protectedAttribute": "AgeOver50",
    "privilegedAttribute": {"type":"FLOAT","value":0},
    "unprivilegedAttribute": {"type":"FLOAT","value":1},
    "outcomeName": "Final_Prediction",
    "favorableOutcome": {"type":"INT64","value":1},
    "batchSize": 50
  }' | jq
EOF
