#!/usr/bin/env sh
# Stage 5: three different real npm packages; network access is required.
set -eu
cd "$(dirname "$0")/.."
mkdir -p output
for package in is-number is-odd is-even; do
    echo "=== Visualizing ${package} ==="
    ./run.sh --package "$package" --repository https://registry.npmjs.org \
        --max-depth 10 --output "output/${package}.d2"
done
printf '\nGenerated: output/is-number.d2, is-odd.d2, is-even.d2\n'
