---
title: UNHEX() as shell-safe MySQL injection for complex string values
source_mode: debugger → builder
novelty_type: reusable_diagnostic
grounding_score: 0.90
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-29
domain: diagnostics
topic: error-handling
tags: api, deployment, quality-gate, empirical
related_entries: []
---

# UNHEX() as shell-safe MySQL injection for complex string values

## Problem

When injecting a string value into MySQL via the shell-mediated mysql CLI (including `docker exec ... mysql`), values containing any of the following cause silent corruption or syntax errors:

- Backticks (`` ` ``) — interpreted by bash/zsh as command substitution
- Curly braces (`{}`) — zsh brace expansion
- Angle brackets (`<`, `>`) — shell redirection
- Single quotes (`'`) — heredoc quoting issues
- JSON content — combines all of the above

Parameterized queries via pymysql/mysql2/etc. are the correct solution when a language runtime is available. But when you're forced into the mysql CLI (e.g., `docker exec ghost-mysql-1 mysql ...`), all standard quoting approaches fail with complex content.

## Solution Pattern

Convert the value to its hex representation, write it to a `.sql` file locally, copy to the container, and use `UNHEX()` in the SQL:

```python
# Generate the SQL file locally (no shell issues — pure Python)
value = "complex string with <tags>, 'quotes', {braces}, `backticks`"
hex_val = value.encode("utf-8").hex().upper()

sql = (
    "UPDATE settings SET value = CONCAT(value, UNHEX('" + hex_val + "')), "
    "updated_at = UTC_TIMESTAMP() "
    "WHERE `key` = 'codeinjection_head';\n"
)

with open("/tmp/update.sql", "w") as f:
    f.write(sql)
```

Then deploy:

```bash
docker cp /tmp/update.sql ghost-mysql-1:/tmp/update.sql
docker exec ghost-mysql-1 bash -c \
  "mysql -u ghost -p<password> ghost_production < /tmp/update.sql 2>&1"
```

`UNHEX()` decodes the hex literal on the MySQL server side — no shell interpretation, no quoting, no encoding ambiguity. The hex string itself is pure `[0-9A-F]` characters.

## Key Details

- **Encoding:** `str.encode("utf-8").hex().upper()` produces the hex. MySQL's `UNHEX()` accepts lowercase too but uppercase is conventional.
- **CONCAT vs full replacement:** Use `CONCAT(value, UNHEX(...))` to append; use `UNHEX(...)` directly to replace the entire value.
- **NULL safety:** `CONCAT(NULL, x)` returns NULL in MySQL. If the column could be NULL, use `CONCAT(COALESCE(value, ''), UNHEX(...))`.
- **Backtick column names:** The `key` column (reserved word in MySQL) still needs backtick quoting in the SQL file, but since the SQL file is written by Python (not a heredoc), backticks are literal — no shell interpretation.
- **File path approach:** Write SQL to a local temp file, scp or `docker cp` to target. This eliminates ALL heredoc + SSH expansion issues simultaneously.

## When to Use

- Forced to use mysql CLI (no language runtime with parameterized queries available)
- Value contains JSON, HTML, shell metacharacters
- Injecting into a Docker container's MySQL via `docker exec`
- SSH-mediated remote MySQL updates with complex content

## When NOT to Use

- If pymysql / mysql2 / any driver with parameterized queries is available — use `%s` parameters instead. That's the correct primary approach.
- For simple alphanumeric values — standard quoting works fine and is more readable.

## Session Grounding

Used 2026-07-29 to inject a SpeakableSpecification JSON-LD script tag into Ghost CMS's `codeinjection_head` setting via `docker exec ghost-mysql-1`. All prior attempts (heredoc, single-quote heredoc, embedded Python via SSH) failed due to shell expansion of `<script`, `{}` in JSON, and backticks in `WHERE \`key\``. UNHEX approach succeeded first try.

## When This Applies

Any shell-mediated MySQL interaction where the value contains metacharacters or JSON. The container boundary (docker exec) makes this particularly common.

## When This Does NOT Apply

When a client library (Python pymysql, Node mysql2, Ruby mysql2, etc.) is available in the calling runtime. Parameterized queries are always preferable.
