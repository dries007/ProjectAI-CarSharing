import logging
import random
from typing import List, Dict

import math
import numpy as np

from CarSharing.RandomDict import RandomDict
from CarSharing.Request import Request
from CarSharing.Solution import Solution
from CarSharing.Zone import Zone


class Problem:
    rng: random.Random
    requests: List[Request]
    request_map: Dict[str, Request]
    zones: List[Zone]
    zone_map: Dict[str, Zone]
    cars: List[str]
    days: int

    overlap: np.ndarray
    opportunity_cost: np.ndarray
    solution: Solution

    def __init__(self, i, rng, requests, request_map, zones, zone_map, cars, days, overlap, opportunity_cost):
        self.log = logging.getLogger('JOB %d' % i)
        self.rng = rng

        self.requests = requests
        # {str id -> Request}
        self.request_map = request_map

        self.zones = zones
        # {str id -> Zone}
        self.zone_map = zone_map

        self.cars = cars
        self.days = days

        # np {(int, int) -> bool}: Indexes are the value indexes of item in requests map.
        self.overlap = overlap
        # np {(int) -> int}: Index is the value indexes of item in requests map. Higher means worse to leave unassigned.
        self.opportunity_cost = opportunity_cost

        # Solution object, holds assignments etc
        self.solution = None

    def __repr__(self):
        return '<CarSharing solution={!r}>'.format(self.solution)

    def save(self, file) -> None:
        if self.solution is None:
            self.log.error('No solution to save.')
            return
        self.solution.save(file)

    def run(self, debug) -> (int, list):
        solution = Solution(self, RandomDict.from_random(self.rng), RandomDict.from_random(self.rng))
        solution.greedy_assign()
        solution.calculate_cost()

        if debug:
            stats = [solution.cost]

        i = 0
        global_best = solution
        working_solution = solution.copy()
        i_since_last_improvement = 0
        stale_factor = 100 * len(self.requests)
        aborted = False
        try:
            # self.log.debug('Started actually iterating...')
            while True:
                # todo: add any extra "move" functions here. They should all have the signature '() -> bool'
                # todo: Maybe make some moves more likely than others. The 'harsher' the change,
                #  the more likely they will have a large impact, but also the more compute power is required.
                func = self.rng.choice((
                    working_solution.move_to_neighbour,
                    working_solution.neighbour_to_self,
                    working_solution.change_car_in_zone,
                    working_solution.unassign_request,
                    working_solution.unassign_request,  # 2x more likely
                    working_solution.unassign_car,
                    working_solution.unassign_car,  # 2x more likely
                ))

                if func():
                    working_solution.calculate_cost()
                    if working_solution.cost < global_best.cost:
                        global_best = working_solution
                        solution = working_solution
                        i_since_last_improvement = 0
                    # todo: implement simulated annealing, not this random 'homebrew' thing
                    # Accept worse thing with a chance that's depending on when the last improvement was.
                    elif self.rng.random() < 0.001*math.exp(-0.001*i_since_last_improvement):
                        solution = working_solution
                    # Also have some chance to reset to the global best.
                    # Lower at the start, but it catches up at ~380, it passes 1 after ~1842
                    elif self.rng.random() < 0.0001*math.exp(0.005*i_since_last_improvement):
                        solution = global_best

                    working_solution = solution.copy()

                i += 1
                i_since_last_improvement += 1
                if debug:
                    stats.append(working_solution.cost)

                # Todo: Fine-tune
                if i_since_last_improvement > stale_factor:
                    break

        except (KeyboardInterrupt, TimeoutError):
            aborted = True

        self.solution = global_best
        return i, stats if debug else (), aborted
