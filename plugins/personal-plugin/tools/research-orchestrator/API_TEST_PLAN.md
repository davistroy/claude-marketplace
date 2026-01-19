# API Test Plan: OpenAI and Gemini Provider Modules

**Date:** 2026-01-17
**Version:** 1.0
**Scope:** Testing OpenAI and Gemini API provider modules in research-orchestrator

## 1. Overview

This test plan covers the `OpenAIProvider` and `GoogleProvider` classes that interact with external APIs for deep research functionality. Tests are organized into unit tests (with mocks) and integration tests (with actual APIs).

## 2. Modules Under Test

| Module | File | Key Classes/Methods |
|--------|------|---------------------|
| OpenAI Provider | `providers/openai.py` | `OpenAIProvider`, `execute()`, `_poll_for_completion()`, `_extract_content()` |
| Google Provider | `providers/google.py` | `GoogleProvider`, `execute()`, `_poll_for_completion()`, `_extract_content()` |
| Base Provider | `providers/base.py` | `BaseProvider`, `_validate_api_key()`, `_status_update()` |

## 3. Test Categories

### 3.1 Unit Tests (Mocked APIs)

#### 3.1.1 BaseProvider Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| BP-001 | `test_validate_api_key_missing` | Call `_validate_api_key()` with no API key | Raises `ValueError` |
| BP-002 | `test_validate_api_key_present` | Call `_validate_api_key()` with valid key | No exception |
| BP-003 | `test_status_update_exists` | Verify `_status_update` method exists | Method callable |
| BP-004 | `test_status_update_with_callback` | Call `_status_update` with orchestrator callback | Callback invoked |
| BP-005 | `test_status_update_without_callback` | Call `_status_update` with no callback | No exception (no-op) |

#### 3.1.2 OpenAI Provider Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| OA-001 | `test_openai_provider_name` | Check provider name property | Returns "openai" |
| OA-002 | `test_openai_get_model_default` | Get model without env override | Returns default model |
| OA-003 | `test_openai_get_model_override` | Get model with env override | Returns env model |
| OA-004 | `test_openai_execute_success` | Execute with mocked successful response | Returns SUCCESS status |
| OA-005 | `test_openai_execute_api_failure` | Execute with mocked API error | Returns FAILED status |
| OA-006 | `test_openai_execute_timeout` | Execute exceeding timeout | Returns TIMEOUT status |
| OA-007 | `test_openai_poll_completion_success` | Poll until completed status | Returns content |
| OA-008 | `test_openai_poll_completion_failed` | Poll returns failed status | Returns FAILED status |
| OA-009 | `test_openai_extract_content_string` | Extract content from string output | Returns string |
| OA-010 | `test_openai_extract_content_list` | Extract content from list output | Returns joined content |
| OA-011 | `test_openai_reasoning_summary_fallback` | Test fallback when org not verified | Retries without reasoning |
| OA-012 | `test_openai_status_update_called` | Verify status updates during polling | `_status_update` called |
| OA-013 | `test_openai_missing_api_key` | Execute without API key | Returns error about missing key |

#### 3.1.3 Google Provider Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| GP-001 | `test_google_provider_name` | Check provider name property | Returns "gemini" |
| GP-002 | `test_google_get_agent_default` | Get agent without env override | Returns default agent |
| GP-003 | `test_google_get_agent_override` | Get agent with env override | Returns env agent |
| GP-004 | `test_google_execute_success` | Execute with mocked successful response | Returns SUCCESS status |
| GP-005 | `test_google_execute_api_failure` | Execute with mocked API error | Returns FAILED status |
| GP-006 | `test_google_execute_timeout` | Execute exceeding timeout | Returns TIMEOUT status |
| GP-007 | `test_google_poll_completion_done_flag` | Poll with done=True flag | Returns content |
| GP-008 | `test_google_poll_completion_status_completed` | Poll with status="completed" | Returns content |
| GP-009 | `test_google_poll_completion_status_failed` | Poll with status="failed" | Returns FAILED |
| GP-010 | `test_google_extract_content_outputs` | Extract from outputs[-1].text | Returns text |
| GP-011 | `test_google_extract_content_result` | Extract from result attribute | Returns text |
| GP-012 | `test_google_extract_content_response_candidates` | Extract from response.candidates | Returns text |
| GP-013 | `test_google_extract_content_fallback` | Extract when all formats fail | Returns str(interaction) |
| GP-014 | `test_google_status_update_called` | Verify status updates during polling | `_status_update` called |
| GP-015 | `test_google_missing_api_key` | Execute without API key | Returns error about missing key |
| GP-016 | `test_google_interaction_id_extraction` | Test interaction ID from various attrs | Extracts from name/id/interaction_id |

### 3.2 Integration Tests (Against Orchestrator)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| INT-001 | `test_orchestrator_with_openai_mock` | Execute orchestrator with mocked OpenAI | Completes without errors |
| INT-002 | `test_orchestrator_with_google_mock` | Execute orchestrator with mocked Google | Completes without errors |
| INT-003 | `test_orchestrator_status_callback_openai` | Status callback called for OpenAI | Callback receives updates |
| INT-004 | `test_orchestrator_status_callback_google` | Status callback called for Google | Callback receives updates |
| INT-005 | `test_orchestrator_parallel_execution` | Execute all providers in parallel | All providers execute concurrently |

## 4. Test Infrastructure Requirements

### 4.1 Fixtures

```python
@pytest.fixture
def openai_provider():
    """Create OpenAI provider with test config."""
    config = ProviderConfig(name="openai", api_key="test-key", timeout_seconds=60)
    return OpenAIProvider(config, Depth.BRIEF)

@pytest.fixture
def google_provider():
    """Create Google provider with test config."""
    config = ProviderConfig(name="gemini", api_key="test-key", timeout_seconds=60)
    return GoogleProvider(config, Depth.BRIEF)

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    # Returns configured mock

@pytest.fixture
def mock_google_client():
    """Mock Google genai client for testing."""
    # Returns configured mock
```

### 4.2 Mock Configurations

**OpenAI Response Mock:**
```python
class MockOpenAIResponse:
    id = "resp_123"
    status = "completed"
    output = [{"type": "text", "text": "Research result"}]
    usage = {"total_tokens": 1000}
```

**Google Interaction Mock:**
```python
class MockGoogleInteraction:
    name = "interactions/123"
    done = True
    outputs = [MockOutput(text="Research result")]
```

## 5. Known Issues to Test

### 5.1 Critical Bug: Missing `_status_update` Method

**Issue:** Both `OpenAIProvider` (lines 65, 141) and `GoogleProvider` (line 125) call `self._status_update()` which is NOT defined in `BaseProvider`.

**Test:** BP-003 through BP-005 verify the fix for this issue.

**Fix Required:** Add `_status_update` method to `BaseProvider`.

## 6. Test Execution Commands

```bash
# Run all provider tests
cd plugins/personal-plugin/tools/research-orchestrator
PYTHONPATH=src pytest tests/test_providers.py -v

# Run with coverage
PYTHONPATH=src pytest tests/test_providers.py -v --cov=research_orchestrator.providers --cov-report=term-missing

# Run specific test
PYTHONPATH=src pytest tests/test_providers.py::TestOpenAIProvider::test_openai_execute_success -v
```

## 7. Success Criteria

- [x] All unit tests pass (100% pass rate) - **63 tests passing**
- [x] `_status_update` bug is fixed and verified
- [x] OpenAI provider executes without AttributeError
- [x] Google provider executes without AttributeError
- [x] Status callbacks propagate correctly from providers to orchestrator
- [x] Content extraction handles all documented response formats
- [x] Timeout handling works correctly for both providers
- [x] Error handling captures and reports API failures appropriately

**Test Execution Date:** 2026-01-17
**Results:** 63/63 tests passed (100% pass rate)

## 8. Test File Location

Tests will be created at:
```
plugins/personal-plugin/tools/research-orchestrator/tests/test_providers.py
```
