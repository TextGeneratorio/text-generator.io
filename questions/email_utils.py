import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sellerinfo import AWS_SMTP_PASSWORD, AWS_SMTP_USERNAME, AWS_REGION, FROM_EMAIL

SMTP_HOST = f"email-smtp.{AWS_REGION}.amazonaws.com"
SMTP_PORT = 587


def send_password_reset_email(to_email: str, reset_link: str):
    subject = "Reset your Text Generator password"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333;">Reset your password</h2>
        <p>We received a request to reset the password for your Text Generator account.</p>
        <p>Click the button below to reset your password. This link expires in 1 hour.</p>
        <p style="margin: 30px 0;">
            <a href="{reset_link}"
               style="background: linear-gradient(90deg, #d79f2a, #d34675); color: white;
                      padding: 12px 24px; text-decoration: none; border-radius: 4px;
                      font-weight: 500; display: inline-block;">
                Reset Password
            </a>
        </p>
        <p>Or copy and paste this link into your browser:</p>
        <p style="color: #555; word-break: break-all;">{reset_link}</p>
        <p style="color: #888; font-size: 12px; margin-top: 30px;">
            If you did not request a password reset, you can safely ignore this email.
            Your password will not be changed.
        </p>
    </body>
    </html>
    """
    text_body = (
        f"Reset your Text Generator password\n\n"
        f"Click the link below to reset your password (expires in 1 hour):\n\n"
        f"{reset_link}\n\n"
        f"If you did not request this, you can safely ignore this email."
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(AWS_SMTP_USERNAME, AWS_SMTP_PASSWORD)
        server.sendmail(FROM_EMAIL, to_email, msg.as_string())
