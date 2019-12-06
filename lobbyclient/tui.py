from __future__ import annotations

import time
import typing as t
import sys
import threading

from asciimatics.widgets import Frame, ListBox, Layout, Divider, Text, Button, TextBox, Widget, MultiColumnListBox
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
from frozendict import frozendict

from lobbyclient.client import LobbyClient, Lobby
from lobbyclient.model import LobbyModel


# class ModelExpander(threading.Thread):
#
#     def __init__(self, model: LobbyModel):
#         super().__init__(daemon=True)
#         self._model = model
#         self._counter = 2
#
#     def run(self) -> None:
#         while True:
#             time.sleep(1)
#             self._model.lobbies.append(
#                 ('cooldt', self._counter)
#             )
#             self._model.updated()
#             self._counter += 1
from lobbyclient.utils import print_f


class LobbyClientModel(LobbyClient):

    def __init__(
        self,
        url: str,
        token: str,
        # lobbies_changed: t.Optional[t.Callable[[t.FrozenSet[str]], None]] = None,
    ):
        super().__init__(url, token)
        self._listeners: t.List[LobbiesView] = []
        # self._lobbies: t.FrozenSet[str] = frozenset()
        # self._lock = threading.Lock()

    def _lobbies_changed(
        self,
        created: t.Mapping[str, Lobby] = frozendict(),
        modified: t.Mapping[str, Lobby] = frozendict(),
        closed: t.AbstractSet[str] = frozenset(),
    ) -> None:
        print_f('updated')
        for listener in self._listeners:
            listener.on_model_updated()

    # def create_lobby(self, name: str) -> None:
    #     LobbyClient.create_lobby(self, name)

    # def _lobbies_changed(self, lobbies: t.FrozenSet[str]) -> None:
    #     print_f('lobbies changed')
    #     with self._lock:
    #         self._lobbies = lobbies
    #     self.updated()

    def listen(self, listener: LobbiesView) -> None:
        self._listeners.append(listener)

    def get_lobbies(self) -> t.List[t.Tuple[t.Tuple[str, str, str], str]]:
        with self._lobbies_lock:
            print_f('get lobbies', self._lobbies)
            return [
                (
                    (
                        lobby.name,
                        lobby.owner,
                        '{}/{}'.format(
                            str(len(lobby.users)),
                            str(lobby.size),
                        ),
                    ),
                    lobby.name,
                )
                for lobby in
                sorted(
                    self._lobbies.values(),
                    key = lambda l: l.name,
                )
            ]

    def _set_lobbies(self, lobbies: t.List[t.Tuple[str, int]]) -> None:
        raise NotImplemented()


class LobbiesView(Frame):

    def __init__(self, screen: Screen, model: LobbyClientModel):
        super().__init__(
            screen,
            screen.height * 2 // 3,
            screen.width * 2 // 3,
            on_load = self._on_model_updated,
            hover_focus = True,
            can_scroll = False,
            title = "Contact List",
        )
        self._model = model
        self._model.listen(self)

        self._list_view = MultiColumnListBox(
            Widget.FILL_FRAME,
            [10, 10, 10],
            model.get_lobbies(),
            name = "lobbies",
            add_scroll_bar = True,
            on_change = self._on_pick,
            # on_select=self._edit
        )
        # self._other_list_view = ListBox(
        #     Widget.FILL_FRAME,
        #     model.get_lobbies(),
        #     name = "lobbies",
        #     add_scroll_bar = True,
        #     on_change = self._on_pick,
        #     # on_select=self._edit
        # )

        # self._edit_button = Button("Edit", self._edit)
        # self._delete_button = Button("Delete", self._delete)

        self._layout = Layout([1], fill_frame = True)
        self.add_layout(self._layout)

        self._layout.add_widget(self._list_view)
        # self._layout.add_widget(self._other_list_view, 1)

        layout2 = Layout([1])
        self.add_layout(layout2)
        layout2.add_widget(Divider())

        layout3 = Layout([1, 1, 1, 1])
        self.add_layout(layout3)

        layout2.add_widget(Button("Create", self._create), 0)
        # layout2.add_widget(self._edit_button, 1)
        # layout2.add_widget(self._delete_button, 2)
        layout3.add_widget(Button("Quit", self._quit), 3)
        self.fix()
        self._on_pick()

    def _create(self):
        raise NextScene("Create Lobby")

    def _on_pick(self):
        pass
        # self._edit_button.disabled = self._list_view.value is None
        # self._delete_button.disabled = self._list_view.value is None

    def _on_model_updated(self):
        self._list_view.options = self._model.get_lobbies()

    def on_model_updated(self):
        self._list_view._options = self._model.get_lobbies()

        self._list_view.update(0)
        self._other_list_view.update(0)
        self.canvas.refresh()
        self._screen.refresh()

    @staticmethod
    def _quit():
        raise StopApplication("User pressed quit")


class CreateLobbyView(Frame):

    def __init__(self, screen: Screen, model: LobbyClientModel):
        super().__init__(
            screen,
            screen.height * 2 // 3,
            screen.width * 2 // 3,
            hover_focus = True,
            can_scroll = False,
            title = "Create lobby",
            reduce_cpu = True,
        )
        self._model = model

        layout = Layout([1], fill_frame = True)
        self.add_layout(layout)

        layout.add_widget(Text("Name:", "name"))

        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("OK", self._ok), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)

        self.fix()

    # def reset(self):
    #     # Do standard reset to clear out form, then populate with new data.
    #     super().reset()
    #     self.data = self._model.get_current_contact()

    def _ok(self):
        self.save()
        self._model.create_lobby(self.data['name'])
        raise NextScene("Lobbies")

    @staticmethod
    def _cancel():
        raise NextScene("Lobbies")
