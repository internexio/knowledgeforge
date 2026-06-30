---
title: REST client tolerance — distinguish 200 OK (soft success) from 201 Created (resource insertion)
source_mode: direct
novelty_type: new_pattern
grounding_score: 0.75
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-15
tags: rest-api, http-status-codes, client-design, integration-patterns, error-handling
related_entries: []
domain: patterns
topic: retrieval
---

# REST client tolerance — 200 OK ≠ 201 Created ≠ failure

## The trap

A REST POST endpoint typically returns:

- **201 Created** when a new resource is inserted (with the resource ID in the body).
- **200 OK** when the request was accepted but **no new resource was created** — e.g., because the request was a deduplicated retry, the resource was filtered out by policy, or the request hit a soft-rate-limit or daily cap.
- **400 / 4xx** for validation failures.
- **5xx** for server errors.

A client that treats "200 OK" identically to "anything except 201" — i.e., as a failure — will log every soft-success as an error and bury real signal in alarm-fatigue. The server is healthy. The client is wrong.

## Concrete trigger ([project], 2026-05-15)

`scripts/karma-scan.sh` on Mac Mini was generating ~17 "Failed HTTP 200" log lines per hourly run for weeks. The log message was self-contradictory (HTTP 200 = success) — a tell that the client's classifier was wrong.

The server (`reddit-monitor-ui.py`'s `/api/ingest`) returns:

```python
# Blocked subreddit (allow-list filter)
return jsonify({"id": None, "status": "blocked", "reason": "subreddit_blocked"}), 200

# Daily karma_building cap hit (20/day max)
return jsonify({"id": None, "status": "capped", "reason": "karma_building_daily_cap"}), 200

# Real insert
return jsonify({"id": task_id, "status": "pending"}), 201
```

`karma-scan.sh` was treating anything ≠ 201 as failure:

```bash
if [ "$HTTP_CODE" = "201" ]; then
    log "INFO" "Submitted [${ks}] r/${sub}"
    SUBMITTED=$((SUBMITTED + 1))
else
    log "ERROR" "Failed HTTP ${HTTP_CODE} for r/${sub}"
    ERRORS=$((ERRORS + 1))
fi
```

So every cap-hit and every blocked-subreddit response was a "Failed HTTP 200 for r/sales" alarm in the log. 20 inserts + 17 soft-skips per hour = 17 false-failures per hour, week after week.

## The fix

Branch on the HTTP code with explicit success-set handling and capture the response body so you can surface the *reason* for soft-success:

```bash
RESPONSE_BODY=$(mktemp)
HTTP_CODE=$(curl -s -o "$RESPONSE_BODY" -w "%{http_code}" \
    -X POST "$API" -H "Content-Type: application/json" -d "$payload" 2>/dev/null || echo "000")

case "$HTTP_CODE" in
    201)
        log "INFO" "Inserted [${id}]"
        SUBMITTED=$((SUBMITTED + 1))
        ;;
    200)
        reason=$(jq -r '.reason // .status // "ok"' "$RESPONSE_BODY" 2>/dev/null)
        log "INFO" "Skipped (${reason})"
        SKIPPED=$((SKIPPED + 1))
        ;;
    *)
        log "ERROR" "Failed HTTP ${HTTP_CODE}"
        ERRORS=$((ERRORS + 1))
        ;;
esac
rm -f "$RESPONSE_BODY"
```

Update the summary line to include `SKIPPED` so daily-cap saturation or block-list hits are visible without grepping individual entries.

## The general rule

A REST client should classify responses into at least three buckets:

| Bucket | Codes | Behaviour |
|--------|-------|-----------|
| Real success (new state) | 201 Created, 202 Accepted | Increment success counter; record resource ID |
| Soft success (no new state, but request was acknowledged) | 200 OK, 204 No Content, 304 Not Modified | Increment a separate "skipped" counter; surface reason from response body |
| Client error | 4xx | Log with the validation message; don't retry indefinitely |
| Server error | 5xx, 0 (connectivity) | Retry with backoff; alert on sustained failure |

The exact codes vary by service; **read the server's source or docs** rather than guessing. The pattern matters more than the specific status codes.

## When This Applies

- Building a client that consumes a POST / PUT / PATCH endpoint where the server can legitimately return 200 instead of 201 (soft-rate-limit, policy filter, deduplication, cap hit).
- Debugging alarm fatigue from HTTP status code misclassification.
- Any integration where observability (knowing *why* a request succeeded without creating new state) matters more than raw success/failure.

## When This Does NOT Apply

- The endpoint guarantees 201 for every legitimate success and there's no soft-success path (rare; most production endpoints grow soft-success paths over time as policy filters are added).
- The client genuinely wants to fail on no-new-resource — e.g., an idempotency check that *requires* a new ID. Even then, error vs. skip categorisation should be explicit.

## Source Context

Discovered during [project] morning-loop foundation work (2026-05-15). `scripts/karma-scan.sh` was treating every soft-rate-limit and policy-filter response as a failure, generating 17 false-error logs per hourly run. Fix shipped in commit `66d9baa` with verified end-to-end validation on Mac Mini: after a daily-cap-saturated run, the script now reports `Done: 0 submitted, 34 skipped, 0 errors` correctly.

## Related patterns

- **Postel's law** (RFC 1122): "Be liberal in what you accept" — the client side. This entry is a concrete instance.
- **Distinguishing skipped-by-policy from failed-by-error** is the underlying observability principle. Same shape applies to job queues (dropped vs failed), database upserts (inserted vs unchanged), and rate-limited APIs (throttled vs erred).
