from .IRequest import IRequest
class RequestLiftRequest(IRequest):
    def __init__(self, lift_id: int):
        self.lift_id = lift_id