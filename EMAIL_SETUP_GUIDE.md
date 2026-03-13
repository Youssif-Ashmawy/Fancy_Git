# Email Notification Setup Guide

This guide explains how to configure email notifications for test results in your GitHub Actions workflow.

## Overview

The email notification system will automatically send test results to the person who pushed the code. The system includes:

- **Email notification script** (`scripts/send_email_notification.py`)
- **GitHub Actions workflow integration** (`.github/workflows/test.yml`)
- **Repository secrets configuration**

## Required Repository Secrets

You need to add the following secrets to your GitHub repository:

### 1. Go to Repository Settings
1. Navigate to your repository on GitHub
2. Go to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

### 2. Add the following secrets:

#### `SENDER_EMAIL`
The email address that will send the notifications.
- Example: `your-email@gmail.com`

#### `SENDER_PASSWORD`
The password or app password for the sender email.
- **Important**: For Gmail, use an App Password instead of your regular password
- [How to create Gmail App Password](https://support.google.com/accounts/answer/185833)

#### `SMTP_SERVER` (Optional)
The SMTP server address. Defaults to `smtp.gmail.com` if not provided.
- Gmail: `smtp.gmail.com`
- Outlook: `smtp-mail.outlook.com`
- Yahoo: `smtp.mail.yahoo.com`

#### `SMTP_PORT` (Optional)
The SMTP port number. Defaults to `587` if not provided.
- Gmail: `587` (TLS)
- Alternative: `465` (SSL)

## Gmail Setup (Recommended)

### 1. Enable 2-Factor Authentication
1. Go to your Google Account settings
2. Enable **2-Step Verification**

### 2. Create App Password
1. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
2. Select **Mail** for the app
3. Select **Other (Custom name)** and enter "GitHub Actions"
4. Copy the generated 16-character password
5. Use this password for the `SENDER_PASSWORD` secret

## How It Works

1. **Trigger**: Tests run on push to `developer` or `main` branches
2. **Email Detection**: The system automatically detects the commit author's email
3. **Notification**: Sends HTML email with test results
4. **Conditions**: 
   - Only runs on Ubuntu with Python 3.10 (to avoid duplicate emails)
   - Separate notifications for success and failure

## Email Content

The notification includes:
- ✅/❌ Test status (passed/failed)
- Repository name
- Branch name
- Commit hash
- Timestamp
- Actionable message based on status

## Testing

To test the email notifications:

1. **Local Testing**:
   ```bash
   python scripts/send_email_notification.py "passed" "test-hash" "main" "your-repo"
   ```

2. **Repository Testing**:
   - Push a small change to trigger the workflow
   - Check your email for the notification

## Troubleshooting

### Common Issues

1. **Email not received**:
   - Check spam/junk folder
   - Verify SMTP settings are correct
   - Ensure app password is used for Gmail

2. **Authentication failed**:
   - Use App Password for Gmail (not regular password)
   - Verify email and password are correct

3. **No email on push**:
   - Check workflow logs in GitHub Actions
   - Verify secrets are properly configured
   - Ensure workflow is triggered on correct branch

### Debug Mode

To enable debug logging, add this to the workflow:
```yaml
- name: Debug environment
  run: |
    echo "Sender email: ${{ secrets.SENDER_EMAIL }}"
    echo "SMTP server: ${{ secrets.SMTP_SERVER }}"
```

## Security Notes

- **Never commit credentials to your repository**
- Use repository secrets for all sensitive information
- Consider using a dedicated email account for notifications
- Regularly rotate your app passwords

## Customization

You can customize the email template by editing `scripts/send_email_notification.py`:
- Modify HTML template in the `send_email_notification` function
- Change status messages in `get_status_message`
- Add additional information to the email body

## Alternative Email Providers

### Outlook/Hotmail
- SMTP Server: `smtp-mail.outlook.com`
- Port: `587`
- Use your regular password (no app password needed)

### Yahoo Mail
- SMTP Server: `smtp.mail.yahoo.com`
- Port: `587`
- Use App Password (enable 2FA first)
