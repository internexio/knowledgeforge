# History rewrite: orphan branch so base_sha is not an ancestor of head.
. "$KF_CANARY_LIB"
git checkout -q --orphan rewritten
fix_all
git add -A
git commit -q -m "rewritten history"
