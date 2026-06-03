from .IResponse import IResponse

class DoorsStatusResponse(IResponse):
    def __init__(self, status):
        self.status = status