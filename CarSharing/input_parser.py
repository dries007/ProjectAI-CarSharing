from .Request import Request
from .Zone import Zone

import numpy as np
import itertools


def parse_input(file):
    requests = []
    zones = []
    vehicles = []
    days = 0

    with open(file, newline='') as csvfile:
        line = csvfile.readline()
        while line != "":
            if "+Requests:" in line:
                amount = int(line.split(" ")[1])

                for x in range(amount):
                    data = map(str.strip, csvfile.readline().split(";"))
                    requests.append(Request(*data, len(requests)))

            if "+Zones:" in line:
                amount = int(line.split(" ")[1])

                for x in range(amount):
                    data = map(str.strip, csvfile.readline().split(";"))
                    zones.append(Zone(*data))

            if "+Vehicles:" in line:
                amount = int(line.split(" ")[1])

                for x in range(amount):
                    vehicles.append(csvfile.readline().strip())

            if "+Days" in line:
                days = int(line.split(" ")[1])

            line = csvfile.readline()

    for request in requests:
        request.link_zones(zones)

    return requests, zones, vehicles, days


def calculate_overlap(requests: [Request]) -> np.ndarray:
    overlaps = np.zeros((len(requests), len(requests)), dtype=bool)

    for (i, request1), (j, request2) in itertools.combinations(enumerate(requests), 2):
        if request1.real_start > request2.real_start:
            tmp = request1
            request1 = request2
            request2 = tmp

        if request1.real_end > request2.real_start or request2.real_end < request1.real_start:
            overlaps[i][j] = True
            overlaps[j][i] = True

    return overlaps


def calculate_opportunity_cost(requests: [Request]) -> np.ndarray:
    """
    Calculate the cost of one request vs another, based on the penalty2 (not accept) cost only.
    Multiply with overlap matrix for easy summing of rows/cols

    A high positive sum in a row/col means the row/col's request is important.

    """
    cost = np.zeros((len(requests), len(requests)), dtype=int)

    request1: Request
    request2: Request
    for (i, request1), (j, request2) in itertools.combinations(enumerate(requests), 2):
        cost[i][j] = request1.penalty1 - request2.penalty1
        cost[j][i] = request2.penalty1 - request1.penalty1

    return cost
