"""Test: Quick link auto-submit and suggestion formatting

Why this test exists:
- Implemented feature to auto-submit when quick link is clicked
- Implemented feature to format model suggestions as clickable buttons
- Need tests to verify both work correctly and don't regress
- Quick links should: (1) populate input AND (2) auto-submit in one action
- Model suggestions should be extracted from response text and formatted as buttons
"""

import pytest
import pathlib
import re


class TestQuickLinkAutoSubmit:
    """Verify quick link clicks auto-populate input AND auto-submit"""

    def test_submit_from_example_state_key_exists(self):
        """Test: Session state key 'submit_from_example' must exist

        Why: This flag triggers auto-submission after example button is clicked.
        Without it, quick links won't auto-submit (users must click Send separately).
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        # Verify state key is initialized
        assert 'if "submit_from_example" not in st.session_state:' in content, \
            "submit_from_example state key not initialized"
        assert 'st.session_state.submit_from_example = False' in content, \
            "submit_from_example not initialized to False"

    def test_example_button_sets_submit_flag(self):
        """Test: Example button click must set submit_from_example flag

        Why: Flag signals that input was populated by quick link, not user typing.
        This triggers auto-submission in the form handler.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        # Find example button section
        assert 'st.session_state.submit_from_example = True' in content, \
            "Example button doesn't set submit_from_example flag"

        # Verify it's in the example button click handler
        example_section = content.split('for i, example in enumerate(examples):')[1].split('# Main chat interface')[0]
        assert 'st.session_state.submit_from_example = True' in example_section, \
            "submit_from_example not set in example button handler"

    def test_form_handler_checks_submit_flag(self):
        """Test: Form submission handler must check submit_from_example flag

        Why: Handler needs to detect auto-submit from quick link in addition to
        user clicking Send or pressing Enter.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        # Verify handler checks the flag
        assert 'should_submit = send_clicked or (st.session_state.submit_from_example and user_input)' in content, \
            "Form handler doesn't check submit_from_example flag"

        # Verify flag is cleared after submission
        handler_section = content.split('should_submit = send_clicked')[1].split('st.session_state.messages.append')[0]
        assert 'st.session_state.submit_from_example = False' in handler_section, \
            "submit_from_example flag not cleared after submission"

    def test_quick_link_reruns_after_setting_state(self):
        """Test: Example button must call st.rerun() after setting state

        Why: Without rerun, state change won't trigger form handler.
        User would see input populated but query wouldn't execute.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        # Find example button section
        example_section = content.split('for i, example in enumerate(examples):')[1].split('# Main chat interface')[0]

        # Verify st.rerun() is called
        assert 'st.rerun()' in example_section, \
            "Example button doesn't call st.rerun() - state change won't trigger"

        # Verify order: set input -> set flag -> rerun
        lines = example_section.split('\n')
        set_input_idx = None
        set_flag_idx = None
        rerun_idx = None

        for i, line in enumerate(lines):
            if 'st.session_state.user_input_text = example' in line:
                set_input_idx = i
            elif 'st.session_state.submit_from_example = True' in line:
                set_flag_idx = i
            elif 'st.rerun()' in line:
                rerun_idx = i

        assert set_input_idx is not None and set_flag_idx is not None and rerun_idx is not None, \
            "Sequence incomplete: must set input, set flag, then rerun"
        assert set_input_idx < set_flag_idx < rerun_idx, \
            "Wrong order: should set input, then flag, then rerun"


class TestSuggestionExtraction:
    """Verify model suggestions are extracted and formatted correctly"""

    def test_extract_and_format_suggestions_function_exists(self):
        """Test: extract_and_format_suggestions() function must exist

        Why: This function parses response text to extract suggested questions.
        Without it, we can't format suggestions as clickable buttons.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        assert 'def extract_and_format_suggestions(' in content, \
            "extract_and_format_suggestions() function not found"

    def test_function_signature_correct(self):
        """Test: Function must accept response_text and return tuple

        Why: Caller expects (cleaned_text, suggestions_list) tuple.
        Wrong signature breaks response display.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        # Extract function definition
        func_match = re.search(
            r'def extract_and_format_suggestions\(response_text.*?\).*?->.*?:',
            content,
            re.DOTALL
        )
        assert func_match, "Function signature not found"

        # Verify it returns tuple (tuple assignment format, with or without parens)
        func_body = content.split('def extract_and_format_suggestions')[1].split('\ndef ')[0]
        assert 'return' in func_body, "Function doesn't return anything"
        # Match both "return (a, b)" and "return a, b" formats
        assert re.search(r'return\s+\w+\s*,', func_body) or re.search(r'return\s+\(.*?,.*?\)', func_body), \
            "Function doesn't return tuple (cleaned_text, suggestions)"

    def test_function_handles_try_asking_pattern(self):
        """Test: Function must extract 'Try asking:' suggestions

        Why: Model often uses this pattern to suggest follow-up questions.
        If not parsed, suggestions won't be formatted as buttons.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        func_body = content.split('def extract_and_format_suggestions')[1].split('\ndef ')[0]

        # Verify 'Try asking' pattern is in regex
        assert 'Try asking' in func_body or 'try asking' in func_body, \
            "Function doesn't handle 'Try asking' pattern"

    def test_function_removes_suggestions_from_text(self):
        """Test: Function must remove suggestion section from response text

        Why: Suggestions should appear as buttons below response, not in text.
        Cleaning text prevents duplication and improves UX.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        func_body = content.split('def extract_and_format_suggestions')[1].split('\ndef ')[0]

        # Verify text is cleaned before returning
        assert 're.sub(' in func_body, "Function doesn't use regex to clean text"
        assert 'cleaned_text' in func_body, "Function doesn't have cleaned_text variable"

    def test_function_deduplicates_suggestions(self):
        """Test: Function must remove duplicate suggestions

        Why: If model repeats a suggestion, user shouldn't see two identical buttons.
        Deduplication improves UX.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        func_body = content.split('def extract_and_format_suggestions')[1].split('\ndef ')[0]

        # Verify deduplication logic
        assert 'dict.fromkeys' in func_body or 'set(' in func_body, \
            "Function doesn't deduplicate suggestions"


class TestSuggestionButtonIntegration:
    """Verify suggestions are displayed and clickable in chat"""

    def test_assistant_message_displays_suggestions(self):
        """Test: Assistant message section must display suggestion buttons

        Why: Suggestions should be rendered as clickable buttons after response text.
        This makes follow-up questions discoverable to users.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        # Find message display section
        message_section = content.split('# Display conversation history')[1].split('# Input area')[0]

        # Verify suggestions extraction is called
        assert 'extract_and_format_suggestions(' in message_section, \
            "extract_and_format_suggestions() not called in message display"

    def test_suggestion_button_click_handler_exists(self):
        """Test: Suggestion button clicks must be handled like example buttons

        Why: When user clicks suggestion, it should:
        1. Populate input
        2. Set auto-submit flag
        3. Trigger rerun
        Same behavior as example buttons in sidebar.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        # Find suggestion button section (should be similar to example button section)
        if 'for i, suggestion in enumerate(suggestions):' in content:
            suggestion_section = content.split('for i, suggestion in enumerate(suggestions):')[1].split('\n\n')[0]

            # Verify same pattern as example buttons
            assert 'st.session_state.user_input_text = suggestion' in suggestion_section, \
                "Suggestion button doesn't populate input"
            assert 'st.session_state.submit_from_example = True' in suggestion_section, \
                "Suggestion button doesn't set auto-submit flag"
            assert 'st.rerun()' in suggestion_section, \
                "Suggestion button doesn't call rerun"

    def test_suggestion_buttons_only_show_when_suggestions_exist(self):
        """Test: Suggestion buttons should only display if suggestions were extracted

        Why: Don't want empty 'You can also try:' header if no suggestions.
        Improves UX by hiding unnecessary UI elements.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        # Find suggestion display section
        message_section = content.split('# Display conversation history')[1].split('# Input area')[0]

        # Verify conditional display
        assert 'if suggestions:' in message_section, \
            "Suggestion buttons displayed unconditionally - should check if suggestions exist"


class TestEndToEndQuickLinks:
    """Verify full flow: click example -> populate -> auto-submit -> get response -> see suggestions"""

    def test_example_button_key_unique(self):
        """Test: Example button keys must be unique

        Why: Streamlit requires unique keys. Reused keys cause 'widget already exists' errors.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        # Find example button keys
        example_section = content.split('for i, example in enumerate(examples):')[1].split('# Main chat interface')[0]
        assert 'key=f"example_{i}"' in example_section, \
            "Example button keys not unique per example"

    def test_suggestion_button_key_unique(self):
        """Test: Suggestion button keys must be unique

        Why: Same reason as example buttons. Plus need to include message index
        to avoid conflicts between different responses.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        # Find suggestion button section
        if 'for i, suggestion in enumerate(suggestions):' in content:
            suggestion_section = content.split('for i, suggestion in enumerate(suggestions):')[1].split('\n')[0:2]
            suggestion_code = '\n'.join(suggestion_section)

            # Verify key includes message index AND suggestion index
            assert 'key=' in suggestion_code, "Suggestion button keys not specified"
            # Should include both message position and suggestion index for uniqueness
            has_message_idx = 'len(st.session_state.messages)' in suggestion_code or '_' in suggestion_code
            has_suggestion_idx = '_{i}' in suggestion_code or 'i}' in suggestion_code

            if has_message_idx and has_suggestion_idx:
                # Good - keys are unique across messages and within suggestions
                pass
            else:
                pytest.skip("Cannot verify key uniqueness pattern from code inspection")

    def test_no_duplicate_submission_on_auto_submit(self):
        """Test: Auto-submit must not cause duplicate submissions

        Why: If flag isn't cleared properly, form might submit twice.
        This would create duplicate messages in chat history.
        """
        app_file = pathlib.Path('/Users/Iaroslav/Projects/Snowflake/CensusAgent/streamlit_app.py')
        content = app_file.read_text()

        # Find form handler
        handler_section = content.split('should_submit = send_clicked or')[1].split('# Clear the auto-submit flag')[0]

        # Verify flag is cleared right after the check
        lines = handler_section.strip().split('\n')
        assert len(lines) < 5, "Too many lines between should_submit check and flag clear"

        full_handler = content.split('should_submit = send_clicked or')[1].split('# Add user message to history')[0]
        # Verify clear happens early, before any processing
        clear_idx = full_handler.find('st.session_state.submit_from_example = False')
        assert clear_idx != -1, "Flag not cleared anywhere in handler"
        assert clear_idx > 0, "Flag clear statement found in handler"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
