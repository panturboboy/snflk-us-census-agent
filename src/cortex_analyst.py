import requests
import json
import os
from src.config import SnowflakeConfig


class CortexAnalyst:
    SEMANTIC_VIEW = "CENSUS_NEIGHBORHOOD_INSIGHTS.SEMANTIC.CENSUS_DEMOGRAPHICS_MODEL"
    API_TOKEN = os.getenv("CORTEX_ANALYST_TOKEN", "")

    # Available dimensions and metrics in the semantic model
    AVAILABLE_DIMENSIONS = {
        "Geographic": ["State", "County", "Block Group"],
        "Demographics": ["Age Group", "Sex/Gender"],
        "Household": ["Household Type"],
        "Race/Ethnicity": ["Race/Ethnicity Category"]
    }

    AVAILABLE_METRICS = {
        "Population": ["Population Estimate", "Margin of Error"],
        "Households": ["Household Count", "Household Margin of Error"]
    }

    AVAILABLE_AGE_GROUPS = [
        "Under 5 years", "5 to 9 years", "10 to 14 years", "15 to 17 years",
        "18 to 19 years", "20 years", "21 years", "22 to 24 years",
        "25 to 29 years", "30 to 34 years", "35 to 39 years", "40 to 44 years",
        "45 to 49 years", "50 to 54 years", "55 to 59 years", "60 to 61 years",
        "62 to 64 years", "65 to 66 years", "67 to 69 years", "70 to 74 years",
        "75 to 79 years", "80 to 84 years", "85 years and over"
    ]

    @staticmethod
    def check_if_age_group_exists(question: str) -> tuple[bool, str]:
        """Check if question mentions an age group and if it exists in data."""
        question_lower = question.lower()

        # Check for common age group mentions
        for age_group in CortexAnalyst.AVAILABLE_AGE_GROUPS:
            if age_group.lower() in question_lower:
                return True, age_group  # Found exact match

        # Check for "age X" or "age X years" pattern (specific age numbers)
        import re
        age_pattern = r'age\s+(\d+)(?:\s+years?)?'
        match = re.search(age_pattern, question_lower)
        if match:
            age_mentioned = match.group(1)
            available = ", ".join(CortexAnalyst.AVAILABLE_AGE_GROUPS)
            return False, f"""I don't have data for a specific "age {age_mentioned}". The Census data only includes age groups, not individual ages.

**Available age groups:**
{available}

**Tip:** Try asking about "Under 5 years" (which includes ages 0-4) or other age ranges instead."""

        return True, ""  # No age group mentioned

    @staticmethod
    def get_capabilities_summary() -> str:
        """Return user-friendly summary of what the agent can answer."""
        age_groups = ", ".join(CortexAnalyst.AVAILABLE_AGE_GROUPS[:5]) + ", ..."
        return f"""I can answer questions about US Census demographics with these available data:

**Geographic Levels:** State, County, Block Group
**Demographics:** Age groups ({age_groups})
**Household Data:** Total households, household types
**Race/Ethnicity:** 9 racial and ethnic categories
**Metrics:** Population estimates and margins of error

Example: "What is the population of California?" or "Show population by age group nationally"."""

    @staticmethod
    def query(user_message: str, conversation_history: list = None) -> dict:
        """
        Query Cortex Analyst REST API with a semantic view.

        Args:
            user_message: Natural language question
            conversation_history: List of previous messages for context

        Returns:
            dict with 'response' and 'success' keys
        """
        if conversation_history is None:
            conversation_history = []

        # Pre-check: detect if asking about specific age groups
        age_exists, age_msg = CortexAnalyst.check_if_age_group_exists(user_message)
        if not age_exists:
            return {
                'response': age_msg,
                'data': [],
                'success': True,
                'error': None
            }

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

            # Make API request
            import sys
            print(f"DEBUG: API URL: {api_url}", file=sys.stderr)
            print(f"DEBUG: Payload: {json.dumps(payload, indent=2)}", file=sys.stderr)

            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=55
            )

            print(f"DEBUG: Response status: {response.status_code}", file=sys.stderr)
            print(f"DEBUG: Response body: {response.text[:500]}", file=sys.stderr)

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

                # Execute SQL query if generated
                data_results = []
                if sql_query:
                    try:
                        from src.snowflake_client import SnowflakeClient
                        data_results = SnowflakeClient.query(sql_query)
                    except Exception as e:
                        analysis_text += f"\n\n[Note: Could not execute query: {str(e)[:100]}]"

                return {
                    'response': analysis_text,
                    'data': data_results,
                    'success': True,
                    'error': None
                }
            else:
                # Gracefully handle API errors - likely irrelevant questions
                if response.status_code == 400:
                    capabilities = CortexAnalyst.get_capabilities_summary()
                    return {
                        'response': f"I couldn't process that question - it may be asking about data I don't have.\n\n{capabilities}",
                        'data': [],
                        'success': True,
                        'error': None
                    }
                else:
                    capabilities = CortexAnalyst.get_capabilities_summary()
                    return {
                        'response': f"I couldn't answer that question.\n\n{capabilities}",
                        'data': [],
                        'success': True,
                        'error': None
                    }

        except Exception as e:
            capabilities = CortexAnalyst.get_capabilities_summary()
            return {
                'response': f"I couldn't answer that question.\n\n{capabilities}",
                'data': [],
                'success': True,
                'error': None
            }
