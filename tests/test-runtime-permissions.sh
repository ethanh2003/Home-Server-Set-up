#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

secret_files=()
while IFS= read -r -d '' path; do
    secret_files+=("$path")
done < <(
    find "$REPO_ROOT" -xdev -maxdepth 4 -type f \
        \( -name '.env' -o -name 'secrets.yaml' -o -name 'SALT.php' -o -name '.jwt_secret' \) \
        -print0
)

for storage_root in \
    "$REPO_ROOT/hass_config/.storage" \
    "$REPO_ROOT/home-assistant/config/homeassistant/.storage" \
    "$REPO_ROOT/home-assistant/config/homeassistant2/.storage"; do
    [[ -d "$storage_root" ]] || continue
    while IFS= read -r -d '' path; do
        secret_files+=("$path")
    done < <(
        find "$storage_root" -maxdepth 1 -type f \
            \( -name 'auth' -o -name 'auth_provider.homeassistant' -o -name 'http.auth' \) \
            -print0
    )
done

while IFS= read -r -d '' path; do
    secret_files+=("$path")
done < <(
    find "$REPO_ROOT/nginx-proxy-manager/nginx_config/letsencrypt" -xdev -type f \
        \( -name 'privkey*.pem' -o -path '*/credentials/*' \) \
        -print0 2>/dev/null
)

secret_files+=(
    "$REPO_ROOT/portainer_data/certs/key.pem"
    "$REPO_ROOT/portainer_data/chisel/private-key.pem"
    "$REPO_ROOT/portainer_data/portainer.key"
)

for path in "${secret_files[@]}"; do
    [[ -e "$path" ]] || continue
    mode=$(stat -c '%a' "$path")
    if (( (8#$mode & 0007) != 0 )); then
        echo "FAIL: secret-bearing runtime file is accessible to other users: $path ($mode)" >&2
        exit 1
    fi
    if (( (8#$mode & 0020) != 0 )); then
        echo "FAIL: secret-bearing runtime file is group-writable: $path ($mode)" >&2
        exit 1
    fi
done

operator_scripts=(
    "$REPO_ROOT/backup_databases.sh"
    "$REPO_ROOT/rclone_backup.sh"
    "$REPO_ROOT/manage-stacks.sh"
)

for path in "${operator_scripts[@]}"; do
    mode=$(stat -c '%a' "$path")
    if (( (8#$mode & 0022) != 0 )); then
        echo "FAIL: operator script is writable outside its owner: $path ($mode)" >&2
        exit 1
    fi
done

echo "PASS: runtime secrets are private and operator scripts are not externally writable"
