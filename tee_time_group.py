class TeeTimeGroup:
    def __init__(self, id, slots, time) -> None:
        self.id = id
        self.slots = slots
        self.time = time

    def __eq__(self, o: object) -> bool:
        return self.__hash__() == o.__hash__()

    def __hash__(self) -> int:
        return hash(tuple(self.slots))

    def __str__(self) -> str:
        return str(self.time)