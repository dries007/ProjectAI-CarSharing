from .Zone import Zone
from typing import List
from typing import Iterable


class Request:
    def __init__(self, id, zone, day, start, duration, vehicles, penalty1, penalty2, index):
        self.id: str = id
        self.zone = zone
        self.day: int = int(day)
        self.start: int = int(start)
        self.duration: int = int(duration)
        self.vehicles: List[str] = vehicles.split(",")
        self.penalty1: int = int(penalty1)  # Not assigned
        self.penalty2: int = int(penalty2)  # Assigned to neighbour
        self.index = index  # index in the numpy matrices

    def __repr__(self):
        return 'Request<id: {!r}, zone: {!r}, day: {!r}, start: {!r}, duration: {!r}, vehicles: {!r}, pen1: {!r}, pen2: {!r}>' \
            .format(self.id, self.zone, self.day, self.start, self.duration, self.vehicles, self.penalty1, self.penalty2)

    @property
    def real_start(self):
        return (self.day * 24 * 60) + self.start

    @property
    def real_end(self):
        return self.real_start + self.duration

    def link_zones(self, zones: Iterable[Zone]):
        """ Replace zone str with zone object """
        for zone in zones:
            if zone.id == self.zone:
                self.zone = zone
