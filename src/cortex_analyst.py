import requests
import json
import os
import re
from src.config import SnowflakeConfig


class CortexAnalyst:
    SEMANTIC_VIEW = "CENSUS_NEIGHBORHOOD_INSIGHTS.SEMANTIC.CENSUS_DEMOGRAPHICS_MODEL"
    API_TOKEN = os.getenv("CORTEX_ANALYST_TOKEN", "")

    # Schema metadata for validation
    SEMANTIC_SCHEMA = {
        "dimensions": {
            "state": "US States",
            "county": "Counties",
            "block_group": "Census Block Groups",
            "age_group": "Age Groups (Under 5, 5-9, 10-14, ...)",
            "race": "Race/Ethnicity categories",
            "household_type": "Household composition types",
            "sex": "Sex/Gender"
        },
        "metrics": {
            "population_estimate": "Population count",
            "margin_of_error": "Statistical margin of error",
            "household_count": "Number of households"
        }
    }

    @staticmethod
    def get_capabilities_summary() -> str:
        """Return user-friendly summary of what the agent can answer."""
        return f"""I can answer questions about US Census demographics with these available data:

**Geographic Levels:** State, County, Block Group
**Demographics:** Age groups, Race/Ethnicity, Sex
**Household Data:** Total households, household types
**Metrics:** Population estimates, margins of error

Example: "What is the population of California?" or "Show population by age group nationally"."""

    @staticmethod
    def get_semantic_schema_description() -> str:
        """Return detailed schema description for Cortex to understand available data."""
        dimensions = "\n".join([f"  - {k}: {v}" for k, v in CortexAnalyst.SEMANTIC_SCHEMA["dimensions"].items()])
        metrics = "\n".join([f"  - {k}: {v}" for k, v in CortexAnalyst.SEMANTIC_SCHEMA["metrics"].items()])

        return f"""CENSUS_DEMOGRAPHICS_MODEL semantic view contains:

**Dimensions (filtering/grouping):**
{dimensions}

**Metrics (aggregations):**
{metrics}

**Available data:** 2020 US Census at block group level (most granular geographic detail)"""


    @staticmethod
    def diagnose_empty_results(user_message: str, sql_query: str) -> str:
        """
        Ask Cortex to explain in user-friendly terms why the query returned no results.
        """
        try:
            account = SnowflakeConfig.ACCOUNT
            api_url = f"https://{account}.snowflakecomputing.com/api/v2/cortex/analyst/message"

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {CortexAnalyst.API_TOKEN}",
                "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN"
            }

            diagnostic_prompt = f"""User asked: "{user_message}"

This query returned 0 rows. Explain to the user in simple terms:
1. WHY their question cannot be answered (e.g., "age 0 doesn't exist as individual values")
2. WHAT they asked for that doesn't exist in the data
3. WHAT alternatives or similar values ARE available (e.g., "age groups like 'Under 5 years'")

Be friendly and actionable. Example:
"I cannot answer this because age 0 is part of a wider age band. The Census data has age GROUPS like 'Under 5 years' (ages 0-4), 'Under 5 to 9 years', etc. Try asking about one of these age groups instead."

Keep it under 100 words."""

            messages = [
                {
                    "role": "user",
                    "content": [{
                        "type": "text",
                        "text": diagnostic_prompt
                    }]
                }
            ]

            payload = {
                "messages": messages,
                "semantic_view": CortexAnalyst.SEMANTIC_VIEW
            }

            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                message = data.get("message", {})
                content_blocks = message.get("content", [])

                for content_block in content_blocks:
                    if content_block.get("type") == "text":
                        return content_block.get("text", "").strip()

                return "No results found for that query."
            else:
                return "No results found for that query."

        except Exception as e:
            return f"No results found for that query."

    @staticmethod
    def query(user_message: str, conversation_history: list = None) -> dict:
        """
        Query Cortex Analyst REST API with layered execution validation.

        Validation layers:
        1. Generate SQL (Cortex interprets question)
        2. Execute SQL (get actual results)
        3. Validate Results: Check if empty
        4. Diagnose: If empty, ask Cortex why

        This approach trusts Cortex to attempt answers and validates based on
        actual results rather than predictions.

        Args:
            user_message: Natural language question
            conversation_history: List of previous messages for context

        Returns:
            dict with 'response' and 'success' keys
        """
        if conversation_history is None:
            conversation_history = []

        import sys

        try:
            # Build Snowflake API endpoint
            account = SnowflakeConfig.ACCOUNT
            api_url = f"https://{account}.snowflakecomputing.com/api/v2/cortex/analyst/message"

            # Build request headers (using PAT, not JWT)
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {CortexAnalyst.API_TOKEN}",
                "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN"
            }

            # Build messages array with correct nested structure
            messages = []

            # Helper to sanitize message content for API payload
            def sanitize_content(text: str) -> str:
                """Clean message content to prevent API payload issues."""
                # Remove markdown formatting that might break JSON
                text = text.replace('**', '')  # Remove bold markers
                text = text.replace('`', '')   # Remove code markers
                text = text.replace('\n\n', ' ')  # Replace double newlines with space
                # Limit length to prevent oversized payloads
                max_len = 500
                if len(text) > max_len:
                    text = text[:max_len] + "..."
                return text.strip()

            # Add conversation history ACCUMULATED INTO SINGLE MESSAGE
            # Build context from previous questions AND their results
            context_messages = conversation_history[-5:]  # Last 5 messages

            # Build context with questions and their results
            context_items = []
            for msg in context_messages:
                if msg.get('role') == 'user':
                    context_items.append(('question', msg['content']))
                elif msg.get('role') == 'assistant':
                    # Include data summary from assistant response
                    data_count = len(msg.get('data', []))
                    context_items.append(('answer', msg['content'], data_count))

            # Build single message combining context + current question
            if context_items and len(context_items) > 1:
                # We have previous context - include Q&A pairs
                context_text = "Context from previous questions and results:\n"
                question_count = 1

                for item in context_items[:-1]:  # Exclude current question
                    if item[0] == 'question':
                        context_text += f"{question_count}. Question: {sanitize_content(item[1])}\n"
                    elif item[0] == 'answer':
                        data_summary = f"(returned {item[2]} rows)" if item[2] > 0 else "(no data)"
                        context_text += f"   Result: {data_summary}\n"
                        question_count += 1

                context_text += f"\nNow, {user_message}"
                combined_message = context_text
            else:
                # No context, just current question
                combined_message = user_message

            # Add as single user message
            messages.append({
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": sanitize_content(combined_message)
                }]
            })

            # Build payload with correct structure
            payload = {
                "messages": messages,
                "semantic_view": CortexAnalyst.SEMANTIC_VIEW
            }

            print(f"DEBUG: Layer 1 - Generating SQL from Cortex", file=sys.stderr)
            print(f"DEBUG: Payload messages count: {len(messages)}", file=sys.stderr)
            if len(messages) > 1:
                print(f"DEBUG: Message roles: {[m.get('role') for m in messages]}", file=sys.stderr)
                print(f"DEBUG: Message structure valid: {all(m.get('role') in ['user', 'assistant'] for m in messages)}", file=sys.stderr)

            # Validate JSON can be serialized
            try:
                json_test = json.dumps(payload)
                print(f"DEBUG: JSON serialization OK, size: {len(json_test)} bytes", file=sys.stderr)
            except Exception as e:
                print(f"DEBUG: JSON serialization ERROR: {e}", file=sys.stderr)
                raise

            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=55
            )

            print(f"DEBUG: Response status: {response.status_code}", file=sys.stderr)

            if response.status_code == 200:
                data = response.json()

                # Parse Cortex response structure: { "message": { "content": [...] } }
                analysis_text = ""
                sql_query = ""

                message = data.get("message", {})
                content_blocks = message.get("content", [])

                for content_block in content_blocks:
                    if content_block.get("type") == "text":
                        analysis_text = content_block.get("text", "")
                    elif content_block.get("type") == "sql":
                        sql_query = content_block.get("statement", "")

                # LAYER 2: Execute SQL and validate results
                data_results = []
                if sql_query:
                    try:
                        print(f"DEBUG: Layer 2 - Executing SQL", file=sys.stderr)
                        from src.snowflake_client import SnowflakeClient
                        data_results = SnowflakeClient.query(sql_query)

                        # LAYER 3: Check if results are empty
                        if not data_results or len(data_results) == 0:
                            print(f"DEBUG: Layer 3 - Empty results, diagnosing", file=sys.stderr)
                            diagnosis = CortexAnalyst.diagnose_empty_results(user_message, sql_query)
                            capabilities = CortexAnalyst.get_capabilities_summary()

                            return {
                                'response': f"No data found for that question.\n\n**Why:** {diagnosis}\n\n{capabilities}",
                                'data': [],
                                'success': True,
                                'error': None
                            }

                        print(f"DEBUG: Layer 3 passed - Got {len(data_results)} rows", file=sys.stderr)

                    except Exception as e:
                        print(f"DEBUG: SQL execution error: {str(e)}", file=sys.stderr)
                        analysis_text += f"\n\n[Note: Could not execute query: {str(e)[:100]}]"

                return {
                    'response': analysis_text,
                    'data': data_results,
                    'success': True,
                    'error': None
                }
            else:
                # API error - get Cortex's error message
                print(f"DEBUG: API error {response.status_code}", file=sys.stderr)
                print(f"DEBUG: Error response: {response.text[:500]}", file=sys.stderr)

                capabilities = CortexAnalyst.get_capabilities_summary()

                # Try to extract error message from Cortex
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', 'Could not process your question.')
                except:
                    error_msg = response.text[:200] if response.text else 'API error'

                return {
                    'response': f"I cannot answer that question.\n\n**Reason:** {error_msg}\n\n{capabilities}",
                    'data': [],
                    'success': True,
                    'error': None
                }

        except Exception as e:
            print(f"DEBUG: Exception in query: {str(e)}", file=sys.stderr)
            capabilities = CortexAnalyst.get_capabilities_summary()
            return {
                'response': f"I encountered an error processing your question.\n\n{capabilities}",
                'data': [],
                'success': True,
                'error': None
            }
