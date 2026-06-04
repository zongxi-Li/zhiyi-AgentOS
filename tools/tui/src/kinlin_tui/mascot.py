"""
AgentOS TUI mascot: "Yi Zai", a soft terminal companion rendered as ASCII art.

The frames are intentionally plain ASCII so they render reliably in Windows
Terminal, cmd, PowerShell, and SSH sessions with different font settings.
"""

from enum import Enum


class MascotMood(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    HAPPY = "happy"
    ERROR = "error"
    WAITING = "waiting"


MASCOT_FRAMES: dict[MascotMood, list[str]] = {
    MascotMood.IDLE: [
        "    .-~~~-.    ",
        "  .'       '.  ",
        " /  o     o  \\ ",
        "|      v      |",
        "|   \\_____/   |",
        " \\           / ",
        "  '._     _.'  ",
        "     '---'     ",
    ],
    MascotMood.THINKING: [
        "    .-~~~-.    ",
        "  .'       '.  ",
        " /  u     u  \\ ",
        "|      ~      |",
        "|    . . .    |",
        " \\           / ",
        "  '._     _.'  ",
        "     '---'     ",
    ],
    MascotMood.WORKING: [
        "    .-~~~-.    ",
        "  .'       '.  ",
        " /  *     *  \\ ",
        "|      o      |",
        "|   /-----\\   |",
        " \\           / ",
        "  '._     _.'  ",
        "     '---'     ",
    ],
    MascotMood.HAPPY: [
        "    .-~~~-.    ",
        "  .'       '.  ",
        " /  ^     ^  \\ ",
        "|      v      |",
        "|   \\_____/   |",
        " \\           / ",
        "  '._     _.'  ",
        "     '---'     ",
    ],
    MascotMood.ERROR: [
        "    .-~~~-.    ",
        "  .'       '.  ",
        " /  >     <  \\ ",
        "|      _      |",
        "|    -----    |",
        " \\           / ",
        "  '._     _.'  ",
        "     '---'     ",
    ],
    MascotMood.WAITING: [
        "    .-~~~-.    ",
        "  .'       '.  ",
        " /  .     .  \\ ",
        "|      ?      |",
        "|    _____    |",
        " \\           / ",
        "  '._     _.'  ",
        "     '---'     ",
    ],
}

WELCOME_BANNER: list[str] = [
    "    .-~~~-.       +----------------------+",
    "  .'       '.     |  Welcome to AgentOS  |",
    " /  ^     ^  \\    |  Terminal Workbench  |",
    "|      v      |   |  Yi Zai is ready     |",
    "|   \\_____/   |   +----------------------+",
    " \\           / ",
    "  '._     _.'  ",
    "     '---'     ",
]


def get_mascot(mood: MascotMood) -> list[str]:
    """Return the ASCII frame for the given mood."""
    return MASCOT_FRAMES.get(mood, MASCOT_FRAMES[MascotMood.IDLE])


def get_mascot_text(mood: MascotMood, color: str = "white") -> str:
    """Return the frame joined by newlines, optionally wrapped in a color tag."""
    text = "\n".join(get_mascot(mood))
    if color != "white":
        text = f"[{color}]{text}[/{color}]"
    return text
