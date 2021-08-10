import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader, select_autoescape

from programArgs import getArgs

port = 465  # For SSL
smtp_server = "smtp.gmail.com"
tab = '&nbsp;&nbsp;&nbsp;&nbsp;'

env = Environment(
    loader=FileSystemLoader('email_templates'),
    autoescape=select_autoescape(['html', 'xml'])
)

def send_email(recipient_emails, new_tee_times, password):
    sender_email = getArgs().sender
    
    body = __generateEmailBody(new_tee_times)
    if getArgs().local:
        __printEmailAsText(body)
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

def __printEmailAsText(emailBody):
    # Make html a bit more readable
    emailBody = emailBody.replace('&nbsp;', ' ')
    emailBody = emailBody.replace('<br>', '\n')

    print(emailBody)

def __generateEmailBody(tee_times):
    template = env.get_template('tee_time_template.html')
    return template.render(tee_times=tee_times)