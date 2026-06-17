from .IResponseTransformer import IResponseTransformer
from ..Responses import DoorsStatusResponse, FloorStatusResponse
from ..Requests import RequestLiftRequest, ChooseFloorRequest, LiftStatusRequest, RobotReadyRequest


class TestLiftProtocolTransformer(IResponseTransformer):


    def to_response(self, message: dict):
        msg_type = message.get('event')

        if msg_type == 'doors status':
            return DoorsStatusResponse(status=message['status'])
        elif msg_type == 'liftArrived':
            # Single arrival event used both when the lift is picked up at the current
            # floor and when it reaches the target floor; the waiting state checks which.
            return FloorStatusResponse(floor=message['floor'])

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
            return {'command': 'api/v1/lift/RequestLiftCommand', 'floor': request.current_floor, 'waitForRobot': True}
        elif isinstance(request, ChooseFloorRequest):
            return {'command': 'api/v1/lift/ChooseLiftFloorCommand', 'floor': request.target_floor, 'waitForRobot': True}
        elif isinstance(request, LiftStatusRequest):
            return {'command': 'lift status', 'lift_id': request.lift_id}
        elif isinstance(request, RobotReadyRequest):
            return {'command': 'api/v1/lift/RobotReadyCommand'}

        raise ValueError(f"Unknown request type: {type(request).__name__}")
