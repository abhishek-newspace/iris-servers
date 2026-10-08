#!/bin/bash 

# script to restart the docker compose 

cd /home/siddharth/Documents/rpi-server/mapping

echo "Downing the containers to restart them with the new versions"

docker compose -f docker-compose-telematics.yml down 

echo "restarting the containers now"

docker compose -f docker-compose-telematics.yml up -d --build

echo "Waiting 15 seconds to verify containers stay alive..."
sleep 15

CRASHED_CONTAINERS=$(docker compose -f docker-compose-telematics.yml ps --status exited --status restarting -q)

RUNNING_CONTAINERS=$(docker compose -f docker-compose-telematics.yml ps --status running -q)

if [ -n "$CRASHED_CONTAINERS" ]; then 
    echo "Update failed. The following containers crashed after starting:"
    docker compose -f docker-compose-telematics.yml logs 
    docker compose -f docker-compose-telematics.yml ps
    exit 1 
elif [ -z "$RUNNING_CONTAINERS" ]; then 
    echo "Update failed. The containers did not start up after the shutdown"
    docker compose -f docker-compose-telematics.yml logs
    docker compose -f docker-compose-telematics.yml ps 
    exit 1
else
    echo "Restarted the containers successfully. All services are running"
    docker compose -f docker-compose-telematics.yml ps 
    exit 0
fi 

