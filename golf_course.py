import json
import os
import errno

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
        self.__id = course_config['course_id']
        self.__cache_path = os.path.join(os.path.dirname(__file__), "cache", f"{self.name.lower().replace(' ', '_')}.json")
        self.__booking_ids_path = os.path.join(os.path.dirname(__file__), "booking_ids", f"{self.name.lower().replace(' ', '_')}.json")
        self.__base_url = course_config['url']
        self.checkout_url = self.__base_url + self.CHECKOUT_ENDPOINT
        self.__lookahead_days = course_config.get('lookahead_days', 14)
        self.__roundTypes = {}

        base_timetable_url = self.__get_base_timetable_url()
        base_add_to_cart_url = self.__base_url + self.ADD_TO_CART_ENDPOINT
        for fee_group_config in course_config['fee_groups']:
            round = GolfRoundType(fee_group_config, base_timetable_url, base_add_to_cart_url)
            self.__roundTypes[round.id] = round

        self.deserialize(self.__load_json_from_path(self.__cache_path))
        self.__set_booking_ids(self.__load_json_from_path(self.__booking_ids_path))

    @staticmethod
    def set_endpoint_formats(endpoints_config):
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

    def get_new_tee_times(self, weekday_cut_time, weekend_cut_time, min_spots):
        new_tee_times_by_round = {}
        for round_type in self.__roundTypes.values():
            print(f'Getting {round_type.name} Tee Times')
            new_tee_times_by_date = round_type.get_new_tee_times_for_period(weekday_cut_time, weekend_cut_time, min_spots, self.__lookahead_days)
            if new_tee_times_by_date:
                new_tee_times_by_round[round_type.name] = new_tee_times_by_date
        self.__save_to_json_to_path(self.serialize(), self.__cache_path)
        self.__save_to_json_to_path(self.__get_booking_ids(), self.__booking_ids_path)
        return new_tee_times_by_round

    def deserialize(self, tee_time_data):
        for round_id, round_tee_time_data in tee_time_data.items():
            self.__roundTypes[round_id].deserialize(round_tee_time_data)

    def serialize(self):
        tee_times = {}
        for round in self.__roundTypes.values():
            round_data = round.serialize()
            if round_data:
                tee_times[round.id] = round_data
        return tee_times

    def __set_booking_ids(self, booking_ids):
        for round_id, bookings_data in booking_ids.items():
            self.__roundTypes[round_id].booking_ids = bookings_data

    def __get_booking_ids(self):
        booking_ids_by_round_type = {}
        for round_id, round in self.__roundTypes.items():
            booking_ids_by_round_type[round_id] = round.booking_ids
        return booking_ids_by_round_type

    def __get_base_timetable_url(self):
        return self.__base_url + GolfCourse.BOOKING_ENDPOINT.format(self.__id, "{}", "{}")

    def __load_json_from_path(self, file_path):
        if not os.path.exists(file_path) \
                or get_args().no_cache \
                or os.path.getsize(file_path) == 0:
            return {}

        with open(file_path, 'r') as f:
            return json.load(f)

    def __save_to_json_to_path(self, data, file_path):
        if not os.path.exists(os.path.dirname(file_path)):
            try:
                os.makedirs(os.path.dirname(file_path))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        with open(file_path, 'w') as f:
            json.dump(data, f)