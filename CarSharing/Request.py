
class Request:
    def __init__(self, id: str, zone: str, day: int, start: int, duration: int, vehicles: [str], penalty1: int, penalty2: int):
        self.id = id
        self.zone = zone
        self.day = day
        self.start = start
        self.duration = duration
        self.vehicles = vehicles
        self.penalty1 = penalty1
        self.penalty2 = penalty2
