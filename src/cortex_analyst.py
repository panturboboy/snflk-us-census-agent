import requests
import json
import os
from src.config import SnowflakeConfig


class CortexAnalyst:
    SEMANTIC_VIEW = "CENSUS_NEIGHBORHOOD_INSIGHTS.SEMANTIC.CENSUS_DEMOGRAPHICS_MODEL"
    API_TOKEN = os.getenv("CORTEX_ANALYST_TOKEN", "")

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
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=55
            )

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
                error_msg = response.json().get("message", response.text[:200]) if response.text else f"HTTP {response.status_code}"
                return {
                    'response': f"Cortex API error: {error_msg}",
                    'data': [],
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                }

        except Exception as e:
            return {
                'response': f"I encountered an error processing your question: {str(e)}",
                'data': [],
                'success': False,
                'error': str(e)
            }
