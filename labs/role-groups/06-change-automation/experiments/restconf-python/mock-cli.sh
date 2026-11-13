#!/bin/sh
printf 'Synthetic IOS XE read-only CLI\n'
while IFS= read -r raw; do
  command_name="$(printf '%s' "$raw" | tr -d '\r')"
  case "$command_name" in
    "terminal length 0")
      ;;
    "show interfaces")
      cat /opt/mock/fixtures/show_interfaces.txt
      ;;
    "exit"|"quit")
      exit 0
      ;;
    "")
      ;;
    *)
      printf '%% Unknown command: %s\n' "$command_name"
      ;;
  esac
done
