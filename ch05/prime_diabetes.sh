#!/bin/bash

# Configuration
export MODEL_URL="https://diabetes-myproj1.apps.ocp4.example.com/v2/models/diabetes/infer"
export TOKEN=$(oc whoami -t)

echo "🚀 Starting data injection for Diabetes Bias Demo..."

# Loop 100 times to create a batch
for i in {1..100}
do
    # 1. Logic to split Age (Feature Index 7)
    # We send 50 "Young" (25) and 50 "Old" (50) to match our SPD configuration
    if [ $i -le 50 ]; then
        AGE=25.0
        GLUCOSE=$(( ( RANDOM % 40 ) + 90 )) # Normal-ish Glucose for young
    else
        AGE=50.0
        GLUCOSE=$(( ( RANDOM % 60 ) + 130 )) # Slightly higher Glucose for old
    fi

    # 2. Randomize other features for "Realism"
    PREG=$(( RANDOM % 5 ))
    BP=$(( ( RANDOM % 20 ) + 70 ))
    SKIN=$(( ( RANDOM % 10 ) + 20 ))
    INSULIN=$(( RANDOM % 100 ))
    BMI="3$(($RANDOM % 9)).$(($RANDOM % 9))" # Random BMI in the 30s
    PEDIGREE="0.$(($RANDOM % 800 + 100))"

    # 3. Construct the KServe V2 JSON Payload
    PAYLOAD=$(cat <<EOF
{
  "inputs": [
    {
      "name": "dense_input",
      "shape": [1, 8],
      "datatype": "FP32",
      "data": [[$PREG, $GLUCOSE, $BP, $SKIN, $INSULIN, $BMI, $PEDIGREE, $AGE]]
    }
  ],
  "outputs": [{"name": "output0"}]
}
EOF
)

    # 4. Send the inference request
    # The inference-logger sidecar will intercept this automatically 
    curl -sk -X POST -H "Authorization: Bearer $TOKEN" \
         -H "Content-Type: application/json" \
         -d "$PAYLOAD" $MODEL_URL > /dev/null

    # Progress indicator
    if (( $i % 10 == 0 )); then echo "✅ Sent $i observations..."; fi
done

echo "✨ Done! TrustyAI is now processing the observations."
