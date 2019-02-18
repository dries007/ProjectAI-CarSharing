
class Zone:
    def __init__(self, id: str, neighbours: str):
        self.id = id
        self.neighbours = neighbours.split(",")

    def __repr__(self):
        return 'Zone<id: {}, neighbours: {}>'.format(self.id, self.neighbours)
