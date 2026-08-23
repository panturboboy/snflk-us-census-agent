# Documentation

This directory contains comprehensive documentation for the Census Agent project.

## Documentation Structure

```
docs/
├── adr/                    # Architecture Decision Records
│   ├── README.md          # ADR index and process
│   └── ADR-001-*.md       # Specific decisions
├── README.md              # This file
└── (future directories)
```

## Key Documentation Files

### Project Documentation
- **[REQUIREMENTS_CHECKLIST.md](../REQUIREMENTS_CHECKLIST.md)** - Requirements verification and status
- **[LIMITATIONS.md](../LIMITATIONS.md)** - Known limitations and architectural weak points
- **[CONTEXT_PRESERVATION.md](../CONTEXT_PRESERVATION.md)** - Multi-turn conversation analysis
- **[DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)** - Deployment instructions
- **[README.md](../README.md)** - Main project README

### Testing Documentation
- **[tests/README.md](../tests/README.md)** - Comprehensive testing guide
- **[pytest.ini](../pytest.ini)** - Pytest configuration

### Architecture Decisions
- **[adr/README.md](./adr/README.md)** - ADR index and process
- **[adr/ADR-001-context-preservation.md](./adr/ADR-001-context-preservation.md)** - Context preservation decision

## Quick Links

### For Developers
- [Testing Guide](../tests/README.md) - How to run tests
- [Architecture Decisions](./adr/README.md) - Why things are designed this way
- [Requirements](../REQUIREMENTS_CHECKLIST.md) - What's implemented vs missing

### For Operators
- [Deployment Guide](../DEPLOYMENT_GUIDE.md) - How to deploy
- [Limitations](../LIMITATIONS.md) - What to watch for

### For Users
- [README](../README.md) - Project overview
- [Example Queries](../README.md#example-queries) - How to use the chat

## Important Decisions

### Context Preservation
**Decision:** Accumulate context into a single message instead of alternating user/assistant messages

**Why:** Cortex Analyst REST API was rejecting multi-message conversations with 400 errors

**Restrictions:**
- Payload size: ~500-2000 characters practical limit
- Context window: Limited to 5 messages
- Data loss: Only row counts included, not values

**See:** [ADR-001: Context Preservation](./adr/ADR-001-context-preservation.md)

### Three-Layer Data Warehouse
**Design:** RAW → CURATED → SEMANTIC

**Why:** Separation of concerns, Cortex Analyst best practices

**See:** [LIMITATIONS.md - Data Warehouse section](../LIMITATIONS.md#data-warehouse)

### Graceful Degradation
**Approach:** Three-layer validation + user-friendly error messages

**Why:** Users understand data limitations and can rephrase questions

**See:** [LIMITATIONS.md - Cortex Analyst Semantic Limitations](../LIMITATIONS.md#cortex-analyst-semantic-limitations)

## Decision Making

When making architectural decisions, follow the ADR process:

1. Document the **Problem** being solved
2. List **Alternatives** considered
3. State the **Decision** and rationale
4. Document **Consequences** (positive & negative)
5. Record **Restrictions** and known limitations
6. Create tests to **Validate** the approach
7. Create an ADR in this directory

See [adr/README.md](./adr/README.md) for full process.

## Documentation Standards

### When Adding New Docs
- Use Markdown format (.md files)
- Include a title and context
- Link to related documentation
- Record decisions with ADRs

### What Should Be Documented
- ✅ Architectural decisions (use ADRs)
- ✅ Known limitations and workarounds
- ✅ API integration details and restrictions
- ✅ Deployment procedures
- ✅ Testing approach and coverage
- ❌ Don't document "how to write Python" (use code comments instead)

## Outdated Documentation

Check these if they're updated:
- [CONTEXT_PRESERVATION.md](../CONTEXT_PRESERVATION.md) - Status changed when context fix was implemented
- [REQUIREMENTS_CHECKLIST.md](../REQUIREMENTS_CHECKLIST.md) - Updated when requirements status changed

## Contributing

When contributing to documentation:

1. Keep it accurate - docs become stale quickly
2. Link related docs together
3. Use headings for structure
4. Include examples for complex topics
5. Update ADRs if changing decisions

---

**Last Updated:** 2026-08-23  
**Maintained By:** Development Team
