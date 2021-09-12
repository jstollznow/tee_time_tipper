import json
from bs4 import BeautifulSoup
from datetime import date, timedelta, datetime
from bs4.element import SoupStrainer
import pickle
import os
import errno
import lxml
import re

from program_args import get_args
from golf_round_type import GolfRoundType, RoundTimeOfWeek

class GolfCourse:
    TEE_TIMES_LIST = ''
    TEE_TIME_OBJECT = ''
    TIME_OBJECT = ''
    AVAILABLE_SLOT = ''

    BOOKING_ENDPOINT = ''
    ADD_TO_CART_ENDPOINT = ''
    CHECKOUT_ENDPOINT = ''

    def __init__(self, course_config, tipper_scraper) -> None:
        self.name = course_config['name']
        self.__id = course_config['course_id']
        self.__cache_path = os.path.join(os.path.dirname(__file__), "cache", f"{self.name.lower().replace(' ', '_')}.pickle")
        self.__booking_ids_path = os.path.join(os.path.dirname(__file__), "booking_ids", f"{self.name.lower().replace(' ', '_')}.json")
        self.tee_times_by_date = self.__restore_times()
        self.__base_url = course_config['url']
        self.__lookahead_days = course_config.get('lookahead_days', 14)
        self.__booking_ids = self.__restore_ids()
        self.__roundTypes = []
        for fee_group_config in course_config['fee_groups']:
            self.__roundTypes.append(GolfRoundType(fee_group_config))

        self.tipper_scraper = tipper_scraper

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
        print_str = '\nName: ' + self.name + '\nId: ' + self.__id \
            + '\nCache Path: ' + self.__cache_path + '\nBooking Ids Path: ' + self.__booking_ids_path \
            + '\nBaseUrl: ' + self.__base_url + '\nLookahead Days: ' + str(self.__lookahead_days)

        if self.__roundTypes:
            print_str += '\nRound Types:\n\t'
            print_str += '\n\t'.join(str(x) for x in self.__roundTypes)
            print_str += '\n'

        return print_str

    def get_new_tee_times(self, request_session, weekday_cut_time, weekend_cut_time, min_spots):
        current_tee_times_by_round = {}
        new_tee_times_by_round = {}
        for round_type in self.__roundTypes:
            print(f'Getting {round_type.name} Tee Times')
            (current_tee_times_by_date, new_tee_times_by_date) = self.__get_tee_times_for_round_type(round_type, request_session, weekday_cut_time, weekend_cut_time, min_spots)
            if len(current_tee_times_by_date) != 0:
                current_tee_times_by_round[round_type.name] = current_tee_times_by_date
            if len(new_tee_times_by_date) != 0:
                new_tee_times_by_round[round_type.name] = new_tee_times_by_date
        self.__save_times(current_tee_times_by_round)
        self.__save_booking_ids()
        return new_tee_times_by_round

    def __get_tee_times_for_round_type(self, round, request_session, weekday_cut_time, weekend_cut_time, min_spots):
        current_tee_times_by_date = {}
        new_tee_times_by_date = {}

        latest_tee_time = datetime.now()

        for i in range(self.__lookahead_days + 1):
            if latest_tee_time.weekday() < 5 and round.type is not RoundTimeOfWeek.weekend:
                latest_tee_time = datetime.combine(latest_tee_time, weekday_cut_time.time())
            elif latest_tee_time.weekday() >= 5 and round.type is not RoundTimeOfWeek.weekday:
                latest_tee_time = datetime.combine(latest_tee_time, weekend_cut_time.time())
            else:
                latest_tee_time += timedelta(1)
                continue
            # current_round_tee_times = self.__getTeeTimes(request_session, latest_tee_time, min_spots, round.id)
            current_round_tee_times = self.tipper_scraper.get_tee_times_for_date(self.__getUrl(latest_tee_time.date(), round.id), latest_tee_time, min_spots, self.__booking_ids)
            if current_round_tee_times:
                current_tee_times_by_date[latest_tee_time.date()] = current_round_tee_times
                if not round.name in self.tee_times_by_date or not latest_tee_time.date() in self.tee_times_by_date[round.name]:
                    new_tee_times_by_date[latest_tee_time.date()] = sorted(current_round_tee_times, key=lambda x: x.time)
                else:
                    new_tee_times = current_round_tee_times - self.tee_times_by_date[round.name][latest_tee_time.date()]
                    if new_tee_times:
                        new_tee_times_by_date[latest_tee_time.date()] = sorted(new_tee_times, key=lambda x: x.time)
            latest_tee_time += timedelta(1)

        return (current_tee_times_by_date, new_tee_times_by_date)

    def __getUrl(self, date, fee_group_id):
        date_str = f'{date.year}-{date.month:02d}-{date.day:02d}'
        return self.__base_url + GolfCourse.BOOKING_ENDPOINT.format(self.__id, date_str, fee_group_id)

    def __restore_times(self):
        if not os.path.exists(self.__cache_path) or get_args().no_cache:
            return {}
        with open(self.__cache_path, 'rb') as f:
            return pickle.load(f)

    def __save_times(self, current_tee_times_by_date):
        if not os.path.exists(os.path.dirname(self.__cache_path)):
            try:
                os.makedirs(os.path.dirname(self.__cache_path))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        self.tee_times_by_date = current_tee_times_by_date
        with open(self.__cache_path, 'wb') as f:
            pickle.dump(self.tee_times_by_date, f)

    def __save_booking_ids(self):
        if not os.path.exists(os.path.dirname(self.__booking_ids_path)):
            try:
                os.makedirs(os.path.dirname(self.__booking_ids_path))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        with open(self.__booking_ids_path, 'w') as f:
            json.dump(self.__booking_ids, f)

    def __restore_ids(self):
        if not os.path.exists(self.__booking_ids_path):
            return {}
        with open(self.__booking_ids_path, 'r') as f:
            return json.load(f)