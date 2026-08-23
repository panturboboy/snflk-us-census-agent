"""Test: Metadata cache non-blocking fix

Why this test exists:
- Previous implementation: SemanticMetadataCache._refresh() raised exceptions on failures
- This caused validator initialization to fail silently
- Second queries would hang because validator wasn't available
- Fix: Made refresh non-blocking with per-table error handling
- This test verifies cache degrades gracefully instead of blocking
"""

import pytest
from unittest.mock import Mock, patch
from src.validation.schema_cache import SemanticMetadataCache


@pytest.mark.unit
class TestMetadataCacheNonBlocking:
    """Verify cache doesn't block on metadata query failures"""

    def test_cache_init_doesnt_raise_on_provider_error(self):
        """Test: Cache initialization must not raise exceptions

        Why: If cache init raises, validator init fails, second queries hang.
        Cache must be resilient to Snowflake metadata query failures.
        """
        with patch('src.validation.schema_cache.SemanticMetadataProvider') as MockProvider:
            # Mock provider to fail on grain lookup
            mock_provider = Mock()
            mock_provider.get_fact_table_grain.side_effect = Exception("Snowflake error")
            MockProvider.return_value = mock_provider

            # Cache init should NOT raise
            cache = SemanticMetadataCache(refresh_minutes=60)
            assert cache is not None

    def test_cache_refresh_continues_on_table_error(self):
        """Test: Cache refresh must continue if one table fails

        Why: If FACT_POPULATION_AGE fails but we need grain for another table,
        we should still be able to use the cache with partial data.
        Per-table error handling prevents cascade failures.
        """
        cache = SemanticMetadataCache(refresh_minutes=60)

        with patch.object(cache.provider, 'get_fact_table_grain') as mock_grain:
            # First table succeeds, second fails
            mock_grain.side_effect = [
                ['BLOCK_GROUP', 'AGE_ID'],  # FACT_POPULATION_AGE succeeds
                Exception("Metadata query failed"),  # FACT_RACE_ETHNICITY fails
                ['BLOCK_GROUP']  # FACT_HOUSEHOLD_COMPOSITION succeeds
            ]

            with patch.object(cache.provider, 'get_table_row_count') as mock_row_count:
                mock_row_count.return_value = 1000

                # Refresh should NOT raise even though one table failed
                try:
                    cache._refresh()
                except Exception as e:
                    pytest.fail(f"Cache refresh raised exception: {e}")

    def test_cache_works_with_partial_data(self):
        """Test: Cache can be used even if some tables failed

        Why: Validator should work with whatever grain data is available.
        Partial cache is better than no validator.
        """
        from datetime import datetime

        cache = SemanticMetadataCache(refresh_minutes=60)

        # Manually set partial cache with recent timestamp
        cache.cache['grain:FACT_POPULATION_AGE'] = ['BLOCK_GROUP', 'AGE_ID', 'SEX']
        cache.last_refresh = datetime.now()  # Mark as fresh so no refresh attempts

        # Should be able to get cached grain without triggering refresh
        grain = cache.get_grain('FACT_POPULATION_AGE')
        assert grain == ['BLOCK_GROUP', 'AGE_ID', 'SEX']

    def test_cache_no_exception_raised_on_refresh(self):
        """Test: _refresh() must never raise exceptions

        Why: Previous code had `raise` at end of except block.
        This caused validator init to fail, breaking second queries.
        """
        cache = SemanticMetadataCache(refresh_minutes=60)

        with patch.object(cache.provider, 'get_fact_table_grain') as mock_grain:
            # Make all calls fail
            mock_grain.side_effect = Exception("All metadata lookups failed")

            with patch.object(cache.provider, 'get_table_row_count') as mock_row_count:
                mock_row_count.side_effect = Exception("All row count lookups failed")

                # Refresh should NOT raise
                try:
                    cache._refresh()
                except Exception as e:
                    pytest.fail(f"_refresh() must not raise, but raised: {type(e).__name__}: {e}")

    def test_validator_can_work_without_grain_data(self):
        """Test: Validator can process queries even if grain lookups failed

        Why: If cache is empty, grain validation will skip gracefully.
        Queries shouldn't hang just because metadata is unavailable.
        """
        from src.validation.validator import QueryValidator

        cache = SemanticMetadataCache(refresh_minutes=60)

        # Cache is empty - no grain data loaded
        assert len(cache.cache) == 0 or all(v is None for v in cache.cache.values())

        # Validator should still init without hanging
        validator = QueryValidator(cache)
        assert validator is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
