#!/usr/bin/env bash
#
# Point the CI pipeline at the current GPU instance.
#
# JarvisLabs hands out a NEW machine id and a NEW public IP every time a VM
# is resumed, so GPU_HOST and GPU_HOST_KEY are stale after every pause. This
# resumes the instance if needed, waits for sshd, and rewrites both secrets.
#
#   scripts/refresh_ci_secrets.sh              # resume if paused, then refresh
#   scripts/refresh_ci_secrets.sh --no-resume  # fail instead of resuming
#
# GPU_SSH_KEY is deliberately NOT touched. It is long-lived and set once by
# hand -- see the comment in .github/workflows/deploy.yml about why that is a
# compromise rather than good practice.

set -euo pipefail

INSTANCE_NAME="${INSTANCE_NAME:-agent-prod-session}"
SSH_USER="${SSH_USER:-ubuntu}"
# The key the deploy job authenticates with. Its public half is installed on
# the instance below, because JarvisLabs only injects account keys when a VM
# is created or resumed -- adding a key does nothing to a running box.
DEPLOY_KEY="${DEPLOY_KEY:-$HOME/.ssh/agent-deploy-ci}"
# A key that is already authorised, used once to install the deploy key.
ADMIN_KEY="${ADMIN_KEY:-$HOME/.ssh/jarvislabs}"
RESUME=1
[ "${1:-}" = "--no-resume" ] && RESUME=0

need() { command -v "$1" >/dev/null || { echo "FATAL: $1 is not installed."; exit 1; }; }
need jl
need gh
need ssh-keyscan
need python3

gh auth status >/dev/null 2>&1 || { echo "FATAL: gh is not authenticated. Run: gh auth login"; exit 1; }

# Reads one field for the named instance out of `jl list --json`.
field() {
  jl list --json 2>/dev/null | python3 -c "
import json, sys
name, key = sys.argv[1], sys.argv[2]
for row in json.load(sys.stdin):
    if row.get('name') == name:
        print(row.get(key) or '')
        break
" "$INSTANCE_NAME" "$1"
}

id="$(field machine_id)"
[ -n "$id" ] || { echo "FATAL: no instance named '$INSTANCE_NAME'. Check: jl list"; exit 1; }
status="$(field status)"
echo "instance : $INSTANCE_NAME (id $id, $status)"

if [ "$status" != "Running" ]; then
  [ "$RESUME" -eq 1 ] || { echo "FATAL: instance is $status and --no-resume was given."; exit 1; }
  echo "resuming (this issues a new id and a new IP)..."
  jl resume "$id" --yes >/dev/null
  # The id changes on resume, so everything below re-reads it by name.
  for _ in $(seq 1 60); do
    [ "$(field status)" = "Running" ] && break
    sleep 10
  done
  id="$(field machine_id)"
  [ "$(field status)" = "Running" ] || { echo "FATAL: instance did not reach Running."; exit 1; }
  echo "resumed   : id $id"
fi

# `ssh_command` looks like: ssh -o StrictHostKeyChecking=no ubuntu@1.2.3.4
host="$(field ssh_command | tr ' ' '\n' | grep '@' | cut -d@ -f2)"
[ -n "$host" ] || { echo "FATAL: could not read a host from the instance's ssh_command."; exit 1; }
echo "host     : $host"

# A resumed instance is a NEW machine that can reuse the previous IP, so the
# local known_hosts entry is stale and every ssh call fails with
# REMOTE HOST IDENTIFICATION HAS CHANGED. Drop it before reconnecting.
ssh-keygen -R "$host" >/dev/null 2>&1 || true

echo -n "waiting for sshd"
ready=0
for _ in $(seq 1 60); do
  if ssh-keyscan -T 5 "$host" >/dev/null 2>&1; then ready=1; break; fi
  echo -n "."
  sleep 10
done
echo
[ "$ready" -eq 1 ] || { echo "FATAL: sshd on $host never answered."; exit 1; }

# Install the deploy key's public half, so the CI job can log in to THIS
# instance. Idempotent, and skipped if either key is missing.
if [ -f "$DEPLOY_KEY.pub" ] && [ -f "$ADMIN_KEY" ]; then
  pub="$(cat "$DEPLOY_KEY.pub")"
  if ssh -o StrictHostKeyChecking=accept-new -o BatchMode=yes -i "$ADMIN_KEY" \
       "$SSH_USER@$host" "
         mkdir -p ~/.ssh && chmod 700 ~/.ssh
         grep -qF '$pub' ~/.ssh/authorized_keys 2>/dev/null \
           || echo '$pub' >> ~/.ssh/authorized_keys
         chmod 600 ~/.ssh/authorized_keys" >/dev/null 2>&1; then
    echo "deploy key installed on the instance"
  else
    echo "WARNING: could not install the deploy key using $ADMIN_KEY."
    echo "         The deploy job will fail to authenticate."
  fi
fi

# Pinned host key, so the deploy job cannot be man-in-the-middled into
# handing its private key to someone else.
keys="$(ssh-keyscan -H "$host" 2>/dev/null)"
[ -n "$keys" ] || { echo "FATAL: ssh-keyscan returned nothing for $host."; exit 1; }

gh secret set GPU_HOST     --body "$host"
gh secret set GPU_USER     --body "$SSH_USER"
printf '%s\n' "$keys" | gh secret set GPU_HOST_KEY

echo
echo "secrets now set:"
gh secret list | sed 's/^/  /'
echo
if gh secret list | grep -q '^GPU_SSH_KEY'; then
  echo "GPU_SSH_KEY is present (left untouched)."
else
  echo "GPU_SSH_KEY is NOT set. The deploy job cannot authenticate without it:"
  echo "  ssh-keygen -t ed25519 -f ~/.ssh/agent-deploy-ci -N ''"
  echo "  # add ~/.ssh/agent-deploy-ci.pub to JarvisLabs, then:"
  echo "  gh secret set GPU_SSH_KEY < ~/.ssh/agent-deploy-ci"
fi
echo
echo "Instance $id is RUNNING and billing. Pause it when you are done:"
echo "  jl pause $id --yes"
