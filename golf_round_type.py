from enum import Enum
from datetime import date, timedelta, datetime
from typing import Any, Dict, List, Optional, Set, Union, cast
from tee_time_group import TeeTimeGroup
from tipper_scraper import TipperScraper

class RoundTimeOfWeek(Enum):
    ALL = 0
    WEEKEND = 1
    WEEKDAY = 2

class GolfRoundType:
    DAY_OF_WEEK: Dict[str, int] = {
        'monday': 0,
        'tuesday': 1,
        'wednesday': 2,
        'thursday': 3,
        'friday': 4,
        'saturday': 5,
        'sunday': 6
    }

    def __init__(self, round_type_config: Dict[str, Any], base_booking_url: str, base_add_to_cart_url: str) -> None:
        self.id: str = round_type_config['id']
        self.name: str = round_type_config['name']
        self.type: RoundTimeOfWeek = RoundTimeOfWeek[round_type_config.get('type', 'all').upper()]
        self.round_fee_ids: List[Optional[str]] = [None for _ in range(7)]
        self._initialize_booking_ids(round_type_config['round_fee_ids'])
        self._base_booking_url: str = base_booking_url.format("{}", self.id)
        self._base_add_to_cart_url: str = base_add_to_cart_url.format("{}", self.id, "{}")
        self._tee_times_by_date: Dict[date, Set[TeeTimeGroup]] = {}
        self.booking_ids: Dict[int, Dict[str, Union[str, int]]] = {}

    def deserialize(self, tee_time_data: Any) -> None:
        for date_str, tee_groups_data in tee_time_data.items():
            tee_groups: Set[TeeTimeGroup] = set()
            round_date: date = datetime.strptime(date_str, '%x').date()

            for tee_group_data in tee_groups_data:
                tee_groups.add(TeeTimeGroup.deserialize(tee_group_data, self._base_add_to_cart_url, self.round_fee_ids[round_date.weekday()]))

            self._tee_times_by_date[round_date] = tee_groups

    def serialize(self) -> Any:
        tee_time_data: Dict[str, List[Any]] = {}
        for date, tee_groups in self._tee_times_by_date.items():
            tee_group_data: List[Any] = []
            for tee_group in tee_groups:
                tee_group_data.append(tee_group.serialize())
            tee_time_data[date.strftime('%x')] = tee_group_data
        return tee_time_data

    def get_new_tee_times_for_period(self, weekday_cut_time: datetime, weekend_cut_time: datetime,
            min_spots: int, lookahead_days: int) -> Dict[date, List[TeeTimeGroup]]:

        latest_tee_time: datetime = datetime.now()
        new_tee_times_for_period: Dict[date, List[TeeTimeGroup]] = {}

        for latest_tee_time in self._get_lookahead_cutoff_times(weekday_cut_time, weekend_cut_time, lookahead_days):
            date_str: str = f'{latest_tee_time.year}-{latest_tee_time.month:02d}-{latest_tee_time.day:02d}'
            undecorated_booking_ids: Dict[str, datetime] = {}
            tee_times_data: List[Dict[str, Any]] = TipperScraper.get_tee_times_for_date(self._base_booking_url.format(date_str), latest_tee_time, min_spots, undecorated_booking_ids)
            if tee_times_data:
                tee_times_for_day: Set[TeeTimeGroup] = self._decorate_tee_time_data(tee_times_data)
                new_tee_times: Set[TeeTimeGroup] = tee_times_for_day - self._tee_times_by_date.get(latest_tee_time.date(), set())
                if new_tee_times:
                    new_tee_times_for_period[latest_tee_time.date()] = sorted(new_tee_times, key=lambda x: x.time)
                self._tee_times_by_date[latest_tee_time.date()] = tee_times_for_day

            self._decorate_and_add_to_booking_ids(undecorated_booking_ids)

        return new_tee_times_for_period

    def _decorate_tee_time_data(self, tee_times_data: List[Dict[str, Any]]) -> Set[TeeTimeGroup]:
        tee_time_groups: Set[TeeTimeGroup] = set()
        for tee_time_data in tee_times_data:
            tee_time_groups.add(self._create_tee_time_group(tee_time_data['group_id'], tee_time_data['slots'], tee_time_data['tee_time']))
        return tee_time_groups

    def _create_tee_time_group(self, id: int, slots: List[str], time: datetime) -> TeeTimeGroup:
        return TeeTimeGroup(id, slots, time, self._base_add_to_cart_url, cast(str, self.round_fee_ids[time.weekday()]))

    def _decorate_and_add_to_booking_ids(self, undecorated_booking_pairings):
        for booking_id, booking_time in undecorated_booking_pairings.items():
            if booking_id not in self.booking_ids:
                self.booking_ids[booking_id] = {
                    'time': booking_time.strftime('%c'),
                    'round_id': self.id,
                    'round_fee_id': self.round_fee_ids[booking_time.weekday()]
                }

    def _initialize_booking_ids(self, booking_id_config_dict: Dict[str, str]) -> None:
        for time_of_week, fee_id in booking_id_config_dict.items():
            if time_of_week == 'all':
                self._set_round_fee_ids_for_days(cast(List[str],self.DAY_OF_WEEK.keys()), fee_id)
            elif time_of_week == 'weekend':
                self._set_round_fee_ids_for_days(['saturday', 'sunday'], fee_id)
            elif time_of_week == 'weekday':
                self._set_round_fee_ids_for_days(list(self.DAY_OF_WEEK.keys())[:5], fee_id)
            elif time_of_week in self.DAY_OF_WEEK:
                self._set_round_fee_ids_for_days([time_of_week], fee_id)
            # TODO: Add public holiday management

    def _set_round_fee_ids_for_days(self, days: List[str], booking_id: str) -> None:
        for day in days:
            self.round_fee_ids[self.DAY_OF_WEEK[day.lower()]] = booking_id

    def _get_lookahead_cutoff_times(self,
            weekday_cut_time: datetime,
            weekend_cut_time: datetime,
            lookahead_days: int) -> List[datetime]:
        cutoff_times: List[datetime] = []
        latest_tee_time: datetime = datetime.now()

        for _ in range(lookahead_days):
            latest_tee_time += timedelta(1)
            is_date_weekday: bool = True if latest_tee_time.weekday() < 5 else False

            if self.type is not RoundTimeOfWeek.ALL \
                    and (is_date_weekday or self.type is not RoundTimeOfWeek.WEEKEND) \
                    and not (is_date_weekday and self.type is RoundTimeOfWeek.WEEKDAY):
                continue

            cutoff_times.append(datetime.combine(latest_tee_time.date(), weekday_cut_time.time() if is_date_weekday else weekend_cut_time.time()))
        return cutoff_times

    def __str__(self) -> str:
        return f"Id: {self.id}, Name: {self.name}, RoundType: {self.type}, FeeIds: {' '.join([str(x) for x in self.round_fee_ids])}" + \
                f"Booking Url: {self._base_booking_url}, Add To Cart Url: {self._base_add_to_cart_url}"