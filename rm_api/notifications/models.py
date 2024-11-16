"""
This module contains the models for the notifications.
Since these notifications are pretty mediocre, don't let the length of this file fool you.
"""


class Notification:  # A class to be used as a base class for all notifications
    ...


class LongLasting:  # A class to be used as a base class for all ongoing operation events
    ...


class SyncCompleted(Notification):
    """
    This event is used by the websocket to spread a sync completion,
    when received from remarkable cloud.
    """
    def __init__(self, message: dict):
        self.source_device_id = message['attributes'].get('sourceDeviceID')


class SyncRefresh(SyncCompleted):
    """
    Used when new files were synced by moss / moss doesn't pick up sync complete.
    This will force a sync refresh to get the latest document information.
    """
    # noinspection PyMissingConstructor
    def __init__(self):
        self.source_device_id = None


class FileSyncProgress(LongLasting):
    """This event is designed to be spread once and kept for monitoring the progress."""

    def __init__(self):
        self.done = 0
        self.total = 0
        self.finished = False
