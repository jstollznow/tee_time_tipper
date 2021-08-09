from emailSender import send_email
from programArgs import getArgs
import requests
from datetime import datetime, timedelta
import time
import getpass
import sys
import re

from golfCourse import GolfCourse

LOOKAHEAD_DAYS = 40
MIN_SPOTS = 2

# for validating an Email
EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

def main():
    password = getArgs().pwd
    requests_session = requests.session()

    email_recipients = getInputEmails()

    mooreParkFeeGroups = {
        1501385381: "18 Holes",
        1501796650: "Twilight",
        1501386657: "Front 10"
    }
    moorePark = GolfCourse("Moore Park", "https://moorepark.miclub.com.au/guests/bookings/ViewPublicTimesheet.msp?bookingResourceId=3050007", mooreParkFeeGroups)

    eastLakeFeeGroups = {
        10230951: "Mon - Fri (before 1pm)",
        10230959: "Mon - Fri (1pm - 2pm)",
        9270388: "Weekend (before 1pm)",
        2251832: "Weekend (1pm - 2pm)",
        10230962: "Sundowner (after 2pm)"
    }
    eastLake = GolfCourse("East Lake", "https://www.eastlakegolfclub.com.au/guests/bookings/ViewPublicTimesheet.msp?bookingResourceId=3000000", eastLakeFeeGroups)

    golfCourses = [moorePark, eastLake]
    print()
    print('Getting new tee times')
    print(datetime.now())
    latestTeeTime = datetime.now().replace(hour = 15, minute = 0, second = 0, microsecond = 0)

    new_tee_times_by_course = {}
    t0 = time.time()
    for golfCourse in golfCourses:
        print(f'{golfCourse.name}')
        new_tee_times = golfCourse.getNewTeeTimes(requests_session, latestTeeTime, LOOKAHEAD_DAYS, MIN_SPOTS)
        if len(new_tee_times) != 0:
            print(f'New times at {golfCourse.name}')
            new_tee_times_by_course[golfCourse.name] = new_tee_times

    if len(new_tee_times_by_course) != 0:
        send_email(email_recipients, new_tee_times_by_course, password)
    t1 = time.time()
    print(f'Scrape took {t1-t0} seconds')
    print()

def getInputEmails():
    input_emails = getArgs().email_recipients
    validated_email_recipients = []
    for pos in range(0, len(input_emails)):
        if re.match(EMAIL_REGEX, input_emails[pos]):
            validated_email_recipients.append(input_emails[pos])
    print('Email Recipients:')
    print(validated_email_recipients)
    return validated_email_recipients
    
main()
