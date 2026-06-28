# Email Rate Limiting Solution

## Problem Solved

The original issue was that emails were being sent too quickly, hitting the rate limits of your email provider (Hostinger SMTP). This caused emails to be rejected or delayed.

## Solution Overview

We've implemented a comprehensive email rate limiting system that includes:

1. **Rate Limiting**: Prevents hitting email provider limits
2. **Email Queuing**: Queues emails for background processing
3. **Batching**: Sends emails in controlled batches
4. **Retry Mechanism**: Automatically retries failed emails
5. **Monitoring**: Tools to monitor email sending status

## Features

### Rate Limiting
- Configurable limits per minute and hour
- Provider-specific presets (Hostinger, Gmail, SendGrid, etc.)
- Automatic waiting when limits are reached

### Email Queuing
- In-memory queue for email processing
- Background thread processing
- Automatic retry on failure (up to 3 attempts)

### Batching
- Send emails in controlled batches
- Configurable delays between batches
- Progress tracking

## Usage

### 1. Configure Rate Limits

First, configure the rate limits for your email provider:

```bash
# For Hostinger (default)
python manage.py configure_email_limits --provider hostinger

# For Gmail
python manage.py configure_email_limits --provider gmail

# Custom limits
python manage.py configure_email_limits --provider custom --max-per-minute 5 --max-per-hour 50
```

### 2. Import Students with Rate Limiting

```bash
# Basic import without sending emails
python manage.py import_students students.xlsx

# Import with email sending (rate limited)
python manage.py import_students students.xlsx --send-emails

# Import with custom batch settings
python manage.py import_students students.xlsx --send-emails --batch-size 5 --delay-between-batches 120
```

### 3. Monitor Email Status

```bash
# Check current status
python manage.py monitor_emails

# Detailed queue information
python manage.py monitor_emails --detailed
```

## Email Provider Limits

| Provider | Per Minute | Per Hour | Notes |
|----------|------------|----------|-------|
| Hostinger | 10 | 100 | SMTP limits |
| Gmail | 20 | 500 | SMTP limits |
| SendGrid | 100 | 1000 | API limits |
| Mailgun | 100 | 1000 | API limits |
| Custom | 5 | 50 | Conservative |

## Configuration Options

### Batch Settings
- `--batch-size`: Number of emails per batch (default: 10)
- `--delay-between-batches`: Seconds between batches (default: 60)

### Rate Limiting
- `--max-per-minute`: Maximum emails per minute
- `--max-per-hour`: Maximum emails per hour

## Code Changes

### 1. Updated `elections/utils.py`
- Added `EmailRateLimiter` class
- Added `EmailQueue` class
- Added `send_rate_limited_email()` function
- Added `send_bulk_emails_with_rate_limiting()` function

### 2. Updated `import_students` command
- Added `--send-emails` flag
- Added batch configuration options
- Emails are now queued instead of sent immediately

### 3. Updated password reset view
- Uses rate-limited email sending

### 4. New management commands
- `configure_email_limits`: Configure rate limits
- `monitor_emails`: Monitor email status

## Best Practices

### 1. For Bulk Imports
```bash
# Conservative approach for large lists
python manage.py import_students large_list.xlsx --send-emails --batch-size 5 --delay-between-batches 120

# Monitor progress
python manage.py monitor_emails --detailed
```

### 2. For Regular Operations
```bash
# Standard import
python manage.py import_students students.xlsx --send-emails

# Check status
python manage.py monitor_emails
```

### 3. For High-Volume Sending
Consider using a dedicated email service like:
- SendGrid
- Mailgun
- Amazon SES
- Postmark

## Troubleshooting

### Emails Not Sending
1. Check if processing is running: `python manage.py monitor_emails`
2. Check rate limits: Look for "Rate limit reached" messages
3. Check email configuration in settings.py

### Slow Email Sending
1. Reduce batch size: `--batch-size 3`
2. Increase delay: `--delay-between-batches 180`
3. Check provider limits: `python manage.py configure_email_limits --provider hostinger`

### Failed Emails
1. Check logs for error messages
2. Emails are automatically retried up to 3 times
3. Failed emails are logged with details

## Monitoring

### Real-time Monitoring
```bash
# Watch email status
watch -n 10 python manage.py monitor_emails
```

### Log Monitoring
Look for these log messages:
- `"Rate limit reached: Minute limit reached. Waiting X seconds"`
- `"Email sent successfully to [email]"`
- `"Failed to send email to [email]: [error]"`

## Performance Tips

1. **Start Small**: Begin with small batch sizes and increase gradually
2. **Monitor Closely**: Use the monitoring command during bulk operations
3. **Use Appropriate Delays**: 60-120 seconds between batches is usually safe
4. **Check Provider Status**: Some providers have maintenance windows

## Migration from Old System

The new system is backward compatible. Existing code using `send_mail()` will continue to work, but you can gradually migrate to `send_rate_limited_email()` for better rate limiting.

## Future Enhancements

1. **Database Queue**: Store emails in database for persistence
2. **Redis Queue**: Use Redis for distributed processing
3. **Email Templates**: Support for HTML templates
4. **Analytics**: Track email delivery rates and failures
5. **Web Interface**: Admin interface for monitoring

## Support

If you encounter issues:

1. Check the monitoring command output
2. Review Django logs for error messages
3. Verify email provider settings
4. Test with a small batch first
5. Contact your email provider for specific limits 