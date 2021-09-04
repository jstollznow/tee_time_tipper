import requests
from datetime import date, datetime
import time
import re
import json
import cProfile

from email_sender import send_tee_time_email
from program_args import get_args
from golf_course import GolfCourse

# for validating an Email
EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

def main():
    with open(get_args().course_config_path) as f:
        tipper_config = json.load(f)

    password = tipper_config['password']
    requests_session = requests.session()

    email_recipients = get_input_emails(tipper_config['recipients'])

    golf_courses = []

    GolfCourse.set_scraping_details(tipper_config['xml_objects'], tipper_config['endpoints'])

    for course_config in tipper_config['golf_courses']:
        golf_courses.append(GolfCourse(course_config))
        print(golf_courses[-1])

    print('Getting new tee times')
    print(datetime.now())
    weekday_cut_time = datetime.strptime(tipper_config['weekday_cut'], '%I:%M%p')
    weekend_cut_time = datetime.strptime(tipper_config['weekend_cut'], '%I:%M%p')

    latestTeeTime = datetime.combine(datetime.now(), weekend_cut_time.time())

    print(latestTeeTime)

    new_tee_times_by_course = {}
    t0 = time.time()

    for golf_course in golf_courses:
        print(f'{golf_course.name}')
        new_tee_times = golf_course.get_new_tee_times(requests_session, latestTeeTime, tipper_config['lookahead_days'], tipper_config['min_spots'])
        if new_tee_times:
            print(f'New times at {golf_course.name}')
            new_tee_times_by_course[golf_course.name] = new_tee_times

    if new_tee_times_by_course:
        send_tee_time_email(tipper_config['sender_email'], email_recipients, new_tee_times_by_course, password)

    t1 = time.time()
    print(f'Scrape took {t1-t0} seconds')
    print()

def get_input_emails(input_emails):
    validated_email_recipients = []
    for pos in range(0, len(input_emails)):
        if re.match(EMAIL_REGEX, input_emails[pos]):
            validated_email_recipients.append(input_emails[pos])

    if validated_email_recipients:
        print('Email Recipients:')
        print(validated_email_recipients)
    return validated_email_recipients

main()
