from .IRobotLiftState import IRobotLiftStateState

class InElevatorState(IRobotLiftStateState):
    def on_enter(self):
        return super().on_enter()
    
    def on_exit(self):
        return super().on_exit()
    
    def update(self):
        return super().update()