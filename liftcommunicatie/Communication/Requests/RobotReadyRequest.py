from .IRequest import IRequest


class RobotReadyRequest(IRequest):
    """Sent once the robot is inside the lift, so the lift knows it may move on."""
    pass
