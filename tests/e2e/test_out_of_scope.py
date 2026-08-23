#!/usr/bin/env python3
"""Test that the app correctly rejects out-of-scope questions"""

import pytest
from src.cortex_analyst import CortexAnalyst


@pytest.mark.e2e
class TestOutOfScopeQuestions:
    """Verify graceful degradation for questions outside data scope"""

    def test_international_question_rejected(self):
        """Germany population should not be answered (US Census data only)"""
        question = "what is the population of Germany"

        result = CortexAnalyst.query(question, [])

        # Verify response indicates data is not available
        assert result is not None
        assert result['success'] == True

        # Should return no data
        assert len(result.get('data', [])) == 0, \
            "Germany question should not return census data"

        # Response should indicate it can't answer
        response_lower = result['response'].lower()

        # Should indicate this is outside available data
        impossible_keywords = [
            'cannot answer',
            'unable to answer',
            'not in',
            'don\'t have',
            'not available',
            'germany',
            'international',
            'outside',
            'not part'
        ]

        has_rejection = any(keyword in response_lower for keyword in impossible_keywords)
        assert has_rejection, \
            f"Response should indicate Germany data unavailable. Got: {result['response'][:200]}"

        print(f"✅ Correctly rejected Germany question")
        print(f"Response: {result['response'][:150]}...")

    def test_weather_question_rejected(self):
        """Weather data should not be answered (not Census data)"""
        question = "what was the weather in California in 2020"

        result = CortexAnalyst.query(question, [])

        assert result is not None
        assert result['success'] == True
        assert len(result.get('data', [])) == 0, \
            "Weather question should not return data"

        response_lower = result['response'].lower()

        # Should indicate weather data is not available
        weather_indicators = ['weather', 'cannot', 'don\'t have', 'not available', 'census']
        has_indication = any(indicator in response_lower for indicator in weather_indicators)
        assert has_indication, \
            f"Response should indicate weather data unavailable. Got: {result['response'][:200]}"

        print(f"✅ Correctly rejected weather question")

    def test_fictional_entity_rejected(self):
        """Questions about fictional entities should be rejected"""
        question = "what is the population of Atlantis"

        result = CortexAnalyst.query(question, [])

        assert result is not None
        assert result['success'] == True
        assert len(result.get('data', [])) == 0, \
            "Fictional place question should not return data"

        response_lower = result['response'].lower()
        rejection_keywords = ['cannot', 'don\'t', 'does not', 'not available', 'no data', 'atlantis']
        has_rejection = any(keyword in response_lower for keyword in rejection_keywords)
        assert has_rejection, \
            f"Response should indicate it cannot answer. Got: {result['response'][:200]}"

        print(f"✅ Correctly rejected fictional entity question")

    def test_time_period_outside_data_range(self):
        """Questions about future years should be rejected"""
        question = "what will be the population in 2050"

        result = CortexAnalyst.query(question, [])

        assert result is not None
        assert result['success'] == True

        # May or may not return data depending on how Cortex interprets it
        # But response should indicate 2050 data is not available
        response_lower = result['response'].lower()

        # Either no data or indication that future data isn't available
        no_data = len(result.get('data', [])) == 0
        mentions_future = any(word in response_lower for word in ['2050', 'future', 'forecast', 'predict'])

        assert no_data or mentions_future, \
            f"Should either have no data or mention future data limitation. Got: {result['response'][:200]}"

        print(f"✅ Correctly handled future date question")

    def test_response_offers_alternatives(self):
        """When rejecting questions, app should suggest what it CAN answer"""
        question = "what is the weather in California"

        result = CortexAnalyst.query(question, [])

        response = result['response']

        # Should mention what capabilities ARE available
        capability_keywords = [
            'can answer',
            'available data',
            'demographics',
            'census',
            'population',
            'age group',
            'example'
        ]

        has_capability_info = any(keyword in response.lower() for keyword in capability_keywords)
        assert has_capability_info, \
            f"Response should suggest what CAN be answered. Got: {response[:300]}"

        print(f"✅ Response includes helpful alternatives")
        print(f"Capabilities mentioned: {response[200:400]}...")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
