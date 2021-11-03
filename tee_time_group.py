from __future__ import annotations
from datetime import date, datetime
from typing import Dict, List, Union, cast

class TeeTimeGroup:
    def __init__(self, id: int, slots: List[str], time: datetime, base_add_to_cart_url: str, fee_id: str) -> None:
        self.id: int = id
        self.slots: List[str] = slots
        self.time: datetime = time
        self.add_to_cart_urls = self._generate_add_to_cart_urls(base_add_to_cart_url, fee_id)

    @staticmethod
    def deserialize(serialized_data: List[Union[str, int]], base_add_to_cart_url: str, fee_id: str) -> TeeTimeGroup:
        return TeeTimeGroup(cast(int, serialized_data[0]), cast(List[str], serialized_data[2:]), datetime.strptime(cast(str, serialized_data[1]), '%c'), base_add_to_cart_url, fee_id)

    def serialize(self) -> List[Union[str, int]]:
        return [self.id, self.time.strftime('%c'), *self.slots]

    def get_time_str(self) -> str:
        return self.time.strftime('%I:%M %p')

    def __eq__(self, o: object) -> bool:
        return self.__hash__() == o.__hash__()

    def __hash__(self) -> int:
        return hash(tuple(self.slots))

    def __str__(self) -> str:
        return f"id: {self.id}, slots: {' '.join(self.slots)}, time: {self.time}"

    @staticmethod
    def _get_date_str(date: datetime) -> str:
        return f'{date.day:02d}-{date.month:02d}-{date.year}'

    def _generate_add_to_cart_urls(self, base_add_to_cart_url: str, fee_id: str):
        add_to_cart_urls_by_group_size: Dict[int, str] = {}
        cells: List[str] = []
        date_str: str = self._get_date_str(self.time)
        for i, slot in enumerate(self.slots):
            cells.append(f'{slot}_{fee_id}Q1')
            if i:
                add_to_cart_urls_by_group_size[i + 1] = base_add_to_cart_url.format(",".join(cells), date_str)
        return add_to_cart_urls_by_group_size