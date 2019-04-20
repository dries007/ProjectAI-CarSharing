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

    def __init__(self, i, rng, requests, zones, cars, days, overlap, opportunity_cost):
        self.log = logging.getLogger('JOB %d' % i)
        self.rng = rng
        # {str id -> Request}
        self.requests = requests
        # {str id -> Zone}
        self.zones = zones
        # [str id]
        self.cars = cars
        # int
        self.days = days
        # np {(int, int) -> bool}: Indexes are the value indexes of item in requests map.
        self.overlap = overlap
        # np {(int) -> int}: Index is the value indexes of item in requests map. Higher means worse to leave unassigned.
        self.opportunity_cost = opportunity_cost

        # Solution object, holds assignments etc
        self.solution = None

    def __repr__(self):
        return 'CarSharing<solution={!r}>'.format(self.solution)

    def save(self, file) -> None:
        if self.solution is None:
            self.log.error('No solution to save.')
            return
        self.solution.save(file)

    def run(self, debug) -> (int, list):
        requests = tuple(self.requests.values())

        self.solution = Solution(self, {}, {})
        self.solution.greedy_assign()
        lowest_cost = self.solution.feasible_cost()[1]

        if debug:
            stats = [lowest_cost]

        i = 0
        sol = self.solution.copy()
        last_improvement = 0
        max_stale_rounds = 10 * len(requests)
        aborted = False
        try:
            self.log.debug('Started actually iterating...')

            while True:
                req = self.rng.choice(requests)
                func = self.rng.choice((sol.move_to_neighbour, sol.neighbour_to_self, sol.change_car_in_zone))

                if func(req):
                    feasible, cost = sol.feasible_cost()
                    if not feasible:
                        raise RuntimeError('Made infeasible?')
                    if cost < lowest_cost:
                        lowest_cost = cost
                        self.solution = sol
                        last_improvement = i

                    sol = self.solution.copy()

                i += 1
                if debug:
                    stats.append(lowest_cost)

                if i - last_improvement > max_stale_rounds:
                    self.log.debug('No improvements for %d cycles.', max_stale_rounds)
                    break

        except (KeyboardInterrupt, TimeoutError):
            aborted = True

        if not debug:
            stats = ()
        return i, lowest_cost, stats, aborted

