import json
import threading
import websocket
from typing import TYPE_CHECKING

from rm_api.notifications.models import *

if TYPE_CHECKING:
    from rm_api import API


def on_message(api: 'API', message):
    message = json.loads(message)
    message_event = message['message']['event']
    if message_event == 'SyncCompleted':
        api.spread_event(SyncCompleted(api, message))



def _listen(api: 'API'):
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://localhost:8765", on_message=lambda _, msg: on_message(api, msg))
    ws.run_forever()


def handle_notifications(api: 'API'):
    threading.Thread(target=_listen, args=(api,), daemon=True).start()
