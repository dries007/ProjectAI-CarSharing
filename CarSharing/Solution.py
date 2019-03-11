from typing import Iterable
from typing import List
from typing import Dict

import os
from pprint import pprint
import math

import numpy as np

from .input_parser import calculate_overlap, calculate_opportunity_cost
from .Request import Request
from .Zone import Zone


class Solution:
    def __init__(self, requests: List[Request], zone: List[Zone], cars: List[str], days: int):
        self.request_list: List[Request] = requests
        self.requests: Dict[str, Request] = {r.id: r for r in requests}
        self.zone: Dict[str, Zone] = {z.id: z for z in zone}
        self.cars: Iterable[str] = cars
        self.days: int = days
        # bool matrix of overlap. X and Y axis are the same.
        self.overlap: np.ndarray = calculate_overlap(requests)
        # List of relative cost of a reservation based on overlap. If high, the cost of not assigning this request would be high.
        self.opportunity_cost: np.ndarray = np.sum(calculate_opportunity_cost(requests), axis=1)

        # print('Input')
        # pprint(self.requests)
        # pprint(self.zone)
        # pprint(self.cars)
        # pprint(self.days)
        # pprint(self.overlap)
        # pprint(self.opportunity_cost)

        # Start with everything unassigned.
        self.car_zone: Dict[str, Zone] = {}
        self.req_car: Dict[Request, str] = {}
        self.unassigned: List[Request] = [*requests]

        self.create_initial_solution()

        print('Initial solution')
        print('car <> zone:')
        pprint(self.car_zone)
        print('request <> car:')
        pprint(self.req_car)
        print('unassigned:')
        pprint(self.unassigned)
        print('Feasible, Cost:', self.feasible())

    def feasible(self) -> (bool, int):
        # Cost is inf if the solutions is not feasible.
        cost = 0
        # Check for overlap. Loop over every assignment and check if any of the overlapping requests are assigned to the same cars.
        for req, car in self.req_car.items():
            for i, overlap in enumerate(self.overlap[req.index]):
                # Don't need to bother if there is no overlap
                if not overlap:
                    continue
                # If there is overlap, error.
                if (self.request_list[i] in self.req_car) and (car == self.req_car[self.request_list[i]]):
                    return False, math.inf
        # Request matched to car in it's own or neighbouring zone.
        for req, car in self.req_car.items():
            zone = self.car_zone[car]
            if zone is None:  # Hard error.
                raise RuntimeError('Request {} assigned to Car {} that is not in a zone.'.format(req, req))
            if req.zone == zone:
                pass
            elif req.zone.id in zone.neighbours:
                cost += req.penalty2
            else:
                print('Not feasible, request {} not in zone or neighbours ({}).'.format(req, zone))
                return False, math.inf
        # Cost for unassigned requests
        cost += sum(r.penalty1 for r in self.unassigned)
        return True, cost

    def save(self, filename: str) -> None:
        feasible, cost = self.feasible()
        if not feasible:
            print('Not feasible, still saving...')

        with open(filename, 'w') as f:
            print(cost, file=f)
            print('+Vehicle assignments', file=f)
            for car, zone in self.car_zone.items():
                print(car, zone.id, sep=';', file=f)
            print('+Assigned requests', file=f)
            for req, car in self.req_car.items():
                print(req.id, car, sep=';', file=f)
            print('+Unassigned requests', file=f)
            for req in self.unassigned:
                print(req.id,  file=f)

    def validate(self, input_filename: str, output_filename: str):
        if not self.feasible():
            print('Not feasible, still validating...')
        print("Verified output")
        print("---------------")
        os.system('java -jar validator.jar "{}" "{}"'.format(input_filename, output_filename))
        print("---------------")

    def create_initial_solution(self):
        """ Create initial feasible solution """
        # Because you can't modify the list on the loop, [:] creates a clone.
        for request in self.unassigned[:]:
            selected_car = False
            selected_zone = False

            # Check for unassigned cars
            for car in request.vehicles:
                if car not in self.car_zone:
                    selected_car = car
                    selected_zone = request.zone
                    break

            # All cars are in a zone, search for a zone
            if not selected_car:
                for car in request.vehicles:
                    zone = self.car_zone[car]
                    if request.zone.check(zone.id) and not self.check_overlap(car, request):
                        selected_car = car
                        selected_zone = zone
                        break

            # If we found a car and a zone, save it
            if selected_car and selected_zone:
                self.car_zone[selected_car] = selected_zone
                self.req_car[request] = selected_car
                self.unassigned.remove(request)

        # Add all unasigned cars to a zone
        print('unassigned cars')
        pprint(set(self.cars) - set(self.car_zone.keys()))
        for car in set(self.cars) - set(self.car_zone.keys()):
            self.car_zone[car] = next(iter(self.zone.values()))

    def check_overlap(self, vehicle: str, request: Request):
        """ Check if a request overlaps with other requests for a given car """
        for req, car in self.req_car.items():
            if car == vehicle:
                if self.overlap[request.index, req.index]:
                    return True

        return False

    def __repr__(self):
        return 'Solution<feasible: {!r}, cost: {!r}>'.format(*self.feasible())
