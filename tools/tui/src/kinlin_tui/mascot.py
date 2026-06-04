"""
AgentOS TUI mascots — four role-themed ASCII companions with colour-filled bodies.

Characters
---------
- YI ZAI   (lawyer)    — Go-stone sprite, deep-blue body, blue-white eyes.
- ZHI BAO  (teacher)   — owl scholar, deep-purple body, golden eyes.
- JUAN JUAN (writer)   — open-book sprite, warm cream body, round glasses.
- DOU DOU  (programmer)— pixel sprite, terminal-black body, neon-cyan eyes.

Each character has 6 mood frames rendered with Rich/Textual BBCode colour tags
so they can be dropped directly into a ``RichLog`` or ``Static`` widget.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List

# ═══════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════


class MascotMood(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    HAPPY = "happy"
    ERROR = "error"
    WAITING = "waiting"


class MascotCharacter(str, Enum):
    LAWYER = "lawyer"
    TEACHER = "teacher"
    PROGRAMMER = "programmer"
    WRITER = "writer"


# ═══════════════════════════════════════════════════════════════════════════
# Colour palettes
# ═══════════════════════════════════════════════════════════════════════════

PALETTES: Dict[MascotCharacter, Dict[str, str]] = {
    MascotCharacter.LAWYER: {
        "outline": "#409EFF",
        "body": "#1a2744",
        "eye": "#c0caf5",
        "mouth": "#e6a23c",
        "cheek": "#ff6b9d",
        "icon": "#ffd700",
    },
    MascotCharacter.TEACHER: {
        "outline": "#9B59B6",
        "body": "#2d1b69",
        "eye": "#ffd700",
        "mouth": "#e6a23c",
        "feather": "#67c23a",
        "beak": "#e6a23c",
        "belly": "#c792ea",
        "gem": "#58a6ff",
        "icon": "#ffd700",
    },
    MascotCharacter.WRITER: {
        "outline": "#E6A23C",
        "body": "#fff3cd",
        "glasses": "#8B4513",
        "lens": "#ffffff",
        "eye": "#5D4037",
        "mouth": "#ff69b4",
        "page": "#d4a574",
        "spine": "#E6A23C",
        "spark": "#67c23a",
        "icon": "#ff69b4",
    },
    MascotCharacter.PROGRAMMER: {
        "outline": "#9B59B6",
        "body": "#0d1117",
        "eye": "#00ffff",
        "mouth": "#c792ea",
        "antenna": "#58a6ff",
        "hand": "#c792ea",
        "led_ok": "#67c23a",
        "led_warn": "#e6a23c",
        "led_err": "#f56c6c",
        "base": "#30363d",
        "icon": "#c792ea",
    },
}


def _c(color_key: str, pal: Dict[str, str]) -> str:
    """Shortcut: ``[bold <colour>]`` tag for a palette key."""
    return f"[bold {pal[color_key]}]"


def _cf(color_key: str, pal: Dict[str, str], text: str) -> str:
    """Wraps *text* in a bold colour tag, returns plain text if empty."""
    if not text:
        return text
    return f"[bold {pal[color_key]}]{text}[/]"


# ═══════════════════════════════════════════════════════════════════════════
# Frames — each is a list[str] with inline Rich/Textual colour markup.
# ═══════════════════════════════════════════════════════════════════════════

_F: Dict[MascotCharacter, Dict[MascotMood, List[str]]] = {}


# ── YI ZAI · Lawyer · Go-stone sprite ─────────────────────────────────────

_YI = MascotCharacter.LAWYER
_P = PALETTES[_YI]
_F[_YI] = {}

_F[_YI][MascotMood.IDLE] = [
    f"    {_c('outline',_P)}.-~~~-.[/]    ",
    f"  {_c('outline',_P)}.'{_c('body',_P)}       {_c('outline',_P)}'.[/]  ",
    f" {_c('outline',_P)}/{_c('body',_P)}  {_c('eye',_P)}o     o{_c('body',_P)}  {_c('outline',_P)}\\[/] ",
    f"{_c('outline',_P)}|{_c('body',_P)}      {_c('mouth',_P)}v{_c('body',_P)}      {_c('outline',_P)}|[/]",
    f"{_c('outline',_P)}|{_c('body',_P)}   {_c('outline',_P)}\\\\{_c('mouth',_P)}_____/{_c('outline',_P)}/[/]{_c('body',_P)}   {_c('outline',_P)}|[/]",
    f" {_c('outline',_P)}\\\\{_c('body',_P)}           {_c('outline',_P)}/[/] ",
    f"  {_c('outline',_P)}'._     _.'[/]  ",
    f"    {_c('outline',_P)}'---'[/]     ",
    f"     {_c('icon',_P)}balance-scale[/]     ",
]

_F[_YI][MascotMood.THINKING] = [
    f"    {_c('outline',_P)}.-~~~-.[/]    ",
    f"  {_c('outline',_P)}.'{_c('body',_P)}       {_c('outline',_P)}'.[/]  ",
    f" {_c('outline',_P)}/{_c('body',_P)}  {_c('eye',_P)}u     u{_c('body',_P)}  {_c('outline',_P)}\\[/] ",
    f"{_c('outline',_P)}|{_c('body',_P)}      {_c('mouth',_P)}~{_c('body',_P)}      {_c('outline',_P)}|[/]",
    f"{_c('outline',_P)}|{_c('body',_P)}    {_c('cheek',_P)}. . .{_c('body',_P)}    {_c('outline',_P)}|[/]",
    f" {_c('outline',_P)}\\\\{_c('body',_P)}           {_c('outline',_P)}/[/] ",
    f"  {_c('outline',_P)}'._     _.'[/]  ",
    f"    {_c('outline',_P)}'---'[/]     ",
    f"     {_c('icon',_P)}scroll[/]     ",
]

_F[_YI][MascotMood.WORKING] = [
    f"    {_c('outline',_P)}.-~~~-.[/]    ",
    f"  {_c('outline',_P)}.'{_c('body',_P)}       {_c('outline',_P)}'.[/]  ",
    f" {_c('outline',_P)}/{_c('body',_P)}  {_c('eye',_P)}*     *{_c('body',_P)}  {_c('outline',_P)}\\[/] ",
    f"{_c('outline',_P)}|{_c('body',_P)}      {_c('mouth',_P)}o{_c('body',_P)}      {_c('outline',_P)}|[/]",
    f"{_c('outline',_P)}|{_c('body',_P)}   {_c('outline',_P)}/-----\\[/]{_c('body',_P)}   {_c('outline',_P)}|[/]",
    f" {_c('outline',_P)}\\\\{_c('body',_P)}           {_c('outline',_P)}/[/] ",
    f"  {_c('outline',_P)}'._     _.'[/]  ",
    f"    {_c('outline',_P)}'---'[/]     ",
    f"     {_c('icon',_P)}bolt[/]     ",
]

_F[_YI][MascotMood.HAPPY] = [
    f"    {_c('outline',_P)}.-~~~-.[/]    ",
    f"  {_c('outline',_P)}.'{_c('body',_P)}       {_c('outline',_P)}'.[/]  ",
    f" {_c('outline',_P)}/{_c('body',_P)}  {_c('eye',_P)}^     ^{_c('body',_P)}  {_c('outline',_P)}\\[/] ",
    f"{_c('outline',_P)}|{_c('body',_P)}      {_c('mouth',_P)}v{_c('body',_P)}      {_c('outline',_P)}|[/]",
    f"{_c('outline',_P)}|{_c('body',_P)}   {_c('outline',_P)}\\\\{_c('mouth',_P)}_____/{_c('outline',_P)}/[/]{_c('body',_P)}   {_c('outline',_P)}|[/]",
    f" {_c('outline',_P)}\\\\{_c('body',_P)}           {_c('outline',_P)}/[/] ",
    f"  {_c('outline',_P)}'._     _.'[/]  ",
    f"    {_c('outline',_P)}'---'[/]     ",
    f"     {_c('icon',_P)}star[/]     ",
]

_F[_YI][MascotMood.ERROR] = [
    f"    {_c('outline',_P)}.-~~~-.[/]    ",
    f"  {_c('outline',_P)}.'{_c('body',_P)}       {_c('outline',_P)}'.[/]  ",
    f" {_c('outline',_P)}/{_c('body',_P)}  {_c('eye',_P)}>     <{_c('body',_P)}  {_c('outline',_P)}\\[/] ",
    f"{_c('outline',_P)}|{_c('body',_P)}      {_c('mouth',_P)}-{_c('body',_P)}      {_c('outline',_P)}|[/]",
    f"{_c('outline',_P)}|{_c('body',_P)}    {_c('cheek',_P)}-----{_c('body',_P)}    {_c('outline',_P)}|[/]",
    f" {_c('outline',_P)}\\\\{_c('body',_P)}           {_c('outline',_P)}/[/] ",
    f"  {_c('outline',_P)}'._     _.'[/]  ",
    f"    {_c('outline',_P)}'---'[/]     ",
    f"     {_c('icon',_P)}cross-mark[/]     ",
]

_F[_YI][MascotMood.WAITING] = [
    f"    {_c('outline',_P)}.-~~~-.[/]    ",
    f"  {_c('outline',_P)}.'{_c('body',_P)}       {_c('outline',_P)}'.[/]  ",
    f" {_c('outline',_P)}/{_c('body',_P)}  {_c('eye',_P)}.     .{_c('body',_P)}  {_c('outline',_P)}\\[/] ",
    f"{_c('outline',_P)}|{_c('body',_P)}      {_c('mouth',_P)}?{_c('body',_P)}      {_c('outline',_P)}|[/]",
    f"{_c('outline',_P)}|{_c('body',_P)}    {_c('cheek',_P)}_____[/]{_c('body',_P)}    {_c('outline',_P)}|[/]",
    f" {_c('outline',_P)}\\\\{_c('body',_P)}           {_c('outline',_P)}/[/] ",
    f"  {_c('outline',_P)}'._     _.'[/]  ",
    f"    {_c('outline',_P)}'---'[/]     ",
    f"     {_c('icon',_P)}hourglass[/]     ",
]


# ── ZHI BAO · Teacher · Owl scholar ───────────────────────────────────────

_ZB = MascotCharacter.TEACHER
_P = PALETTES[_ZB]
_F[_ZB] = {}

_F[_ZB][MascotMood.IDLE] = [
    f"     {_c('outline',_P)}.-.-.{_c('body',_P)}.{_c('outline',_P)}.-.-.[/]     ",
    f"   {_c('outline',_P)}.'{_c('body',_P)} {_c('eye',_P)}o     o{_c('body',_P)} {_c('outline',_P)}'.[/]   ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('gem',_P)}diamond-2{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('mouth',_P)}------{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"   {_c('outline',_P)}\\\\{_c('belly',_P)}_________{_c('outline',_P)}/[/]   ",
    f"    {_c('outline',_P)}||{_c('feather',_P)}     {_c('outline',_P)}||[/]    ",
    f"    {_c('beak',_P)}__{_c('outline',_P)}||{_c('beak',_P)}_____||{_c('outline',_P)}[/]    ",
    f"        {_c('beak',_P)}~~~~~[/]        ",
    f"       {_c('icon',_P)}books[/]       ",
]

_F[_ZB][MascotMood.THINKING] = [
    f"     {_c('outline',_P)}.-.-.{_c('body',_P)}.{_c('outline',_P)}.-.-.[/]     ",
    f"   {_c('outline',_P)}.'{_c('body',_P)} {_c('eye',_P)}u     u{_c('body',_P)} {_c('outline',_P)}'.[/]   ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('gem',_P)}diamond-2{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('mouth',_P)}......{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"   {_c('outline',_P)}\\\\{_c('belly',_P)}_________>{_c('outline',_P)}/[/]   ",
    f"    {_c('outline',_P)}||{_c('feather',_P)}     {_c('outline',_P)}||[/]    ",
    f"    {_c('beak',_P)}__{_c('outline',_P)}||{_c('beak',_P)}_____||{_c('outline',_P)}[/]    ",
    f"        {_c('beak',_P)}~~~~~[/]        ",
    f"       {_c('icon',_P)}thinking-face[/]       ",
]

_F[_ZB][MascotMood.WORKING] = [
    f"     {_c('outline',_P)}.-.-.{_c('body',_P)}.{_c('outline',_P)}.-.-.[/]     ",
    f"   {_c('outline',_P)}.'{_c('body',_P)} {_c('eye',_P)}*     *{_c('body',_P)} {_c('outline',_P)}'.[/]   ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('gem',_P)}diamond-2{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('mouth',_P)}o-o-o-o{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"   {_c('outline',_P)}\\\\{_c('belly',_P)}_________>{_c('outline',_P)}/[/]   ",
    f"    {_c('outline',_P)}||{_c('feather',_P)}  ||  {_c('outline',_P)}||[/]    ",
    f"    {_c('beak',_P)}__{_c('outline',_P)}||{_c('beak',_P)}_____||{_c('outline',_P)}[/]    ",
    f"        {_c('beak',_P)}~~~~~[/]        ",
    f"       {_c('icon',_P)}graduation-cap[/]       ",
]

_F[_ZB][MascotMood.HAPPY] = [
    f"     {_c('outline',_P)}.-.-.{_c('body',_P)}.{_c('outline',_P)}.-.-.[/]     ",
    f"   {_c('outline',_P)}.'{_c('body',_P)} {_c('eye',_P)}^     ^{_c('body',_P)} {_c('outline',_P)}'.[/]   ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('gem',_P)}diamond-2{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('mouth',_P)}v--v--v{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"   {_c('outline',_P)}\\\\{_c('belly',_P)}_________>{_c('outline',_P)}/[/]   ",
    f"    {_c('outline',_P)}||{_c('feather',_P)}  ^^  {_c('outline',_P)}||[/]    ",
    f"    {_c('beak',_P)}__{_c('outline',_P)}||{_c('beak',_P)}_____||{_c('outline',_P)}[/]    ",
    f"        {_c('beak',_P)}~~~~~[/]        ",
    f"       {_c('icon',_P)}star-struck[/]       ",
]

_F[_ZB][MascotMood.ERROR] = [
    f"     {_c('outline',_P)}.-.-.{_c('body',_P)}.{_c('outline',_P)}.-.-.[/]     ",
    f"   {_c('outline',_P)}.'{_c('body',_P)} {_c('eye',_P)}>     <{_c('body',_P)} {_c('outline',_P)}'.[/]   ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('gem',_P)}diamond-2{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('mouth',_P)}-..-..-{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"   {_c('outline',_P)}\\\\{_c('belly',_P)}_________>{_c('outline',_P)}/[/]   ",
    f"    {_c('outline',_P)}||{_c('feather',_P)}  xx  {_c('outline',_P)}||[/]    ",
    f"    {_c('beak',_P)}__{_c('outline',_P)}||{_c('beak',_P)}_____||{_c('outline',_P)}[/]    ",
    f"        {_c('beak',_P)}~~~~~[/]        ",
    f"       {_c('icon',_P)}no-entry[/]       ",
]

_F[_ZB][MascotMood.WAITING] = [
    f"     {_c('outline',_P)}.-.-.{_c('body',_P)}.{_c('outline',_P)}.-.-.[/]     ",
    f"   {_c('outline',_P)}.'{_c('body',_P)} {_c('eye',_P)}.     .{_c('body',_P)} {_c('outline',_P)}'.[/]   ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('gem',_P)}diamond-2{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('mouth',_P)}?--?--?{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"   {_c('outline',_P)}\\\\{_c('belly',_P)}_________>{_c('outline',_P)}/[/]   ",
    f"    {_c('outline',_P)}||{_c('feather',_P)}  ??  {_c('outline',_P)}||[/]    ",
    f"    {_c('beak',_P)}__{_c('outline',_P)}||{_c('beak',_P)}_____||{_c('outline',_P)}[/]    ",
    f"        {_c('beak',_P)}~~~~~[/]        ",
    f"       {_c('icon',_P)}hourglass[/]       ",
]


# ── JUAN JUAN · Writer · Open-book sprite ─────────────────────────────────

_JJ = MascotCharacter.WRITER
_P = PALETTES[_JJ]
_F[_JJ] = {}

_F[_JJ][MascotMood.IDLE] = [
    f"  {_c('spine',_P)}.===============.[/]  ",
    f"  {_c('spine',_P)}||{_c('page',_P)}~~~~~~~~~~~~~{_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('body',_P)} {_c('glasses',_P)}.-{_c('lens',_P)} o   o {_c('glasses',_P)}-.[/]{_c('body',_P)} {_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('body',_P)} {_c('glasses',_P)}| {_c('lens',_P)}   {_c('mouth',_P)}v{_c('lens',_P)}    {_c('glasses',_P)}|[/]{_c('body',_P)} {_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('body',_P)} {_c('glasses',_P)}'-{_c('lens',_P)}       {_c('glasses',_P)}-'[/]{_c('body',_P)} {_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('page',_P)}_____________>{_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}'==============='[/]  ",
    f"      {_c('mouth',_P)}~~~~~~~~[/]      ",
    f"      {_c('icon',_P)}open-book[/]      ",
]

_F[_JJ][MascotMood.THINKING] = [
    f"  {_c('spine',_P)}.===============.[/]  ",
    f"  {_c('spine',_P)}||{_c('page',_P)}~~~~~~~~~~~~~{_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('body',_P)} {_c('glasses',_P)}.-{_c('lens',_P)} u   u {_c('glasses',_P)}-.[/]{_c('body',_P)} {_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('body',_P)} {_c('glasses',_P)}| {_c('lens',_P)}   {_c('mouth',_P)}~{_c('lens',_P)}    {_c('glasses',_P)}|[/]{_c('body',_P)} {_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('body',_P)} {_c('glasses',_P)}'-{_c('lens',_P)}       {_c('glasses',_P)}-'[/]{_c('body',_P)} {_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('page',_P)} {_c('spark',_P)}*{_c('page',_P)} {_c('spark',_P)}*{_c('page',_P)} {_c('spark',_P)}*{_c('page',_P)} {_c('spark',_P)}*{_c('page',_P)} {_c('spark',_P)}*[/]{_c('page',_P)} {_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}'==============='[/]  ",
    f"      {_c('mouth',_P)}~~~~~~~~[/]      ",
    f"      {_c('icon',_P)}thought-balloon[/]      ",
]

_F[_JJ][MascotMood.WORKING] = [
    f"  {_c('spine',_P)}.===============.[/]  ",
    f"  {_c('spine',_P)}||{_c('page',_P)}~~~~~~~~~~~~~{_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('body',_P)} {_c('glasses',_P)}.-{_c('lens',_P)} *   * {_c('glasses',_P)}-.[/]{_c('body',_P)} {_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('body',_P)} {_c('glasses',_P)}| {_c('lens',_P)}   {_c('mouth',_P)}O{_c('lens',_P)}    {_c('glasses',_P)}|[/]{_c('body',_P)} {_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('body',_P)} {_c('glasses',_P)}'-{_c('lens',_P)}       {_c('glasses',_P)}-'[/]{_c('body',_P)} {_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('page',_P)} {_c('spark',_P)}*  *  *  *  *[/]{_c('page',_P)} {_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}'==============='[/]  ",
    f"      {_c('mouth',_P)}~~~~~~~~[/]      ",
    f"      {_c('icon',_P)}sparkles[/]      ",
]

_F[_JJ][MascotMood.HAPPY] = [
    f"  {_c('spine',_P)}.===============.[/]  ",
    f"  {_c('spine',_P)}||{_c('page',_P)}~~~~~~~~~~~~~{_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('body',_P)} {_c('glasses',_P)}.-{_c('lens',_P)} ^   ^ {_c('glasses',_P)}-.[/]{_c('body',_P)} {_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('body',_P)} {_c('glasses',_P)}| {_c('lens',_P)}   {_c('mouth',_P)}V{_c('lens',_P)}    {_c('glasses',_P)}|[/]{_c('body',_P)} {_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('body',_P)} {_c('glasses',_P)}'-{_c('lens',_P)}       {_c('glasses',_P)}-'[/]{_c('body',_P)} {_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('page',_P)}~~~~~~~~~~~~~{_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}'==============='[/]  ",
    f"      {_c('mouth',_P)}~~~~~~~~[/]      ",
    f"      {_c('icon',_P)}party-popper[/]      ",
]

_F[_JJ][MascotMood.ERROR] = [
    f"  {_c('spine',_P)}.===============.[/]  ",
    f"  {_c('spine',_P)}||{_c('page',_P)}~~~~~~~~~~~~~{_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('body',_P)} {_c('glasses',_P)}.-{_c('lens',_P)} x   x {_c('glasses',_P)}-.[/]{_c('body',_P)} {_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('body',_P)} {_c('glasses',_P)}| {_c('lens',_P)}   {_c('mouth',_P)}n{_c('lens',_P)}    {_c('glasses',_P)}|[/]{_c('body',_P)} {_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('body',_P)} {_c('glasses',_P)}'-{_c('lens',_P)}       {_c('glasses',_P)}-'[/]{_c('body',_P)} {_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('page',_P)}~~~~~~~~~~~~~{_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}'==============='[/]  ",
    f"      {_c('mouth',_P)}~~~~~~~~[/]      ",
    f"      {_c('icon',_P)}broken-heart[/]      ",
]

_F[_JJ][MascotMood.WAITING] = [
    f"  {_c('spine',_P)}.===============.[/]  ",
    f"  {_c('spine',_P)}||{_c('page',_P)}~~~~~~~~~~~~~{_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('body',_P)} {_c('glasses',_P)}.-{_c('lens',_P)} .   . {_c('glasses',_P)}-.[/]{_c('body',_P)} {_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('body',_P)} {_c('glasses',_P)}| {_c('lens',_P)}   {_c('mouth',_P)}?{_c('lens',_P)}    {_c('glasses',_P)}|[/]{_c('body',_P)} {_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('body',_P)} {_c('glasses',_P)}'-{_c('lens',_P)}       {_c('glasses',_P)}-'[/]{_c('body',_P)} {_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}||{_c('page',_P)}~~~~~~~~~~~~~{_c('spine',_P)}||[/]  ",
    f"  {_c('spine',_P)}'==============='[/]  ",
    f"      {_c('mouth',_P)}~~~~~~~~[/]      ",
    f"      {_c('icon',_P)}hourglass[/]      ",
]


# ── DOU DOU · Programmer · Pixel sprite ────────────────────────────────────

_DD = MascotCharacter.PROGRAMMER
_P = PALETTES[_DD]
_F[_DD] = {}

_F[_DD][MascotMood.IDLE] = [
    f"     {_c('antenna',_P)}_|_[/]     ",
    f"   {_c('outline',_P)}.-------.[/]   ",
    f"  {_c('outline',_P)}|{_c('body',_P)} {_c('eye',_P)}o     o{_c('body',_P)} {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('led_ok',_P)}diamond[/]{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('mouth',_P)}------{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)} {_c('hand',_P)}__{_c('body',_P)} {_c('hand',_P)}__{_c('body',_P)} {_c('outline',_P)}|[/]  ",
    f"   {_c('outline',_P)}'-------'[/]   ",
    f"    {_c('base',_P)}||     ||[/]    ",
    f"    {_c('icon',_P)}coffee[/]    ",
]

_F[_DD][MascotMood.THINKING] = [
    f"     {_c('antenna',_P)}_|_[/]     ",
    f"   {_c('outline',_P)}.-------.[/]   ",
    f"  {_c('outline',_P)}|{_c('body',_P)} {_c('eye',_P)}u     u{_c('body',_P)} {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('led_warn',_P)}diamond[/]{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('mouth',_P)}......{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)} {_c('hand',_P)}__{_c('body',_P)} {_c('hand',_P)}__{_c('body',_P)} {_c('outline',_P)}|[/]  ",
    f"   {_c('outline',_P)}'-------'[/]   ",
    f"    {_c('base',_P)}||     ||[/]    ",
    f"    {_c('icon',_P)}electric-light-bulb[/]    ",
]

_F[_DD][MascotMood.WORKING] = [
    f"     {_c('antenna',_P)}_|_[/]     ",
    f"   {_c('outline',_P)}.-------.[/]   ",
    f"  {_c('outline',_P)}|{_c('body',_P)} {_c('eye',_P)}*     *{_c('body',_P)} {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('led_warn',_P)}diamond[/]{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('mouth',_P)}o-o-o-o{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)} {_c('hand',_P)}/\\{_c('body',_P)} {_c('hand',_P)}/\\{_c('body',_P)} {_c('outline',_P)}|[/]  ",
    f"   {_c('outline',_P)}'-------'[/]   ",
    f"    {_c('base',_P)}||     ||[/]    ",
    f"    {_c('icon',_P)}gear[/]    ",
]

_F[_DD][MascotMood.HAPPY] = [
    f"     {_c('antenna',_P)}_|_[/]     ",
    f"   {_c('outline',_P)}.-------.[/]   ",
    f"  {_c('outline',_P)}|{_c('body',_P)} {_c('eye',_P)}^     ^{_c('body',_P)} {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('led_ok',_P)}diamond[/]{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('mouth',_P)}v--v--v{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)} {_c('hand',_P)}^^{_c('body',_P)} {_c('hand',_P)}^^{_c('body',_P)} {_c('outline',_P)}|[/]  ",
    f"   {_c('outline',_P)}'-------'[/]   ",
    f"    {_c('base',_P)}||     ||[/]    ",
    f"    {_c('icon',_P)}check-mark-button[/]    ",
]

_F[_DD][MascotMood.ERROR] = [
    f"     {_c('antenna',_P)}_|_[/]     ",
    f"   {_c('outline',_P)}.-------.[/]   ",
    f"  {_c('outline',_P)}|{_c('body',_P)} {_c('eye',_P)}>     <{_c('body',_P)} {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('led_err',_P)}diamond[/]{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('mouth',_P)}------{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)} {_c('hand',_P)}xx{_c('body',_P)} {_c('hand',_P)}xx{_c('body',_P)} {_c('outline',_P)}|[/]  ",
    f"   {_c('outline',_P)}'-------'[/]   ",
    f"    {_c('base',_P)}||     ||[/]    ",
    f"    {_c('icon',_P)}collision[/]    ",
]

_F[_DD][MascotMood.WAITING] = [
    f"     {_c('antenna',_P)}_|_[/]     ",
    f"   {_c('outline',_P)}.-------.[/]   ",
    f"  {_c('outline',_P)}|{_c('body',_P)} {_c('eye',_P)}.     .{_c('body',_P)} {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('led_warn',_P)}diamond[/]{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)}  {_c('mouth',_P)}???{_c('body',_P)}  {_c('outline',_P)}|[/]  ",
    f"  {_c('outline',_P)}|{_c('body',_P)} {_c('hand',_P)}__{_c('body',_P)} {_c('hand',_P)}__{_c('body',_P)} {_c('outline',_P)}|[/]  ",
    f"   {_c('outline',_P)}'-------'[/]   ",
    f"    {_c('base',_P)}||     ||[/]    ",
    f"    {_c('icon',_P)}magnifying-glass-tilted-left[/]    ",
]


# ═══════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════

CHARACTER_NAMES: Dict[MascotCharacter, str] = {
    MascotCharacter.LAWYER: "Yi Zai",
    MascotCharacter.TEACHER: "Zhi Bao",
    MascotCharacter.WRITER: "Juan Juan",
    MascotCharacter.PROGRAMMER: "Dou Dou",
}

WELCOME_BANNER: List[str] = [
    "  .---.        +------------------------+",
    " /     \\       |  Welcome to AgentOS    |",
    "|  ^ ^  |      |  Terminal Workbench    |",
    " \\  V  /       |  zhiyi os --help       |",
    "  '---'        +------------------------+",
    "",
    "    Ready.  Type a message or press F2 to switch roles.",
]


def get_mascot(
    mood: MascotMood = MascotMood.IDLE,
    character: MascotCharacter = MascotCharacter.LAWYER,
) -> List[str]:
    """Return the Rich-markup frame lines for *mood* and *character*."""
    frames = _F.get(character, _F[MascotCharacter.LAWYER])
    return frames.get(mood, frames[MascotMood.IDLE])


def get_mascot_text(
    mood: MascotMood = MascotMood.IDLE,
    character: MascotCharacter = MascotCharacter.LAWYER,
) -> str:
    """Return the full mascot frame as a newline-joined Rich-markup string."""
    return "\n".join(get_mascot(mood, character))
