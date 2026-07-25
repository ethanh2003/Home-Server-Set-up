#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STACK_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${ENV_FILE:-${STACK_DIR}/.env}"

read_env() {
  local key="$1"
  local fallback="$2"

  if [[ -f "${ENV_FILE}" ]]; then
    local value
    value="$(awk -F= -v key="${key}" '$1 == key { sub(/^[^=]*=/, ""); print; exit }' "${ENV_FILE}")"
    if [[ -n "${value}" ]]; then
      value="${value%\"}"
      value="${value#\"}"
      value="${value%\'}"
      value="${value#\'}"
      printf '%s\n' "${value}"
      return
    fi
  fi

  printf '%s\n' "${fallback}"
}

LAN_PARENT="${LAN_PARENT:-$(read_env LAN_PARENT enp1s0)}"
HOST_SHIM_IP="${HOST_SHIM_IP:-$(read_env HOST_SHIM_IP 192.168.1.229)}"
TIMEMACHINE_IP="${TIMEMACHINE_IP:-$(read_env TIMEMACHINE_IP 192.168.1.230)}"
SHIM_IF="${SHIM_IF:-tm-shim}"

if [[ "${EUID}" -eq 0 ]]; then
  SUDO=()
else
  SUDO=(sudo -n)
fi

if ! ip link show "${LAN_PARENT}" >/dev/null 2>&1; then
  echo "Parent interface ${LAN_PARENT} does not exist" >&2
  exit 1
fi

if ! ip link show "${SHIM_IF}" >/dev/null 2>&1; then
  "${SUDO[@]}" ip link add "${SHIM_IF}" link "${LAN_PARENT}" type macvlan mode bridge
fi

"${SUDO[@]}" ip addr replace "${HOST_SHIM_IP}/32" dev "${SHIM_IF}"
"${SUDO[@]}" ip link set "${SHIM_IF}" up
"${SUDO[@]}" ip route replace "${TIMEMACHINE_IP}/32" dev "${SHIM_IF}"

echo "macvlan shim ready: ${SHIM_IF} ${HOST_SHIM_IP}/32 -> ${TIMEMACHINE_IP}/32 via ${LAN_PARENT}"
