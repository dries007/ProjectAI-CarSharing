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
                    data = csvfile.readline().split(";")
                    requests.append(Request(*data, len(requests)))

            if "+Zones:" in line:
                amount = int(line.split(" ")[1])

                for x in range(amount):
                    data = csvfile.readline().rstrip("\n").split(";")
                    zones.append(Zone(*data))

            if "+Vehicles:" in line:
                amount = int(line.split(" ")[1])

                for x in range(amount):
                    vehicles.append(csvfile.readline().rstrip("\n"))

            if "+Days" in line:
                days = int(line.split(" ")[1])

            line = csvfile.readline()

    return requests, zones, vehicles, days, calculate_overlap(requests)


def calculate_overlap(requests: [Request]) -> np.ndarray:
    overlaps = np.zeros((len(requests), len(requests)), dtype=bool)

    request1: Request
    request2: Request
    for (i, request1), (j, request2) in itertools.combinations(enumerate(requests), 2):
        if request1.real_end() > request2.real_start() or request2.real_end() < request1.real_start():
            overlaps[i][j] = True
            overlaps[j][i] = True

    return overlaps
