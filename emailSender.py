import smtplib, ssl

port = 465  # For SSL
smtp_server = "smtp.gmail.com"


def send_email(recipient_emails, new_tee_times, password):
    sender_email = "teetimetipper@gmail.com"
    message = f"""Subject: New Tee Times

Hi Lucky Recipient,

The following new tee times are now available:

{format_tee_times(new_tee_times)}
    
Thanks,
Tee Time Tipper."""

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, recipient_emails, message)


def format_tee_times(new_tee_times):
    tee_times_str = ''
    for golf_course in new_tee_times:
        tee_times_str += golf_course + '\n'
        for tee_time_date in new_tee_times[golf_course]:
            tee_times_str += '\n' + tee_time_date.strftime('%A %x') + '\n'
            for tee_time in new_tee_times[golf_course][tee_time_date]:
                tee_times_str += tee_time + '\n'

    return tee_times_str
