import itertools
import logging
import random
from typing import List, Dict

import numpy as np

from CarSharing.Solution import Solution
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

        feasible, cost = self.solution.feasible_cost()

        prev_cost = -1
        while prev_cost != cost:
            prev_cost = cost
            logging.info('Result: %r %r', feasible, cost)
            logging.info('Car <> Zone: %r', {k: v.id for k, v in self.solution.car_zone.items()})
            logging.info('Request <> Car: %r', {k.id: v for k, v in self.solution.req_car.items()})
            logging.info('Unassigned: %r', {k.id for k in self.solution.get_unassigned()})
            logging.info('Feasible: %r Cost: %r', *self.solution.feasible_cost())

            changed: List[Solution] = []

            sol = self.solution.copy()

            # n = len(self.requests) // 4
            n = 4

            for r in self.requests.values():
                for _ in range(self.rng.randint(1, n)):
                    if sol.move_to_neighbour(r):
                        changed.append(sol)
                        sol = self.solution.copy()
                        # logging.info('move_to_neighbour True')
                for _ in range(self.rng.randint(1, n)):
                    if sol.neighbour_to_self(r):
                        changed.append(sol)
                        sol = self.solution.copy()
                        # logging.info('neighbour_to_self True')
                for _ in range(self.rng.randint(1, n)):
                    if sol.change_car_in_zone(r):
                        changed.append(sol)
                        sol = self.solution.copy()
                        # logging.info('change_car_in_zone True')

            if len(changed) == 0:
                logging.info('No more changes.')
                break

            changed = [(x, *x.feasible_cost()) for x in changed]
            changed.sort(key=lambda x: x[2])

            logging.info('Changes: n=%r, %r', len(changed), changed)

            if any(filter(lambda x: not x[1], changed)):
                raise RuntimeError("Made infeasible?")

            changed = list(filter(lambda x: x[2] <= cost and x[2] <= changed[0][2], changed))

            self.solution = self.rng.choice(changed)[0]

            feasible, cost = self.solution.feasible_cost()
