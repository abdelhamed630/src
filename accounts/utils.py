from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_otp_email(user_email: str, otp: str) -> None:
    """Send HTML OTP email to the user."""
    subject = 'Your Verification Code'
    from_email = settings.DEFAULT_FROM_EMAIL

    # Plain text fallback
    text_content = f'Your OTP code is: {otp}. It expires in 5 minutes.'

    # HTML content
    html_content = render_to_string('accounts/otp_email.html', {
        'otp': otp,
        'email': user_email,
    })

    msg = EmailMultiAlternatives(subject, text_content, from_email, [user_email])
    msg.attach_alternative(html_content, 'text/html')
    msg.send()
