import logging
import math
from typing import Dict, TYPE_CHECKING, Iterable

from .Request import Request
from .Zone import Zone


if TYPE_CHECKING:
    from .Problem import Problem


class Solution:
    if TYPE_CHECKING:
        problem: Problem
    car_zone: Dict[str, Zone]
    req_car: Dict[Request, str]

    def __init__(self, problem, car_zone, req_car):
        self.problem = problem
        self.car_zone = car_zone
        self.req_car = req_car
        self.cost = None

    def __repr__(self):
        return '<Solution: Last run cost={}>'.format(self.cost)

    def copy(self):
        return Solution(self.problem, self.car_zone.copy(), self.req_car.copy())

    def feasible_cost(self) -> (bool, int):
        # Cost is inf if the solutions is not feasible.
        cost = 0

        # todo: replace all of these "list(self.problem.requests.values())" with a cached value or generator instead of list copy.

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
                logging.warning('Not feasible, request {} not in zone or neighbours ({}).'.format(req, zone))
                return False, math.inf
        # Cost for unassigned requests
        cost += sum(r.penalty1 for r in self.get_unassigned(shuffle=False))
        self.cost = cost
        return True, cost

    def save(self, file):
        logging.info('Saving a solution with score %r', self.cost)

        print(self.cost, file=file)
        print('+Vehicle assignments', file=file)
        for car, zone in self.car_zone.items():
            print(car, zone.id, sep=';', file=file)
        # Add all unassigned cars to a zone, to satisfy the verifier
        unassigned_cars = set(self.problem.cars) - set(self.car_zone.keys())
        if unassigned_cars:
            first_zone = next(iter(self.problem.zones.values()))
            logging.warning('Their are unassigned cars: %r', unassigned_cars)
            for car in unassigned_cars:
                print(car, first_zone.id, sep=';', file=file)
        print('+Assigned requests', file=file)
        for req, car in self.req_car.items():
            print(req.id, car, sep=';', file=file)
        print('+Unassigned requests', file=file)
        for req in self.get_unassigned(shuffle=False):
            print(req.id, file=file)

    def get_requests_by_car(self, car_needle: str, shuffle=True) -> Iterable[Request]:
        """
        Generator. Use in for loops.
        """
        items = (req for req, car in filter(lambda x: x[1] == car_needle, self.req_car.items()))
        if shuffle:
            items = list(items)
            self.problem.rng.shuffle(items)
        return items

    def get_unassigned(self, shuffle=True) -> Iterable[Request]:
        """
        Generator. Use in for loops.
        """
        assigned = self.req_car.keys()
        requests = self.problem.requests.values()
        filtered = filter(lambda r: r not in assigned, requests)
        if shuffle:
            filtered = list(filtered)
            self.problem.rng.shuffle(filtered)
        return filtered

    def check_overlap_car_request(self, car, request):
        """
        Returns True if there is overlap between the already assigned requests and a new one.
        """
        for r in self.get_requests_by_car(car, shuffle=False):
            if self.problem.overlap[request.index, r.index]:
                # There is overlap
                return True
        return False

    def move_to_neighbour(self, req: Request) -> bool:
        """
        Attempt to move a request to a neighbour. Returns False if nothing changed.
        If already in a neighbour, it tries another. Does _not_ move back to it's own zone.
        Does not move to another car in the same zone.
        """
        if req not in self.req_car.keys():
            # Request is not assigned.
            return False

        # Current data
        current_car = self.req_car[req]
        current_zone = self.car_zone[current_car]

        # Make a rng list of assigned cars, excluding our own.
        possible_cars = filter(lambda x: x in self.car_zone.keys() and x != current_car, req.vehicles)
        # Check conditions for the zone.             Ignore same zone.      Don't move to own zone.    Zone is not a neighbour.
        possible_cars = filter(lambda x: x[1] != current_zone and x[1] != req.zone and x[1].id in req.zone.neighbours,
                               ((x, self.car_zone[x]) for x in possible_cars))
        # Check conditions for the car (overlap)
        possible_cars = filter(lambda x: not self.check_overlap_car_request(x[0], req), possible_cars)

        possible_cars = list(x for x, _ in possible_cars)
        if len(possible_cars) == 0:
            return False

        picked_car = self.problem.rng.choice(possible_cars)
        # logging.info('possible_cars: Picked %r out of %r', picked_car, possible_cars)

        self.req_car[req] = picked_car
        self.greedy_assign()
        return True

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

    def neighbour_to_self(self, request: Request) -> bool:
        """
        Move a request from a neighbour zone to the best zone
        :param request: Request to move
        :return: bool: Has a change been made?
        """
        # Check if the request is already assigned to a car
        if request not in self.req_car.keys():
            return False

        current_car = self.req_car[request]
        current_zone = self.car_zone[current_car]

        # Check if request is already in the right zone
        if current_zone == request.zone:
            return False

        # Check if other cars are available in the right zone
        for car in request.vehicles:
            if car != current_car:
                # Check if the car has a zone, and this zone is the right zone
                if car in self.car_zone.keys() and self.car_zone[car] == request.zone:
                    # Check for overlap with the new car and the request
                    if not self.check_overlap_car_request(car, request):
                        # This car is suitable as a replacement
                        self.req_car[request] = car
                        self.greedy_assign()
                        return True

        return False

    def change_car_in_zone(self, request: Request) -> bool:
        """
        Try to swap the car for this request with a different car in the same zone
        :param request: Request to change car
        :return: bool: Has a change been made?
        """
        if request not in self.req_car.keys():
            return False

        current_car = self.req_car[request]
        current_zone = self.car_zone[current_car]

        for car in request.vehicles:
            if car != current_car:
                # Check if the car has a zone, and this zone is the current zone
                if car in self.car_zone.keys() and self.car_zone[car] == current_zone:
                    # Check for overlap with the new car and the request
                    if not self.check_overlap_car_request(car, request):
                        # This car is suitable as a replacement
                        self.req_car[request] = car
                        self.greedy_assign()
                        return True

        return False
