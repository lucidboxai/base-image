#!/bin/bash

# Store environment variables so they can be used by supervisor processes
key="$1"
value="$(printenv $1)"
code=$?

if [[ -z $key ]]; then
    printf "Usage: env-store key\n"
    exit 1
fi

if [[ $code -ne 0 ]]; then
    printf "Could not store key: %s\n" "$key"
    exit 1
fi

printf "export %s=\'%s\'\n" "${key}" "${value}" >> /opt/ai-dock/etc/environment.sh
# Name only: init stores EVERY variable in the environment, so echoing values
# puts API tokens and passwords into the container log. The name alone is what
# makes this line useful for debugging.
printf "Stored environment variable '%s'\n" "$key"