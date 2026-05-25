#!/usr/bin/env bash
# Wrapper: gitagent invokes hooks via sh regardless of runtime declaration.
# This shell script passes stdin → python3 → stdout.
exec python3 "$(dirname "$0")/load_memory_namespace.py" "$@"
