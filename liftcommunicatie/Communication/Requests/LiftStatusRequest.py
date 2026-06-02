from .IRequest import IRequest

class ChooseFloorRequest(IRequest):
    def __init__(self, lift_id: int, target_floor: int):
        self.lift_id = lift_id
        self.target_floor = target_floor