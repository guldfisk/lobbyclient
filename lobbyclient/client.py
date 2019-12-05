from __future__ import annotations

import typing as t
from abc import ABC

import requests as r
import socket
import csv
import json
import os
import time
import csv
import re
import threading

from websocket import create_connection
import websocket


class LobbyClient(ABC):

    def __init__(
        self,
        url: str,
        lobbies_changed: t.Optional[t.Callable[[t.FrozenSet[str]], None]] = None,
    ):
        self._lobbies_changed = (lambda _: None) if lobbies_changed is None else lobbies_changed

        self._ws = websocket.WebSocketApp(
            url,
            on_message = self._on_message,
            on_error = self._on_error,
            on_close = self._on_close,
        )
        self._ws.on_open = self.on_open
        self._ws.run_forever()

        self._lobbies_lock = threading.Lock()
        self._lobbies: t.FrozenSet[str] = frozenset()

    def _on_error(self, error):
        print(error)

    def _on_close(self):
        print("### closed ###")

    def on_open(self):
        pass
        # self._ws.send(
        #     json.dumps(
        #         {
        #             'type': 'authentication',
        #             'token': 'cb14f2cb8f73ea356d0cb82e04f4f4219a3bb580b7582b4e23427637257a973f',
        #         }
        #     )
        # )

    def _on_message(self, message):
        message = json.loads(message)
        print(message)
        message_type = message['type']

        if message_type == 'lobby_update':
            self._lobbies = frozenset(message['lobbies'])
            self._lobbies_changed(self._lobbies)
