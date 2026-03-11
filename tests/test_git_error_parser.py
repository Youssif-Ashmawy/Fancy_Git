import pytest
from src.git_error_parser import GitErrorParser
from src.git_error import GitError

@pytest.mark.unit
class TestGitErrorParser:
    """Test cases for GitErrorParser class"""
    
    def setup_method(self):
        """Setup method called before each test"""
        self.parser = GitErrorParser()
    
    def test_detect_no_errors(self):
        """Test parsing clean git output"""
        stdout = "On branch main\nnothing to commit, working tree clean\n"
        stderr = ""
        
        errors = self.parser.detect_warnings_errors(stdout, stderr)
        
        assert len(errors) == 0
    
    def test_detect_error_patterns(self):
        """Test detection of various error patterns"""
        test_cases = [
            ("error: pathspec 'test.txt' did not match any files", "error", 1),
            ("fatal: not a git repository", "error", 1),
            ("failed to push some refs", "error", 1),
            ("rejected: non-fast-forward", "error", 1),
            ("conflict in README.md", "error", 1),
            ("merge conflict detected", "error", 2),  # "conflict" and "merge conflict" patterns match
            ("unable to checkout", "error", 1)
        ]
        
        for message, expected_severity, expected_count in test_cases:
            errors = self.parser.detect_warnings_errors(message, "")
            assert len(errors) == expected_count
            assert all(error.severity == expected_severity for error in errors)
            # Check that at least one error matches the full message
            assert any(error.message == message for error in errors)
            assert all(error.source == "stdout" for error in errors)
    
    def test_detect_warning_patterns(self):
        """Test detection of various warning patterns"""
        test_cases = [
            ("warning: LF will be replaced by CRLF", "warning", 2),  # Both "warning:" and "WARNING:" patterns match
            ("WARNING: file is too large", "warning", 2),  # Both patterns match
            ("Your branch is behind by 2 commits", "warning", 1),  # Only "behind" pattern matches
            ("Your branch is ahead by 1 commit", "warning", 1),  # Only "ahead" pattern matches
            ("branches have diverged", "warning", 1)  # Only "diverged" pattern matches
        ]
        
        for message, expected_severity, expected_count in test_cases:
            errors = self.parser.detect_warnings_errors(message, "")
            assert len(errors) == expected_count
            assert all(error.severity == expected_severity for error in errors)
            # Check that the message contains the expected pattern
            assert all(error.message in message or message in error.message for error in errors)
            assert all(error.source == "stdout" for error in errors)
    
    def test_detect_stderr_errors(self):
        """Test error detection in stderr"""
        stderr = "error: merge conflict in README.md\n"
        
        errors = self.parser.detect_warnings_errors("", stderr)
        
        assert len(errors) == 3  # "error:", "conflict", and "merge conflict" patterns match
        assert all(error.severity == "error" for error in errors)
        assert all(error.source == "stderr" for error in errors)
        # Check that at least one error contains the full message
        assert any("error: merge conflict in README.md" in error.message for error in errors)
    
    def test_multiple_errors_same_output(self):
        """Test detection of multiple errors in same output"""
        output = "error: first issue\nwarning: some warning\nfatal: critical error\n"
        
        errors = self.parser.detect_warnings_errors(output, "")
        
        assert len(errors) == 4  # warning matches both "warning:" and "WARNING:" patterns
        error_severities = [error.severity for error in errors]
        assert error_severities.count("error") == 2
        assert error_severities.count("warning") == 2
    
    def test_case_insensitive_matching(self):
        """Test that pattern matching is case insensitive"""
        test_cases = [
            ("ERROR: uppercase error", 1),
            ("Error: Title case error", 1),
            ("WARNING: uppercase warning", 2),  # Both "warning:" and "WARNING:" patterns match
            ("Warning: Title case warning", 2)   # Both patterns match
        ]
        
        for message, expected_count in test_cases:
            errors = self.parser.detect_warnings_errors(message, "")
            assert len(errors) == expected_count
            assert all(error.message == message for error in errors)
    
    def test_partial_word_matching(self):
        """Test that patterns match partial words correctly"""
        output = "This command failed because it was unable to complete\n"
        
        errors = self.parser.detect_warnings_errors(output, "")
        
        assert len(errors) == 2
        error_messages = [error.message for error in errors]
        assert any("failed" in msg for msg in error_messages)
        assert any("unable to" in msg for msg in error_messages)
    
    def test_empty_outputs(self):
        """Test handling of empty outputs"""
        errors = self.parser.detect_warnings_errors("", "")
        assert len(errors) == 0
    
    def test_complex_git_output(self, sample_git_outputs):
        """Test parsing realistic git command outputs"""
        # Test clean output
        clean_errors = self.parser.detect_warnings_errors(
            sample_git_outputs["clean_output"]["stdout"],
            sample_git_outputs["clean_output"]["stderr"]
        )
        assert len(clean_errors) == 0
        
        # Test error output
        error_errors = self.parser.detect_warnings_errors(
            sample_git_outputs["error_output"]["stdout"],
            sample_git_outputs["error_output"]["stderr"]
        )
        assert len(error_errors) == 1
        assert error_errors[0].severity == "error"
        assert "pathspec" in error_errors[0].message
