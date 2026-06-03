from .IResponseTransformer import IResponseTransformer

class TestLiftProtocolTransformer(IResponseTransformer):
    
    def from_request(self, request):
        return super().from_request(request)
    
    def to_response(self, response):
        return super().to_response(response)