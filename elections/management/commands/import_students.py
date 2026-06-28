from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from elections.models import OTPVerification
from django.utils import timezone
from datetime import timedelta
import random
import pandas as pd
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Import students from an Excel file and send password reset emails.'

    def add_arguments(self, parser):
        parser.add_argument('excel_path', type=str, help='Path to the Excel file')

    def handle(self, *args, **options):
        excel_path = options['excel_path']
        if not os.path.exists(excel_path):
            raise CommandError(f"File does not exist: {excel_path}")
        try:
            df = pd.read_excel(excel_path)
        except Exception as e:
            raise CommandError(f"Error reading Excel file: {e}")

        required_columns = {'email', 'full_name'}
        if not required_columns.issubset(df.columns):
            raise CommandError(f"Excel file must contain columns: {', '.join(required_columns)}")

        created, updated, errors = 0, 0, []
        for idx, row in df.iterrows():
            email = str(row['email']).strip().lower()
            full_name = str(row['full_name']).strip()
            if not email or not full_name:
                errors.append(f"Row {idx+2}: Missing required fields.")
                continue
            # Parse full_name: expected format 'Last First Second' (all separated by spaces)
            name_parts = full_name.split()
            last_name = name_parts[0] if len(name_parts) > 0 else ''
            first_name = name_parts[1] if len(name_parts) > 1 else ''
            second_name = name_parts[2] if len(name_parts) > 2 else ''
            try:
                user, user_created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'username': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'is_active': True,
                        'role': getattr(User, 'STUDENT', 'student'),
                    }
                )
                if not user_created:
                    updated += 1
                    user.username = email
                    user.first_name = first_name
                    user.last_name = last_name
                    if hasattr(user, 'role'):
                        user.role = getattr(User, 'STUDENT', 'student')
                    user.is_active = True
                    user.save()
                else:
                    created += 1
                self.send_password_reset_email(user)
            except Exception as e:
                errors.append(f"Row {idx+2}: {e}")
        self.stdout.write(self.style.SUCCESS(f"Created: {created}, Updated: {updated}."))
        if errors:
            self.stdout.write(self.style.WARNING(f"Errors: {len(errors)}. See details below."))
            for err in errors:
                self.stdout.write(self.style.WARNING(err))

    def send_password_reset_email(self, user):
        # Generate 6-digit OTP
        otp_code = str(random.randint(100000, 999999))
        
        # Save OTP to database (valid for 15 minutes)
        OTPVerification.objects.create(
            user=user,
            otp=otp_code,
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        
        subject = "Your Verification Code for College Election Portal"
        
        user_name = user.first_name or user.username
        intro_text = "You have been registered as an eligible voter for the NOCEN Student Union Election 2026."
        
        context = {
            'user_name': user_name,
            'intro_text': intro_text,
            'otp_code': otp_code,
            'reset_url': None,
        }
        
        html_message = render_to_string('emails/otp_email.html', context)
        
        message = (
            f"Hello {user_name},\n\n"
            f"{intro_text}\n"
            f"Your verification code to set your password is: {otp_code}\n\n"
            f"This code will expire in 15 minutes.\n"
            f"If you did not expect this email, please ignore it."
        )
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True, html_message=html_message)