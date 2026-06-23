from .IRequest import IRequest

class ChooseFloorRequest(IRequest):
    def __init__(self, target_floor: int):
        self.target_floor = target_floor