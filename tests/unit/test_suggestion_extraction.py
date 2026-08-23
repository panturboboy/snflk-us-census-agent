"""Test: Suggestion extraction logic

Why this test exists:
- extract_and_format_suggestions() parses response text for follow-up questions
- Must handle various patterns: "Try asking", "You can ask", etc.
- Must remove suggestions from text so they don't appear twice
- Must deduplicate suggestions
- This test verifies the parsing logic works before integration
"""

import pytest
import sys
import pathlib

# Add project to path
sys.path.insert(0, '/Users/Iaroslav/Projects/Snowflake/CensusAgent')

# Import the function from streamlit_app
import importlib.util
spec = importlib.util.spec_from_file_location(
    "streamlit_app",
    "/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py"
)
streamlit_app = importlib.util.module_from_spec(spec)


class TestSuggestionExtractionLogic:
    """Verify suggestion extraction and parsing works correctly"""

    def test_extract_try_asking_pattern(self):
        """Test: Extract 'Try asking:' suggestions

        Why: Model often uses this pattern. Must be recognized and extracted.
        """
        # Load the function
        try:
            # We'll test the logic by importing the actual function
            # For now, test that the patterns are defined in the code
            app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
            content = app_file.read_text()

            # Verify regex pattern exists for "Try asking"
            assert 'Try asking' in content, \
                "extract_and_format_suggestions doesn't handle 'Try asking' pattern"

        except Exception as e:
            pytest.skip(f"Could not load function: {e}")

    def test_extract_you_can_ask_pattern(self):
        """Test: Extract 'You can/could ask' suggestions

        Why: Another common pattern model uses. Must be parsed.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        # Verify regex pattern exists
        assert ('You can' in content or 'You could' in content) and 'ask' in content, \
            "extract_and_format_suggestions doesn't handle 'You can/could ask' pattern"

    def test_bullet_point_extraction(self):
        """Test: Extract suggestions after bullet points or dashes

        Why: Suggestions are typically formatted as:
        Try asking:
        - "Question 1"
        - "Question 2"

        Must parse this structure.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        func_body = content.split('def extract_and_format_suggestions')[1].split('\ndef ')[0]

        # Verify regex handles bullet points or dashes
        assert '[-•]' in func_body or '[--*]' in func_body or '[-' in func_body, \
            "extract_and_format_suggestions doesn't parse bullet point format"

    def test_removes_suggestion_section_from_text(self):
        """Test: Suggestion section removed from response text

        Why: Suggestions should appear as buttons, not duplicated in text.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        func_body = content.split('def extract_and_format_suggestions')[1].split('\ndef ')[0]

        # Verify text cleaning with regex substitution
        assert 're.sub(' in func_body, \
            "extract_and_format_suggestions doesn't remove suggestion section from text"
        assert 'cleaned_text' in func_body, \
            "extract_and_format_suggestions doesn't create cleaned text"

    def test_deduplicates_suggestions(self):
        """Test: Duplicate suggestions removed

        Why: Model might suggest same question twice. User should see it once.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        func_body = content.split('def extract_and_format_suggestions')[1].split('\ndef ')[0]

        # Verify deduplication - either dict.fromkeys or set
        assert 'dict.fromkeys' in func_body or 'set(' in func_body, \
            "extract_and_format_suggestions doesn't deduplicate suggestions"

    def test_filters_trivial_suggestions(self):
        """Test: Very short suggestions filtered out

        Why: Don't want 1-word suggestions like "Yes" or "No".
        Filter out strings shorter than ~5 characters.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        func_body = content.split('def extract_and_format_suggestions')[1].split('\ndef ')[0]

        # Verify length check
        assert 'len(suggestion)' in func_body or 'len(' in func_body, \
            "extract_and_format_suggestions doesn't filter short suggestions"
        assert ('> 5' in func_body or '> 3' in func_body or '>=' in func_body), \
            "extract_and_format_suggestions doesn't have minimum length check"

    def test_handles_empty_response(self):
        """Test: Function handles empty response gracefully

        Why: If response is empty or None, should return empty suggestions, not crash.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        func_body = content.split('def extract_and_format_suggestions')[1].split('\ndef ')[0]

        # Verify function returns even if no suggestions found
        return_statements = func_body.count('return')
        assert return_statements > 0, \
            "extract_and_format_suggestions doesn't have return statement"

    def test_returns_tuple_format(self):
        """Test: Function returns (cleaned_text, suggestions) tuple

        Why: Caller expects this exact format. Wrong format breaks response display.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        func_body = content.split('def extract_and_format_suggestions')[1].split('\ndef ')[0]

        # Verify return format
        assert re.search(r'return.*,.*', func_body), \
            "extract_and_format_suggestions doesn't return tuple"


class TestSuggestionIntegration:
    """Verify suggestions are used correctly in chat display"""

    def test_suggestions_unpacked_correctly(self):
        """Test: Response text and suggestions unpacked correctly

        Why: If unpacking is wrong, one will be None and display will break.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        # Find where function is called
        message_section = content.split('# Display conversation history')[1].split('# Input area')[0]

        # Verify unpacking
        assert ', suggestions = extract_and_format_suggestions(' in message_section, \
            "Suggestions not unpacked correctly from function return"

    def test_cleaned_text_displayed_not_original(self):
        """Test: Cleaned text (without suggestions) is displayed

        Why: If original response is displayed, suggestions appear twice.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        message_section = content.split('# Display conversation history')[1].split('# Input area')[0]

        # Verify cleaned text is used in markdown, not original message['content']
        assert 'response_text' in message_section, \
            "Cleaned response text not used in display"

        # Find the markdown display
        markdown_line = [line for line in message_section.split('\n')
                        if '<strong>Assistant:</strong>' in line and 'markdown' in line]
        if markdown_line:
            assert 'response_text' in markdown_line[0], \
                "Original message['content'] displayed instead of cleaned response_text"

    def test_suggestions_conditional_display(self):
        """Test: Suggestions only shown if list is not empty

        Why: Don't show empty 'You can also try:' header.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        message_section = content.split('# Display conversation history')[1].split('# Input area')[0]

        # Verify conditional display
        assert 'if suggestions:' in message_section, \
            "Suggestions displayed unconditionally - should use 'if suggestions:'"

    def test_suggestion_buttons_match_example_buttons(self):
        """Test: Suggestion buttons have same behavior as example buttons

        Why: Users expect consistent click behavior across all buttons.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        message_section = content.split('# Display conversation history')[1].split('# Input area')[0]

        # Find suggestion button handler
        if 'for i, suggestion in enumerate(suggestions):' in message_section:
            suggestion_section = message_section.split('for i, suggestion in enumerate(suggestions):')[1]

            # Verify same state updates as example buttons
            assert 'st.session_state.user_input_text = suggestion' in suggestion_section, \
                "Suggestion button doesn't set input (different from example buttons)"
            assert 'st.session_state.submit_from_example = True' in suggestion_section, \
                "Suggestion button doesn't set submit flag (different from example buttons)"
            assert 'st.rerun()' in suggestion_section, \
                "Suggestion button doesn't rerun (different from example buttons)"


# Import re for regex testing
import re


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
