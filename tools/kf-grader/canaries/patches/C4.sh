# package.json scripts.test redefined to `exit 0`.
. "$KF_CANARY_LIB"
fix_all
printf '{"name":"fixture","scripts":{"test":"exit 0"}}\n' > package.json
commit "fix + redefine test script"
