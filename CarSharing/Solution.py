from typing import Iterable
from typing import List
from typing import Dict

import os
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
        self.overlap: np.ndarray = calculate_overlap(requests)
        self.opportunity_cost: np.ndarray = calculate_opportunity_cost(requests) * self.overlap

        print(self.requests)
        print(self.zone)
        print(self.cars)
        print(self.days)
        print(self.overlap)
        print(self.opportunity_cost)

        # Start with everything unassigned.
        self.car_zone: Dict[str, Zone] = {}
        self.req_car: Dict[Request, str] = {}
        self.unassigned: List[Request] = [*requests]

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
                if car == self.req_car[self.request_list[i]]:
                    return False, math.inf
        # Request matched to car in it's own or neighbouring zone.
        for req, car in self.req_car.items():
            zone = self.car_zone[car]
            if zone is None:  # Hard error.
                raise RuntimeError('Request {} assigned to Car {} that is not in a zone.'.format(req, req))
            if req.zone == zone.id:
                pass
            elif req.zone not in zone.neighbours:
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

        os.system('java -jar validator.jar "{}" "{}"'.format(input_filename, output_filename))

    def __repr__(self):
        return 'Solution<feasible: {}, cost: {}>'.format(*self.feasible())
