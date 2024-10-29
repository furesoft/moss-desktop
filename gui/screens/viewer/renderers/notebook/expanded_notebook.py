from abc import ABC, abstractmethod

class ExpandedNotebook(ABC):
    def __init__(self, frame_width: int, frame_height: int):
        self.frame_width = frame_width
        self.frame_height = frame_height

    def get_frames(self, area_x: int, area_y: int, area_width: int, area_height: int):
        visible_frames = []

        start_x = area_x // self.frame_width
        end_x = (area_x + area_width) // self.frame_width
        start_y = area_y // self.frame_height
        end_y = (area_y + area_height) // self.frame_height

        for frame_x in range(start_x, end_x + 1):
            for frame_y in range(start_y, end_y + 1):
                frame_left = frame_x * self.frame_width
                frame_right = frame_left + self.frame_width
                frame_top = frame_y * self.frame_height
                frame_bottom = frame_top + self.frame_height

                if (frame_right > area_x and frame_left < area_x + area_width and
                    frame_bottom > area_y and frame_top < area_y + area_height):
                    visible_frames.append((frame_x, -frame_y))

        return [
            self.get_frame_from_initial(
                frame[0]*self.frame_width,
                frame[1]*self.frame_height
            )
            for frame in visible_frames
        ]

    @abstractmethod
    def get_frame_from_initial(self, x, y): ...