from bs4 import BeautifulSoup
from datetime import timedelta, datetime
from bs4.element import SoupStrainer
import pickle
import os
import errno
import lxml
import re

from program_args import get_args
from golf_round_type import GolfRoundType

class GolfCourse:
    TEE_TIMES_LIST = ''
    TEE_TIME_OBJECT = ''
    TIME_OBJECT = ''
    AVAILABLE_SLOT = ''

    BOOKING_ENDPOINT = ''
    ADD_TO_CART_ENDPOINT = ''
    CHECKOUT_ENDPOINT = ''

    def __init__(self, course_config) -> None:
        self.name = course_config['name']
        self.id = course_config['course_id']
        self.__file_name = os.path.join(os.path.dirname(__file__), "cache", f"{self.name.lower().replace(' ', '_')}.pickle")
        self.tee_times_by_date = self.__restore_times()
        self.__base_url = course_config['url']
        self.__roundTypes = {}
        for fee_group_config in course_config['fee_groups']:
            fee_group = GolfRoundType(fee_group_config)
            self.__roundTypes[fee_group.round_type_id] = fee_group

    @staticmethod
    def set_scraping_details(xml_config, endpoints_config):
        GolfCourse.TEE_TIMES_LIST = re.compile(xml_config['TEE_TIMES_LIST'])
        GolfCourse.TEE_TIME_OBJECT = re.compile(xml_config['TEE_TIME_OBJECT'])
        GolfCourse.TIME_OBJECT = re.compile(xml_config['TIME_OBJECT'])
        GolfCourse.AVAILABLE_SLOT = re.compile(xml_config['AVAILABLE_SLOT'])

        GolfCourse.BOOKING_ENDPOINT = endpoints_config['booking_timetable']
        GolfCourse.ADD_TO_CART_ENDPOINT = endpoints_config['add_tee_time_to_cart']
        GolfCourse.CHECKOUT_ENDPOINT = endpoints_config['checkout']

    def __str__(self):
        print_str = '\nName: ' + self.name + '\nFileName: ' + self.__file_name \
            + '\nBaseUrl: ' + self.__base_url

        if self.__roundTypes:
            print_str += '\nRound Types:\n\t'
            print_str += '\n\t'.join(str(x) for x in self.__roundTypes.values())
            print_str += '\n'

        return print_str

    def get_new_tee_times(self, request_session, latest_tee_time, lookahead_days, min_spots):
        current_tee_times_by_round = {}
        new_tee_times_by_round = {}
        for (round_id, round_name) in self.__roundTypes.items():
            print(f'Getting {round_name} Tee Times')
            (current_tee_times_by_date, new_tee_times_by_date) = self.__getTeeTimesForRoundType(round_name, round_id, request_session, latest_tee_time, min_spots, lookahead_days)
            if len(current_tee_times_by_date) != 0:
                current_tee_times_by_round[round_name] = current_tee_times_by_date
            if len(new_tee_times_by_date) != 0:
                new_tee_times_by_round[round_name] = new_tee_times_by_date
        self.__save_times(current_tee_times_by_round)
        return new_tee_times_by_round

    def __getTeeTimesForRoundType(self, round_name, round_id, request_session, latest_tee_time, min_spots, lookahead_weekends):
        current_tee_times_by_date = {}
        new_tee_times_by_date = {}
        # if (latest_tee_time.weekday() < 5):
        #     latest_tee_time += timedelta(days= 5 - latest_tee_time.weekday())

        for _ in range(lookahead_weekends):
            current_round_tee_times = self.__getTeeTimes(request_session, latest_tee_time, min_spots, round_id)
            if len(current_round_tee_times) > 0:
                current_tee_times_by_date[latest_tee_time.date()] = current_round_tee_times
                if not round_name in self.tee_times_by_date or not latest_tee_time.date() in self.tee_times_by_date[round_name]:
                    new_tee_times_by_date[latest_tee_time.date()] = sorted(current_round_tee_times)
                else:
                    new_tee_times = current_round_tee_times - self.tee_times_by_date[round_name][latest_tee_time.date()]
                    if len(new_tee_times) > 0:
                        new_tee_times_by_date[latest_tee_time.date()] = sorted(new_tee_times)
            if (latest_tee_time.weekday() == 5):
                latest_tee_time += timedelta(1)
            else:
                latest_tee_time += timedelta(1)

        return (current_tee_times_by_date, new_tee_times_by_date)

    def __getTeeTimes(self, request_session, latest_tee_time, min_spots, round_id):
        tee_times = set()
        strainer = SoupStrainer('div', GolfCourse.TEE_TIMES_LIST)
        soup = BeautifulSoup(self.__getContent(request_session, latest_tee_time, round_id), 'lxml', parse_only=strainer)
        for row in soup.find_all('div', GolfCourse.TEE_TIME_OBJECT):
            tee_time = self.__getTeeTime(row)
            if (tee_time.time() <= latest_tee_time.time()):
                if (self.__getSpotsAvailable(row) >= min_spots):
                    tee_times.add(tee_time.strftime('%I:%M %p'))
            else:
                break
        return tee_times

    def __getUrl(self, date, fee_group_id):
        date_str = f'{date.year}-{date.month:02d}-{date.day:02d}'
        return self.__base_url + GolfCourse.BOOKING_ENDPOINT.format(self.id, date_str, fee_group_id)

    def __getContent(self, request_session, date, feeGroupId):
        url = self.__getUrl(date, feeGroupId)
        return request_session.get(url).text

    def __getTeeTime(self, row):
        time = datetime.strptime(row.find(self.TIME_OBJECT).text.strip(), '%I:%M %p')
        return time

    def __getSpotsAvailable(self, row):
        spotsAvailable = 0
        for spot in row.find_all("div", GolfCourse.AVAILABLE_SLOT):
            # print(spot.get('id'))
            spotsAvailable += 1
        return spotsAvailable

    def __restore_times(self):
        if not os.path.exists(self.__file_name) or get_args().no_cache:
            return {}
        with open(self.__file_name, 'rb') as f:
            return pickle.load(f)

    def __save_times(self, current_tee_times_by_date):
        if not os.path.exists(os.path.dirname(self.__file_name)):
            try:
                os.makedirs(os.path.dirname(self.__file_name))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        self.tee_times_by_date = current_tee_times_by_date
        with open(self.__file_name, 'wb') as f:
            pickle.dump(self.tee_times_by_date, f)
