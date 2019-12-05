from __future__ import annotations

import time
import typing as t
import sys
import threading

from asciimatics.widgets import Frame, ListBox, Layout, Divider, Text, Button, TextBox, Widget, MultiColumnListBox
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication

from lobbyclient.client import LobbyClient
from lobbyclient.model import LobbyModel


class ModelExpander(threading.Thread):

    def __init__(self, model: LobbyModel):
        super().__init__(daemon=True)
        self._model = model
        self._counter = 2

    def run(self) -> None:
        while True:
            time.sleep(1)
            self._model.lobbies.append(
                ('cooldt', self._counter)
            )
            self._model.updated()
            self._counter += 1


class LobbyClientModel(LobbyModel, LobbyClient):

    def listen(self, listener) -> None:
        pass

    def updated(self) -> None:
        pass

    def _get_lobbies(self) -> t.List[t.Tuple[str, int]]:
        pass

    def set_lobbies(self, lobbies: t.List[t.Tuple[str, int]]) -> None:
        pass


class LobbiesView(Frame):

    def __init__(self, screen: Screen, model: LobbyModel):
        super().__init__(
            screen,
            screen.height // 2,
            screen.width // 2,
            on_load=self._on_model_updated,
            hover_focus=True,
            can_scroll=False,
            title="Contact List",
        )
        # Save off the model that accesses the contacts database.
        self._model = model
        self._model.listen(self)

        # Create the form for displaying the list of contacts.
        self._list_view = ListBox(
            Widget.FILL_FRAME,
            model.lobbies,
            name="lobbies",
            add_scroll_bar=True,
            on_change=self._on_pick,
            # on_select=self._edit
        )
        self._other_list_view = ListBox(
            Widget.FILL_FRAME,
            model.lobbies,
            name="lobbies",
            add_scroll_bar=True,
            on_change=self._on_pick,
            # on_select=self._edit
        )

        # self._edit_button = Button("Edit", self._edit)
        # self._delete_button = Button("Delete", self._delete)

        self._layout = Layout([1, 1], fill_frame=True)
        self.add_layout(self._layout)

        self._layout.add_widget(self._list_view)
        self._layout.add_widget(self._other_list_view, 1)

        layout2 = Layout([1])
        self.add_layout(layout2)
        layout2.add_widget(Divider())

        layout3 = Layout([1, 1, 1, 1])
        self.add_layout(layout3)

        # layout2.add_widget(Button("Add", self._add), 0)
        # layout2.add_widget(self._edit_button, 1)
        # layout2.add_widget(self._delete_button, 2)
        layout3.add_widget(Button("Quit", self._quit), 3)
        self.fix()
        self._on_pick()

    def _on_pick(self):
        pass
        # self._edit_button.disabled = self._list_view.value is None
        # self._delete_button.disabled = self._list_view.value is None

    def _on_model_updated(self):
        self._list_view.options = self._model.lobbies

    def on_model_updated(self):
        self._list_view._options = self._model.lobbies

        self._list_view.update(0)
        self._other_list_view.update(0)
        self.canvas.refresh()
        self._screen.refresh()

        # self._list_view.update(0)
        # self._other_list_view.update(0)
        # self.canvas.refresh()
        # self._screen.refresh()

    @staticmethod
    def _quit():
        raise StopApplication("User pressed quit")

