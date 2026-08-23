# Known Limitations & Trade-offs

This document records architectural weak points and scalability concerns discovered during development.

## 1. Multi-Fact Table Queries (CRITICAL)

**Issue:** Cortex Analyst struggles with comprehensive queries across multiple fact tables (e.g., "demographics of X county" should return age + race + household, but returns only age/sex).

**Root Cause:** Semantic model has three separate fact tables that only connect via `block_group` dimension. No direct cross-fact relationships.

**Current State:** 
- ✅ Single fact table queries work perfectly (age breakdown, race breakdown, household types separately)
- ❌ Comprehensive queries return incomplete results

**Impact:** 
- Users asking "What are the demographics of County X?" get only age/sex data
- Must ask separate questions for race and household composition
- Creates poor UX for broad exploratory queries

**Solution Options (Ranked by Trade-offs):**
1. **Unified VIEW (UNION-based)** - Recommended
   - Pros: No storage overhead, Cortex can query all data
   - Cons: UNION queries slower on large datasets, complex result schema

2. **Materialized VIEW (Pre-aggregated)**
   - Pros: Fast queries, clean schema
   - Cons: Storage overhead, stale data (refresh lag)

3. **Multi-Query API Layer**
   - Pros: Each query simple, works with current schema
   - Cons: 3 API calls = more latency, app logic complexity

4. **Semantic Model Relationships** (Not recommended)
   - Pros: No code changes
   - Cons: Cortex Analyst may still not use intelligently

5. **Denormalized Fact Table** (NOT RECOMMENDED)
   - Pros: Simple queries
   - Cons: Cartesian product explosion, storage bloat, unmaintainable at scale

**Recommendation:** Implement Unified VIEW + monitor performance. Upgrade to Materialized VIEW if UNION queries exceed 5-second latency.

**Status:** Documented, not yet implemented.

---

## 2. Cortex Analyst Semantic Limitations

**Issue:** Cortex occasionally misinterprets questions or generates queries that return 0 rows.

**Examples:**
- "number of people of age 0 in california" → Cortex treats "age 0" as literal, not age group
- "demographics of County X" → Queries only age/sex fact table

**Mitigation:** Layered validation catches these at execution time:
- Layer 1: Generate SQL (Cortex interprets)
- Layer 2: Execute SQL (actual results)
- Layer 3: Validate & Diagnose (if empty, ask Cortex why)

**Limitation:** Cannot prevent all misinterpretations. Relies on post-execution detection.

**Status:** Mitigated with layered validation. Users understand limitations via friendly error messages.

---

## 3. Age Group Specificity

**Issue:** Census data uses age GROUPS (0-4, 5-9, etc.) not individual ages. Users often ask for "age 0" or specific ages.

**Current Handling:** 
- Cortex tries to answer, returns 0 rows
- Diagnostic explains why and suggests valid age groups
- Better than hard-coded validation, but still requires user education

**Trade-off:** No way to enforce validation without hard-coding. Chose semantic approach + good error messages.

**Status:** Acceptable. Users learn quickly from error messages.

---

## 4. Real-time Data Constraints

**Issue:** Census data is static (2020 snapshot). Users may ask for recent/current year data.

**Current:** No validation for year. Cortex queries with year filter that returns empty.

**Future Improvement:** 
- Add data currency info to capabilities summary
- Detect year-based questions, warn about stale data

**Status:** Low priority. Rare user expectation mismatch.

---

## 5. Geographic Granularity Limits

**Issue:** Data available at block group level only (most granular). Smaller geographic units (census tract, zip code) not available.

**Current:** Cortex may generate queries for unavailable geographies.

**Future Improvement:**
- Add geographic dimension schema to capabilities
- Cortex should understand available levels

**Status:** Documented, not yet prioritized.

---

## 6. Cross-Dimensional Analysis

**Issue:** No direct way to correlate age + race + household in single query (each is separate fact table).

**Current:** Users must query each dimension separately, mentally combine results.

**Workaround:** Unified VIEW (when implemented) will enable this.

**Status:** Known limitation, roadmap item.

---

## 7. Margin of Error Handling

**Issue:** Each fact table has margin_of_error, but aggregating across tables requires statistical methodology (not implemented).

**Current:** Each metric shows its own margin separately.

**Implication:** Users aggregating results manually may get incorrect error bounds.

**Status:** Documented. Not in scope for current version.

---

## Recommendations for Future Versions

**High Priority:**
1. Implement Unified VIEW for comprehensive demographics queries
2. Add geographic granularity info to schema
3. Document and warn about data freshness (2020 Census)

**Medium Priority:**
1. Monitor UNION query performance; upgrade to materialized view if needed
2. Improve semantic model relationships for Cortex
3. Add cross-dimensional correlation analysis

**Low Priority:**
1. Statistical error bound aggregation
2. Support for more recent census releases
3. Sub-block-group geographic levels (would require new data source)

---

## Testing Recommendations

- **Regression Testing:** Verify single-table queries remain fast after VIEW implementation
- **Performance Testing:** Monitor UNION query latency as data grows
- **User Testing:** Validate that comprehensive queries now return complete results
- **Error Cases:** Test queries that should fail gracefully with helpful messages

---

## Architecture Debt

- Semantic model relationships may need refinement as Cortex Analyst capabilities evolve
- Consider adopting Cortex Analyst's recommended semantic modeling best practices
- Monitor Snowflake documentation for better cross-fact relationship patterns
