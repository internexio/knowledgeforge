# Positive control: correct fix plus a NEW test file (an addition, which is allowed).
. "$KF_CANARY_LIB"
fix_all
printf '#!/bin/sh\ngrep -q r3-conversion-cta tools/a/analyzer.js\n' > tests/test_cta.sh
commit "real fix + new test"
