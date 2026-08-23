# Validation Failure Handling Strategy

## Decision Matrix: When to Reject vs Warn vs Execute

```
Validation Check | Severity | Action | Reason
────────────────────────────────────────────────────────────────
Grain Mismatch   | CRITICAL | REJECT | Data structure issue
Duplicates       | CRITICAL | REJECT | Data corruption
Fan-out          | HIGH     | WARN   | Likely wrong but possible
Cardinality      | MEDIUM   | WARN   | Might be filtered data
```

## 1. GRAIN VALIDATION FAILS

**What it means:**
```
Query: SELECT STATE, AGE_GROUP, SUM(POPULATION) FROM FACT_POPULATION_AGE
Query GROUP BY: [STATE, AGE_GROUP]
Fact table grain: [BLOCK_GROUP, AGE_ID, SEX]  ← Missing BLOCK_GROUP!

Result: Data is being implicitly aggregated across block groups
→ Correct data but at wrong grain level
```

**Action: REJECT** ❌

```python
if grain_validation.status == 'FAIL':
    return {
        'response': """
I cannot answer this question because the query structure is invalid.

**Problem:** The generated query tries to aggregate at the wrong level.

**Details:**
- Fact table grain: [CENSUS_BLOCK_GROUP, AGE_ID, SEX]
- Query groups by: [STATE, AGE_GROUP]
- Missing: CENSUS_BLOCK_GROUP (blocks data at neighborhood level)

**Solution:** Try asking for:
- "Population by state" (state-level aggregation)
- "Average population per block group by state" (preserves grain)
- "Population by state and age group" (adds another dimension)
""",
        'data': [],
        'validation_error': {
            'type': 'GRAIN_MISMATCH',
            'severity': 'CRITICAL',
            'action': 'REJECT',
            'details': {
                'fact_table_grain': ['CENSUS_BLOCK_GROUP', 'AGE_ID', 'SEX'],
                'query_group_by': ['STATE', 'AGE_GROUP'],
                'missing': ['CENSUS_BLOCK_GROUP']
            }
        }
    }
```

**Why reject?**
- Indicates a fundamental query structure problem
- Result would be misleading (wrong aggregation level)
- Cortex generated invalid query

---

## 2. DUPLICATE ROWS DETECTED

**What it means:**
```
Results preview (LIMIT 1000):
STATE    | AGE_GROUP | POPULATION
────────┼───────────┼────────────
CA       | 25-29     | 1,234,567
CA       | 25-29     | 1,234,567  ← DUPLICATE!
```

**Action: REJECT** ❌

```python
if duplicate_validation.status == 'FAIL':
    return {
        'response': """
I found duplicate rows in the results, which indicates a data quality issue.

**Problem:** The query returned duplicate rows at the grain level.

**Details:**
- Grain: [STATE, AGE_GROUP, SEX]
- Duplicate count: 45 rows
- Example duplicate:
  STATE='CA', AGE_GROUP='25-29', SEX='Male' appears 2 times

**Why this happens:**
- Likely cause: Bad JOIN between fact tables
- Example: FACT_POPULATION_AGE joined to FACT_RACE_ETHNICITY without proper keys

**What to do:**
- This is a Cortex Analyst error (generated bad SQL)
- Try rephrasing your question
- If it persists, there may be a data pipeline issue
""",
        'data': [],
        'validation_error': {
            'type': 'DUPLICATE_ROWS',
            'severity': 'CRITICAL',
            'action': 'REJECT',
            'details': {
                'duplicate_count': 45,
                'grain': ['STATE', 'AGE_GROUP', 'SEX'],
                'example': {
                    'STATE': 'CA',
                    'AGE_GROUP': '25-29',
                    'SEX': 'Male'
                }
            }
        }
    }
```

**Why reject?**
- Indicates JOIN logic is broken
- Results would be inflated/incorrect
- Data integrity issue that needs investigation

---

## 3. FAN-OUT DETECTED (Unexpected Row Multiplication)

**What it means:**
```
User asks: "Population by state"
Expected grain: [STATE]
Expected rows: 50 states
Actual rows: 50 * 23 * 2 = 2,300 rows (also has AGE_GROUP × SEX)

Result: Query is returning more detailed data than asked for
→ Technically valid but unexpected
```

**Action: WARN + EXECUTE** ⚠️

```python
if fanout_validation.status == 'WARN':
    # Execute the query but warn the user
    data_results = SnowflakeClient.query(sql_query)
    
    return {
        'response': f"""
I found the answer, but with a caveat:

{cortex_response}

⚠️ **Note:** The results are more detailed than your question suggests.

**What you asked:** Population by state
**What you got:** Population by state × age group × sex

**Why:** Your question was interpreted to include age and gender breakdowns.

**What to do:**
- The data is valid ✅
- You can use it to see more detail
- If you want just state-level totals, ask: "Total population by state"
""",
        'data': data_results,
        'validation_warning': {
            'type': 'FAN_OUT',
            'severity': 'MEDIUM',
            'action': 'WARN_AND_EXECUTE',
            'details': {
                'expected_rows': 50,
                'actual_rows': len(data_results),
                'expected_grain': ['STATE'],
                'actual_grain': ['STATE', 'AGE_GROUP', 'SEX'],
                'multiplier': len(data_results) / 50
            }
        }
    }
```

**Why warn but execute?**
- Data IS valid, just more detailed
- User might actually want this breakdown
- Common for exploratory analysis

---

## 4. CARDINALITY MISMATCH (Unexpected Row Count)

**What it means:**
```
Expected for state-level aggregation: ~50 rows
Actual: 5 rows

Possible reasons:
1. Heavy filtering (WHERE clause) - OK
2. Data is missing - Might be problem
3. Query bug - Possible issue
```

**Action: WARN + EXECUTE** ⚠️

```python
if cardinality_validation.status == 'WARN':
    data_results = SnowflakeClient.query(sql_query)
    
    return {
        'response': f"""
I found the answer, but something looks unusual:

{cortex_response}

⚠️ **Anomaly Detected:** Fewer states in results than expected.

**Details:**
- Expected: ~50 US states
- Got: {len(data_results)} rows
- Difference: Possible filtering or data availability issue

**Possible reasons:**
1. Your question filtered to specific regions
2. Some states have no data for the requested metrics
3. Data quality issue in source system

**Recommendation:**
- Check if results make sense
- If missing data, you may want to ask: "Which states have this data?"
""",
        'data': data_results,
        'validation_warning': {
            'type': 'CARDINALITY_MISMATCH',
            'severity': 'LOW',
            'action': 'WARN_AND_EXECUTE',
            'details': {
                'expected_cardinality': 50,
                'actual_cardinality': len(data_results),
                'variance_percent': (50 - len(data_results)) / 50 * 100
            }
        }
    }
```

**Why warn but execute?**
- Data might be valid (filtering is normal)
- User should decide if it looks right
- Low confidence issue, not a blocker

---

## 5. MULTIPLE VALIDATIONS FAIL

**Severity Cascade:**
```
If ANY validation is CRITICAL → REJECT entire query
If NO CRITICAL failures but some WARNINGS → WARN + EXECUTE

Example:
- Grain: ✅ PASS
- Duplicates: ❌ FAIL (CRITICAL)
- Fan-out: ⚠️ WARN (HIGH)
- Cardinality: ⚠️ WARN (MEDIUM)

Decision: REJECT (because of duplicates)
```

**Code:**
```python
def get_validation_action(validation_results: dict) -> str:
    """Determine overall action based on validation results"""
    
    critical_failures = [
        v for v in validation_results.values() 
        if v.severity == 'CRITICAL' and v.status == 'FAIL'
    ]
    
    if critical_failures:
        return 'REJECT'
    else:
        return 'WARN_AND_EXECUTE'
```

---

## 6. User Experience Flow

```
User: "What's the population of California?"
         ↓
    Cortex generates SQL
         ↓
    Validation runs
         ↓
    ┌────────────────────────────────┐
    │ CRITICAL FAILURE               │
    │ (Grain/Duplicates)             │
    └────────────────────────────────┘
         ↓
    Return error explanation
    Don't execute query
    Suggest how to rephrase
    Example: "Try: 'Total population of California'"
    
    
    ┌────────────────────────────────┐
    │ WARNINGS ONLY                  │
    │ (Fan-out/Cardinality)          │
    └────────────────────────────────┘
         ↓
    Execute query
    Return results with ⚠️ note
    Explain what's unexpected
    Example: "Note: Results include age breakdowns (more detail than asked)"
```

---

## 7. Error Response Format

**CRITICAL FAILURE:**
```json
{
    "response": "Explanation of why query failed + how to fix",
    "data": [],
    "success": true,
    "validation_error": {
        "type": "GRAIN_MISMATCH | DUPLICATE_ROWS",
        "severity": "CRITICAL",
        "action": "REJECT",
        "details": {
            "grain": [...],
            "missing": [...]
        }
    }
}
```

**WARNING (but executed):**
```json
{
    "response": "Results + explanation of unusual behavior",
    "data": [...actual results...],
    "success": true,
    "validation_warning": {
        "type": "FAN_OUT | CARDINALITY_MISMATCH",
        "severity": "HIGH | MEDIUM",
        "action": "WARN_AND_EXECUTE",
        "details": {
            "expected_rows": 50,
            "actual_rows": 2300
        }
    }
}
```

---

## 8. Logging & Monitoring

**Log all validation failures:**
```python
logger.info(f"Validation PASSED: {validation_summary}")
logger.warning(f"Validation WARNING: {validation_summary}")
logger.error(f"Validation FAILED: {validation_summary}")

# Structured logging for alerts:
# - Track rejection reasons
# - Monitor fan-out frequency
# - Detect cardinality anomalies
```

---

## 9. Fallback: What If Validation Crashes?

```python
try:
    validation = validator.validate_compiled_query(sql)
except Exception as e:
    logger.error(f"Validation error: {e}")
    
    # Fall back to safe behavior
    return {
        'response': """
I encountered an error checking the query validity.

Since I can't guarantee correctness, I won't execute the query.

**Error:** {validation error details}

**Workaround:** Try asking a simpler question or rephrasing.
""",
        'data': [],
        'validation_error': {
            'type': 'VALIDATION_ENGINE_ERROR',
            'severity': 'CRITICAL',
            'action': 'REJECT',
            'reason': str(e)
        }
    }
```

---

## Summary: Validation Action Rules

| Validation | Passes | Fails |
|-----------|--------|-------|
| **Grain** | ✅ Continue | ❌ REJECT |
| **Duplicates** | ✅ Continue | ❌ REJECT |
| **Fan-out** | ✅ Continue | ⚠️ WARN |
| **Cardinality** | ✅ Continue | ⚠️ WARN |

**Overall:** IF ANY CRITICAL FAILS → REJECT (don't execute)
Otherwise: Warn about issues + execute

This ensures data integrity while staying practical for exploratory analysis!
