#!/usr/bin/env bash
set -e

# Extract device serial
export DEVICE_SERIAL=$(awk '/Serial/ {print tolower($3)}' /proc/cpuinfo)

# Extract device type/model, sanitize
if [ -f /tmp/model ]; then
    export DEVICE_TYPE=$(tr -d '\0' </tmp/model | sed -E 's/[^A-Za-z0-9]+/_/g' | sed -E 's/_+/_/g' | cut -c1-40)
else
    export DEVICE_TYPE="unknown_pi"
fi

# Execute Promtail with whatever arguments are passed
exec /usr/bin/promtail "$@"

