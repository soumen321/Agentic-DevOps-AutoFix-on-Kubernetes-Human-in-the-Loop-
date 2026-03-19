#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: ./scripts/approve_fix.sh <incident-id>"
  exit 1
fi

INCIDENT_ID="$1"
APPROVAL_DIR="approvals"

mkdir -p "$APPROVAL_DIR"

APPROVED_FILE="${APPROVAL_DIR}/${INCIDENT_ID}.approved"

echo "approved" > "$APPROVED_FILE"

echo "Approved: $INCIDENT_ID"
echo "Approval file created: $(pwd)/$APPROVED_FILE"