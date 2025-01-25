import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
from typing import Optional

def send_welcome_email(email: str, password: str, first_name: str, class_name: str) -> bool:
    """Send a welcome email to new students with their login credentials"""
    try:
        # Get email configuration from app config
        smtp_host = current_app.config.get('SMTP_HOST')
        smtp_port = current_app.config.get('SMTP_PORT')
        smtp_user = current_app.config.get('SMTP_USER')
        smtp_password = current_app.config.get('SMTP_PASSWORD')
        from_email = current_app.config.get('DEFAULT_FROM_EMAIL')
        
        if not all([smtp_host, smtp_port, smtp_user, smtp_password, from_email]):
            current_app.logger.error("Missing email configuration")
            return False

        # Create email message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = email
        msg['Subject'] = f"Welcome to {class_name}!"
        
        # Create email body
        body = f"""Hello {first_name},

Welcome to {class_name}! Here are your login credentials:

Email: {email}
Password: {password}

Please login at: {current_app.config.get('BASE_URL')}

You'll be prompted to change your password after your first login.

Best regards,
The {class_name} Team
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {email}: {str(e)}")
        return False
