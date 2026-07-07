# COS Profile Schemas — Captured for Calibrator Integration

**Captured:** 2026-07-07  
**Source:** Live calls to `mcp__cos-mcp__profile_agent` and `mcp__cos-mcp__audience_profile`  
**Purpose:** Schema stability reference for Calibrator Module 11 comms-project detection + artifact emit (cos-bej7)  
**Version stamp:** COS MCP as of 2026-07-07 — re-capture if COS schema changes

---

## 1. `profile_agent` — Output Schema

Call: `profile_agent(agent_name, samples[])` — analyzes 1-10 writing samples to infer author personality.

```json
{
  "agent_name": "string",
  "ocean_traits": {
    "openness":          { "score": 0.0–1.0, "evidence": "string" },
    "conscientiousness": { "score": 0.0–1.0, "evidence": "string" },
    "extraversion":      { "score": 0.0–1.0, "evidence": "string" },
    "agreeableness":     { "score": 0.0–1.0, "evidence": "string" },
    "neuroticism":       { "score": 0.0–1.0, "evidence": "string" }
  },
  "style_label": "string",
  "strengths":   ["string"],
  "blind_spots": ["string"],
  "persuasion_profile": {
    "attention_hooks":       ["string"],
    "trust_builders":        ["string"],
    "turn_offs":             ["string"],
    "effective_principles":  ["string"]
  },
  "overall_score": 0.0–10.0,
  "summary":       "string",
  "sample_count":  1
}
```

### Key fields for Calibrator emit

| Field | Use in Calibrator artifact |
|-------|---------------------------|
| `agent_name` | Project/team name from calibration interview |
| `ocean_traits.*.score` | Primary trait scores → drives comms style guidance |
| `style_label` | Human-readable label for the COS `.profile` file |
| `strengths` | Positive communication patterns to reinforce |
| `blind_spots` | Communication gaps to flag in calibration warnings |
| `persuasion_profile.effective_principles` | Cialdini-based principles for outbound messaging |
| `summary` | Long-form interpretation → embed in generated CLAUDE.md comms section |

---

## 2. `audience_profile` — Output Schema

Call: `audience_profile(audience_description, campaign_objective, domain)` — maps free-text description to OCEAN profile.

```json
{
  "ocean_scores": {
    "openness":          0.0–1.0,
    "conscientiousness": 0.0–1.0,
    "extraversion":      0.0–1.0,
    "agreeableness":     0.0–1.0,
    "neuroticism":       0.0–1.0
  },
  "ocean_confidence": 0.0–1.0,
  "elm_route": "central" | "peripheral" | "mixed",
  "dominant_traits":   ["string"],
  "trait_rationale":   "string",
  "dominant_moral_foundations": ["string"],
  "vulnerability_flags":         ["string"],
  "recommended_persuasion_principle": "string",
  "persuasion_rationale": "string"
}
```

### Key fields for Calibrator emit

| Field | Use in Calibrator artifact |
|-------|---------------------------|
| `ocean_scores` | Target audience OCEAN → drives message tailoring guidance |
| `ocean_confidence` | Emit warning in artifact if < 0.6 |
| `elm_route` | Central = logic-driven copy; Peripheral = social-proof/heuristics; Mixed = both |
| `dominant_traits` | Short list for artifact header |
| `recommended_persuasion_principle` | Cialdini principle to lead with |
| `vulnerability_flags` | Safety flags — if non-empty, add ethics-review note to artifact |
| `dominant_moral_foundations` | MFT framing for message tone |

---

## 3. Calibrator Artifact Emit Format (Proposed)

When Calibrator detects a comms-heavy project, it emits two companion files alongside `CLAUDE.md`:

### `cos-agent-profile.json`
Maps to `profile_agent` output — describes the **writer/agent** personality:

```json
{
  "_schema": "cos-agent-profile/v1",
  "_generated_by": "kf-calibrator",
  "_captured": "ISO-8601",
  "project": "string",
  "agent_name": "string",
  "ocean_traits": { /* profile_agent.ocean_traits */ },
  "style_label": "string",
  "strengths": [],
  "blind_spots": [],
  "persuasion_profile": { /* profile_agent.persuasion_profile */ },
  "summary": "string"
}
```

### `cos-audience-profile.json`
Maps to `audience_profile` output — describes the **target audience**:

```json
{
  "_schema": "cos-audience-profile/v1",
  "_generated_by": "kf-calibrator",
  "_captured": "ISO-8601",
  "audience_description": "string",
  "ocean_scores": { /* audience_profile.ocean_scores */ },
  "ocean_confidence": 0.0,
  "elm_route": "central|peripheral|mixed",
  "dominant_traits": [],
  "dominant_moral_foundations": [],
  "vulnerability_flags": [],
  "recommended_persuasion_principle": "string",
  "persuasion_rationale": "string"
}
```

Both files reference each other via a `_paired_with` field and cross-reference the generating `CLAUDE.md`.

---

## 4. Comms-Heavy Detection Heuristics (for Module 11)

Ordered by reliability (highest signal first):

1. **Interview answer** — explicit "comms / marketing / content" as primary domain
2. **Directory presence** — `content/`, `copy/`, `campaigns/`, `newsletters/`, `emails/` dirs
3. **File patterns** — `*.md` > 40% of tracked files, presence of `ghost/`, `substack/`
4. **`package.json` signals** — `@sendgrid`, `nodemailer`, `mailchimp`, `brevo` deps
5. **No primary code signal** — no `src/`, no `app/`, no `*.py`/`*.ts`/`*.go` majority

Threshold: 2+ signals → comms-heavy. Mixed (comms + code) → dual-emit (both `CLAUDE.md` and COS profiles).

---

## 5. Schema Stability Notes

- `profile_agent` — fields stable since COS v1.0; `persuasion_profile.effective_principles` added mid-2025
- `audience_profile` — `vulnerability_flags` field was `[]` in this capture; non-empty for health/politics domains
- `ocean_confidence` < 0.6 → add a `⚠️ Low confidence` note in the emitted artifact header
- Re-capture schemas when COS MCP version bumps to avoid field drift
