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
    # opportunity_cost: np.ndarray
    solution: Solution

    # def __init__(self, i, rng, requests, request_map, zones, zone_map, cars, days, overlap, opportunity_cost):
    def __init__(self, i, rng, requests, request_map, zones, zone_map, cars, days, overlap):
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
        # self.opportunity_cost = opportunity_cost

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

        # Simulated Annealing parameters
        t_max = 1000            # Max temp
        t_min = 10              # Min temp
        iterations = 1000       # Iterations for equilibrium
        alpha = 0.65            # Cooling factor

        temp = t_max

        aborted = False
        try:
            # Simulated Annealing
            while temp >= t_min:                    # Iterate until stopcondition is reached
                for x in range(iterations):         # Iterate until equilibrium is reached
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

                    # Generate random neighbour of solution
                    if func():
                        # Calculate energy difference
                        working_solution.calculate_cost()
                        delta_e = working_solution.cost - global_best.cost

                        if delta_e <= 0:
                            # This solution is better, save it
                            global_best = working_solution
                            solution = working_solution
                        # New solution is worse, accept it anyway with a probability
                        elif math.exp(-delta_e / temp) > self.rng.random():
                            global_best = working_solution
                            solution = working_solution

                    working_solution = solution.copy()

                    i += 1
                    if debug:
                        stats.append(working_solution.cost)

                # Apply cooling and reduce temp
                temp = temp * alpha

        except (KeyboardInterrupt, TimeoutError):
            aborted = True

        self.solution = global_best
        return i, stats if debug else (), aborted
