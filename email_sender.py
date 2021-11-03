import smtplib, ssl
import os
from typing import List, Optional
import webbrowser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time

class EmailSender:
    _port: int = 465
    _smtp_server_name: str = "smtp.gmail.com"

    def __init__(self, sender_email: Optional[str] = None, password: Optional[str] = None) -> None:
        self._context: ssl.SSLContext = ssl.create_default_context()
        self._sender_email: str = sender_email or str()
        self._password: str = password or str()

    def send_email(self, recipient_emails: List[str], body: str, subject: str) -> None:
        msg: MIMEMultipart = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self._sender_email
        html = body
        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP_SSL(self._smtp_server_name, self._port, context=self._context) as server:
            server.login(self._sender_email, self._password)
            server.sendmail(self._sender_email, recipient_emails, msg.as_string())

class MockSender(EmailSender):
    def __init__(self) -> None:
        super().__init__()

    def send_email(self, recipient_emails: List[str], body: str, subject: str) -> None:
        temp_file_path: str = os.path.join(os.path.dirname(__file__),'email_output.html')
        with open(temp_file_path, 'w') as f:
            f.write(f"To: {', '.join(recipient_emails)}<br><br>")
            f.write(f"Subject: {subject}<br><br><br>")
            f.write(body)
        webbrowser.open(f"file://{temp_file_path}")
        time.sleep(0.5)
        os.remove(temp_file_path)