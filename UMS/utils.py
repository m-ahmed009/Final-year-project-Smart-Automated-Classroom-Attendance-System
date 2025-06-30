import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
import logging
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator


# create an instance to store the success and error message

logger = logging.getLogger(__name__)

# create template for approval email
def get_approval_email_template(user, random_password):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Account Approval</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                background: #ffffff;
                padding: 20px;
                border-radius: 8px;
                margin: auto;
            }}
            .header {{
                background: #007bff;
                color: white;
                padding: 15px;
                text-align: center;
            }}
            .content {{
                padding: 20px;
                font-size: 16px;
            }}
            .credentials {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin-top: 10px;
            }}
            .footer {{
                margin-top: 20px;
                text-align: center;
                color: #777;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">Your Account has been Approved!</div>
            <div class="content">
                <p>Dear <strong>{user.first_name}</strong>,</p>
                <p>Your account has been successfully approved.</p>
                <p><strong>Username:</strong> {user.username}</p>
                <p><strong>Password:</strong> {random_password}</p>
                <p>Please change your password after logging in.</p>
            </div>
            <div class="footer">Best Regards,<br>Admin Team</div>
        </div>
    </body>
    </html>
    """



#create basic  function for send email
def send_email(subject, recipient_email, message):
    """ Sends an email using SMTP. """
    sender_email = settings.EMAIL_HOST_USER
    password = settings.EMAIL_HOST_PASSWORD

    try:
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "html"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient_email, msg.as_string())

        logger.info(f"Email sent successfully to {recipient_email}")
    except Exception as e:
        logger.error(f" Email sending failed to {recipient_email}: {str(e)}")



#create function for send message username and password and also call a send email function

def send_approval_email(user, random_password):
    subject = "Your Account has been Approved!"
    message = get_approval_email_template(user, random_password)
    send_email(subject, user.email, message)
logger = logging.getLogger(__name__)


#create function where reset password email template  defined

def get_reset_password_email_template(user, protocol, domain, uid, token):
    """ Returns an HTML template for password reset email. """
    
    reset_link = f"{protocol}://{domain}/ums/reset/{uid}/{token}/"  # Added 'ums/' here

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Password Reset</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                background: #ffffff;
                padding: 20px;
                border-radius: 8px;
                margin: auto;
            }}
            .header {{
                background: #dc3545;
                color: white;
                padding: 15px;
                text-align: center;
            }}
            .content {{
                padding: 20px;
                font-size: 16px;
            }}
            .btn {{
                display: block;
                max-width: 200px;
                background: #007bff;
                color: white;
                text-align: center;
                padding: 10px;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px auto;
                font-weight: bold;
            }}
            .footer {{
                margin-top: 20px;
                text-align: center;
                color: #777;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">Password Reset Request</div>
            <div class="content">
                <p>Hello <strong>{user.first_name}</strong>,</p>
                <p>You requested a password reset. Click the button below to reset your password:</p>
                <a href="{reset_link}" class="btn">Reset Your Password</a>
                <p>If you did not request this, please ignore this email.</p>
            </div>
            <div class="footer">Best regards,<br>Admin Team</div>
        </div>
    </body>
    </html>
  
    
  """


#create function for send email to reset pasword.

def send_reset_password_email(user, request):
    """ Sends a password reset email with a secure token link. """
    if not user.email:
        raise ValueError(f"User {user.username} does not have an email address!")

    if user.pk is None:
        raise ValueError(f"User {user.username} has no primary key (ID)!")

    uid = urlsafe_base64_encode(force_bytes(str(user.pk)))  # Ensure it's a string
    token = default_token_generator.make_token(user)
    domain = request.get_host()
    protocol = "https" if request.is_secure() else "http"

    reset_link = f"{protocol}://{domain}/ums/reset/{uid}/{token}/"
    email_template = get_reset_password_email_template(user, protocol, domain, uid, token)
    print(f"Generated reset link: {reset_link}")


    print(f"Generated reset link: {reset_link}")  # Debugging

    try:
        send_email(
            subject="Password Reset Request",
            recipient_email=user.email,
            message=email_template
        )
        logger.info(f"Password reset email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")
