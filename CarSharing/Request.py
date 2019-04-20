from typing import List

from CarSharing.Zone import Zone


class Request:
    def __init__(self, id, zone, day, start, duration, vehicles, penalty1, penalty2, index):
        self.id: str = id
        self.zone: Zone = zone  # Initially a string, then replaced after the zones have been read.
        self.day: int = int(day)
        self.start: int = int(start)
        self.duration: int = int(duration)
        self.vehicles: List[str] = vehicles.split(",")
        self.penalty1: int = int(penalty1)  # Not assigned
        self.penalty2: int = int(penalty2)  # Assigned to neighbour
        self.index: int = index  # index in the numpy matrices
        self.real_start = (self.day * 24 * 60) + self.start
        self.real_end = self.real_start + self.duration

    def __repr__(self):
        return 'Request<id: {!r}, zone: {!r}, day: {!r}, start: {!r}, duration: {!r}, vehicles: {!r}, pen1: {!r}, pen2: {!r}>' \
            .format(self.id, self.zone.id, self.day, self.start, self.duration, self.vehicles, self.penalty1, self.penalty2)
