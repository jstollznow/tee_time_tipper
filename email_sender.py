import smtplib, ssl
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader, select_autoescape

import webbrowser

from program_args import get_args

port = 465  # For SSL
smtp_server = "smtp.gmail.com"
tab = '&nbsp;&nbsp;&nbsp;&nbsp;'

env = Environment(
    loader = FileSystemLoader(searchpath= os.path.join(os.path.dirname(__file__),'./email_templates'))
)

def send_tee_time_email(sender_email, recipient_emails, new_tee_times, password):
    body = __generate_email_body(new_tee_times)
    if get_args().local:
        __print_email_as_text(body)
        return

    msg = MIMEMultipart('alternative')
    msg["Subject"] = "New Tee Times"
    msg["From"] = sender_email
    html = body
    msg.attach(MIMEText(html, 'html'))
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, recipient_emails, msg.as_string())

def __print_email_as_text(emailBody):
    # Make html a bit more readable
    emailBody = emailBody.replace('&nbsp;', ' ')
    emailBody = emailBody.replace('<br>', '\n')

    print(emailBody)

def __generate_email_body(tee_times):
    template = env.get_template('new_tee_times_template.html')
    return template.render(tee_times=tee_times)