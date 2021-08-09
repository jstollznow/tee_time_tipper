from programArgs import getArgs
from jinja2 import Environment, FileSystemLoader, select_autoescape

tab = '&nbsp;&nbsp;&nbsp;&nbsp;'

env = Environment(
    loader=FileSystemLoader('email_templates'),
    autoescape=select_autoescape(['html', 'xml'])
)

def generateEmailBody(tee_times):
    if getArgs().email_template:
        return templated_email(tee_times)
    else:
        return standard_email(tee_times)

def templated_email(tee_times):
    template = env.get_template('tee_time_template.html')
    return template.render(tee_times=tee_times)


def standard_email(tee_times):
   return f"""<html>
                <body>
                    <p>Hi lucky recipient,<br><br>
                    The following new tee times are now available:<br><br>
                    {format_tee_times(tee_times)}<br><br>
                    Thanks, <br>
                    Tee Time Tipper.
                    </p>
                </body>
                </html>
            """

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