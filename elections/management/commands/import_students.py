from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
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
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        frontend_reset_url = getattr(settings, 'FRONTEND_RESET_URL', 'https://nocenelections.com/reset-password')
        reset_url = f"{frontend_reset_url}/{uid}/{token}/"
        subject = "Set your password for College Election Portal"
        message = f"Hello {user.first_name or user.username},\n\nYou have been registered as an eligible voter for the NOCEN Student Union Election 2025. Please set your password using the link below:\n{reset_url}\n\nIf you did not expect this email, please ignore it."
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True) 