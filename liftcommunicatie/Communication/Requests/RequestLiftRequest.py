from .IRequest import IRequest
class RequestLiftRequest(IRequest):
    def __init__(self, current_floor: int):
        self.current_floor = current_floor