#---------------------------------------------23-10-2025---------------------------------------------------------------------------
# #!/bin/bash

# # Path to CRL inside volume mounted folder
# CRL_PATH="/home/server/iris/infra/mosquitto/certs/intermediate.crl.pem"

# # Temporary file for atomic update
# TMP_PATH="${CRL_PATH}.tmp"

# # URL of your PKI CRL endpoint
# CRL_URL="https://linnie-tinglier-ima.ngrok-free.dev/api/v1/crl"

# # Fetch CRL
# curl -sSf "$CRL_URL" | jq -r '.crl' | sed 's/\\n/\n/g' > "$TMP_PATH"

# if [ $? -eq 0 ]; then
#     mv "$TMP_PATH" "$CRL_PATH"
#     docker restart mosquitto
#     echo "$(date) - CRL updated successfully."
# else
#     echo "$(date) - Failed to fetch CRL."
#     rm -f "$TMP_PATH"
# fi

#-----------------------------------------24-10-2025----------------------------------------------------------------------------
#This script executes on the system and basically makes a http req to the pki endpoint and gets the updated crl
#if changes are present it updates or it skips and logs.
#Right now the script runs every 45 mins and does not run if the container is offline, crontab -e can be used to configure it.
#*/45 8-18 * * 1-5 docker ps --format '{{.Names}}' | grep -qx mosquitto && /home/server/iris/infra/mosquitto/scripts/update_crl.sh >> /home/server/iris/infra/mosquitto/scripts/update_crl.log 2>&1 
#* 8-18 * * 1-5 docker ps --format '{{.Names}}' | grep -qx mosquitto && /home/azureuser/iris-backend/infra/mosquitto/scripts/update_crl.sh >> /home/azureuser/iris-backend/infra/mosquitto/scripts/update_crl.log 2>&1 
#current command that makes sure the script runs every 30 mins from MON-FRI 8:00:00 AM to 6:00:00 PM

#!/bin/bash

CRL_PATH="/home/azureuser/iris-backend/infra/mosquitto/certs/intermediate.crl.pem"
TMP_PATH="${CRL_PATH}.tmp"
CRL_URL="http://localhost:9000/api/v1/crl" # Change URL as required.
CONTAINER_NAME="mosquitto"

# Gracefully exit process if the container is not running.
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "$(date) - Mosquitto container not running. Skipping CRL update."
    exit 0
fi

# Fetching the HTTP status code from the PKI server (skip certificate verification).
HTTP_STATUS=$(curl -k -s -w "%{http_code}" -o "$TMP_PATH" "$CRL_URL")

# Condition to check the status code.
if [ "$HTTP_STATUS" -eq 200 ]; then
    # Extract and decode CRL content
    jq -r '.crl' "$TMP_PATH" | sed 's/\\n/\n/g' > "${TMP_PATH}.decoded"
    
    # Check if decoded file is non-empty
    if [ ! -s "${TMP_PATH}.decoded" ]; then
        echo "$(date) - Decoded CRL is empty. Skipping update."
        rm -f "$TMP_PATH" "${TMP_PATH}.decoded"
        exit 1
    fi

    NEW_LAST_UPDATE=$(openssl crl -in "${TMP_PATH}.decoded" -noout -lastupdate 2>/dev/null | cut -d= -f2)

    if [ -z "$NEW_LAST_UPDATE" ]; then
        echo "$(date) - Failed to read lastUpdate from new CRL. Skipping."
        rm -f "$TMP_PATH" "${TMP_PATH}.decoded"
        exit 1
    fi

    NEW_EPOCH=$(date -d "$NEW_LAST_UPDATE" +%s 2>/dev/null)

    # Extract lastUpdate from existing CRL if present
    if [ -f "$CRL_PATH" ]; then
        CURRENT_LAST_UPDATE=$(openssl crl -in "$CRL_PATH" -noout -lastupdate 2>/dev/null | cut -d= -f2)

        if [ -n "$CURRENT_LAST_UPDATE" ]; then
            CURRENT_EPOCH=$(date -d "$CURRENT_LAST_UPDATE" +%s 2>/dev/null)
        else
            CURRENT_EPOCH=0
        fi
    else
        CURRENT_EPOCH=0
    fi

    # Compare timestamps
    if [ "$NEW_EPOCH" -le "$CURRENT_EPOCH" ]; then
        echo "$(date) - CRL is not newer than the current one. Skipping update."
        rm -f "$TMP_PATH" "${TMP_PATH}.decoded"
        exit 0
    fi

    # Compare and update if different
    if [ -f "$CRL_PATH" ] && cmp -s "${TMP_PATH}.decoded" "$CRL_PATH"; then
        echo "$(date) - No updates in the current CRL."
        rm -f "$TMP_PATH" "${TMP_PATH}.decoded"
    else
        mv "${TMP_PATH}.decoded" "$CRL_PATH"
        docker restart "$CONTAINER_NAME"
        echo "$(date) - CRL updated successfully. Container restarted."
    fi
    rm -f "$TMP_PATH"
elif [ "$HTTP_STATUS" -eq 404 ]; then
    echo "$(date) - CRL endpoint returned 404. Skipping update."
    rm -f "$TMP_PATH"
else
    echo "$(date) - Failed to fetch CRL. HTTP status: $HTTP_STATUS"
    rm -f "$TMP_PATH"
fi

