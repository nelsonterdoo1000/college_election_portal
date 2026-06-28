from django.utils import timezone
from datetime import timedelta
import random
from django.core.mail import send_mail
from django.conf import settings
from .models import OTPVerification, User
import logging

logger = logging.getLogger(__name__)

def send_password_reset_email(user_id):
    try:
        user = User.objects.get(id=user_id)
        
        # Generate 6-digit OTP
        otp_code = str(random.randint(100000, 999999))
        
        # Save OTP to database (valid for 15 minutes)
        OTPVerification.objects.create(
            user=user,
            otp=otp_code,
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        
        subject = "Your Verification Code for NOCEN Student Union Election 2026"
        message = (
            f"Hello {user.first_name or user.username},\n\n"
            f"You have been registered as an eligible voter for the NOCEN Student Union Election 2026.\n"
            f"Please visit the following link to activate your account and set your password:\n"
            f"{settings.FRONTEND_RESET_URL}?email={user.email}\n\n"
            f"Your verification code is: {otp_code}\n\n"
            f"This code will expire in 15 minutes.\n"
            f"If you did not expect this email, please ignore it."
        )
        
        # fail_silently=False to ensure we see ZeptoMail/SMTP errors in the qcluster logs
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        logger.info(f"Successfully sent OTP to {user.email}")
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} does not exist.")
    except Exception as e:
        logger.error(f"Failed to send email to user_id {user_id}: {str(e)}")
        raise e  # re-raise so the task is marked as failed and can be retried
