#!/usr/bin/env python3
"""
Script to send email notifications about test status to the person who pushed the code.
"""

import smtplib
import os
import sys
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def get_commit_author_email():
    """Get the email of the person who made the commit."""
    # Try to get from environment variables first (GitHub Actions)
    if 'GITHUB_ACTOR' in os.environ:
        # For GitHub, we need to get the user's email from the API or use a default
        # This is a limitation - GitHub doesn't expose user emails directly
        return f"{os.environ['GITHUB_ACTOR']}@users.noreply.github.com"
    
    # Fallback to git command
    try:
        import subprocess
        result = subprocess.run(['git', 'log', '-1', '--pretty=format:%ae'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    
    return "unknown@example.com"


def send_email_notification(test_status, commit_hash, branch, repo_name, recipient_email):
    """Send email notification about test results."""
    
    # Email configuration
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    sender_email = os.environ.get('SENDER_EMAIL')
    sender_password = os.environ.get('SENDER_PASSWORD')
    
    print(f"DEBUG: SMTP Server: {smtp_server}")
    print(f"DEBUG: SMTP Port: {smtp_port}")
    print(f"DEBUG: Sender Email: {sender_email}")
    print(f"DEBUG: Recipient Email: {recipient_email}")
    print(f"DEBUG: Sender Password configured: {'Yes' if sender_password else 'No'}")
    
    if not sender_email or not sender_password:
        print("Error: SENDER_EMAIL and SENDER_PASSWORD environment variables are required")
        return False
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = f"Test Results for {repo_name} - {test_status.upper()}"
    
    # Email body
    status_emoji = "✅" if test_status == "passed" else "❌"
    status_color = "green" if test_status == "passed" else "red"
    
    body = f"""
    <html>
    <body>
        <h2>{status_emoji} Test Results for {repo_name}</h2>
        
        <table border="1" cellpadding="10" cellspacing="0">
            <tr>
                <td><strong>Status:</strong></td>
                <td style="color: {status_color}; font-weight: bold;">{test_status.upper()}</td>
            </tr>
            <tr>
                <td><strong>Repository:</strong></td>
                <td>{repo_name}</td>
            </tr>
            <tr>
                <td><strong>Branch:</strong></td>
                <td>{branch}</td>
            </tr>
            <tr>
                <td><strong>Commit:</strong></td>
                <td>{commit_hash}</td>
            </tr>
            <tr>
                <td><strong>Time:</strong></td>
                <td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
            </tr>
        </table>
        
        <br>
        <p>
            {get_status_message(test_status)}
        </p>
        
        <p>
            <small>This email was sent automatically by the CI/CD pipeline.</small>
        </p>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(body, 'html'))
    
    try:
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        
        print(f"Email notification sent successfully to {recipient_email}")
        return True
        
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False


def get_status_message(test_status):
    """Get appropriate status message based on test result."""
    if test_status == "passed":
        return """
        🎉 <strong>Congratulations!</strong> All tests passed successfully. 
        Your code is ready to be merged.
        """
    else:
        return """
        ⚠️ <strong>Action Required:</strong> Some tests failed. 
        Please review the test results and fix the issues before merging.
        """


def main():
    """Main function to handle command line arguments and send email."""
    if len(sys.argv) != 5:
        print("Usage: python send_email_notification.py <test_status> <commit_hash> <branch> <repo_name>")
        sys.exit(1)
    
    test_status = sys.argv[1]
    commit_hash = sys.argv[2]
    branch = sys.argv[3]
    repo_name = sys.argv[4]
    
    # Get the recipient email (commit author)
    recipient_email = get_commit_author_email()
    
    # Send notification
    success = send_email_notification(test_status, commit_hash, branch, repo_name, recipient_email)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
