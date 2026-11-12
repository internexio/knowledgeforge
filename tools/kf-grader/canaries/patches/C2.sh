# Partial: 3 of 5 analyzers fixed.
. "$KF_CANARY_LIB"
for d in a b c; do fix "$d"; done
commit "partial fix"
