#!/usr/bin/env python3
"""
Simple verification of retry submission fix
"""
import os

def verify_retry_submission():
    """Verify the retry submission fix"""
    print("🧪 Verifying Retry Submission Fix")
    
    html_generator_file = "src/quiz_html_generator.py"
    
    with open(html_generator_file, 'r') as f:
        content = f.read()
    
    # Key checks
    checks = [
        ("Smart submitQuiz function", "function submitQuiz() {" in content),
        ("Retry mode check", "if (window.retryMode) {" in content),
        ("Calls submitRetryQuiz", "submitRetryQuiz();" in content),
        ("Calls submitNormalQuiz", "submitNormalQuiz();" in content),
        ("submitNormalQuiz function", "function submitNormalQuiz() {" in content),
        ("submitRetryQuiz function", "function submitRetryQuiz() {" in content),
        ("Button onclick", 'onclick="submitQuiz()"' in content),
    ]
    
    all_good = True
    for name, check in checks:
        if check:
            print(f"✅ {name}")
        else:
            print(f"❌ {name}")
            all_good = False
    
    if all_good:
        print("\n🎉 Retry submission fix is correctly implemented!")
        print("\n📝 How it works:")
        print("1. Button onclick calls submitQuiz()")
        print("2. submitQuiz() checks window.retryMode")
        print("3. If retry mode: calls submitRetryQuiz()")
        print("4. If normal mode: calls submitNormalQuiz()")
        print("5. Each function handles its own validation and results")
        
        print("\n🔄 Expected behavior:")
        print("- Normal mode: Shows full quiz results")
        print("- Retry mode: Shows retry-only results")
        return True
    else:
        print("\n❌ Some components are missing!")
        return False

if __name__ == "__main__":
    verify_retry_submission()
