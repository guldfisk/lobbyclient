from __future__ import annotations

import typing as t


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
        options: t.Any,
        users: t.MutableMapping[str, User],
        owner: str,
        size: int,
        key: t.Optional[str],
    ):
        self._name = name
        self._state = state
        self._options = options
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

    @property
    def options(self) -> t.Any:
        return self._options

    @options.setter
    def options(self, values) -> None:
        self._options = values

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
            options = remote['options'],
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
