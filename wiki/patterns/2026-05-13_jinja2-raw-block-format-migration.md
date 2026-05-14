---
title: Jinja2 {% raw %} required when migrating .format() templates with literal curly braces
source_mode: direct
novelty_type: new_pattern
grounding_score: 0.9
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-13
tags: migration, jinja2, prompt-engineering, llm, escape-syntax
related_entries: []
---

# Jinja2 {% raw %} Required When Migrating .format() Templates with Literal Curly Braces

## What

Python's `str.format()` only consumes `{var}` substitutions; literal `{` and `}` characters anywhere else in the string pass through untouched. Jinja2 additionally parses `{{ }}` for variable substitution, `{% %}` for control flow, and `{# #}` for comments — all of which trigger a `TemplateSyntaxError` when present as literal text.

When migrating a Python `.format()` template to Jinja2, any literal curly braces in the source (typically JSON schema examples, regex character classes, set/dict literals shown to the model) must be wrapped in `{% raw %}...{% endraw %}` blocks — or Jinja2 will try to parse them and crash at template load.

## The Migration Recipe

For a template that has BOTH variable substitutions AND literal-brace sections:

```jinja2
{{ variable_name }}

Output JSON matching this schema:

{% raw %}
{
  "field": "value",
  "items": [{"x": 1}]
}
{% endraw %}
```

For a template that is ALL literal (no variables — e.g. a constant system prompt with a JSON schema example), the whole body can sit inside one `{% raw %}{% endraw %}` block.

## When This Applies

You are doing a CLAUDE.md "use Jinja2 from /prompts/"-style migration:
- moving an inline `_FOO_TEMPLATE.format(...)` string to a `.jinja2` file
- rendering via `Environment.get_template(...).render(...)`

The template contains any of:
- JSON schema examples with `{"foo": "bar"}` literal braces
- Regex character classes shown to the model: `[{a-z}]`
- Python dict/set literals shown as illustration
- Documentation of `f"{var}"` syntax (rare but possible)

## Concrete Grounding

DUP-L1 migration in `backend/app/buyers_committee/run_orchestrator.py` (cos-week4-audit-2026-05-13) moved five inline prompts to `backend/app/prompts/buyers_committee/`:

- `t1.jinja2`, `t2.jinja2`, `t3.jinja2` — variable-substituted persona prompts. No literal braces. Straight `{var}` → `{{ var }}` rewrite.
- `t4.jinja2` — judge model prompt. No variables, no literal braces. Trivial rewrite.
- `t5.jinja2` — blindspot auditor with a literal JSON schema example *inside* the prompt body. **Required wrapping the entire body in `{% raw %}...{% endraw %}`** because the schema example contained `{`, `}`, `"summary_md": ...` lines.

`api/buyers_committee.py` `_DEMO_SYSTEM_TEMPLATE` migrated to `demo_persona_react.jinja2` — variables only, no literals, simple.

## Verification

After migration, the system import path itself exercises the templates (the module loads them at import time when constants like `_T5_SYSTEM_PROMPT = render_bc_prompt("t5")` run). A `TemplateSyntaxError` at template load surfaces immediately as an ImportError in any test that imports the module. Running the existing test suite is sufficient — no special template-parsing test needed.

## When This Does NOT Apply

- Pure-variable migrations (no JSON / no regex character classes / no dict literals in the prompt body) — these convert one-to-one.
- Migrating in the other direction (Jinja2 → `.format()`): no special escaping needed; `{var}` is the only sigil `.format()` cares about.
- Templates that compute the JSON example via a Jinja2 variable (`{{ schema_example }}`) — the variable contents pass through literally, no raw block needed.

## Related Gotchas

**Companion gotcha:** trailing-newline divergence between Python triple-quoted strings and Jinja2's `keep_trailing_newline=False` default. When migrating, inspect both the original string's final character and the rendered template output to ensure newlines match expected behavior.
