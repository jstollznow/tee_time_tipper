import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

port = 465  # For SSL
smtp_server = "smtp.gmail.com"
tab = '&nbsp;&nbsp;&nbsp;&nbsp;'


def send_email(recipient_emails, new_tee_times, password):
    sender_email = "teetimetipper@gmail.com"
    msg = MIMEMultipart('alternative')
    msg["Subject"] = "New Tee Times"
    msg["From"] = sender_email
    html = f"""<html>
<body>
    <p>Hi lucky recipient,<br><br>
    The following new tee times are now available:<br><br>
    {format_tee_times(new_tee_times)}<br><br>
    Thanks, <br>
    Tee Time Tipper.
    </p>
</body>
</html>
    """
    msg.attach(MIMEText(html, 'html'))
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, recipient_emails, msg.as_string())


def format_tee_times(new_tee_times):
    tee_times_str = ''
    for golf_course in new_tee_times:
        tee_times_str += golf_course + '<br>'
        for round_type in new_tee_times[golf_course]:
            tee_times_str += tab + round_type + '<br>'
            for tee_time_date in new_tee_times[golf_course][round_type]:
                tee_times_str += tab + tab + tee_time_date.strftime('%A %d/%m/%Y') + '<br>'
                for tee_time in new_tee_times[golf_course][round_type][tee_time_date]:
                    tee_times_str += tab + tab + tab + tee_time + '<br>'

    return tee_times_str
