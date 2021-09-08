import smtplib, ssl
import os
import webbrowser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time

class EmailSender:
    def __init__(self, sender_email, password):
        self.__port = 465  # For SSL
        self.__smtp_server = "smtp.gmail.com"
        self.__context = ssl.create_default_context()
        self.__sender_email = sender_email
        self.__password = password

    def send_email(self, recipient_emails, body, subject):
        msg = MIMEMultipart('alternative')
        msg["Subject"] = subject
        msg["From"] = self.__sender_email
        html = body
        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP_SSL(self.__smtp_server, self.__port, context=self.__context) as server:
            server.login(self.__sender_email, self.__password)
            server.sendmail(self.__sender_email, recipient_emails, msg.as_string())

class MockSender(EmailSender):
    def __init__(self):
        super().__init__('', '')

    def send_email(self, recipient_emails, body, subject):
        temp_file_path = os.path.join(os.path.dirname(__file__),'email_output.html')
        with open(temp_file_path, 'w') as f:
            f.write(f"To: {', '.join(recipient_emails)}<br><br>")
            f.write(f"Subject: {subject}<br><br><br>")
            f.write(body)
        webbrowser.open(f"file://{temp_file_path}")
        time.sleep(0.5)
        os.remove(temp_file_path)