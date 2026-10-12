#!/usr/bin/env bash

usage() {
    echo "Использование: ./report.sh <каталог> <ERROR|WARN> [--top N]" >&2
    exit 1
}

if [[ $# -ne 2 && $# -ne 4 ]]; then
    usage
fi

DATA_DIR="$1"
LEVEL="$2"

if [[ "$LEVEL" != "ERROR" && "$LEVEL" != "WARN" ]]; then
    usage
fi

if [[ ! -d "$DATA_DIR" ]]; then
    usage
fi

TOP=""

if [[ $# -eq 4 ]]; then
    if [[ "$3" != "--top" ]]; then
        usage
    fi

    if ! [[ "$4" =~ ^[0-9]+$ ]]; then
        usage
    fi

    TOP="$4"
fi

echo "module        count"

result=$(
    awk -v level="$LEVEL" '
        $3 == level {
            module = $4
            sub(/^module=/, "", module)
            count[module]++
        }
        END {
            for (module in count) {
                print module, count[module]
            }
        }
    ' "$DATA_DIR"/*.log | sort -k2,2nr
)

if [[ -n "$TOP" ]]; then
    printf '%s\n' "$result" | head -n "$TOP"
else
    printf '%s\n' "$result"
fi
