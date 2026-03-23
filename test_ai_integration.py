#!/usr/bin/env python3
"""
Test script for the new AI Engine + Provider architecture
"""
import sys
import os

# Add the project root to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from src.config_manager import ConfigManager
from src.ai_engine import AIEngine
from src.git_error import GitError

def test_provider_connection():
    """Test that the configured provider connects successfully"""
    print("🔍 Testing AI provider connection...")
    config = ConfigManager()
    engine = AIEngine(config)
    
    if engine.analysis_provider.test_connection():
        print("✅ AI provider is running and accessible")
        
        # Check if Ollama-specific features are available
        from src.providers.ollama_model import OllamaModel
        if isinstance(engine.analysis_provider, OllamaModel):
            models = engine.analysis_provider.get_available_models()
            if models:
                print(f"📋 Available models: {', '.join(models[:5])}")
                if len(models) > 5:
                    print(f"    ... and {len(models) - 5} more")
            else:
                print("⚠️  No models found. You may need to pull a model first:")
                print("   ollama pull llama3.2")
        
        return True
    else:
        print("❌ Cannot connect to AI provider")
        print("   Make sure your configured provider is running.")
        return False

def test_error_analysis():
    """Test error message analysis through AIEngine"""
    print("\n🧠 Testing error analysis via AIEngine...")
    config = ConfigManager()
    engine = AIEngine(config)
    
    # Create sample error messages
    sample_errors = [
        {
            'severity': 'error',
            'type': 'MERGE_CONFLICT',
            'message': 'Merge conflict in src/main.py',
            'file': 'src/main.py',
            'line': 42
        },
        {
            'severity': 'warning',
            'type': 'DETACHED_HEAD',
            'message': 'You are in detached HEAD state',
            'file': None,
            'line': None
        }
    ]
    
    try:
        analysis = engine.analyze_error_messages(sample_errors)
        if analysis:
            print("✅ AI Analysis successful:")
            print("-" * 40)
            print(analysis)
            print("-" * 40)
            return True
        else:
            print("❌ AI Analysis failed")
            return False
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return False

def test_explain_command():
    """Test the explain command through AIEngine"""
    print("\n💡 Testing explain command via AIEngine...")
    config = ConfigManager()
    engine = AIEngine(config)
    
    try:
        response = engine.explain_command("rebase")
        if response:
            print("✅ Explain command successful:")
            print("-" * 40)
            print(response[:500])  # First 500 chars
            print("-" * 40)
            return True
        else:
            print("❌ Explain command failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_fancygit_integration():
    """Test integration with FancyGit"""
    print("\n🔧 Testing FancyGit integration...")
    try:
        from fancygit import FancyGit
        
        # Create FancyGit instance (this will test that AIEngine initializes correctly)
        fg = FancyGit()
        
        # Test AI toggle
        print("Testing AI toggle...")
        original_state = fg.config_manager.config.ai_analysis_enabled
        fg.toggle_ai_analysis(False)
        print(f"AI disabled: {not fg.config_manager.config.ai_analysis_enabled}")
        
        fg.toggle_ai_analysis(True)
        print(f"AI enabled: {fg.config_manager.config.ai_analysis_enabled}")
        
        # Restore original state
        fg.toggle_ai_analysis(original_state)
        
        print("✅ FancyGit integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ FancyGit integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting AI Engine Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Provider Connection", test_provider_connection),
        ("Error Analysis", test_error_analysis),
        ("Explain Command", test_explain_command),
        ("FancyGit Integration", test_fancygit_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! AI Engine integration is ready.")
        print("\nUsage examples:")
        print("  python fancygit.py ai status    # Check AI status")
        print("  python fancygit.py ai on        # Enable AI analysis")
        print("  python fancygit.py ai models    # List available models")
        print("  python fancygit.py explain push  # Explain a git command")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
