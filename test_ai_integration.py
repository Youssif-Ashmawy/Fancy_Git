#!/usr/bin/env python3
"""
Test script for AI integration with Ollama
"""
import sys
import os

# Add the project root to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from src.ollama_client import OllamaClient
from src.git_error import GitError

def test_ollama_connection():
    """Test basic Ollama connection"""
    print("🔍 Testing Ollama connection...")
    client = OllamaClient()
    
    if client.test_connection():
        print("✅ Ollama is running and accessible")
        
        models = client.get_available_models()
        if models:
            print(f"📋 Available models: {', '.join(models[:5])}")
            if len(models) > 5:
                print(f"    ... and {len(models) - 5} more")
        else:
            print("⚠️  No models found. You may need to pull a model first:")
            print("   ollama pull llama3.2")
        
        return True
    else:
        print("❌ Cannot connect to Ollama")
        print("   Make sure Ollama is installed and running:")
        print("   1. Install from https://ollama.ai/")
        print("   2. Run 'ollama serve' in terminal")
        print("   3. Pull a model: 'ollama pull llama3.2'")
        return False

def test_error_analysis():
    """Test error message analysis"""
    print("\n🧠 Testing error analysis...")
    client = OllamaClient()
    
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
        analysis = client.analyze_error_messages(sample_errors)
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

def test_fancygit_integration():
    """Test integration with FancyGit"""
    print("\n🔧 Testing FancyGit integration...")
    try:
        from fancygit import FancyGit
        
        # Create FancyGit instance
        fg = FancyGit()
        
        # Test AI toggle
        print("Testing AI toggle...")
        original_state = fg.ai_analysis_enabled
        fg.toggle_ai_analysis(False)
        print(f"AI disabled: {not fg.ai_analysis_enabled}")
        
        fg.toggle_ai_analysis(True)
        print(f"AI enabled: {fg.ai_analysis_enabled}")
        
        # Restore original state
        fg.toggle_ai_analysis(original_state)
        
        print("✅ FancyGit integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ FancyGit integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting AI Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Ollama Connection", test_ollama_connection),
        ("Error Analysis", test_error_analysis),
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
        print("🎉 All tests passed! AI integration is ready to use.")
        print("\nUsage examples:")
        print("  python fancygit.py ai status    # Check AI status")
        print("  python fancygit.py ai on        # Enable AI analysis")
        print("  python fancygit.py ai models    # List available models")
        print("  python fancygit.py status       # Test with real git command")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
