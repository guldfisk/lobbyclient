from __future__ import annotations

import copy
import json
import threading
import typing as t
from abc import ABC, abstractmethod

from frozendict import frozendict
import websocket

from lobbyclient.utils import print_f


class Lobby(object):

    def __init__(self, name: str, users: t.MutableSet[str], owner: str, size: int):
        self._name = name
        self._users = users
        self._owner = owner
        self._size = size

    @property
    def name(self) -> str:
        return self._name

    @property
    def users(self) -> t.MutableSet[str]:
        return self._users

    @property
    def owner(self) -> str:
        return self._owner

    @property
    def size(self) -> int:
        return self._size

    @classmethod
    def deserialize(cls, remote: t.Any) -> Lobby:
        return cls(
            name = remote['name'],
            users = set(remote['users']),
            owner = remote['owner'],
            size = remote['size'],
        )


class LobbyClient(ABC):

    def __init__(
        self,
        url: str,
        token: str,
    ):
        self._token = token

        self._ws = websocket.WebSocketApp(
            url,
            on_message = self._on_message,
            on_error = self._on_error,
            on_close = self._on_close,
        )
        self._ws.on_open = self._on_open

        self._ws_thread = threading.Thread(target = self._ws.run_forever, daemon = True)

        self._lobbies_lock = threading.Lock()
        self._lobbies: t.MutableMapping[str, Lobby] = {}

        self._ws_thread.start()

    @abstractmethod
    def _lobbies_changed(
        self,
        created: t.Mapping[str, Lobby] = frozendict(),
        modified: t.Mapping[str, Lobby] = frozendict(),
        closed: t.AbstractSet[str] = frozenset(),
    ) -> None:
        pass

    def get_lobbies(self) -> t.Mapping[str, Lobby]:
        with self._lobbies_lock:
            return copy.copy(self._lobbies)

    def get_lobby(self, name: str) -> t.Optional[Lobby]:
        with self._lobbies_lock:
            return self._lobbies.get(name)

    def create_lobby(self, name: str) -> None:
        self._ws.send(
            json.dumps(
                {
                    'type': 'create',
                    'name': name,
                }
            )
        )

    def _on_error(self, error):
        print_f(error)

    def _on_close(self):
        print_f("### closed ###")

    def _on_open(self):
        print_f('opened')
        self._ws.send(
            json.dumps(
                {
                    'type': 'authentication',
                    'token': self._token,
                }
            )
        )

    def _on_message(self, message):
        message = json.loads(message)
        print_f(message)
        message_type = message['type']

        if message_type == 'all_lobbies':
            self._lobbies = {
                lobby['name']: Lobby.deserialize(lobby)
                for lobby in
                message['lobbies']
            }
            self._lobbies_changed(
                created = self._lobbies
            )

        elif message_type == 'lobby_created':
            lobby = Lobby.deserialize(message['lobby'])
            self._lobbies[lobby.name] = lobby
            self._lobbies_changed(
                created = {lobby.name: lobby}
            )

        elif message_type == 'lobby_update':
            lobby = Lobby.deserialize(message['lobby'])
            self._lobbies[lobby.name]._users = lobby.users
            self._lobbies_changed(
                modified = {lobby.name: lobby}
            )

        elif message_type == 'lobby_closed':
            try:
                del self._lobbies[message['name']]
            except KeyError:
                pass
            else:
                self._lobbies_changed(
                    closed = {message['name']},
                )

