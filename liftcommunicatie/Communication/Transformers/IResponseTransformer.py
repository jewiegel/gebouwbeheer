from abc import ABC, abstractmethod

class IResponseTransformer(ABC):
    
    # This method translates incoming responses into the Responses that are being used by the state machine
    @abstractmethod
    def to_response(self, response):
        pass
    
    
    #This method translates incoming requests to something the corresponding API can read
    @abstractmethod
    def from_request(self, request):
        pass