from __future__ import annotations

import copy
import json
import logging
import ssl
import threading
import typing as t
from abc import ABC, abstractmethod

from frozendict import frozendict
import websocket

from lobbyclient.model import Lobby, LobbyOptions


class LobbyClient(ABC):

    def __init__(
        self,
        url: str,
        token: str,
        *,
        verify_ssl: bool = True,
    ):
        self._token = token

        self._ws = websocket.WebSocketApp(
            url,
            on_message = self._on_message,
            on_error = self._on_error,
            on_close = self._on_close,
        )
        self._ws.on_open = self._on_open

        self._ws_thread = threading.Thread(
            target = self._ws.run_forever,
            daemon = True,
            kwargs = None if verify_ssl else {'sslopt': {'cert_reqs': ssl.CERT_NONE}},
        )

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

    def create_lobby(
        self, name: str,
        game_type: str,
        lobby_options: LobbyOptions,
        game_options: t.Mapping[str, t.Any],
    ) -> None:
        self._ws.send(
            json.dumps(
                {
                    'type': 'create',
                    'name': name,
                    'game_type': game_type,
                    'lobby_options': lobby_options.__dict__,
                    'game_options': game_options,
                }
            )
        )

    def set_game_type(self, name: str, game_type: str, options: t.Mapping[str, t.Any]) -> None:
        self._ws.send(
            json.dumps(
                {
                    'type': 'game_type',
                    'name': name,
                    'game_type': game_type,
                    'options': options,
                }
            )
        )

    def set_options(self, name: str, options: t.Mapping[str, t.Any]) -> None:
        self._ws.send(
            json.dumps(
                {
                    'type': 'options',
                    'name': name,
                    'options': options,
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

    def start_game(self, name: str) -> None:
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
        logging.info(f'socket error: {error}')

    def _on_client_error(self, message: t.Mapping[str, t.Any]) -> None:
        pass

    def _on_close(self):
        logging.info('socket closed')

    def _on_open(self):
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
        logging.info(f'message {message}')
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
                old_lobby.game_options = lobby.game_options
                old_lobby.game_type = lobby.game_type
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
                old_lobby.state = lobby.state
                self._lobbies_changed(
                    modified = {lobby.name: old_lobby}
                )
                self._game_started(old_lobby, message['key'])

            elif message_type == 'error':
                self._on_client_error(message)
