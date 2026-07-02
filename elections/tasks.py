from django.utils import timezone
from datetime import timedelta
import random
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import OTPVerification, User
import logging

logger = logging.getLogger(__name__)

import time

def send_password_reset_email(user_id):
    try:
        # Throttle sending heavily (5s) to ensure ZeptoMail and recipient servers don't soft bounce
        time.sleep(5)
        user = User.objects.get(id=user_id)
        
        # Generate 6-digit OTP
        otp_code = str(random.randint(100000, 999999))
        
        # Save OTP to database (valid for 24 hours — extended for bulk onboarding)
        OTPVerification.objects.create(
            user=user,
            otp=otp_code,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        subject = "Your Verification Code for NOCEN Student Union Election 2026"
        
        user_name = user.first_name or user.username
        reset_url = f"{settings.FRONTEND_RESET_URL}?email={user.email}"
        intro_text = "You have been registered as an eligible voter for the NOCEN Student Union Election 2026."
        
        context = {
            'user_name': user_name,
            'intro_text': intro_text,
            'otp_code': otp_code,
            'reset_url': reset_url,
        }
        
        html_message = render_to_string('emails/otp_email.html', context)
        
        message = (
            f"Hello {user_name},\n\n"
            f"{intro_text}\n"
            f"Please visit the following link to activate your account and set your password:\n"
            f"{reset_url}\n\n"
            f"Your verification code is: {otp_code}\n\n"
            f"This code will expire in 24 hours.\n"
            f"If you did not expect this email, please ignore it."
        )
        
        # fail_silently=False to ensure we see ZeptoMail/SMTP errors in the qcluster logs
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False, html_message=html_message)
        logger.info(f"Successfully sent OTP to {user.email}")
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} does not exist.")
    except Exception as e:
        logger.error(f"Failed to send email to user_id {user_id}: {str(e)}")
        raise e  # re-raise so the task is marked as failed and can be retried
