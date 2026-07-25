class FixedFrameTool:
    def __init__(self):
        self.fixed_frame = None

    def set_fixed_frame(self, frame):
        self.fixed_frame = frame

    def get_fixed_frame(self):
        return self.fixed_frame

class Doctor:
    def __init__(self, fixed_frame_tool):
        self.fixed_frame_tool = fixed_frame_tool

    def reflect_frame(self):
        fixed_frame = self.fixed_frame_tool.get_fixed_frame()
        if fixed_frame:
            print(f"Doctor reflects frame: {fixed_frame}")
        else:
            print("No fixed frame set")

class MockState:
    def __init__(self):
        self.fixed_frame_tool = FixedFrameTool()

    def update_fixed_frame(self, frame):
        self.fixed_frame_tool.set_fixed_frame(frame)

def main():
    mock_state = MockState()
    doctor = Doctor(mock_state.fixed_frame_tool)

    mock_state.update_fixed_frame("mock_frame")
    doctor.reflect_frame()

if __name__ == "__main__":
    main()