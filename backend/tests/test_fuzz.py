import hypothesis.strategies as st
from hypothesis import given
from backend.security.validator import CommandValidator

validator = CommandValidator()

@given(st.text())
def test_fuzz_validator(command):
    """
    Fuzz the command validator with randomized text strings to ensure 
    it doesn't crash on unexpected inputs (e.g. weird encodings, null bytes).
    It should always return one of the 3 valid statuses.
    """
    status, reason = validator.evaluate(command)
    assert status in ["ALLOWED", "REQUIRES_APPROVAL", "BLOCKED"]
