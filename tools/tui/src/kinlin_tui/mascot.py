"""
AgentOS TUI mascot: "Yi Zai" (Go-stone sprite) rendered as ASCII art.

Moods control eyes and mouth: IDLE, THINKING, WORKING, HAPPY, ERROR, WAITING.
Each frame is 5 lines tall and 9 characters wide.
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
        "  .---.",
        " /     \\",
        "|  o o  |",
        " \\  w  /",
        "  '---'",
    ],
    MascotMood.THINKING: [
        "  .---.",
        " /     \\",
        "|  u u  |",
        " \\  ~  /",
        "  '---'",
    ],
    MascotMood.WORKING: [
        "  .---.",
        " /     \\",
        "|  * *  |",
        " \\  O  /",
        "  '---'",
    ],
    MascotMood.HAPPY: [
        "  .---.",
        " /     \\",
        "|  ^ ^  |",
        " \\  V  /",
        "  '---'",
    ],
    MascotMood.ERROR: [
        "  .---.",
        " /     \\",
        "|  x x  |",
        " \\  n  /",
        "  '---'",
    ],
    MascotMood.WAITING: [
        "  .---.",
        " /     \\",
        "|  . .  |",
        " \\  ?  /",
        "  '---'",
    ],
}

WELCOME_BANNER: list[str] = [
    "  .---.        ╔══════════════════════════╗",
    " /     \\       ║     Welcome to AgentOS    ║",
    "|  ^ ^  |      ║   Your AI Coding Agent    ║",
    " \\  V  /       ║   powered by Yi Zai [stone]║",
    "  '---'        ╚══════════════════════════╝",
    "",
    "    Ready to assist.  Type /help for commands.",
]


def get_mascot(mood: MascotMood) -> list[str]:
    """Return the 5-line ASCII frame for the given mood."""
    return MASCOT_FRAMES.get(mood, MASCOT_FRAMES[MascotMood.IDLE])


def get_mascot_text(mood: MascotMood, color: str = "white") -> str:
    """Return the 5-line ASCII frame joined by newlines, annotated with a
    Textual BBCode color tag when *color* is not the default ``"white"``."""
    frame = get_mascot(mood)
    text = "\n".join(frame)
    if color != "white":
        text = f"[{color}]{text}[/{color}]"
    return text
