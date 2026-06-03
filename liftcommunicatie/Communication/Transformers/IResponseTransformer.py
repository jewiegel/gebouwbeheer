from abc import ABC, abstractmethod

class IResponseTransformer(ABC):
    
    @abstractmethod
    def to_response(self, response):
        pass
    
    
    @abstractmethod
    def from_request(self, request):
        pass