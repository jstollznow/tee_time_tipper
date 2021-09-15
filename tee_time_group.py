from datetime import datetime

class TeeTimeGroup:
    def __init__(self, id, slots, time) -> None:
        self.id = id
        self.slots = slots
        self.time = time

    @staticmethod
    def deserialize(serialized_data):
        return TeeTimeGroup(serialized_data[0], serialized_data[2:], datetime.strptime(serialized_data[1], '%c'))

    def serialize(self):
        return [self.id, self.time.strftime('%c'), *self.slots]

    def __eq__(self, o: object) -> bool:
        return self.__hash__() == o.__hash__()

    def __hash__(self) -> int:
        return hash(tuple(self.slots))

    def __str__(self) -> str:
        return str(self.time)