
from functools import wraps
from django.shortcuts import render, redirect
from django.utils import timezone
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import random
from datetime import timedelta
from .models import UserProfile


def role_required(allowed_roles):
    if isinstance(allowed_roles, str):
        allowed = {allowed_roles}
    else:
        allowed = set(allowed_roles)

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:user_login')
            try:
                role = request.user.role
            except Exception:
                return redirect('accounts:user_login')
            if role not in allowed:
                return render(request, 'accounts/forbidden.html', status=403)
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def generate_otp(length: int = 6) -> str:
    return ''.join(str(random.randint(0, 9)) for _ in range(length))


def set_user_otp(user: UserProfile, ttl_minutes: int = 10) -> str:
    code = generate_otp(6)
    user.otp_code = code
    user.otp_expires_at = timezone.now() + timedelta(minutes=ttl_minutes)
    user.save(update_fields=["otp_code", "otp_expires_at"])
    return code


def send_otp_email(user: UserProfile, code: str) -> bool:
    """
    Send OTP email to user with HTML template.
    Returns True if email was sent successfully, False otherwise.
    """
    if not user.email:
        return False
    
    subject = "Your verification code - Car Service System"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", None)
    
    if not from_email:
        # Log error in development
        if settings.DEBUG:
            print(f"ERROR: DEFAULT_FROM_EMAIL or EMAIL_HOST_USER not set. Cannot send OTP to {user.email}")
        return False
    
    # Plain text version (fallback for email clients that don't support HTML)
    plain_message = f"""Hello {user.username},

Your OTP verification code is: {code}

This code will expire in 10 minutes.

Please use this code to verify your account on the Car Service System.

If you did not request this code, please ignore this email or contact support.

---
This is an automated email from Car Service System.
Please do not reply to this email.
"""
    
    # HTML version from template
    try:
        html_message = render_to_string(
            'accounts/otp_email.html',
            {
                'username': user.username,
                'otp_code': code,
            }
        )
    except Exception as e:
        if settings.DEBUG:
            print(f"ERROR rendering HTML template: {str(e)}")
        html_message = None
    
    try:
        # Use EmailMultiAlternatives to send both plain text and HTML
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=from_email,
            to=[user.email]
        )
        
        # Attach HTML version if template rendered successfully
        if html_message:
            email.attach_alternative(html_message, "text/html")
        
        result = email.send(fail_silently=False)
        
        if settings.DEBUG:
            print(f"OTP email sent to {user.email}: {result}")
        return result > 0
    except Exception as e:
        # Log error in development
        if settings.DEBUG:
            print(f"ERROR sending OTP email to {user.email}: {str(e)}")
        return False


def verify_otp_code(user: UserProfile, code: str) -> bool:
    """
    Verify OTP code for user.
    Returns True if code is valid and not expired, False otherwise.
    """
    if not code or not code.strip():
        return False
    if not user.otp_code or not user.otp_expires_at:
        return False
    if timezone.now() > user.otp_expires_at:
        return False
    # Compare codes after stripping whitespace and converting to string
    return str(code).strip() == str(user.otp_code).strip()
