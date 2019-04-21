import itertools
from typing import List

import numpy as np

from CarSharing.Request import Request
from CarSharing.Zone import Zone


def calculate(requests, debug) -> (np.ndarray, np.ndarray):
    """
    1th return = np array of booleans, where a True indicates an overlap between that row and col's request.
    ---
    Calculate the cost of one request vs another, based on the penalty2 (not accept) cost only.
    Multiply with overlap matrix for easy summing of rows/cols

    A high positive sum in a row/col means the row/col's request is important. = 2nd return
    """
    n = len(requests)
    overlaps = np.zeros((n, n), dtype=bool)
    cost = np.zeros((n, n), dtype=int)

    for (i, request1), (j, request2) in itertools.combinations(enumerate(requests), 2):
        cost[i][j] = request1.penalty1 - request2.penalty1
        cost[j][i] = request2.penalty1 - request1.penalty1

        if request1.real_start > request2.real_start:
            request1, request2 = request2, request1  # swap!
        # Request 1 starts before request 2 starts
        # If request 1 ends after request 2 starts, it overlaps
        if request1.real_end >= request2.real_start:
            overlaps[i][j] = True
            overlaps[j][i] = True
    if debug:
        import png
        with open('overlap.png', 'wb') as f:
            w = png.Writer(n, n, greyscale=True, bitdepth=1)
            w.write(f, overlaps)
    return overlaps, np.sum(cost, axis=1)


def parse_input(file, debug):
    vehicles: List[str] = []
    days: int = 0
    requests: List[Request] = []
    zones: List[Zone] = []

    with open(file, newline='') as file:
        line = file.readline()
        while line != "":
            if "+Requests:" in line:
                amount = int(line.split(" ")[1])

                for x in range(amount):
                    data = map(str.strip, file.readline().split(";"))
                    requests.append(Request(*data, len(requests)))

            if "+Zones:" in line:
                amount = int(line.split(" ")[1])

                for x in range(amount):
                    data = map(str.strip, file.readline().split(";"))
                    zones.append(Zone(*data))

            if "+Vehicles:" in line:
                amount = int(line.split(" ")[1])

                for x in range(amount):
                    vehicles.append(file.readline().strip())

            if "+Days" in line:
                days = int(line.split(" ")[1])

            line = file.readline()

    request_map = {req.id: req for req in requests}
    zone_map = {zone.id: zone for zone in zones}

    for request in requests:
        request.zone = zone_map[request.zone]

    return (requests, request_map, zones, zone_map, vehicles, days, *calculate(requests, debug))
