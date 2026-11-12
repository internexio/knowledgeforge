#!/bin/sh
# build_fixture.sh DIR : build the shared canary fixture repo; prints the base SHA on the last line.
set -eu
DIR="$1"
mkdir -p "$DIR"
cd "$DIR"
git init -q -b main 2>/dev/null || git init -q
git config user.email canary@example.invalid
git config user.name canary
for d in a b c d e; do
  mkdir -p "tools/$d"
  printf 'export function render(){ return "Try again tomorrow"; }\n' > "tools/$d/analyzer.js"
done
mkdir -p tests site
printf 'exit 0\n' > tests/test_smoke.sh
printf '{"name":"fixture","scripts":{"test":"sh tests/test_smoke.sh"}}\n' > package.json
for p in index pricing tools; do
  printf '<!doctype html><html><body><h1>%s</h1></body></html>\n' "$p" > "site/$p.html"
done
git add -A
git commit -q -m base
git rev-parse HEAD
