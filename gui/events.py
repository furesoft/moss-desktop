from rm_api.notifications.models import Notification


class ResizeEvent:
    def __init__(self, new_size):
        self.new_size = new_size


class MossFatal(Notification):
    """
        This signals the code should stop execution instantly
    """
    ...
