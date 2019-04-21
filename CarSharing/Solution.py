import logging
import math
import numpy as np
from typing import TYPE_CHECKING, Iterable

from CarSharing.RandomDict import RandomDictType
from CarSharing.Request import Request
from CarSharing.Zone import Zone


if TYPE_CHECKING:
    from .Problem import Problem


class Solution:
    if TYPE_CHECKING:
        problem: Problem
    car_zone: RandomDictType[str, Zone]
    req_car: RandomDictType[Request, str]

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

        for req, car in self.req_car.items():
            # Check if a request is matched to car in it's own or neighbouring zone.
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

            # Check for overlap in car assignments (nonzero returns a list of lists of indexes)
            for i in np.nonzero(self.problem.overlap[req.index])[0]:
                req_i = self.problem.requests[i]
                # If there is overlap (req is assigned and is assigned to the same car), error.
                if req_i in self.req_car and car == self.req_car[req_i]:
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
            first_zone = next(iter(self.problem.zone_map.values()))
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
        items = (req for req, car in self.req_car.items() if car == car_needle)
        if shuffle:
            items = list(items)
            self.problem.rng.shuffle(items)
        return items

    def get_unassigned(self, shuffle=True) -> Iterable[Request]:
        """
        Generator. Use in for loops.
        """
        filtered = filter(lambda r: r not in self.req_car, self.problem.requests)
        if shuffle:
            filtered = list(filtered)
            self.problem.rng.shuffle(filtered)
        return filtered

    def check_overlap_car_request(self, car: str, request: Request):
        """
        Returns True if there is overlap between the already assigned requests and a new one.
        """
        # All indexes with overlap
        overlap = self.problem.overlap[request.index]
        for r in self.get_requests_by_car(car, shuffle=False):
            if overlap[r.index]:
                return True
        return False

    def greedy_assign(self, to_assign=None):
        """
        Used for the initial solution, but can also to used after changes to fill in the blanks.
        By default works on the unassigned set. Otherwise specify to_assign.
        """
        if to_assign is None:
            to_assign = self.get_unassigned(shuffle=True)

        for request in to_assign:
            selected_car = None

            # Check to see if a car is already assigned to this zone, if it is non-overlapping, use that.
            # Also store free cars
            free_cars = []
            # Also store possible neighbours
            possible_neighbours = []
            for car in request.vehicles:

                if car in self.car_zone:
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

    def move_to_neighbour(self, req: Request = None) -> bool:
        """
        Attempt to move a request to a neighbour. Returns False if nothing changed.
        If already in a neighbour, it tries another. Does _not_ move back to it's own zone.
        Does not move to another car in the same zone.
        :param req: Request to move, or None for a random assigned request
        :return: bool: Has a change been made?
        """
        if req is None:
            req = self.req_car.random_key()
        elif req not in self.req_car:
            # Request is not assigned.
            return False

        # Current data
        current_car = self.req_car[req]
        current_zone = self.car_zone[current_car]
        assigned_cars = self.car_zone

        # Make a list of all cars the request can be assigned to, excluding our current and excluding any unassigned cars
        possible_cars = filter(lambda c: c != current_car and c in assigned_cars, req.vehicles)

        # Set of acceptable zones based on the conditions:                    Ignore same zone, Don't move to own zone, Zone must be a neighbour.
        allowed_zones = {z for z in {self.car_zone[c] for c in possible_cars} if z != current_zone and z != req.zone and z.id in req.zone.neighbours}
        # If there are no acceptable zones, quit
        if len(allowed_zones) == 0:
            return False

        # Now filter out cars that are not assigned to one of those zones or that would result in overlap
        possible_cars = filter(lambda c: self.car_zone[c] in allowed_zones and not self.check_overlap_car_request(c, req), possible_cars)

        possible_cars = tuple(possible_cars)
        if len(possible_cars) == 0:
            return False

        picked_car = self.problem.rng.choice(possible_cars)
        # logging.info('possible_cars: Picked %r out of %r', picked_car, possible_cars)

        self.req_car[req] = picked_car
        self.greedy_assign()
        return True

    def neighbour_to_self(self, req: Request = None) -> bool:
        """
        Move a request from a neighbour zone to the best zone
        :param req: Request to move, or None for a random assigned request
        :return: bool: Has a change been made?
        """
        if req is None:
            req = self.req_car.random_key()
        elif req not in self.req_car:
            # Request is not assigned.
            return False

        current_car = self.req_car[req]
        current_zone = self.car_zone[current_car]

        # Check if request is already in the right zone
        if current_zone == req.zone:
            return False

        # Check if other cars are available in the right zone
        for car in req.vehicles:
            if car != current_car:
                # Check if the car has a zone, and this zone is the right zone
                if car in self.car_zone and self.car_zone[car] == req.zone:
                    # Check for overlap with the new car and the request
                    if not self.check_overlap_car_request(car, req):
                        # This car is suitable as a replacement
                        self.req_car[req] = car
                        self.greedy_assign()
                        return True

        return False

    def change_car_in_zone(self, req: Request = None) -> bool:
        """
        Try to swap the car for this request with a different car in the same zone
        :param req: Request to move, or None for a random assigned request
        :return: bool: Has a change been made?
        """
        if req is None:
            req = self.req_car.random_key()
        elif req not in self.req_car:
            # Request is not assigned.
            return False

        current_car = self.req_car[req]
        current_zone = self.car_zone[current_car]

        for car in req.vehicles:
            if car != current_car:
                # Check if the car has a zone, and this zone is the current zone
                if car in self.car_zone and self.car_zone[car] == current_zone:
                    # Check for overlap with the new car and the request
                    if not self.check_overlap_car_request(car, req):
                        # This car is suitable as a replacement
                        self.req_car[req] = car
                        self.greedy_assign()
                        return True

        return False

    def unassign_request(self, req: Request = None) -> bool:
        """
        Unassign a request.
        :param req: Request to unassign, or None for a random assigned request
        :return: bool: Has a change been made?
        """
        if req is None:
            req = self.req_car.random_key()
        elif req not in self.req_car:
            # Request is not assigned.
            return False

        del self.req_car[req]
        self.greedy_assign()

        return True

    def unassign_car(self, car: str = None) -> bool:
        """
        Unassign a car from all requests.
        :param car: Car to unassign, or None for a random assigned car
        :return: bool: Has a change been made?
        """
        if car is None:
            car = self.car_zone.random_key()
        elif car not in self.car_zone:
            # Car is not assigned.
            return False

        del self.car_zone[car]
        # Tuple because we need to modify the list inplace
        for req, _ in tuple(filter(lambda x: x[1] == car, self.req_car.items())):
            del self.req_car[req]

        # for req, req_car in tuple(self.req_car.items()):
        #     if req_car == car:
        #         del self.req_car[req]

        self.greedy_assign()

        return True

    # todo: add more "drastic" moves, such as just moving a car to a different region.
    # todo: add a "switch cars" move, where a request just moves to a different car.
