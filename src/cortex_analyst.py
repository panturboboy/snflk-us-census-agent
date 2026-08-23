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
        Ask Cortex why the query returned no results.
        """
        try:
            account = SnowflakeConfig.ACCOUNT
            api_url = f"https://{account}.snowflakecomputing.com/api/v2/cortex/analyst/message"

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {CortexAnalyst.API_TOKEN}",
                "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN"
            }

            diagnostic_prompt = f"""The query for "{user_message}" returned 0 rows:

{sql_query}

Briefly explain why this query might return no results. Is this expected (e.g., data doesn't exist)
or should we try a different approach? Be concise."""

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

                return "Could not determine why no results were found."
            else:
                return "Could not diagnose empty results."

        except Exception as e:
            return f"Error diagnosing results: {str(e)}"

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

            # Add conversation history (alternate user/assistant messages)
            for msg in conversation_history[-3:]:
                if msg.get('role') == 'user':
                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "text",
                            "text": msg['content']
                        }]
                    })
                elif msg.get('role') == 'assistant':
                    messages.append({
                        "role": "assistant",
                        "content": [{
                            "type": "text",
                            "text": msg['content']
                        }]
                    })

            # Add current message (must be last and must be user role)
            messages.append({
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": user_message
                }]
            })

            # Build payload with correct structure
            payload = {
                "messages": messages,
                "semantic_view": CortexAnalyst.SEMANTIC_VIEW
            }

            print(f"DEBUG: Layer 1 - Generating SQL from Cortex", file=sys.stderr)

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
                # API error - likely invalid question for semantic model
                print(f"DEBUG: API error {response.status_code}", file=sys.stderr)
                capabilities = CortexAnalyst.get_capabilities_summary()
                return {
                    'response': f"I couldn't process that question.\n\n{capabilities}",
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
