# Context Preservation Analysis

## Current Implementation Status

### ✅ What's Working

1. **Session State Storage**
   - All messages stored in `st.session_state.messages`
   - Persistent across user interactions
   - Clear conversation button to reset

2. **Context Passed to Cortex**
   - Last 3 messages sent to Cortex Analyst
   - Includes both user questions and assistant responses
   - Proper message structure with roles

3. **Message History**
   - User messages: `{"role": "user", "content": "..."}`
   - Assistant messages: `{"role": "assistant", "content": "..."}`
   - Maintains conversation transcript

### ⚠️ Known Issues

#### Issue 1: Long Error Messages Break Context
When assistant response contains long error diagnostics, subsequent queries fail with:
```
"Incoming request does not contain a valid payload"
```

**Example:**
```
Q1: "What is the population of Texas?"
A1: "No data found for that question. Why: This is our interpretation..."
     (Long diagnostic message)

Q2: "What about age breakdown for that state?"
→ ERROR: Invalid payload
```

**Root Cause:** 
- Long assistant responses (errors + diagnostics) may exceed Cortex API payload limits
- Or Cortex struggles parsing previous error messages when generating new queries

**Impact:** Multi-turn conversations fail when first query returns an error

#### Issue 2: Anaphoric References Don't Work
User asks: "What about age breakdown for that state?"
- "that state" refers to Texas from previous query
- Cortex has context (Q1 + A1) but still fails

**Root Cause:** Unclear if it's the anaphoric reference or the error message in context

### Current Context Window

**Size:** Last 3 messages (1.5 conversation turns)

```
Turn 1: Q1 + A1 → [Q1] passed (no context yet)
Turn 2: Q2 + A2 → [Q1, A1] passed as context
Turn 3: Q3 + A3 → [A1, Q2, A2] passed as context (Q1 dropped)
Turn 4: Q4 + A4 → [Q2, A2, Q3, A3]... wait, last 3 means [A2, Q3, A3]
```

**Assessment:** 3-message window is quite short for complex multi-step analysis

---

## Testing Results

Ran `test_context_preservation.py` with 4-question conversation:

| Turn | Question | Success | Issue |
|------|----------|---------|-------|
| 1 | "What is the population of Texas?" | ❌ NO DATA | Query returned 0 rows |
| 2 | "What about age breakdown for that state?" | ❌ PAYLOAD ERROR | Context contains error |
| 3 | "Which age group has the most people?" | ❌ PAYLOAD ERROR | Context contaminated |
| 4 | "Now show me the same data for California" | ❌ PAYLOAD ERROR | Still failing |

**Conclusion:** Context preservation works structurally but breaks when error messages are in history.

---

## Root Cause Analysis

The issue is likely that when we pass error messages as part of the context, Cortex Analyst API rejects the payload. The error diagnostics might contain:
- Special characters
- Long text blocks
- Markdown formatting (`**`, `\n`, etc.)
- Escaped characters that break JSON encoding

**Specific Problem Code** (in `src/cortex_analyst.py`, line 175-182):
```python
elif msg.get('role') == 'assistant':
    messages.append({
        "role": "assistant",
        "content": [{
            "type": "text",
            "text": msg['content']  # ← This might have markdown/special chars
        }]
    })
```

---

## Solutions

### Option 1: Filter Error Messages from Context (Recommended)
```python
# Only include successful responses in context, skip error messages
for msg in conversation_history[-3:]:
    if msg.get('role') == 'assistant':
        # Skip if it's an error response
        if "cannot answer" in msg['content'].lower() or \
           "no data found" in msg['content'].lower():
            continue
    
    # Add to context
    messages.append(format_message(msg))
```

**Pros:**
- Simple to implement
- Cleans up context window
- Errors don't pollute future queries

**Cons:**
- Loses some context about what didn't work
- Might miss learning opportunities

### Option 2: Sanitize Message Content
```python
def sanitize_for_api(text):
    # Strip markdown, escape special chars
    text = text.replace('**', '')
    text = text.replace('\n\n', ' ')
    # Limit length
    return text[:500]

content = sanitize_for_api(msg['content'])
```

**Pros:**
- Keeps context, just cleaned up
- Prevents payload errors

**Cons:**
- Loses formatting
- Risk of truncating important info

### Option 3: Extend Context Window & Increase API Timeout
```python
# Use last 5 messages instead of 3
for msg in conversation_history[-5:]:
    # ... format message ...
```

**Pros:**
- Longer context for multi-turn analysis
- More information available to Cortex

**Cons:**
- Larger payloads → slower API calls
- May still hit limits on error messages

### Option 4: Store Separate "Clean" Context
```python
# Track two histories:
# 1. Full history (for UI display)
# 2. Clean history (for Cortex API, no errors)

if result['success']:
    clean_history.append(msg)
else:
    full_history.append(msg)

# Pass clean_history to Cortex
result = CortexAnalyst.query(question, clean_history)
```

**Pros:**
- Best of both worlds
- UI shows full history
- Cortex gets clean context

**Cons:**
- More complex code
- Two histories to manage

---

## Recommendation

**Implement Option 1 (Filter Error Messages)** because:
1. ✅ Simple to implement
2. ✅ Solves the payload error immediately
3. ✅ Cleaner context for Cortex
4. ✅ Still preserves UI history
5. ⚠️ Trade-off: Loses context about failed queries

**Then monitor** if users need longer context for complex analysis.

---

## Action Items

- [ ] Implement error message filtering in `cortex_analyst.py`
- [ ] Test multi-turn conversation with context
- [ ] Verify payload errors are resolved
- [ ] Document context window limitations for users
- [ ] Monitor if longer context window is needed

---

## Files Affected

If implementing Option 1:
- `src/cortex_analyst.py` - Add filtering logic in `query()` method
- `streamlit_app.py` - No changes (UI still shows full history)
- Tests - Update `test_context_preservation.py` to verify fix
