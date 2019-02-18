from typing import List
from typing import Dict

from .Request import Request
from .Zone import Zone


class Solution:
    def __init__(self, requests: List[Request], zone: List[Zone], cars: List[str]):
        self.requests: Dict[str, Request] = {r.id: r for r in requests}
        self.zone: Dict[str, Zone] = {z.id: z for z in zone}
        self.cars: List[str] = cars

        self.car_zone: Dict[str, Zone] = {}
        self.req_car: Dict[Request, str] = {}
        self.unassigned: List[Request] = requests[:]
        self.assigned_to_neighbour: List[Request] = []

    def cost(self) -> int:
        return sum(r.penalty1 for r in self.unassigned) + sum(r.penalty2 for r in self.assigned_to_neighbour)

    def save(self, filename: str) -> None:
        with open(filename, 'w') as f:
            print(self.cost(), file=f)
            print('+Vehicle assignments', file=f)
            for car, zone in self.car_zone.items():
                print(car, zone.id, sep=';', file=f)
            print('+Assigned requests', file=f)
            for req, car in self.req_car.items():
                print(req, car, sep=';', file=f)
            print('+Unassigned requests', file=f)
            for req in self.unassigned:
                print(req.id,  file=f)
