# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) that document significant architectural decisions, their rationale, and consequences.

## Format

Each ADR follows the lightweight format:
- **Status**: PROPOSED, ACCEPTED, DEPRECATED, SUPERSEDED
- **Context**: The issue or requirement being addressed
- **Decision**: What was decided and how
- **Rationale**: Why this decision was made
- **Consequences**: Positive and negative impacts
- **Restrictions**: Known limitations and constraints

## ADRs

### [ADR-001: Context Preservation Strategy](./ADR-001-context-preservation.md)

**Status:** ACCEPTED

**Summary:** Use accumulated single-message context instead of alternating user/assistant messages to enable reliable multi-turn conversations with Cortex Analyst REST API.

**Key Restrictions:**
- Payload size limits (~500-2000 chars practical limit)
- Context window limited to 5 messages
- Data loss: only row counts, not values
- Anaphoric references require explicit context

**Tested:** ✅ 3-turn conversations working  
**Issues:** None known  
**Next:** Production validation

---

## Decision Making Process

When proposing a new architectural decision:

1. **Identify the Problem** - What issue needs solving?
2. **Propose Alternatives** - What are 3-5 possible solutions?
3. **Document Rationale** - Why choose the selected approach?
4. **Define Consequences** - What trade-offs are we accepting?
5. **Record Restrictions** - What are the known limitations?
6. **Test & Validate** - Prove it works with tests
7. **Seek Approval** - Get team consensus
8. **Document Decision** - Create the ADR record

## Using ADRs

**When Reading Code:**
- If you see an unusual pattern, check ADRs for the rationale
- ADRs document "why", not just "what"

**When Making Changes:**
- Check if an ADR exists for this area
- If changing a decision, mark existing ADR as SUPERSEDED
- Create new ADR for significant changes

**When Debugging Issues:**
- Look for related ADRs to understand constraints
- Check "Restrictions" section for known limitations
- Review "Consequences" for expected behavior

## ADR Index

| ID | Title | Status | Area |
|----|-------|--------|------|
| [001](./ADR-001-context-preservation.md) | Context Preservation Strategy | ACCEPTED | Multi-turn Conversations |
| (Propose your ADR here) | | | |

---

## Questions?

For questions about specific decisions:
1. Read the relevant ADR
2. Check the "References" section for related code
3. Review test files mentioned in the ADR
4. Contact the decision's author (listed in ADR header)

## Future ADRs to Consider

- ADR-002: Semantic Model Design (fact tables vs denormalized)
- ADR-003: Error Handling Strategy (graceful degradation approach)
- ADR-004: Deployment Architecture (Streamlit Cloud vs alternatives)
- ADR-005: Data Warehouse Layers (RAW/CURATED/SEMANTIC rationale)
