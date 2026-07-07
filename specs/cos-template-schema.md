# COS Template Schema — Captured for Synthesizer Integration

**Captured:** 2026-07-07  
**Source:** Live calls to `mcp__cos-mcp__get_templates` (14 templates) + `mcp__cos-mcp__get_template_details` (combo_analyzer)  
**Purpose:** Schema stability reference for Synthesizer Module 08 comms-pattern → COS template emit (cos-rmqq)  
**Version stamp:** COS MCP as of 2026-07-07. Total templates in system: 14. Re-capture if COS schema changes.

---

## 1. COS Template JSON Schema

Both `get_templates` and `get_template_details` return identical objects. No hidden fields.

```json
{
  "id":          "string",        // slug: kebab-case, e.g. "combo_analyzer"
  "name":        "string",        // Human title, e.g. "HAPE + Big Five Combo Analyzer"
  "description": "string",        // One-sentence summary shown in template picker
  "category":    "string",        // See categories below
  "tags":        ["string"],       // Free-form but conventionally from known set
  "variables": [
    {
      "name":        "string",        // Python identifier, used in Jinja2 as {{ name }}
      "label":       "string",        // UI label
      "type":        "textarea|select|text|url",
      "required":    true|false,
      "placeholder": "string|null",
      "help_text":   "string|null",
      "options":     null | [
        {"label": "string", "value": "string"},
        // OR a bare string (select items without label/value split)
      ]
    }
  ],
  "knowledge_modules": ["string"],   // COS module refs (see §4)
  "template":    "string",           // Jinja2 template body (see §3)
  "scoring": {
    "dimensions": [
      {"name": "string", "weight": 0.0–1.0}  // weights sum to 1.0
    ]
  }
}
```

---

## 2. Known Categories (exhaustive as of capture)

| Category    | Description                              | Example templates |
|-------------|------------------------------------------|-------------------|
| `framing`   | Sovereign Mind / authority-empowerment   | message_framing_transformer, autonomy_authority_analyzer |
| `engagement`| HAPE, Big Five, emotional impact         | combo_analyzer, emotional_impact_analyzer |
| `audience`  | Personality profiling, targeting         | audience_personality_profiler |
| `outreach`  | Cold email, LinkedIn, follow-up          | cold_outreach_optimizer, email_optimizer |
| `clarity`   | Brand, positioning, website, LinkedIn    | brand_guidelines_checker, website_positioning_audit, pitch_deck_analysis, linkedin_profile_audit |
| `quick`     | Fast single-purpose tools                | roast_my_content, will_this_land |

---

## 3. Template Body Conventions (Jinja2)

Templates use standard Jinja2:
- `{{ variable_name }}` — insert variable value
- `{% if variable %} ... {% endif %}` — conditional block
- `{% elif condition %}` — branch
- `{{ variable | title }}` — filter (capitalize)

**Structure pattern observed across 14 templates:**

```jinja2
[SECTION HEADER / UPPERCASE TITLE]

--- [PRIMARY INPUT LABEL] ---
{{ content }}
--- END [LABEL] ---

[Supporting variables as labeled lines]

## [Analysis Section 1]

[Instructions for LLM to analyze / output structured content]

## [Analysis Section 2]

{% if optional_variable %}
[Conditional extra analysis block]
{% endif %}

## [Output / Recommendations / Rewrite]

[Final deliverable section]

## [Score]

- [Dimension 1]: X/10
- [Dimension 2]: X/10
- **Overall**: X/10
```

**Constant template pattern:** Every template ends with a scored output section. The `scoring.dimensions` array matches what appears in the final section.

---

## 4. Known Knowledge Module IDs

Referenced across the 14 captured templates:

```
01_EngagementPsychology
01_ContentAnalysis
01_AudienceProfiler
01_FrameMapping
02_BigFive_Foundation
02_BigFive_Persuasion
02_BigFive_Reframing
03_Business_PersuasionFrameworks
03_Masculinity_ReframingPatterns
04_FramingStrategy_Implementation
04_VoiceTone_PersonalityMapping
04_EngagementProtocols_Ethical
05_Platform_Optimization
05_Platform_Constraints
06_Quality_Assurance
```

Pattern: `NN_ModuleName` — two-digit prefix groups related modules.

---

## 5. Synthesizer → COS Template Field Mapping

When a KF Synthesizer pattern is comms-domain, the emitted COS template is derived from the `pattern_framework_output` (6.6.1) and the standard synthesis markdown output.

| COS template field | Derived from Synthesizer output |
|--------------------|-------------------------------|
| `id` | `slugify(pattern_name)` — kebab-case |
| `name` | `pattern_name` (verbatim from synthesis) |
| `description` | First sentence of `unifying_framework.core_principle` |
| `category` | Map from KF domain/topic: see §6 |
| `tags` | KF pattern tags + comms-domain inferral tags |
| `variables` | `content` (textarea, required) + pattern-specific inputs derived from `variation_points` |
| `knowledge_modules` | Map from KF modules used in synthesis (see §7) |
| `template` | Generated Jinja2 from synthesis `response_pattern`: header + `{{ content }}` block + analysis sections derived from pattern structure + score block derived from quality gates |
| `scoring.dimensions` | Derived from pattern's `quality_gates` / `applicability` criteria |

---

## 6. KF Domain → COS Category Mapping

| KF domain / topic | COS category |
|-------------------|--------------|
| `communication`, `outreach`, `sales-copy` | `outreach` |
| `framing`, `positioning`, `authority`, `autonomy` | `framing` |
| `audience-analysis`, `profiling`, `persona` | `audience` |
| `engagement`, `emotional-impact`, `HAPE`, `personality` | `engagement` |
| `brand`, `clarity`, `website`, `pitch` | `clarity` |
| Short diagnostic / single-concept patterns | `quick` |
| Unknown / mixed | `engagement` (default) |

---

## 7. KF Module → COS knowledge_module Mapping (Proposed)

| KF module context | Suggested COS module ref |
|-------------------|--------------------------|
| OCEAN / Big Five analysis | `02_BigFive_Foundation` |
| Framing / frame analysis | `01_FrameMapping` + `04_FramingStrategy_Implementation` |
| HAPE / engagement scoring | `01_EngagementPsychology` |
| Audience profiling | `01_AudienceProfiler` |
| Business persuasion | `03_Business_PersuasionFrameworks` |
| Platform optimization | `05_Platform_Optimization` |
| Quality / QA | `06_Quality_Assurance` |
| Voice/tone calibration | `04_VoiceTone_PersonalityMapping` |

---

## 8. Comms-Domain Detection for Synthesizer (proposed, mirroring §5 of cos-profile-schemas.md)

A Synthesizer synthesis result is comms-domain when ≥1 of:

1. `synthesis_goal` or topic includes: `communication`, `framing`, `outreach`, `persuasion`, `content`, `messaging`, `audience`, `engagement`, `brand`, `copy`
2. KF domain field is `communication`, `marketing`, or `psychology-communications`
3. ≥2 of the source examples are marketing/comms artifacts (emails, posts, pitches, landing pages)
4. Extracted patterns explicitly describe human-to-human influence, persuasion, or communication dynamics

Non-comms signals that should NOT trigger emit: agent architectures, code patterns, infra patterns, data models, coordination protocols — even if they involve "messaging" in the technical sense.

---

## 9. Emit Trigger Logic for Module 08

```
IF synthesis_is_comms_domain (§8)
  AND pattern_has_at_least_2_examples
  AND pattern_confidence >= 0.6        # below this → surface with caveat, don't auto-emit
THEN
  EMIT cos-template artifact
  EMIT standard KF wiki entry (existing behavior — unchanged)
ELSE
  EMIT standard KF wiki entry only
```

COS MCP unavailable at emit time → emit wiki entry, log `COS template emit skipped: MCP unavailable`, surface note to user.

---

## 10. Schema Stability Notes

- All 14 captured templates confirm the schema above is consistent — no template-level extensions
- `options` field: most `select` types use `[{"label": ..., "value": ...}]`; one template uses bare string list (legacy? safe to always use label/value form in emitted templates)
- `scoring.dimensions` weights always sum to 1.0 across all 14 templates
- `knowledge_modules` are not validated client-side — safe to use proposed mapping from §7 without breakage risk
- Re-capture after any COS MCP version bump (check `get_templates` total count; 14 as of this capture)
