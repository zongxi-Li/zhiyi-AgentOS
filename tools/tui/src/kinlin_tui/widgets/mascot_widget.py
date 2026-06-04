"""Mascot widget rendering the role-themed ASCII sprite with mood and colour."""

from textual.widgets import Static
from textual.reactive import reactive

from kinlin_tui.mascot import (
    MascotCharacter,
    MascotMood,
    get_mascot_text,
)
from kinlin_tui.theme import RoleTheme

# RoleTheme -> MascotCharacter mapping
_ROLE_TO_CHARACTER = {
    RoleTheme.LAWYER: MascotCharacter.LAWYER,
    RoleTheme.TEACHER: MascotCharacter.TEACHER,
    RoleTheme.PROGRAMMER: MascotCharacter.PROGRAMMER,
    RoleTheme.WRITER: MascotCharacter.WRITER,
}


class MascotWidget(Static):
    """Renders the role-appropriate mascot with the current mood.

    Reactive attributes
    -------------------
    mood : MascotMood
        Current facial expression (IDLE, THINKING, WORKING, HAPPY, ERROR, WAITING).
    role : RoleTheme
        Current agent role — changes the character and accent colour.
    """

    mood: MascotMood = reactive(MascotMood.IDLE, layout=True)
    role: RoleTheme = reactive(RoleTheme.LAWYER, layout=True)

    def watch_mood(self, _old: MascotMood, _new: MascotMood) -> None:
        self.refresh(layout=True)

    def watch_role(self, _old: RoleTheme, _new: RoleTheme) -> None:
        self.refresh(layout=True)

    def render(self) -> str:
        character = _ROLE_TO_CHARACTER.get(self.role, MascotCharacter.LAWYER)
        return get_mascot_text(mood=self.mood, character=character)
