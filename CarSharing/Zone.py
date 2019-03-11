
class Zone:
    def __init__(self, id: str, neighbours: str):
        self.id = id
        self.neighbours = neighbours.split(",")

    def __repr__(self):
        return 'Zone<id: {}, neighbours: {}>'.format(self.id, self.neighbours)

    def check(self, zone_id: str):
        """ Check if given zone matches or is a neighbour  """
        return zone_id == self.id or zone_id in self.neighbours
