from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

from .ui import console, print_help

if TYPE_CHECKING:
    from .session import ChatSession


@dataclass
class Command:
    name: str
    aliases: list[str]
    description: str
    handler: Callable[[ChatSession, str], bool]  # retorna True para sair do loop


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: list[Command] = []

    def register(self, cmd: Command) -> None:
        self._commands.append(cmd)

    def dispatch(self, session: ChatSession, raw_input: str) -> tuple[bool, bool]:
        """
        Retorna (handled, should_exit).
        handled=True  → era um comando, não enviar como mensagem
        should_exit=True → encerrar o loop REPL
        """
        lower = raw_input.lower()
        for cmd in self._commands:
            triggers = [cmd.name] + cmd.aliases
            for trigger in triggers:
                if lower == trigger or lower.startswith(trigger + " "):
                    args = raw_input[len(trigger):].strip()
                    should_exit = cmd.handler(session, args)
                    return True, bool(should_exit)
        return False, False


# --- Handlers ---

def handle_help(session: ChatSession, args: str) -> bool:
    print_help()
    return False


def handle_exit(session: ChatSession, args: str) -> bool:
    console.print("[dim]encerrado[/dim]")
    return True


def handle_clear(session: ChatSession, args: str) -> bool:
    session.clear_attachments()
    return False


def handle_arquivo(session: ChatSession, args: str) -> bool:
    if not args:
        console.print("  [red]Uso: /arquivo <caminho>[/red]")
        return False
    path = args.strip()
    if not os.path.exists(path):
        console.print(f"  [red]Não encontrado: {path}[/red]")
        return False
    try:
        session.add_attachment(path)
    except Exception as e:
        console.print(f"  [red]Erro ao ler: {e}[/red]")
    return False


# --- Factory ---

def build_default_registry(session: ChatSession) -> CommandRegistry:
    registry = CommandRegistry()
    registry.register(Command(
        name="/help",
        aliases=[],
        description="Mostra lista de comandos",
        handler=handle_help,
    ))
    registry.register(Command(
        name="/sair",
        aliases=["/exit", "/quit"],
        description="Encerra o chat",
        handler=handle_exit,
    ))
    registry.register(Command(
        name="/limpar",
        aliases=["limpar"],
        description="Remove todos os anexos pendentes",
        handler=handle_clear,
    ))
    registry.register(Command(
        name="/arquivo",
        aliases=["arquivo:"],
        description="Anexa um arquivo ou imagem",
        handler=handle_arquivo,
    ))
    return registry
