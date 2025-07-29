#!/usr/bin/env bash

# ----------------------------------------------------------------------
# validate-tailscale-policy.sh
#
# Validates a Tailscale policy.hujson file using the Tailscale API.
# Exits with non-zero if validation fails.
# Export the following two variables before executing:
# export TAILSCALE_API_KEY="tskey-abc123..."       # your API key
# export TAILSCALE_TAILNET="example.com"           # your Tailscale tailnet
# ----------------------------------------------------------------------

set -euo pipefail

# Configurable Variables
POLICY_FILE="${1:-policy.hujson}"
TAILNET="${TAILSCALE_TAILNET:-}"   # e.g. myorg.com
API_KEY="${TAILSCALE_API_KEY:-}"   # create via https://login.tailscale.com/admin/settings/authkeys

# ANSI colors for output
RED=$(tput setaf 1 || true)
GREEN=$(tput setaf 2 || true)
YELLOW=$(tput setaf 3 || true)
RESET=$(tput sgr0 || true)

# Helper: Print error message and exit
die() {
    echo "${RED}✖ $*${RESET}" >&2
    exit 1
}

# Helper: Print success message
success() {
    echo "${GREEN}✔ $*${RESET}"
}

# Helper: Print info message
info() {
    echo "${YELLOW}➜ $*${RESET}"
}

# 1. Ensure required inputs are set
[[ -z "$TAILNET" ]] && die "Missing TAILSCALE_TAILNET environment variable"
[[ -z "$API_KEY" ]] && die "Missing TAILSCALE_API_KEY environment variable"
[[ ! -f "$POLICY_FILE" ]] && die "Policy file not found: $POLICY_FILE"

# 2. Validate policy via Tailscale API
info "Validating policy file: $POLICY_FILE"
VALIDATE_URL="https://api.tailscale.com/api/v2/tailnet/${TAILNET}/acl/validate"

RESPONSE=$(curl -sS -u "${API_KEY}:" \
  -H "Content-Type: application/json" \
  --data-binary "@${POLICY_FILE}" \
  "${VALIDATE_URL}")

# 3. Check API response
if [[ "${RESPONSE}" == "{}" ]]; then
    success "Tailscale policy is valid."
    exit 0
else
    die "Policy validation failed:\n${RESPONSE}"
fi
