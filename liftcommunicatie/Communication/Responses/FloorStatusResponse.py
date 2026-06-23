from .IResponse import IResponse

class FloorStatusResponse(IResponse):
    def __init__(self, floor):
        self.floor = floor