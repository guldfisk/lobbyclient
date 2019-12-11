from __future__ import annotations

import copy
import json
import threading
import typing as t
from abc import ABC, abstractmethod

from frozendict import frozendict
import websocket

from lobbyclient.utils import print_f


class User(object):

    def __init__(self, username: str, ready: bool):
        self._username = username
        self._ready = ready

    @property
    def username(self) -> str:
        return self._username

    @property
    def ready(self) -> bool:
        return self._ready

    def __hash__(self) -> int:
        return hash(self._username)

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._username == other._username
        )


class Lobby(object):

    def __init__(
        self,
        name: str,
        state: str,
        users: t.MutableMapping[str, User],
        owner: str,
        size: int,
        key: t.Optional[str],
    ):
        self._name = name
        self._state = state
        self._users = users
        self._owner = owner
        self._size = size
        self._key = key

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> str:
        return self._state

    @state.setter
    def state(self, value: bool) -> None:
        self._state = value

    @property
    def users(self) -> t.MutableMapping[str, User]:
        return self._users

    @users.setter
    def users(self, value: t.MutableSet[User]) -> None:
        self._users = value

    @property
    def owner(self) -> str:
        return self._owner

    @property
    def size(self) -> int:
        return self._size

    @property
    def key(self) -> t.Optional[str]:
        return self._key

    @key.setter
    def key(self, value: str) -> None:
        self._key = value

    @classmethod
    def deserialize(cls, remote: t.Any) -> Lobby:
        return cls(
            name = remote['name'],
            state = remote['state'],
            users = {
                user['username']: User(
                    username = user['username'],
                    ready = user['ready'],
                )
                for user in
                remote['users']
            },
            owner = remote['owner'],
            size = remote['size'],
            key = remote.get('key'),
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

    @abstractmethod
    def _game_started(self, lobby: Lobby, key: str) -> None:
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

    def leave_lobby(self, name: str) -> None:
        self._ws.send(
            json.dumps(
                {
                    'type': 'leave',
                    'name': name,
                }
            )
        )

    def join_lobby(self, name: str) -> None:
        self._ws.send(
            json.dumps(
                {
                    'type': 'join',
                    'name': name,
                }
            )
        )

    def set_ready(self, name: str, ready: bool):
        self._ws.send(
            json.dumps(
                {
                    'type': 'ready',
                    'name': name,
                    'state': ready,
                }
            )
        )

    def start_game(self, name: str):
        self._ws.send(
            json.dumps(
                {
                    'type': 'start',
                    'name': name,
                }
            )
        )

    def close(self):
        self._ws.close()

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

        with self._lobbies_lock:
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
                old_lobby = self._lobbies[lobby.name]
                old_lobby.users = lobby.users
                old_lobby.state = lobby.state
                self._lobbies_changed(
                    modified = {lobby.name: old_lobby}
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

            elif message_type == 'game_started':
                lobby = Lobby.deserialize(message['lobby'])
                old_lobby = self._lobbies[lobby.name]
                old_lobby.key = message['key']
                self._lobbies_changed(
                    modified = {lobby.name: old_lobby}
                )
                self._game_started(old_lobby, message['key'])
