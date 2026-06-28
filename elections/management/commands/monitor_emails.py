from django.core.management.base import BaseCommand
from elections.utils import email_queue, email_rate_limiter
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Monitor email sending status and queue'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed queue information'
        )

    def handle(self, *args, **options):
        detailed = options['detailed']
        
        # Get queue status
        with email_queue.lock:
            queue_size = len(email_queue.queue)
            processing = email_queue.processing
        
        # Get rate limiter status
        now = timezone.now()
        with email_rate_limiter.lock:
            minute_emails = [t for t in email_rate_limiter.minute_emails if now - t < timedelta(minutes=1)]
            hour_emails = [t for t in email_rate_limiter.hour_emails if now - t < timedelta(hours=1)]
            
            minute_count = len(minute_emails)
            hour_count = len(hour_emails)
            
            can_send, reason = email_rate_limiter.can_send_email()
            wait_time = email_rate_limiter.get_wait_time()
        
        # Display status
        self.stdout.write("=== Email Sending Status ===")
        self.stdout.write(f"Queue Size: {queue_size} emails")
        self.stdout.write(f"Processing: {'Yes' if processing else 'No'}")
        self.stdout.write(f"Rate Limiter Status:")
        self.stdout.write(f"  Emails in last minute: {minute_count}/{email_rate_limiter.max_emails_per_minute}")
        self.stdout.write(f"  Emails in last hour: {hour_count}/{email_rate_limiter.max_emails_per_hour}")
        self.stdout.write(f"  Can send email: {'Yes' if can_send else 'No'}")
        
        if not can_send:
            self.stdout.write(f"  Reason: {reason}")
            self.stdout.write(f"  Wait time: {wait_time:.1f} seconds")
        
        # Show detailed queue information
        if detailed and queue_size > 0:
            self.stdout.write("\n=== Detailed Queue Information ===")
            for i, email_data in enumerate(email_queue.queue[:10]):  # Show first 10
                age = now - email_data['created_at']
                self.stdout.write(f"Email {i+1}:")
                self.stdout.write(f"  To: {email_data['recipient_list']}")
                self.stdout.write(f"  Subject: {email_data['subject']}")
                self.stdout.write(f"  Age: {age.total_seconds():.1f} seconds")
                self.stdout.write(f"  Retry count: {email_data['retry_count']}/{email_data['max_retries']}")
                self.stdout.write("")
            
            if queue_size > 10:
                self.stdout.write(f"... and {queue_size - 10} more emails in queue")
        
        # Show recommendations
        self.stdout.write("\n=== Recommendations ===")
        if queue_size > 0:
            self.stdout.write("• Queue has emails waiting to be sent")
            if not processing:
                self.stdout.write("• Email processing is not running - emails will be sent when next email is queued")
        
        if minute_count >= email_rate_limiter.max_emails_per_minute * 0.8:
            self.stdout.write("• Approaching minute rate limit - consider reducing batch size")
        
        if hour_count >= email_rate_limiter.max_emails_per_hour * 0.8:
            self.stdout.write("• Approaching hour rate limit - consider increasing delay between batches")
        
        if queue_size == 0 and minute_count == 0 and hour_count == 0:
            self.stdout.write("• No email activity detected")
        
        # Show usage tips
        self.stdout.write("\n=== Usage Tips ===")
        self.stdout.write("• Use --detailed flag to see queue contents")
        self.stdout.write("• Monitor this command regularly during bulk email operations")
        self.stdout.write("• Consider using a dedicated email service for high-volume sending") 