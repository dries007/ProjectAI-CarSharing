from typing import List


class Request:
    def __init__(self, id, zone, day, start, duration, vehicles, penalty1, penalty2, index):
        self.id: str = id
        self.zone: str = zone
        self.day: int = int(day)
        self.start: int = int(start)
        self.duration: int = int(duration)
        self.vehicles: List[str] = vehicles.split(",")
        self.penalty1: int = int(penalty1)  # Not assigned
        self.penalty2: int = int(penalty2)  # Assigned to neighbour
        self.index = index  # index in the numpy matrices

    def __repr__(self):
        return 'Request<id: {}, zone: {}, day: {}, start: {}, duration: {}, vehicles: {}, pen1: {}, pen2: {}>' \
            .format(self.id, self.zone, self.day, self.day, self.duration, self.vehicles, self.penalty1, self.penalty2)

    def real_start(self):
        return (self.day * 24 * 60) + self.start

    def real_end(self):
        return self.real_start() + self.duration
