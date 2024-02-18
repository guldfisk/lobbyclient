from __future__ import annotations

import typing as t
from dataclasses import dataclass


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
        return isinstance(other, self.__class__) and self._username == other._username


@dataclass
class LobbyOptions(object):
    size: int
    minimum_size: int
    require_ready: bool
    unready_on_change: bool


@dataclass
class Lobby(object):
    name: str
    state: str
    lobby_options: LobbyOptions
    game_options: t.Mapping[str, t.Any]
    users: t.MutableMapping[str, User]
    owner: str
    game_type: str
    key: t.Optional[str]

    @classmethod
    def deserialize(cls, remote: t.Any) -> Lobby:
        return cls(
            name=remote["name"],
            state=remote["state"],
            lobby_options=LobbyOptions(**remote["lobby_options"]),
            game_options=remote["game_options"],
            users={
                user["username"]: User(
                    username=user["username"],
                    ready=user["ready"],
                )
                for user in remote["users"]
            },
            owner=remote["owner"],
            game_type=remote["game_type"],
            key=remote.get("key"),
        )
