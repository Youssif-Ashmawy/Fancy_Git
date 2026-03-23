# Testing Guide for FancyGit

This directory contains the test suite for the FancyGit project.

## Test Structure

```
tests/
├── __init__.py                 # Package initialization
├── conftest.py                 # Pytest fixtures and configuration
├── test_git_error.py          # Unit tests for GitError dataclass
├── test_git_error_parser.py   # Unit tests for GitErrorParser
├── test_git_runner.py         # Unit tests for GitRunner
├── test_ai_engine.py          # Unit tests for AI Engine
├── test_config_manager.py     # Unit tests for Config Manager
├── test_model_provider.py     # Unit tests for Model Provider factory
├── test_providers.py          # Unit tests for AI providers (Ollama, OpenAI, Anthropic)
├── test_ai_integration.py     # Integration tests for AI architecture
├── test_fancygit_integration.py # Integration tests for FancyGit
├── test_conflict_parser_integration.py # Conflict parser integration tests
└── README.md                  # This file
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Test individual components in isolation
- Fast and focused
- Use mocks to avoid external dependencies
- **New AI Architecture Tests**: AI Engine, Config Manager, Model Provider, and AI providers

### Integration Tests (`@pytest.mark.integration`)
- Test multiple components working together
- Slower but more comprehensive
- Test real workflows
- **AI Integration Tests**: End-to-end AI architecture workflows

### Slow Tests (`@pytest.mark.slow`)
- Tests that take significant time to run
- Often involve real git operations
- Not run by default in quick test runs

## Running Tests

### Quick Test Run (Recommended for Development)
```bash
# Run unit and integration tests (excludes slow tests)
make test
# or
pytest -m "unit or integration" -v
```

### Run Specific Test Categories
```bash
# Only unit tests
make test-unit
# or
pytest -m "unit" -v

# Only integration tests
make test-integration
# or
pytest -m "integration" -v

# Only slow tests
make test-slow
# or
pytest -m "slow" -v
```

### Run All Tests
```bash
make test-all
# or
pytest -v --cov=src --cov-report=html --cov-report=term-missing
```

### Individual Test Files
```bash
pytest tests/test_git_error.py -v
pytest tests/test_git_error_parser.py -v
```

## Coverage

Tests generate coverage reports to show how much of the codebase is tested:

```bash
# Generate HTML coverage report
make test-unit

# View the report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Fixtures

### `temp_git_repo`
Creates a temporary git repository for testing:
```python
def test_something(temp_git_repo):
    # temp_git_repo is the path to a clean git repo
    # Automatically cleaned up after the test
    pass
```

### `sample_ai_messages`
Provides sample AI error messages for testing:
```python
def test_ai_analysis(sample_ai_messages):
    error_messages = sample_ai_messages
    # ... test with sample AI messages
```

### `mock_config_manager`
Provides a mock config manager for AI components:
```python
def test_ai_component(mock_config_manager):
    config_manager = mock_config_manager
    # ... test with mock configuration
```

### `temp_config_file`
Creates a temporary config file for testing:
```python
def test_config_persistence(temp_config_file):
    config_path = temp_config_file
    # ... test with temporary config file
```

## Writing New Tests

### Unit Test Example
```python
import pytest
from src.module import ClassToTest

@pytest.mark.unit
class TestClassToTest:
    def test_method_should_return_expected_result(self):
        # Arrange
        obj = ClassToTest()
        
        # Act
        result = obj.method()
        
        # Assert
        assert result == expected_value
```

### AI Architecture Unit Test Example
```python
import pytest
from unittest.mock import patch, MagicMock
from src.ai_engine import AIEngine

@pytest.mark.unit
class TestAIEngine:
    def test_analyze_error_messages(self, mock_config_manager, sample_ai_messages):
        # Arrange
        with patch('src.model_provider.ModelProvider.get_model') as mock_get_model:
            mock_provider = MagicMock()
            mock_provider._call_model.return_value = "Analysis result"
            mock_get_model.return_value = mock_provider
            
            ai_engine = AIEngine(mock_config_manager)
        
        # Act
        result = ai_engine.analyze_error_messages(sample_ai_messages)
        
        # Assert
        assert result == "Analysis result"
        mock_provider._call_model.assert_called_once()
```

### Integration Test Example
```python
import pytest
from unittest.mock import patch

@pytest.mark.integration
class TestWorkflow:
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_complete_workflow(self, mock_run_git):
        # Setup mock
        mock_run_git.return_value = (0, "success", "")
        
        # Test workflow
        # ...
```

## Best Practices

1. **Use descriptive test names** that explain what is being tested
2. **Follow Arrange-Act-Assert pattern** for clear test structure
3. **Mock external dependencies** to keep tests fast and reliable
4. **Use fixtures** for common setup code
5. **Mark tests appropriately** with `@pytest.mark.unit`, `@pytest.mark.integration`, or `@pytest.mark.slow`
6. **Test both happy path and error cases**
7. **Keep tests focused** - one assertion per test when possible

## CI/CD

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` branch

The CI pipeline runs:
1. Unit tests with coverage on all Python versions (3.8-3.11) and OS platforms
2. Integration tests
3. Coverage reporting to Codecov

## Troubleshooting

### Tests Fail with Import Errors
Make sure you're running from the project root:
```bash
cd /path/to/Fancy_Git
pytest tests/
```

### Git Command Tests Fail
Ensure git is installed and available in your PATH:
```bash
git --version
```

### Slow Tests Taking Too Long
Skip slow tests during development:
```bash
pytest -m "not slow" -v
```
