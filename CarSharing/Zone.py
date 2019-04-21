from typing import Set


class Zone:
    def __init__(self, id: str, neighbours: str):
        self.id: str = id
        self.neighbours: Set[str] = set(neighbours.split(","))

    def __repr__(self):
        return 'Zone<id: {!r}, neighbours: {!r}>'.format(self.id, self.neighbours)

    def check(self, zone_id: str):
        """ Check if given zone matches or is a neighbour  """
        return zone_id == self.id or zone_id in self.neighbours
