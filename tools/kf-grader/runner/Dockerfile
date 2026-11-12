# kf-grader-runner: disposable container for command ACs and test_command. Built once on the grader host:
#   docker build -t kf-grader-runner tools/kf-grader/runner
# The runner starts it with --network none, read-only source mount, --user 65534, --cap-drop ALL, tmpfs /work.
FROM node:22-bookworm-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ripgrep python3 jq ca-certificates \
 && rm -rf /var/lib/apt/lists/*
USER 65534:65534
WORKDIR /work
