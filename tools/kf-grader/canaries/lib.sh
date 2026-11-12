# Shared helpers sourced by canary patches. cwd = fixture repo; $KF_BASE = base sha.
fix() { printf 'export function render(){ return "<div data-hook=\\"r3-conversion-cta\\"></div>"; }\n' > "tools/$1/analyzer.js"; }
fix_all() { for d in a b c d e; do fix "$d"; done; }
commit() { git add -A; git commit -q -m "$1"; }
