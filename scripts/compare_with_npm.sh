#!/usr/bin/env sh
# Stages 4-5. Compare generated graph with npm's installed dependency tree.
# npm is NOT used by the implementation to obtain dependency information.
set -eu
cd "$(dirname "$0")/.."
package="${1:-is-odd}"
echo "=== Our analyzer ==="
./run.sh --package "$package" --repository https://registry.npmjs.org \
    --max-depth 10
echo "=== npm view: direct dependencies ==="
npm view "$package" dependencies --json
echo "=== npm ls: actual installed dependency graph ==="
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
printf '{"name":"dependency-comparison","version":"1.0.0","private":true}\n' > "$tmp/package.json"
npm install --prefix "$tmp" --save --ignore-scripts --no-audit --no-fund "$package"
npm ls --prefix "$tmp" --all
