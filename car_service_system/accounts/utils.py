from functools import wraps
from django.shortcuts import render, redirect
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import random
from .models import UserProfile

# ==============================
# Role-based access decorator
# ==============================
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

            if request.user.role not in allowed:
                return render(request, 'accounts/forbidden.html', status=403)

            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


# ==============================
# OTP Utilities (Redis)
# ==============================
OTP_TTL_SECONDS = 600  # 10 minutes


def generate_otp(length=6):
    return ''.join(str(random.randint(0, 9)) for _ in range(length))


def set_user_otp(user: UserProfile):
    """
    Store OTP in Redis with TTL.
    """
    otp = generate_otp()
    cache.set(
        key=f"otp:{user.username}",
        value=otp,
        timeout=OTP_TTL_SECONDS
    )
    return otp


def verify_otp_code(user: UserProfile, code: str) -> bool:
    """
    Verify OTP from Redis.
    OTP is deleted after successful verification.
    """
    if not code:
        return False

    redis_otp = cache.get(f"otp:{user.username}")
    if not redis_otp:
        return False

    if str(code).strip() != str(redis_otp):
        return False

    # OTP verified → remove from Redis
    cache.delete(f"otp:{user.username}")
    return True


# ==============================
# Email OTP Sender
# ==============================
def send_otp_email(user: UserProfile, code: str) -> bool:
    if not user.email:
        return False

    subject = "Your verification code - Car Service System"
    from_email = settings.DEFAULT_FROM_EMAIL

    plain_message = f"""
Hello {user.username},

Your OTP verification code is: {code}

This code will expire in 10 minutes.

If you did not request this, please ignore this email.
"""

    html_message = render_to_string(
        'accounts/otp_email.html',
        {
            'username': user.username,
            'otp_code': code
        }
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=from_email,
        to=[user.email]
    )
    email.attach_alternative(html_message, "text/html")
    return email.send() > 0
