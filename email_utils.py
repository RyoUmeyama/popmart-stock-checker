#!/usr/bin/env python3
"""
Shared Email Utility Module
Provides robust SMTP email sending with retry logic
"""

import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List


def send_email_with_retry(
    smtp_server: str,
    smtp_port: int,
    username: str,
    password: str,
    from_email: str,
    to_email: str,
    subject: str,
    text_content: str,
    html_content: Optional[str] = None,
    max_retries: int = 3,
    retry_delay: int = 5,
    timeout: int = 30
) -> bool:
    """
    Send email with retry logic for handling temporary SMTP connection issues.

    Args:
        smtp_server: SMTP server hostname
        smtp_port: SMTP server port
        username: SMTP username
        password: SMTP password
        from_email: Sender email address
        to_email: Recipient email address (can be comma-separated for multiple recipients)
        subject: Email subject
        text_content: Plain text content
        html_content: HTML content (optional)
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Delay between retries in seconds (default: 5)
        timeout: SMTP connection timeout in seconds (default: 30)

    Returns:
        bool: True if email sent successfully, False otherwise

    Raises:
        Exception: Re-raises exception after all retry attempts fail
    """
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    # Attach text content
    part1 = MIMEText(text_content, 'plain', 'utf-8')
    msg.attach(part1)

    # Attach HTML content if provided
    if html_content:
        part2 = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part2)

    # Retry loop
    for attempt in range(max_retries):
        try:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=timeout) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)

            print(f"✓ Email sent successfully to {to_email}")
            return True

        except (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError, TimeoutError) as e:
            if attempt < max_retries - 1:
                print(f"⚠ SMTP connection error (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"  Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"✗ Failed to send email after {max_retries} attempts: {e}")
                raise
        except Exception as e:
            # For other exceptions, don't retry
            print(f"✗ Error sending email: {e}")
            raise

    return False


def send_email_simple(
    smtp_server: str,
    smtp_port: int,
    username: str,
    password: str,
    to_email: str,
    subject: str,
    content: str,
    is_html: bool = False
) -> bool:
    """
    Simplified email sending function with retry logic.

    Args:
        smtp_server: SMTP server hostname
        smtp_port: SMTP server port
        username: SMTP username (also used as from_email)
        password: SMTP password
        to_email: Recipient email address
        subject: Email subject
        content: Email content
        is_html: Whether content is HTML (default: False)

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    text_content = content if not is_html else ""
    html_content = content if is_html else None

    return send_email_with_retry(
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        username=username,
        password=password,
        from_email=username,
        to_email=to_email,
        subject=subject,
        text_content=text_content or "Please view this email in HTML format.",
        html_content=html_content
    )
