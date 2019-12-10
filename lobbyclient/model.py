import typing as t

from abc import ABC, abstractmethod


class LobbyModel(ABC):

    @abstractmethod
    def create_lobby(self, name: str) -> None:
        pass

    @abstractmethod
    def listen(self, listener) -> None:
        pass
        # self._listeners.append(listener)

    @abstractmethod
    def updated(self) -> None:
        pass
        # for listener in self._listeners:
        #     listener.on_model_updated()

    @abstractmethod
    def get_lobbies(self) -> t.List[t.Tuple[str, int]]:
        pass
        # return self._lobbies

    @abstractmethod
    def _set_lobbies(self, lobbies: t.List[t.Tuple[str, int]]) -> None:
        pass
        # self._lobbies = lobbies
        # self.updated()

