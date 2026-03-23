import pytest
from src.git_error import GitError

@pytest.mark.unit
class TestGitError:
    """Test cases for GitError dataclass"""
    
    def test_git_error_creation_minimal(self):
        """Test creating GitError with minimal required fields"""
        error = GitError(source="stdout", message="error: test message")
        
        assert error.source == "stdout"
        assert error.message == "error: test message"
        assert error.severity == "unknown"
        assert error.type is None
        assert error.file is None
        assert error.line is None
    
    def test_git_error_creation_full(self):
        """Test creating GitError with all fields"""
        error = GitError(
            source="stderr",
            message="fatal: merge conflict",
            severity="error",
            type="MERGE_CONFLICT",
            file="README.md",
            line=42
        )
        
        assert error.source == "stderr"
        assert error.message == "fatal: merge conflict"
        assert error.severity == "error"
        assert error.type == "MERGE_CONFLICT"
        assert error.file == "README.md"
        assert error.line == 42
    
    def test_git_error_immutability(self):
        """Test that GitError is immutable"""
        error = GitError(source="stdout", message="test")
        
        with pytest.raises(AttributeError):
            error.source = "stderr" # type: ignore
        
        with pytest.raises(AttributeError):
            error.message = "changed"   #type: ignore
    
    def test_git_error_str_representation(self):
        """Test string representation of GitError"""
        error = GitError(
            source="stderr",
            message="error: test message",
            severity="error",
            type="TEST_ERROR",
            file="test.py",
            line=10
        )
        
        str_repr = str(error)
        assert "type: TEST_ERROR" in str_repr
        assert "source: stderr" in str_repr
        assert "message: error: test message" in str_repr
        assert "severity: error" in str_repr
        assert "file: test.py" in str_repr
        assert "line: 10" in str_repr
        assert "============================================================" in str_repr
    
    def test_git_error_equality(self):
        """Test GitError equality comparison"""
        error1 = GitError(source="stdout", message="test", severity="error")
        error2 = GitError(source="stdout", message="test", severity="error")
        error3 = GitError(source="stderr", message="test", severity="error")
        
        assert error1 == error2
        assert error1 != error3
