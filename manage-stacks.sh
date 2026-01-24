#!/bin/bash

# Directory containing the stacks
STACKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTION=$1

# Help message
if [[ -z "$ACTION" ]]; then
    echo "Usage: ./manage-stacks.sh [start|stop|restart|pull]"
    echo ""
    echo "  start   : Starts all stacks (docker compose up -d)"
    echo "  stop    : Stops all stacks (docker compose down)"
    echo "  restart : Stops and then starts all stacks"
    echo "  pull    : Pulls the latest images for all stacks"
    exit 1
fi

# Function to ensure the shared proxy network exists
ensure_network() {
    if ! docker network ls --format '{{.Name}}' | grep -q "^proxy_net$"; then
        echo "Network 'proxy_net' not found. Creating it..."
        docker network create proxy_net
    else
        echo "Network 'proxy_net' exists."
    fi
}

# Create network if starting up
if [[ "$ACTION" == "start" || "$ACTION" == "restart" ]]; then
    ensure_network
fi

# Iterate through each subdirectory
find "$STACKS_DIR" -mindepth 1 -maxdepth 1 -type d | sort | while read -r stack; do
    if [[ -f "$stack/docker-compose.yml" ]]; then
        STACK_NAME=$(basename "$stack")
        echo "==================================================="
        echo "Processing stack: $STACK_NAME ($ACTION)"
        echo "==================================================="
        
        cd "$stack" || continue
        
        case "$ACTION" in
            start)
                docker compose up -d --remove-orphans
                ;;
            stop)
                docker compose down
                ;;
            restart)
                docker compose down && docker compose up -d --remove-orphans
                ;;
            pull)
                docker compose pull
                ;;
            *)
                echo "Error: Invalid action '$ACTION'"
                exit 1
                ;;
        esac
        echo ""
    fi
done

echo "Done!"
