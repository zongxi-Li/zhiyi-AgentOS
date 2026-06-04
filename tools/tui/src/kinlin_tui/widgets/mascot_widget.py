"""Mascot widget rendering the Yi Zai ASCII art sprite with mood and role color."""

from textual.widgets import Static
from textual.reactive import reactive
from kinlin_tui.mascot import MascotMood, get_mascot_text
from kinlin_tui.theme import RoleTheme, ROLE_COLORS


class MascotWidget(Static):
    """Renders the Yi Zai mascot with current mood and role color."""

    mood: MascotMood = reactive(MascotMood.IDLE)
    role: RoleTheme = reactive(RoleTheme.LAWYER)

    def on_mount(self) -> None:
        self.update(self.render())

    def watch_mood(self, _old: MascotMood, _new: MascotMood) -> None:
        self.update(self.render())

    def watch_role(self, _old: RoleTheme, _new: RoleTheme) -> None:
        self.update(self.render())

    def render(self) -> str:
        color = ROLE_COLORS.get(self.role, "#409EFF")
        return get_mascot_text(self.mood, color=color)
