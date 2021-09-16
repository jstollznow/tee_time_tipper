from datetime import datetime

class TeeTimeGroup:
    def __init__(self, id, slots, time, base_add_to_cart_url, fee_id) -> None:
        self.id = id
        self.slots = slots
        self.time = time
        self.add_to_cart_urls = self.__generate_add_to_cart_urls(base_add_to_cart_url, fee_id)

    @staticmethod
    def deserialize(serialized_data, base_add_to_cart_url, fee_id):
        return TeeTimeGroup(serialized_data[0], serialized_data[2:], datetime.strptime(serialized_data[1], '%c'), base_add_to_cart_url, fee_id)

    def serialize(self):
        return [self.id, self.time.strftime('%c'), *self.slots]

    def get_time_str(self):
        return self.time.strftime('%I:%M %p')

    def __eq__(self, o: object) -> bool:
        return self.__hash__() == o.__hash__()

    def __hash__(self) -> int:
        return hash(tuple(self.slots))

    def __str__(self) -> str:
        return str(self.time)

    @staticmethod
    def __get_date_str(date):
        return f'{date.day:02d}-{date.month:02d}-{date.year}'

    def __generate_add_to_cart_urls(self, base_add_to_cart_url, fee_id):
        add_to_cart_urls_by_group_size = {}
        cells = []
        date_str = self.__get_date_str(self.time)
        for i, slot in enumerate(self.slots):
            cells.append(f'{slot}_{fee_id}Q1')
            if i:
                add_to_cart_urls_by_group_size[i + 1] = base_add_to_cart_url.format(",".join(cells), date_str)
        return add_to_cart_urls_by_group_size