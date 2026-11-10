#!/usr/bin/env sh
# Stages 3–5: offline cases demonstrate chains, depth, filtering and cycles.
set -eu
cd "$(dirname "$0")/.."
./run.sh --package A --repository test_data/simple.json --test-mode --max-depth 3
./run.sh --package A --repository test_data/cycle.json --test-mode --max-depth 5
./run.sh --package A --repository test_data/deep.json --test-mode \
    --max-depth 2 --exclude C
