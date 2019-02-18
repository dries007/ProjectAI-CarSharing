
class Request:
    def __init__(self, id: str, zone: str, day, start, duration, vehicles: str, penalty1, penalty2):
        self.id = id
        self.zone = zone
        self.day = int(day)
        self.start = int(start)
        self.duration = int(duration)
        self.vehicles = vehicles.split(",")
        self.penalty1 = int(penalty1)
        self.penalty2 = int(penalty2)

    def __repr__(self):
        return "id: {}, zone: {}, day: {}, start: {}, duration: {}, vehicles: {}, pen1: {}, pen2: {}".format(self.id, self.zone, self.day, self.day, self.duration, self.vehicles, self.penalty1, self.penalty2)