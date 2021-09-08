import requests
from datetime import datetime
import time
import json
import cProfile

from email_manager import EmailManager
from program_args import get_args
from golf_course import GolfCourse

def main():
    with open(get_args().course_config_path) as f:
        tipper_config = json.load(f)

    requests_session = requests.session()

    golf_courses = []

    GolfCourse.set_scraping_details(tipper_config['xml_objects'], tipper_config['endpoints'])

    for course_config in tipper_config['golf_courses']:
        golf_courses.append(GolfCourse(course_config))

    print('Getting new tee times')
    print(datetime.now())
    weekday_cut_time = datetime.strptime(tipper_config['weekday_cut'], '%I:%M%p')
    weekend_cut_time = datetime.strptime(tipper_config['weekend_cut'], '%I:%M%p')

    new_tee_times_by_course = {}
    t0 = time.time()

    for golf_course in golf_courses:
        print(f'{golf_course.name}')
        new_tee_times = golf_course.get_new_tee_times(requests_session, weekday_cut_time, weekend_cut_time, tipper_config['min_spots'])
        if new_tee_times:
            print(f'New times at {golf_course.name}')
            new_tee_times_by_course[golf_course.name] = new_tee_times

    if new_tee_times_by_course:
        email_manager = EmailManager(get_args().local, tipper_config['email_details'])
        email_manager.create_and_send_email("new_tee_times", tee_times = new_tee_times_by_course)

    t1 = time.time()
    print(f'Scrape took {t1-t0} seconds')
    print()

main()
