---
title: Google Ads Editor .aes Schema Inference from Sampled Elements
source_mode: builder
novelty_type: reusable_diagnostic
grounding_score: 0.75
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-11
domain: integration
topic: external-tools
tags: api, empirical
related_entries: []
---

# Google Ads Editor .aes Schema Inference from Sampled Elements

## Context

Google Ads Editor supports importing change files in .aes format (zip archive containing data.xml). The XML follows a v2.2 schema. Not all entity element types are documented publicly or easily sampled — you only see the schema when you export a specific type of change from a live account.

## Pattern

When an AES entity element type has NOT been sampled from a real Editor export, its XML structure can be inferred with high confidence from already-sampled elements using the **{kind} / {kind}-data naming convention**:

```
Sampled <geotarget>:
  <geotarget operation="add">
    <geotarget-data>
      <locationPath>United States - Washington - Seattle - 98101</locationPath>
      <bidModifier>+25%</bidModifier>
    </geotarget-data>
  </geotarget>

Inferred <geotargetnegative> (exclusion, no bid modifier):
  <geotargetnegative operation="add">
    <geotargetnegative-data>
      <locationPath>United States - Washington - Seattle - 98101</locationPath>
    </geotargetnegative-data>
  </geotargetnegative>
```

The pattern:
1. The root element name is the kind name (e.g., `geotargetnegative`)
2. The child data container follows `{kind}-data` (e.g., `geotargetnegative-data`)
3. Scalar field names are camelCase within the data container (e.g., `locationPath`, `bidModifier`)
4. `operation="add"` is the attribute on the root element

The AES renderer (aes.py in client-project) maps `kind` values to collection wrapper element names via `_COLLECTION_FOR_KIND`. Collection wrappers pluralize the kind name (e.g., `geotarget` → `geotargets`, `geotargetnegative` → `geotargetnegatives`).

## When This Applies

- Building a new AES exporter for an entity type not yet sampled
- A related entity type has already been sampled (same schema family)
- The risk of a schema mismatch is acceptable (Editor will surface an error on import rather than silently misfiring — operator sees the rejection and can provide feedback)

## When This Does NOT Apply

- Entity types with no known-sampled relative (e.g., the first entity type in a new schema family)
- When the schema inference would affect high-volume automated imports (manual operator review is required as the quality gate)
- When exact schema conformance is required before any operator testing

## Concrete Grounding

Applied 2026-07-10 in client-project sa-ltx bead: inferred `<geotargetnegative>` structure from the existing `<geotarget>` sample in exports/geo_target.py. The AES renderer already had `"geotarget_negative" → "geotargetnegatives"` mapped in `_COLLECTION_FOR_KIND`, confirming the naming convention was already understood at the renderer level. The inferred structure was implemented in `exports/geo_negative.py` and tested with 20 unit tests including AES round-trip tests verifying the XML structure parses correctly.

## Risk Mitigation

Document the inference in the module docstring clearly ("Schema inference note") so future maintainers know to validate against a real AES sample when one becomes available. Include a note that Editor will prompt the operator on import rather than silently accepting a wrong schema.

## Source Context

Surfaced during client-project sa-ltx (ZIP geo-targeting export Part A) session. The pattern captures a reusable diagnostic for inferring undocumented XML schemas from documented siblings, applicable to any versioned XML export format with structural naming conventions.
