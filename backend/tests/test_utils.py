"""Test utilities and helper functions."""


def extract_error_from_response(response_data):
    """Extract error from FastAPI error response structure."""
    if "detail" in response_data and isinstance(response_data["detail"], dict) and "error" in response_data["detail"]:
        return response_data["detail"]["error"]
    elif "error" in response_data:
        return response_data["error"]
    else:
        return None


def assert_error_response(response_data, expected_code, expected_message_contains=None):
    """Helper to assert error response structure and content."""
    error = extract_error_from_response(response_data)
    assert error is not None, f"No error found in response: {response_data}"
    assert error["code"] == expected_code, f"Expected error code {expected_code}, got {error['code']}"
    
    if expected_message_contains:
        assert expected_message_contains.lower() in error["message"].lower(), \
            f"Expected '{expected_message_contains}' in error message: {error['message']}"
