import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from programArgs import getArgs
from emailGenerator import generateEmailBody

port = 465  # For SSL
smtp_server = "smtp.gmail.com"

def send_email(recipient_emails, new_tee_times, password):
    if getArgs().sender is not None :
        sender_email = getArgs().sender
    else:
        sender_email = "teetimetipper@gmail.com"

    msg = MIMEMultipart('alternative')
    msg["Subject"] = "New Tee Times"
    msg["From"] = sender_email
    html = generateEmailBody(new_tee_times)
    msg.attach(MIMEText(html, 'html'))
    context = ssl.create_default_context()
    if getArgs().local:
        printEmailAsText(html)
    else:
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient_emails, msg.as_string())



def printEmailAsText(emailBody):
    # Make html a bit more readable
    emailBody = emailBody.replace('&nbsp;', ' ')
    emailBody = emailBody.replace('<br>', '\n')

    print(emailBody)