"""
Management command to resend OTP/password-reset emails to specific students.

Use this when you have soft bounces from ZeptoMail:

  1. Copy the bounced email addresses from ZeptoMail dashboard
  2. Paste them into a plain text file, one per line (e.g. bounced.txt)
  3. Run:
       python manage.py resend_emails --file bounced.txt

  Or pass emails directly on the command line:
       python manage.py resend_emails --emails student1@school.edu student2@school.edu

Options:
  --file      Path to a .txt file with one email address per line
  --emails    One or more email addresses passed directly as arguments
  --dry-run   Preview which users would be re-emailed without actually sending
"""

from django.core.management.base import BaseCommand, CommandError
from django_q.tasks import async_task
from elections.models import User
import os


class Command(BaseCommand):
    help = 'Resend OTP/password-reset emails to students with bounced or failed emails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Path to a .txt file containing one email address per line',
        )
        parser.add_argument(
            '--emails',
            nargs='+',
            type=str,
            help='One or more email addresses to resend to',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually queuing any tasks',
        )

    def handle(self, *args, **options):
        emails = []

        # --- Collect emails from file ---
        if options['file']:
            file_path = options['file']
            if not os.path.exists(file_path):
                raise CommandError(f"File not found: {file_path}")
            with open(file_path, 'r') as f:
                for line in f:
                    email = line.strip().lower()
                    if email and '@' in email:
                        emails.append(email)
            self.stdout.write(f"📂 Loaded {len(emails)} email(s) from {file_path}")

        # --- Collect emails from command line ---
        if options['emails']:
            cli_emails = [e.strip().lower() for e in options['emails'] if '@' in e]
            emails.extend(cli_emails)
            self.stdout.write(f"📋 Added {len(cli_emails)} email(s) from command line")

        if not emails:
            raise CommandError(
                "No emails provided. Use --file bounced.txt or --emails addr1@x.com addr2@x.com"
            )

        # Deduplicate
        emails = list(dict.fromkeys(emails))
        self.stdout.write(f"\n🔍 Processing {len(emails)} unique email address(es)...\n")

        found = []
        not_found = []

        for email in emails:
            try:
                user = User.objects.get(email=email)
                found.append(user)
            except User.DoesNotExist:
                not_found.append(email)

        # --- Report not found ---
        if not_found:
            self.stdout.write(self.style.WARNING(
                f"⚠️  {len(not_found)} email(s) NOT found in database:"
            ))
            for e in not_found:
                self.stdout.write(f"   - {e}")
            self.stdout.write("")

        # --- Dry run ---
        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS(
                f"✅ DRY RUN — would resend to {len(found)} user(s):"
            ))
            for user in found:
                self.stdout.write(f"   - {user.email} ({user.get_full_name() or user.username})")
            self.stdout.write("\nNo emails were sent. Remove --dry-run to actually send.")
            return

        # --- Queue async tasks ---
        queued = 0
        for user in found:
            async_task(
                'elections.tasks.send_password_reset_email',
                user.id,
                task_name=f"resend_{user.email}"
            )
            queued += 1
            self.stdout.write(f"   ✉️  Queued: {user.email}")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"✅ Successfully queued {queued} email(s) for resending."
        ))
        if not_found:
            self.stdout.write(self.style.WARNING(
                f"⚠️  {len(not_found)} address(es) were skipped (not in database)."
            ))
        self.stdout.write("\n💡 Monitor progress with: python manage.py monitor_emails")
