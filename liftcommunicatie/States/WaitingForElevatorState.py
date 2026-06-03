from .IRobotLiftState import IRobotLiftState
from .WaitingForDoorsState import WaitingForDoorsState
from ..Communication.Requests.RequestLiftRequest import RequestLiftRequest


class WaitingForElevatorState(IRobotLiftState):
    def on_enter(self):
        self.context._elevator_arrived.clear()
        self.context.publish_feedback("Waiting for elevator")
        request = RequestLiftRequest(lift_id=self.context._lift_id)
        self.context.protocol.send_message(request.__dict__)
        self.context.get_logger().info(f"Requested elevator {self.context._lift_id}")

    async def execute(self):
        await self.context._elevator_arrived.wait()
        self.context.transition_to_state(WaitingForDoorsState(self.context))

    def on_exit(self):
        self.context.get_logger().info("Elevator arrived, proceeding")
