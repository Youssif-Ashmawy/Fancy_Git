import pytest
import tempfile
import os
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fancygit import FancyGit

@pytest.mark.integration
@pytest.mark.slow
class TestConflictParserIntegration:
    """Integration tests for conflict parser functionality"""
    
    def setup_method(self):
        """Setup method called before each test"""
        # Initialize FancyGit with mocked config
        with patch.object(FancyGit, '_load_commands', return_value=['add', 'commit', 'push', 'pull']):
            with patch.object(FancyGit, '_load_confirmation_state', return_value=True):
                with patch.object(FancyGit, '_load_ai_analysis_state', return_value=False):
                    with patch.object(FancyGit, '_load_animation_type', return_value='simple'):
                        self.fancy_git = FancyGit()
    
    def test_conflict_parser_no_conflicts(self, temp_git_repo):
        """Test conflict parser when no conflicts exist"""
        conflicts = self.fancy_git.conflict_parser()
        
        # Should return empty list when no conflicts
        assert isinstance(conflicts, list)
        assert len(conflicts) == 0
    
    def test_conflict_parser_method_exists(self):
        """Test that conflict_parser method exists and is callable"""
        assert hasattr(self.fancy_git, 'conflict_parser')
        assert callable(self.fancy_git.conflict_parser)
        
        # Should return a list
        result = self.fancy_git.conflict_parser()
        assert isinstance(result, list)
    
    def test_get_repo_state_integration(self, temp_git_repo):
        """Test repository state functionality"""
        repo_state = self.fancy_git.get_repo_state()
        
        # Should return a dictionary with expected keys
        assert isinstance(repo_state, dict)
        expected_keys = ['branch', 'clean', 'staged', 'modified', 'untracked', 'conflicts', 'ahead', 'behind']
        for key in expected_keys:
            assert key in repo_state
        
        # In a clean temp repo, should be clean with no conflicts
        assert repo_state['clean'] is True
        assert isinstance(repo_state['conflicts'], list)
        assert len(repo_state['conflicts']) == 0
