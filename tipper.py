from emailSender import send_email
import requests
from datetime import datetime, timedelta
import time

from golfCourse import GolfCourse

LOOKAHEAD_DAYS = 40
MIN_SPOTS = 2

def main():
    
    requests_session = requests.session()

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

    latestTeeTime = datetime.now()
    latestTeeTime = latestTeeTime.replace(hour = 14, minute = 0, second = 0, microsecond= 0)

    golfCourses = [moorePark, eastLake]

    while 1:
        print('Getting new tee times')
        new_tee_times_by_course = {}
        t0 = time.time()
        for golfCourse in golfCourses:
            new_tee_times = golfCourse.getNewTeeTimes(requests_session, latestTeeTime, LOOKAHEAD_DAYS, MIN_SPOTS)
            if len(new_tee_times) != 0:
                print(f'New times at {golfCourse.name}')
                new_tee_times_by_course[golfCourse.name] = new_tee_times
        if len(new_tee_times_by_course) != 0:
            send_email('jstollznow12@gmail.com', new_tee_times_by_course)
        t1 = time.time()
        print(f'Scrap took {t1-t0} seconds')
        print()
        print()
        dt = datetime.now() + timedelta(minutes=5)
        while datetime.now() < dt:
            time.sleep(1)
        
main()
