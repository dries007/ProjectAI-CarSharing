import itertools

import numpy as np

from typing import Dict, List

from CarSharing.Zone import Zone
from CarSharing.Request import Request


def calculate_overlap(requests, debug) -> np.ndarray:
    """
    Returns np array of booleans, where a True indicates an overlap between that row and col's request.
    """
    overlaps = np.zeros((len(requests), len(requests)), dtype=bool)

    for (i, request1), (j, request2) in itertools.combinations(enumerate(requests.values()), 2):
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
            w = png.Writer(len(requests), len(requests), greyscale=True, bitdepth=1)
            w.write(f, overlaps)
    return overlaps


def calculate_opportunity_cost(requests) -> np.ndarray:
    """
    Calculate the cost of one request vs another, based on the penalty2 (not accept) cost only.
    Multiply with overlap matrix for easy summing of rows/cols

    A high positive sum in a row/col means the row/col's request is important.
    """
    cost = np.zeros((len(requests), len(requests)), dtype=int)
    for (i, request1), (j, request2) in itertools.combinations(enumerate(requests.values()), 2):
        cost[i][j] = request1.penalty1 - request2.penalty1
        cost[j][i] = request2.penalty1 - request1.penalty1
    return np.sum(cost, axis=1)


def parse_input(file, debug):
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

    return requests, zones, vehicles, days, calculate_overlap(requests, debug), calculate_opportunity_cost(requests)
