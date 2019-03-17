import logging
import math
from typing import Dict, TYPE_CHECKING, Iterable

from .Request import Request
from .Zone import Zone


if TYPE_CHECKING:
    from .Problem import Problem


class Solution:
    # problem: Problem
    car_zone: Dict[str, Zone]
    req_car: Dict[Request, str]

    def __init__(self, problem, car_zone, req_car):
        """
        :type problem: Problem
        """
        self.problem = problem
        self.car_zone = car_zone
        self.req_car = req_car

    def __str__(self):
        return '<Solution: Feasible={} Cost={}>'.format(*self.feasible_cost())

    def feasible_cost(self) -> (bool, int):
        # Cost is inf if the solutions is not feasible.
        cost = 0
        requests = list(self.problem.requests.values())
        # Check for overlap in car assignments
        for req, car in self.req_car.items():
            for i, overlap in enumerate(self.problem.overlap[req.index]):
                # Don't need to bother if there is no overlap
                if not overlap:
                    continue
                # If there is overlap, error.
                if (requests[i] in self.req_car.values()) and (car == self.req_car[requests[i]]):
                    return False, math.inf
        # Check if a request is matched to car in it's own or neighbouring zone.
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
        cost += sum(r.penalty1 for r in self.get_unassigned())
        return True, cost

    def save(self, filename):
        feasible, cost = self.feasible_cost()
        if not feasible:
            logging.warning('Not feasible, still saving...')

        with open(filename, 'w') as f:
            print(cost, file=f)
            print('+Vehicle assignments', file=f)
            for car, zone in self.car_zone.items():
                print(car, zone.id, sep=';', file=f)
            # Add all unassigned cars to a zone, to satisfy the verifier
            unassigned_cars = set(self.problem.cars) - set(self.car_zone.keys())
            if unassigned_cars:
                first_zone = next(iter(self.problem.zones.values()))
                logging.warning('Their are unassigned cars: %r', unassigned_cars)
                for car in unassigned_cars:
                    print(car, first_zone.id, sep=';', file=f)
            print('+Assigned requests', file=f)
            for req, car in self.req_car.items():
                print(req.id, car, sep=';', file=f)
            print('+Unassigned requests', file=f)
            for req in self.get_unassigned():
                print(req.id, file=f)

    def get_requests_by_car(self, car: str) -> Iterable[Request]:
        """
        Generator. Use in for loops.
        """
        for k, v in self.req_car.items():
            if v == car:
                yield k

    def get_unassigned(self) -> Iterable[Request]:
        """
        Generator. Use in for loops.
        """
        assigned = self.req_car.keys()
        for r in self.problem.requests.values():
            if r not in assigned:
                yield r

    def check_overlap_car_request(self, car, request):
        """
        Returns True if there is overlap between the already assigned requests and a new one.
        """
        for r in self.get_requests_by_car(car):
            if self.problem.overlap[request.index, r.index]:
                # There is overlap
                return True
        return False

    def greedy_assign(self, to_assign=None):
        """
        Used for the initial solution, but can also to used after changes to fill in the blanks.
        By default works on the unassigned set. Otherwise specify to_assign.
        """
        if to_assign is None:
            to_assign = self.get_unassigned()

        for request in to_assign:
            selected_car = None

            # Check to see if a car is already assigned to this zone, if it is non-overlapping, use that.
            # Also store free cars
            free_cars = []
            # Also store possible neighbours
            possible_neighbours = []
            for car in request.vehicles:

                if car in self.car_zone.keys():
                    zone = self.car_zone[car]
                else:
                    # Car still unassigned, skip for now.
                    if car not in free_cars:
                        free_cars.append(car)
                    continue

                # Car is assigned to a zone.
                if request.zone == zone:
                    # Car is assigned to our zone. Now check overlap.
                    if not self.check_overlap_car_request(car, request):
                        # Found a match!
                        selected_car = car
                        break
                elif request.zone.id in zone.neighbours:
                    # Car is assigned to our neighbour. Now check overlap.
                    if not self.check_overlap_car_request(car, request):
                        # If we don't find a direct match, we can use this later.
                        if car not in possible_neighbours:
                            possible_neighbours.append(car)

            if selected_car is None:
                if possible_neighbours:
                    # Pick one at random from the neighbour pile
                    selected_car = self.problem.rng.choice(possible_neighbours)
                elif free_cars:
                    # Pick one at random from the free car pile
                    selected_car = self.problem.rng.choice(free_cars)
                    # Assign the car to this zone.
                    self.car_zone[selected_car] = request.zone
                else:
                    # This request will be left unassigned.
                    continue

            # Here we must have a selected car.
            self.req_car[request] = selected_car

