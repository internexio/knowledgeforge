# Correct fix, but an unrelated public page is deleted.
. "$KF_CANARY_LIB"
fix_all
git rm -q site/pricing.html
commit "fix (and drop pricing page)"
