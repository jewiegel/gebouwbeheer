from .IResponseTransformer import IResponseTransformer
from ..Responses import DoorsStatusResponse, FloorStatusResponse, ElevatorArrivedResponse
from ..Requests import RequestLiftRequest, ChooseFloorRequest, LiftStatusRequest


class TestLiftProtocolTransformer(IResponseTransformer):


    def to_response(self, message: dict):
        msg_type = message.get('event')

        if msg_type == 'doors status':
            return DoorsStatusResponse(status=message['status'])
        elif msg_type == 'floorReached':
            return FloorStatusResponse(floor=message['floor'])
        elif msg_type == 'liftArrived':
            return ElevatorArrivedResponse(floor=message['floor'])

        return None

    def to_request(self, message: dict):
        msg_type = message.get('type')

        if msg_type == 'request lift':
            return RequestLiftRequest(current_floor=message['current_floor'])
        elif msg_type == 'choose floor':
            return ChooseFloorRequest(target_floor=message['target_floor'])
        elif msg_type == 'lift status':
            return LiftStatusRequest(lift_id=message['lift_id'])

        return None

    def from_request(self, request):
        if isinstance(request, RequestLiftRequest):
            return {'command': 'api/v1/lift/RequestLiftCommand', 'floor': request.current_floor}
        elif isinstance(request, ChooseFloorRequest):
            return {'command': 'api/v1/lift/ChooseLiftFloorCommand', 'floor': request.target_floor}
        elif isinstance(request, LiftStatusRequest):
            return {'command': 'lift status', 'lift_id': request.lift_id}

        raise ValueError(f"Unknown request type: {type(request).__name__}")
