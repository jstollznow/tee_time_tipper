from enum import Enum
from datetime import timedelta, datetime
from tee_time_group import TeeTimeGroup
from tipper_scraper import TipperScraper

class RoundTimeOfWeek(Enum):
    all = 0
    weekend = 1
    weekday = 2

class GolfRoundType:
    DAY_OF_WEEK = {
        'monday': 0,
        'tuesday': 1,
        'wednesday': 2,
        'thursday': 3,
        'friday': 4,
        'saturday': 5,
        'sunday': 6
    }

    def __init__(self, round_type_config, base_booking_url, base_add_to_cart_url) -> None:
        self.id = round_type_config['id']
        self.name = round_type_config['name']
        self.type = RoundTimeOfWeek[round_type_config.get('type', 'all').lower()]
        self.round_fee_ids = [None for _ in range(7)]
        self.__initialize_booking_ids(round_type_config['round_fee_ids'])
        self.__base_booking_url = base_booking_url.format("{}", self.id)
        self.__base_add_to_cart_url = base_add_to_cart_url.format("{}", self.id, "{}")
        self.__tee_times_by_date = {}
        self.booking_ids = {}

    def deserialize(self, tee_time_data):
        for date_str, tee_groups_data in tee_time_data.items():
            tee_groups = set()
            date = datetime.strptime(date_str, '%x').date()
            for tee_group_data in tee_groups_data:
                tee_groups.add(TeeTimeGroup.deserialize(tee_group_data, self.__base_add_to_cart_url, self.round_fee_ids[date.weekday()]))
            self.__tee_times_by_date[date] = tee_groups

    def serialize(self):
        tee_time_data = {}
        for date, tee_groups in self.__tee_times_by_date.items():
            tee_group_data = []
            for tee_group in tee_groups:
                tee_group_data.append(tee_group.serialize())
            tee_time_data[date.strftime('%x')] = tee_group_data
        return tee_time_data

    def get_new_tee_times_for_period(self, weekday_cut_time, weekend_cut_time, min_spots, lookahead_days):
        latest_tee_time = datetime.now()
        new_tee_times_for_period = {}

        for latest_tee_time in self.__get_lookahead_cutoff_times(weekday_cut_time, weekend_cut_time, lookahead_days):
            date_str = f'{latest_tee_time.year}-{latest_tee_time.month:02d}-{latest_tee_time.day:02d}'
            undecorated_booking_ids = {}
            tee_times_data = TipperScraper.get_tee_times_for_date(self.__base_booking_url.format(date_str), latest_tee_time, min_spots, undecorated_booking_ids)
            if tee_times_data:
                tee_times_for_day = self.__decorate_tee_time_data(tee_times_data)
                new_tee_times = tee_times_for_day - self.__tee_times_by_date.get(latest_tee_time.date(), set())
                if new_tee_times:
                    new_tee_times_for_period[latest_tee_time.date()] = sorted(new_tee_times, key=lambda x: x.time)
                self.__tee_times_by_date[latest_tee_time.date()] = tee_times_for_day

            self.__decorate_and_add_to_booking_ids(undecorated_booking_ids)

        return new_tee_times_for_period

    def __decorate_tee_time_data(self, tee_times_data):
        tee_time_groups = set()
        for tee_time_data in tee_times_data:
            tee_time_groups.add(self.__create_tee_time_group(tee_time_data['group_id'], tee_time_data['slots'], tee_time_data['tee_time']))
        return tee_time_groups

    def __create_tee_time_group(self, id, slots, time):
        return TeeTimeGroup(id, slots, time, self.__base_add_to_cart_url, self.round_fee_ids[time.weekday()])

    def __decorate_and_add_to_booking_ids(self, undecorated_booking_pairings):
        for booking_id, booking_time in undecorated_booking_pairings.items():
            if booking_id not in self.booking_ids:
                self.booking_ids[booking_id] = {
                    'time': booking_time.strftime('%c'),
                    'round_id': self.id,
                    'round_fee_id': self.round_fee_ids[booking_time.weekday()]
                }

    def __initialize_booking_ids(self, booking_id_config_dict):
        for time_of_week, fee_id in booking_id_config_dict.items():
            if time_of_week == 'all':
                self.__set_round_fee_ids_for_days(self.DAY_OF_WEEK.keys(), fee_id)
            elif time_of_week == 'weekend':
                self.__set_round_fee_ids_for_days(['saturday', 'sunday'], fee_id)
            elif time_of_week == 'weekday':
                self.__set_round_fee_ids_for_days(list(self.DAY_OF_WEEK.keys())[:5], fee_id)
            elif time_of_week in self.DAY_OF_WEEK:
                self.__set_round_fee_ids_for_days([time_of_week], fee_id)
            # TODO: Add public holiday management

    def __set_round_fee_ids_for_days(self, days, booking_id):
        for day in days:
            self.round_fee_ids[self.DAY_OF_WEEK[day.lower()]] = booking_id

    def __get_lookahead_cutoff_times(self, weekday_cut_time, weekend_cut_time, lookahead_days):
        cutoff_times = []
        latest_tee_time = datetime.now()

        for _ in range(lookahead_days):
            latest_tee_time += timedelta(1)
            is_date_weekday = True if latest_tee_time.weekday() < 5 else False

            if self.type is not RoundTimeOfWeek.all \
                    and (is_date_weekday or self.type is not RoundTimeOfWeek.weekend) \
                    and not (is_date_weekday and self.type is RoundTimeOfWeek.weekday):
                continue

            cutoff_times.append(datetime.combine(latest_tee_time.date(), weekday_cut_time.time() if is_date_weekday else weekend_cut_time.time()))
        return cutoff_times

    def __str__(self):
        return str(vars(self))