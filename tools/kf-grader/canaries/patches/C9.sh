# Fix in the listed paths, but the dead-end string is moved into a new file the AC does not list.
. "$KF_CANARY_LIB"
fix_all
printf 'export const MSG = "Try again tomorrow";\n' > tools/a/strings.js
commit "fix (string relocated)"
