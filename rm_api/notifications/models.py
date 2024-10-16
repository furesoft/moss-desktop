"""
This module contains the models for the notifications.
Since these notifications are pretty mediocre, don't let the length of this file fool you.
"""


class Notification:  # A class to be used as a base class for all notifications
    ...


class SyncCompleted(Notification):
    def __init__(self, message: dict):
        self.source_device_id = message['attributes']['sourceDeviceID']
