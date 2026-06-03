from .IResponseTransformer import IResponseTransformer
from ..Responses import DoorsStatusResponse, FloorStatusResponse
from ..Requests import RequestLiftRequest, ChooseFloorRequest, LiftStatusRequest


class TestLiftProtocolTransformer(IResponseTransformer):

    _RESPONSE_MAP = {
        'doors status': (DoorsStatusResponse, ['status']),
        'floor status': (FloorStatusResponse, ['floor']),
    }

    _REQUEST_MAP = {
        RequestLiftRequest: 'request lift',
        ChooseFloorRequest: 'choose floor',
        LiftStatusRequest:  'lift status',
    }

    def to_response(self, message: dict):
        msg_type = message.get('type')
        entry = self._RESPONSE_MAP.get(msg_type)
        if entry is None:
            return None
        cls, fields = entry
        kwargs = {field: message[field] for field in fields}
        return cls(**kwargs)

    def from_request(self, request):
        msg_type = self._REQUEST_MAP.get(type(request))
        if msg_type is None:
            raise ValueError(f"Unknown request type: {type(request).__name__}")
        return {'type': msg_type, **request.__dict__}
