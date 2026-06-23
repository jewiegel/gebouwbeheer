from .IResponse import IResponse


class ElevatorArrivedResponse(IResponse):
    def __init__(self, floor: int):
        self.floor = floor
