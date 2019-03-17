import itertools
import logging
import random
from typing import List, Dict

import numpy as np

from .Request import Request
from .Solution import Solution
from .Zone import Zone


class Problem:
    rng: random.Random
    requests: Dict[str, Request]
    zones: Dict[str, Zone]
    cars: List[str]
    days: int

    overlap: np.ndarray
    opportunity_cost: np.ndarray
    solution: Solution

    def __init__(self, rng, requests, zones, cars, days):
        self.rng = rng
        # {str id -> Request}
        self.requests = requests
        # {str id -> Zone}
        self.zones = zones
        # [str id]
        self.cars = cars
        # int
        self.days = days

        # Computed in run, since they are part of the computation, not input parsing.
        # ---------------

        # np {(int, int) -> bool}: Indexes are the value indexes of item in requests map.
        self.overlap = None
        # np {(int) -> int}: Index is the value indexes of item in requests map. Higher means worse to leave unassigned.
        self.opportunity_cost = None
        # Solution object, holds assignments etc
        self.solution = None

    def __repr__(self):
        return 'CarSharing<solution={!r}>'.format(self.solution)

    def calculate_overlap(self) -> np.ndarray:
        """
        Returns np array of booleans, where a True indicates an overlap between that row and col's request.
        """
        overlaps = np.zeros((len(self.requests), len(self.requests)), dtype=bool)

        for (i, request1), (j, request2) in itertools.combinations(enumerate(self.requests.values()), 2):
            if request1.real_start > request2.real_start:
                tmp = request1
                request1 = request2
                request2 = tmp
            if request1.real_end > request2.real_start or request2.real_end < request1.real_start:
                overlaps[i][j] = True
                overlaps[j][i] = True
        return overlaps

    def calculate_opportunity_cost(self) -> np.ndarray:
        """
        Calculate the cost of one request vs another, based on the penalty2 (not accept) cost only.
        Multiply with overlap matrix for easy summing of rows/cols

        A high positive sum in a row/col means the row/col's request is important.
        """
        cost = np.zeros((len(self.requests), len(self.requests)), dtype=int)
        for (i, request1), (j, request2) in itertools.combinations(enumerate(self.requests.values()), 2):
            cost[i][j] = request1.penalty1 - request2.penalty1
            cost[j][i] = request2.penalty1 - request1.penalty1
        return cost

    def save(self, filename: str) -> None:
        if self.solution is None:
            logging.error('No solution to save.')
            return
        self.solution.save(filename)

    def run(self, threads):
        self.overlap = self.calculate_overlap()
        self.opportunity_cost = np.sum(self.calculate_opportunity_cost(), axis=1)

        self.solution = Solution(self, {}, {})

        self.solution.greedy_assign()

        logging.info('Initial solution')
        logging.info('Car <> Zone: %r', {k: v.id for k, v in self.solution.car_zone.items()})
        logging.info('Request <> Car: %r', {k.id: v for k, v in self.solution.req_car.items()})
        logging.info('Unassigned: %r', {k.id for k in self.solution.get_unassigned()})
        logging.info('Feasible: %r Cost: %r', *self.solution.feasible_cost())
