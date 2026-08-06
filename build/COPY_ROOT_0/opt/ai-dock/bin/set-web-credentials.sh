#!/bin/bash

if [[ -z $2 ]]; then
    printf "Usage: set-web-credentials.sh username password\n"
    exit 1
fi

export WEB_USER=$1
env-store WEB_USER
export WEB_PASSWORD=$2
env-store WEB_PASSWORD
# -w 0: a long user:password would otherwise wrap and embed a newline.
export WEB_PASSWORD_B64="$(printf "%s:%s" "$WEB_USER" "$WEB_PASSWORD" | base64 -w 0)"
env-store WEB_PASSWORD_B64
# Sessions carry WEB_TOKEN, not a password-derived value, so rotate it here too
# — otherwise cookies issued under the old password would survive the change.
export WEB_TOKEN="$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)"
env-store WEB_TOKEN

printf "Setting credentials and restarting proxy server...\n"

supervisorctl restart serviceportal
supervisorctl restart caddy
