from .Request import Request
from .Zone import Zone


def parse_input():
    requests = []
    zones = []
    vehicles = []
    days = 0

    with open('toy1.csv', newline='') as csvfile:
        line = csvfile.readline()
        while line != "":
            if "+Requests:" in line:
                amount = int(line.split(" ")[1])

                for x in range(amount):
                    data = csvfile.readline().split(";")
                    requests.append(Request(*data))

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

    return requests, zones, vehicles, days



