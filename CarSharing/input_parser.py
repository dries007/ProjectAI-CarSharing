from typing import Dict, List

from .Request import Request
from .Zone import Zone


def parse_input(file):
    requests: Dict[str, Request] = {}
    zones: Dict[str, Zone] = {}
    vehicles: List[str] = []
    days: int = 0

    with open(file, newline='') as file:
        line = file.readline()
        while line != "":
            if "+Requests:" in line:
                amount = int(line.split(" ")[1])

                for x in range(amount):
                    data = map(str.strip, file.readline().split(";"))
                    r = Request(*data, len(requests))
                    requests[r.id] = r

            if "+Zones:" in line:
                amount = int(line.split(" ")[1])

                for x in range(amount):
                    data = map(str.strip, file.readline().split(";"))
                    z = Zone(*data)
                    zones[z.id] = z

            if "+Vehicles:" in line:
                amount = int(line.split(" ")[1])

                for x in range(amount):
                    vehicles.append(file.readline().strip())

            if "+Days" in line:
                days = int(line.split(" ")[1])

            line = file.readline()

    for request in requests.values():
        # noinspection PyTypeChecker
        request.zone = zones[request.zone]

    return requests, zones, vehicles, days
