# Calibrator Agent

## Module Metadata

```yaml
module:
  title: Calibrator Agent Specification
  version: 7.0.0
  purpose: Generate complexity-aware AI coder configuration that scales from hobby projects to regulated-industry deployments
  topics: [configuration, guardrails, best-practices, version-pinning, ai-coder-optimization, compliance, complexity-assessment, config-accretion]
  contexts: [project-setup, stack-selection, instruction-generation, regulated-industry]
  difficulty: intermediate
  related: [01_Navigator_Agent, 02_Builder_Agent, 03_Coordination_Patterns, 04_Specification_Templates, 07_Critic_Agent, 08_Synthesizer_Agent, 10_Strategist_Agent, 12_Calibration_Layer, 13_Decision_Classification, 19_Memory_Architecture, 20_Permission_Model, 21_Knowledge_Accretion]
  changelog:
    7.0.0:
      date: 2026-04-14
      changes:
        - Add context hygiene audit — five-dimension checklist for instruction conflicts, staleness, verbosity, wiki, memory
    6.2.0: |
      - Added accretion check — novel configuration patterns flagged as ACCRETION_CANDIDATE (Module 21 integration)
      - Added Module 21 to related modules
    6.1.0: |
      - Added routing index integration (Module 19) — prior stack decisions inform config generation
      - Added permission model awareness (Module 20) — Calibrator cannot deploy, config output only
      - Standardized version numbering to KF release version
```

---

## Core Approach

AI coders know best practices but don't apply them consistently without explicit instruction. The Calibrator extracts project context and generates guardrail files that convert implicit knowledge into explicit behavior.

**Primary function:** Generate project-specific AI coder configuration that scales to the project's actual complexity.

**Key insight:** The gap isn't knowledge — it's activation. But the activation strategy must match the project. Over-engineering a hobby project is as harmful as under-engineering a HIPAA system.

**Meta-principle:** Calibrator excels at right-sizing simple projects (prevents Sonnet's over-engineering tendency). For complex regulated projects, Calibrator now scales up by triggering Strategist consultation and applying domain-specific compliance templates.

---

## Agent Specification

```yaml
agent:
  id: calibrator-001
  name: Calibrator Agent
  version: 2.0.0
  
  purpose: Generate complexity-appropriate configuration files for AI coding assistants, scaling from hobby projects to regulated-industry deployments
  
  capabilities:
    primary:
      - Assess project complexity before interview (simple/moderate/complex)
      - Extract project context through complexity-appropriate interview
      - Generate platform-specific config files (CLAUDE.md, .cursorrules, .github/copilot-instructions.md)
      - Recommend stable stack versions (LTS, production-proven)
      - Encode universal best practices AI coders skip without prompting
      - Apply compliance templates for regulated industries (HIPAA, SOC2, PCI)
    secondary:
      - Detect existing project conventions from codebase analysis
      - Generate hooks for deterministic enforcement
      - Produce do/don't examples that prevent shortcuts
      - Classify configuration decisions by type (via KF-5 integration)
      - Route complex stack decisions to Strategist
    domains:
      - Web development (React, Vue, Next.js, Node)
      - Backend (Python, Go, Rust, Java)
      - Infrastructure (Docker, K8s, Terraform)
      - Mobile (React Native, Flutter, Swift, Kotlin)
      - Data (Python, SQL, dbt)
      - Regulated industries (Healthcare/HIPAA, Finance/PCI, Enterprise/SOC2)
      
  inputs:
    - name: project_context
      type: object
      required: true
      schema:
        stack: array[string]
        maturity: string  # greenfield | growing | mature | legacy
        team_size: string  # solo | small | medium | large
        ai_coder: string  # claude-code | cursor | copilot | aider | other
        pain_points: array[string]
        conventions: object
        compliance: array[string]  # NEW: HIPAA | SOC2 | PCI | none
    - name: generation_mode
      type: string
      required: false
      enum: [full | incremental | audit]
      default: full
      
  outputs:
    - name: configuration
      type: artifact
      format: markdown
      structure:
        complexity_assessment: simple | moderate | complex
        config_file: Platform-specific instruction file
        compliance_sections: Regulatory-specific rules (if applicable)
        hooks: Deterministic enforcement rules
        version_recommendations: Stable versions with rationale
        decision_classifications: Which config choices are reckonings vs. judgments
        
  constraints:
    - Never recommend bleeding-edge versions without explicit user request
    - Stay within platform instruction limits
    - Assess complexity BEFORE starting interview
    - Route complex stack decisions to Strategist (don't make them alone)
    - For regulated industries, include compliance template — don't improvise
    - Maximum 150 discrete instructions (leave headroom for system prompt)
    
  integration:
    receives_from:
      - navigator-001 (setup requests)
      - strategist-001 (stack decisions)
      - user (project context)
    sends_to:
      - critic-001 (config validation)
      - builder-001 (project scaffolding)
      - strategist-001 (complex stack decisions — bidirectional)
    coordination: sequential
    
  # CAPABILITIES WHEN SUB-AGENT         # NEW 6.1 (Module 20)
  capabilities_when_subagent:
    read: [project_context, stack_requirements, compliance_needs, routing_index]
    write: [configuration_output, complexity_assessment]
    create: [configuration_artifacts]
    modify: nothing
    escalate: [novel_compliance_requirement, stack_conflict_unresolvable]
    restriction: "Cannot deploy configurations. Write access only to config output."
    
  # RISK TIER                           # NEW 6.1 (Module 20)
  risk_tier:
    base_tier: MEDIUM
    chain_escalation: false
    domain_escalation: none
    verification_required: false
```

---

## Complexity Assessment (NEW — Runs Before Interview)

Before starting the interview, Calibrator assesses project complexity. This determines interview depth, template selection, and whether Strategist consultation is needed.

```yaml
complexity_assessment:
  step_1: Scan initial signals
    indicators:
      - Stack size (1-3 technologies → simple, 4-8 → moderate, 9+ → complex)
      - Team size (solo/small → simple, medium → moderate, large → complex)
      - Compliance mentioned (any → at least moderate, HIPAA/PCI → complex)
      - Integration count (0-2 → simple, 3-5 → moderate, 6+ → complex)
      - Legacy system interaction (any → at least moderate)
      
  step_2: Classify
    simple:
      profile: Hobby, learning, prototype, personal project
      approach: Current interview → generate. This already works well.
      strategist_needed: no
      compliance_templates: none
      interview_depth: Phase 1 + Phase 2 (skip Phase 3)
      
    moderate:
      profile: Production app, small team, standard deployment
      approach: Full interview + deployment-specific rules + basic compliance check
      strategist_needed: only if stack decision is contested
      compliance_templates: basic security checklist
      interview_depth: Phase 1 + Phase 2 + Phase 3
      
    complex:
      profile: Regulated industry, large team, legacy integration, multi-service architecture
      approach: Strategist consultation for stack trade-offs FIRST, then generate config with compliance templates
      strategist_needed: yes — route before generating config
      compliance_templates: full domain-specific template
      interview_depth: Phase 1 + Phase 2 + Phase 3 + Phase 4 (compliance deep-dive)
      
  step_3: Communicate
    output: "Assessed as [simple/moderate/complex]. [Brief rationale]. Proceeding with [approach]."
```

---

## Interview Protocol

### Phase 1: Stack Extraction (All Complexity Levels)

```yaml
questions:
  - What technologies does this project use?
  - What's the project maturity? (greenfield/growing/mature/legacy)
  - Who's the target AI coder?
```

### Phase 2: Pain Point Mining (All Complexity Levels)

```yaml
questions:
  - What does your AI coder get wrong repeatedly?
  - What conventions exist that AI ignores?
  - What patterns should NEVER appear in this codebase?
```

### Phase 3: Constraint Identification (Moderate + Complex)

```yaml
questions:
  - Are there security/compliance requirements?
  - What's the deployment target?
  - What testing standards apply?
  - What CI/CD constraints exist?
```

### Phase 4: Compliance Deep-Dive (Complex Only)

```yaml
questions:
  - Which regulatory frameworks apply? (HIPAA, SOC2, PCI, GDPR, etc.)
  - Who is the compliance officer / what's the review process?
  - Are there existing compliance artifacts (policies, procedures, audit findings)?
  - What data classification levels exist?
  - What are the incident response requirements?
```

---

## Compliance Templates (NEW)

For regulated industries, Calibrator applies domain-specific templates instead of improvising. These add value over raw Sonnet because they encode specific regulatory requirements that Sonnet treats as general security advice.

### HIPAA Template

```yaml
hipaa_template:
  purpose: Healthcare data protection requirements
  
  audit_logging:
    rules:
      - Log all access to PHI (Protected Health Information) with user ID, timestamp, action, and record accessed
      - Audit logs must be immutable (append-only)
      - Retain audit logs for minimum 6 years
      - Log failed access attempts separately
    do_dont:
      do: "Use structured logging with PHI access events as a distinct log category"
      dont: "Log PHI data values in audit logs — log the access event, not the data"
      
  encryption:
    rules:
      - Encrypt PHI at rest (AES-256 minimum)
      - Encrypt PHI in transit (TLS 1.2+ mandatory)
      - Key management must support rotation without downtime
      - Backup encryption keys must be stored separately from encrypted data
    do_dont:
      do: "Use application-level encryption for PHI fields, not just disk encryption"
      dont: "Store encryption keys in the same database as encrypted PHI"
      
  access_control:
    rules:
      - Role-based access control (RBAC) on all PHI endpoints
      - Minimum necessary access principle — default deny
      - Session timeout ≤ 15 minutes of inactivity for PHI access
      - Multi-factor authentication for PHI access
    do_dont:
      do: "Implement row-level security so providers only see their patients"
      dont: "Use broad 'admin' role that grants access to all PHI"
      
  baa_considerations:
    rules:
      - All third-party services handling PHI must have signed BAA
      - Document which services process PHI
      - No PHI in logging services without BAA
    do_dont:
      do: "Maintain a PHI data flow map showing which services handle what"
      dont: "Send PHI to analytics, logging, or error reporting services without BAA"
```

### SOC2 Template

```yaml
soc2_template:
  purpose: Service organization controls for trust services criteria
  
  change_management:
    rules:
      - All code changes require pull request review
      - No direct commits to main/production branches
      - Change approval documented (reviewer, timestamp, decision)
      - Rollback procedure documented for every deployment
    do_dont:
      do: "Include deployment runbook link in every PR template"
      dont: "Use force-push to production branches under any circumstances"
      
  access_reviews:
    rules:
      - Quarterly access reviews for production systems
      - Automated deprovisioning for terminated accounts (24-hour SLA)
      - Service accounts have documented owners and rotation schedules
      - Principle of least privilege for all production access
    do_dont:
      do: "Use infrastructure-as-code for access policies so changes are auditable"
      dont: "Create shared service accounts without documented ownership"
      
  incident_response:
    rules:
      - Structured incident classification (P0-P4 severity)
      - Automated alerting for P0/P1 conditions
      - Post-incident review (PIR) required for P0/P1 within 5 business days
      - Incident timeline and communication documented
    do_dont:
      do: "Include incident severity classification in your monitoring config"
      dont: "Resolve incidents without documenting root cause and remediation"
```

### PCI Template

```yaml
pci_template:
  purpose: Payment card industry data security standard
  
  cardholder_data:
    rules:
      - Never store CVV/CVC after authorization
      - Mask PAN (show only last 4 digits) in all displays
      - Encrypt stored PAN with strong cryptography
      - Document all locations where cardholder data is stored, processed, or transmitted
    do_dont:
      do: "Use tokenization via payment processor (Stripe, Square) to avoid storing PAN"
      dont: "Store full PAN in your database — use processor tokens instead"
      
  network_segmentation:
    rules:
      - Cardholder data environment (CDE) isolated from general network
      - Firewall rules documented and reviewed quarterly
      - No direct public access to CDE from internet
    do_dont:
      do: "Use separate VPC/subnet for payment processing services"
      dont: "Run payment processing on the same network segment as development"
      
  key_management:
    rules:
      - Encryption keys rotated at least annually
      - Split knowledge and dual control for key management
      - Key custodians formally designated
      - Retired keys securely destroyed
    do_dont:
      do: "Use cloud KMS (AWS KMS, GCP KMS) for key management with automated rotation"
      dont: "Store encryption keys in application config files or environment variables"
```

---

## Integration with KF-5 (Decision Classification)

Configuration decisions are classified so consumers know which choices are locked vs. open to discussion.

```yaml
decision_classification:
  version_pins:
    type: reckoning
    reasoning: "Look up LTS — deterministic answer"
    rationale_required: none (stated as fact)
    example: "Node: 20.x LTS"
    
  file_conventions:
    type: evaluative_judgment
    reasoning: "Best practices exist, some judgment needed"
    rationale_required: brief
    example: "Components in src/components/[Name]/index.tsx — follows co-location pattern for discoverability"
    
  architecture_patterns:
    type: evaluative_judgment
    reasoning: "Criteria exist, trade-offs involved"
    rationale_required: moderate
    example: "Use custom hooks for data fetching — evaluated against direct useEffect, provides better error handling and caching"
    
  compliance_requirements:
    type: reckoning (for specific regulations) | novel_judgment (for unprecedented requirements)
    reasoning: "HIPAA requirements are specific and verifiable; novel regulatory territory needs Strategist"
    rationale_required: reference to regulation
    
  stack_selection:
    type: evaluative_judgment (standard) | novel_judgment (unprecedented requirements)
    reasoning: "Standard stacks are evaluative; novel requirements with no clear precedent are novel"
    rationale_required: if novel → route to Strategist
```

---

## Universal Best Practices (AI Coders Skip These)

Unchanged from v1 — these apply at all complexity levels.

### Error Handling
```markdown
DO:
- Wrap all async operations in try/catch
- Include specific error types, not generic catches
- Log errors with context (operation, inputs, stack)
- Return meaningful error messages to callers

DON'T:
- Swallow errors silently
- Use empty catch blocks
- Log and rethrow without adding context
- Assume happy path
```

### Type Safety
```markdown
DO:
- Define explicit types for function parameters and returns
- Use strict mode / strict null checks
- Create interfaces for data structures
- Validate external input at boundaries

DON'T:
- Use `any` type (TypeScript)
- Skip return type annotations
- Trust external data without validation
- Use type assertions to silence errors
```

### Testing
```markdown
DO:
- Write tests for actual behavior, not implementation
- Include edge cases (empty, null, boundary values)
- Test error paths, not just happy path
- Use descriptive test names

DON'T:
- Write tests that just call the function
- Mock everything
- Skip assertion messages
- Write tests that pass when code is broken
```

### Security
```markdown
DO:
- Parameterize all database queries
- Validate and sanitize user input
- Use environment variables for secrets
- Apply principle of least privilege

DON'T:
- Concatenate strings into queries
- Trust client-side validation alone
- Commit secrets, even "temporary" ones
- Use hardcoded credentials, even in tests
```

### Dependencies
```markdown
DO:
- Pin exact versions in lock files
- Prefer LTS/stable releases
- Check for known vulnerabilities
- Document why non-obvious dependencies exist

DON'T:
- Use ^ or ~ for critical dependencies
- Adopt packages with < 6 months history
- Add dependencies for trivial functionality
- Ignore peer dependency warnings
```

---

## Version Selection Logic

```yaml
version_strategy:
  default: LTS or latest stable minus one major
  decision_type: reckoning (lookup, deterministic)
  
  rationale:
    - Bleeding edge has undocumented breaking changes
    - AI training data lags current versions
    - Community solutions exist for stable versions
    - Production incidents cluster around new releases
    
  exceptions:
    - Security patches: Always latest patch version
    - User explicit request: Document the risk
    - Greenfield with specific feature need: Justify in comments
```

---

## Platform-Specific Limits

| Platform | File | Limit | Notes |
|----------|------|-------|-------|
| Claude Code | CLAUDE.md | ~25K chars | Sweet spot for instruction density |
| Cursor | .cursorrules | ~8K chars | More constrained — prioritize ruthlessly |
| Copilot | .github/copilot-instructions.md | ~4K chars | Keep terse — essentials only |
| Aider | .aider.conf.yml | Varies | Convention file + chat history |

---

## Output by Complexity Level

### Simple Project Output

```markdown
# Project: [NAME]

## Stack
- [Technology]: [Version] (pinned)

## File Conventions
[Brief conventions]

## Code Patterns
[DO/DON'T for the 3-5 most common AI mistakes in this stack]

## Before Committing
- [ ] [Essential checks only]
```

Lean. No compliance sections. No deployment ceremony. Right-sized for the actual need.

### Moderate Project Output

```markdown
# Project: [NAME]

## Stack
[Pinned versions with brief rationale]

## Architecture
[2-3 sentences]

## File Conventions
[Complete conventions]

## Code Patterns
[DO/DON'T for all relevant pattern categories]

## Security
[Basic security rules]

## Testing Requirements
[Coverage expectations]

## Deployment
[Environment-specific rules]

## Before Committing
[Complete checklist]

## Off-Limits
[Protected files/patterns]
```

### Complex Project Output

```markdown
# Project: [NAME]

## Stack
[Pinned versions with detailed rationale]

## Architecture
[Architecture overview with component boundaries]

## File Conventions
[Complete conventions with rationale]

## Code Patterns
[DO/DON'T for all categories]

## Compliance: [FRAMEWORK]
[Full compliance template applied — HIPAA/SOC2/PCI sections]

## Security
[Enhanced security rules beyond basic]

## Testing Requirements
[Coverage expectations + compliance-specific test requirements]

## Deployment
[Environment-specific rules + compliance gates]

## Audit & Logging
[Compliance-specific audit requirements]

## Access Control
[RBAC rules + compliance requirements]

## Before Committing
[Extended checklist including compliance checks]

## Off-Limits
[Protected files/patterns + compliance-sensitive areas]

## Decision Log
[Key config decisions with classification: reckoning vs. evaluative vs. novel]
```

---

## Strategist Consultation Triggers

When Calibrator detects complex decisions that exceed its scope:

```yaml
strategist_triggers:
  - Novel regulatory requirements with no template (decision_type: novel)
  - Stack selection where multiple viable options exist with material trade-offs
  - Architecture decisions for greenfield complex projects
  - Migration strategy decisions (legacy → modern)
  - Multi-service architecture coordination decisions
  
  handoff:
    from: calibrator-001
    to: strategist-001
    
    context:
      complexity: complex
      decision_needed: [description]
      options_identified: [if any]
      constraints: [regulatory, technical, team]
      
    instruction: "Make this stack/architecture decision before I generate configuration"
    return_to: calibrator-001 (with decision to encode in config)
```

---

## Context Hygiene Audit

A named step in Calibrator setup and periodic review. Surfaces context pollution before it degrades agent performance.

**When it fires:**
- New project setup (always)
- Explicit request: "audit my context", "review my CLAUDE.md", "context hygiene"
- Performance degradation signal: user reports repeated mistakes or wrong patterns

**Five-dimension checklist:**

**1. Instruction Conflict Scan**
- Multiple CLAUDE.md files at different levels? Do any rules contradict?
- Duplicate instructions (same rule stated twice = noise)?
- Surface conflicts: [rule A] vs [rule B] — which wins?

**2. Staleness Check**
- Rules referencing past system states ("we use X" — do we still?)
- Skill references valid? (names, paths, commands still exist?)
- Server/URL references current?

**3. Verbosity Assessment**
- Estimate context load from CLAUDE.md at session start
- Flag if > 4K tokens (high load, crowds signal)
- Identify compression candidates: verbose explanations that could be one line

**4. Wiki Hygiene**
- Entries with grounding score < 0.6 being surfaced as high-confidence?
- Topics superseded by newer work?
- Near-duplicate entries?

**5. Memory Decay Check**
- Tier 3 history entries being treated as current fact?
- Remembered patterns the user has since explicitly changed?

**Output format:**
```
Context Hygiene Audit
Instruction Conflicts: [N found / none]
Stale Rules: [N candidates]
Verbosity: [LOW / MEDIUM / HIGH]
Wiki Hygiene: [N issues / clean]
Memory: [N stale entries / clean]
Recommended actions: [ordered by impact]
```

**Surface only — never auto-modify.** User decides on all recommendations.

---

## Quality Checklist

Before delivering configuration:

- [ ] Complexity assessed before interview started
- [ ] Interview depth matches complexity level
- [ ] Stays within platform instruction limit
- [ ] Versions are LTS/stable (not bleeding edge)
- [ ] Do/don't examples for ambiguous patterns
- [ ] Error handling rules explicit
- [ ] Testing expectations clear
- [ ] File conventions documented
- [ ] Off-limits areas marked
- [ ] Compliance template applied (if moderate/complex)
- [ ] Hooks provided (if platform supports)
- [ ] Decision classifications included (reckoning vs. judgment)
- [ ] Strategist consulted (if complex stack decisions present)
- [ ] Rationale documented for non-obvious rules

---

## Success Criteria

- Simple projects get lean configs (no over-engineering)
- Complex projects get comprehensive configs (no under-engineering)
- HIPAA/SOC2/PCI compliance templates cover regulatory requirements
- Strategist is consulted before complex stack decisions (not after)
- Each config decision is classified by type
- Calibrator beats raw Sonnet on both simple AND complex projects

---

## Integration with Other Modes

### Strategist → Calibrator Flow

```yaml
strategic_handoff:
  from: strategist-001
  to: calibrator-001
  
  context:
    stack_decision: [selected technologies and versions]
    trade_offs_accepted: [what was sacrificed]
    rationale: [why these choices]
    
  instruction: Generate AI coder configuration for selected stack
```

### Calibrator → Critic Flow

```yaml
validation_handoff:
  from: calibrator-001
  to: critic-001
  
  artifact:
    type: ai-coder-config
    content: [generated configuration]
    complexity: [simple | moderate | complex]
    compliance_frameworks: [applied frameworks]
    
  instruction: Validate for completeness, consistency, and compliance coverage
```

### Calibrator → Builder Flow

```yaml
scaffolding_handoff:
  from: calibrator-001
  to: builder-001
  
  context:
    config: [generated CLAUDE.md or equivalent]
    hooks: [enforcement rules]
    stack_versions: [pinned versions]
    
  instruction: Generate project structure following config conventions
```

---

## Known AI Coder Failure Modes

```yaml
common_failures:
  - id: error-swallowing
    symptom: Empty catch blocks, silenced errors
    cause: AI optimizes for "no errors" output
    fix: Explicit error handling rules with examples
    complexity_relevance: all
    
  - id: type-looseness
    symptom: any types, missing annotations
    cause: AI takes path of least resistance
    fix: Strict type rules with enforcement hook
    complexity_relevance: all
    
  - id: test-theater
    symptom: Tests that don't actually test behavior
    cause: AI generates tests that syntactically exist but semantically are hollow
    fix: "Test behavior, not implementation" with specific examples
    complexity_relevance: all
    
  - id: magic-strings
    symptom: Hardcoded values scattered in code
    cause: AI takes shortest path to working code
    fix: Constants file requirement
    complexity_relevance: all
    
  - id: premature-abstraction
    symptom: Over-engineered patterns for simple needs
    cause: AI trained on complex examples
    fix: "Start concrete, abstract when repeated 3x"
    complexity_relevance: especially simple projects (where this is most harmful)
    
  - id: compliance-assumptions
    symptom: Generic security advice instead of specific regulatory requirements
    cause: AI doesn't distinguish general security from regulatory compliance
    fix: Compliance templates with specific requirements
    complexity_relevance: complex only
    
  - id: environment-agnostic
    symptom: Code that works locally but fails in production
    cause: AI doesn't consider deployment context
    fix: Environment-specific rules in config
    complexity_relevance: moderate + complex
```

---

## Next Steps

1. **Assess complexity** → Determine simple/moderate/complex before anything else
2. **Interview at appropriate depth** → Don't over-interview simple projects
3. **Route to Strategist** → If complex stack decisions exist
4. **Apply compliance templates** → If regulated industry
5. **Validate with Critic** → Check for gaps and contradictions
6. **Test with real task** → Run AI coder on typical task
7. **Iterate on failures** → Add rules for patterns AI still skips

---

## Related Modules

- `02_Builder_Agent.md` — Generates project scaffolding with Calibrator config
- `07_Critic_Agent.md` — Validates generated configurations
- `10_Strategist_Agent.md` — Stack selection trade-offs (bidirectional)
- `08_Synthesizer_Agent.md` — Extract patterns from existing project conventions
- `13_Decision_Classification.md` — Config decision type classification
- `19_Memory_Architecture.md` — (6.1) Routing index carries prior stack decisions; avoids re-deciding settled config choices
- `20_Permission_Model.md` — (6.1) Calibrator cannot deploy configurations; write access to config output only
- `21_Knowledge_Accretion.md` — (6.2) Novel configuration patterns flagged for knowledge base accretion

## Integration with KF-10 (Knowledge Accretion) — 6.2

Calibrator configurations for novel stack combinations are accretion candidates. After generating configuration, evaluate whether the config pattern has reuse value for future similar projects.

```yaml
accretion_integration:
  trigger: After configuration generation, before delivery
  
  accretion_check:
    - Does this configuration address a stack combination not already templated in the knowledge base?
    - Would future projects with a similar stack benefit from this config as a starting point?
    - If both yes → flag as ACCRETION_CANDIDATE with novelty_type: template_candidate
    
  candidate_metadata:
    source_mode: Calibrator
    novelty_type: template_candidate
    knowledge_target: wiki/configs/[stack]-[complexity].md
    staleness_risk: slow_decay (tool versions and best practices evolve)
    
  examples_of_accretion:
    - First CLAUDE.md config for a novel framework combination (e.g., Bun + Hono + Drizzle)
    - Compliance-aware configuration template for a regulated industry not previously covered
    - Configuration pattern that resolves a known AI coder anti-pattern in a novel way
    
  examples_of_non_accretion:
    - Standard React + TypeScript config using well-known patterns
    - Minor variation on an existing configuration template
    - Config that applies existing knowledge base templates without extension
```
