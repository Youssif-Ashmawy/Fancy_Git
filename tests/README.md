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
├── test_fancygit_integration.py # Integration tests for FancyGit
├── test_conflict_parser_integration.py # Conflict parser integration tests
└── README.md                  # This file
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Test individual components in isolation
- Fast and focused
- Use mocks to avoid external dependencies

### Integration Tests (`@pytest.mark.integration`)
- Test multiple components working together
- Slower but more comprehensive
- Test real workflows

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

### `sample_git_outputs`
Provides sample git command outputs:
```python
def test_parser(sample_git_outputs):
    clean_output = sample_git_outputs["clean_output"]
    error_output = sample_git_outputs["error_output"]
    # ... test with sample data
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
