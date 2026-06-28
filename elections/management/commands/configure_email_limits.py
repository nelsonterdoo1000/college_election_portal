from django.core.management.base import BaseCommand
from django.conf import settings
from elections.utils import email_rate_limiter

class Command(BaseCommand):
    help = 'Configure email rate limits based on your email provider'

    def add_arguments(self, parser):
        parser.add_argument(
            '--provider',
            type=str,
            choices=['hostinger', 'gmail', 'sendgrid', 'mailgun', 'custom'],
            default='hostinger',
            help='Email provider to configure limits for'
        )
        parser.add_argument(
            '--max-per-minute',
            type=int,
            help='Maximum emails per minute (overrides provider default)'
        )
        parser.add_argument(
            '--max-per-hour',
            type=int,
            help='Maximum emails per hour (overrides provider default)'
        )

    def handle(self, *args, **options):
        provider = options['provider']
        max_per_minute = options['max_per_minute']
        max_per_hour = options['max_per_hour']

        # Provider-specific rate limits
        provider_limits = {
            'hostinger': {
                'max_per_minute': 10,
                'max_per_hour': 100,
                'description': 'Hostinger SMTP limits'
            },
            'gmail': {
                'max_per_minute': 20,
                'max_per_hour': 500,
                'description': 'Gmail SMTP limits'
            },
            'sendgrid': {
                'max_per_minute': 100,
                'max_per_hour': 1000,
                'description': 'SendGrid API limits'
            },
            'mailgun': {
                'max_per_minute': 100,
                'max_per_hour': 1000,
                'description': 'Mailgun API limits'
            },
            'custom': {
                'max_per_minute': 5,
                'max_per_hour': 50,
                'description': 'Conservative custom limits'
            }
        }

        if provider in provider_limits:
            limits = provider_limits[provider]
            if max_per_minute is None:
                max_per_minute = limits['max_per_minute']
            if max_per_hour is None:
                max_per_hour = limits['max_per_hour']
            
            self.stdout.write(f"Configuring rate limits for {provider}:")
            self.stdout.write(f"  Description: {limits['description']}")
            self.stdout.write(f"  Max per minute: {max_per_minute}")
            self.stdout.write(f"  Max per hour: {max_per_hour}")
            
            # Update the rate limiter
            email_rate_limiter.max_emails_per_minute = max_per_minute
            email_rate_limiter.max_emails_per_hour = max_per_hour
            
            self.stdout.write(self.style.SUCCESS("Rate limits configured successfully!"))
            
            # Show current email configuration
            self.stdout.write("\nCurrent email configuration:")
            self.stdout.write(f"  EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
            self.stdout.write(f"  EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
            self.stdout.write(f"  EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}")
            
        else:
            self.stdout.write(self.style.ERROR(f"Unknown provider: {provider}"))
            self.stdout.write("Available providers: hostinger, gmail, sendgrid, mailgun, custom")

        # Show usage tips
        self.stdout.write("\nUsage tips:")
        self.stdout.write("1. For bulk imports, use: python manage.py import_students file.xlsx --send-emails --batch-size 5 --delay-between-batches 120")
        self.stdout.write("2. Monitor email sending in Django logs")
        self.stdout.write("3. Consider using a dedicated email service for high-volume sending") 