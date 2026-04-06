import os
import sys
from io import StringIO

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import ANSI
from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from chat import ollama_client

__version__ = "1.0.0"

PASTEL_THEME = Theme({
    "markdown.h1": "bold #8cacff",
    "markdown.h2": "bold #a0b8e0",
    "markdown.h3": "bold #b0c4d8",
    "markdown.code": "#c4b28a on #1e1e1e",
    "markdown.code_inline": "#c4b28a on #1e1e1e",
    "markdown.link": "#8cacff",
    "markdown.item.bullet": "#7a9cc6",
    "markdown.block_quote": "italic #888888",
})

console = Console(theme=PASTEL_THEME)

_history_path = os.path.join(os.path.expanduser("~"), ".ollama-chat-history")
_prompt_session = None


def _get_prompt_session() -> PromptSession:
    global _prompt_session
    if _prompt_session is None:
        _prompt_session = PromptSession(history=FileHistory(_history_path))
    return _prompt_session

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}


def _render_rich_to_ansi(markup: str) -> str:
    buf = StringIO()
    temp = Console(file=buf, theme=PASTEL_THEME, force_terminal=True, no_color=False)
    temp.print(markup, end="")
    return buf.getvalue()


def build_stream_grid(spinner: Spinner, partial_text: str, tip: Text) -> Table:
    grid = Table.grid()
    grid.add_row(spinner)
    if partial_text:
        lines = partial_text.splitlines()
        if len(lines) > 6:
            lines = lines[-6:]
        grid.add_row(Padding(Text("  " + "\n  ".join(lines), style="dim"), (1, 0)))
    grid.add_row(tip)
    return grid


def print_welcome() -> None:
    console.print()
    console.print(Panel(
        "[bold cyan]Ollama Chat[/bold cyan]  "
        f"[dim]v{__version__}[/dim]\n\n"
        "[dim]Chat interativo com modelos locais Ollama[/dim]\n"
        "[dim]Use /help para ver todos os comandos[/dim]",
        border_style="cyan",
        padding=(1, 4),
        expand=True,
    ))
    console.print()


def print_help(commands=None) -> None:
    console.print("[bold cyan]Comandos e Funções:[/bold cyan]")
    if commands:
        for cmd in commands:
            label = ", ".join([cmd.name] + cmd.aliases)
            console.print(f"  [green]{label.ljust(40)}[/green] [dim]{cmd.description}[/dim]")
    console.print()


def print_stats(stats: dict, used: int = 0, total: int = 0) -> None:
    dur = stats.get("total_duration", 0) / 1e9
    ev = stats.get("eval_duration", 0) / 1e9
    tps = stats.get("eval_count", 0) / ev if ev else 0
    left = Text(f"{tps:.1f} t/s · {dur:.1f}s · {used:,}/{total:,}", style="dim")
    console.print(left)


def print_response(response: str) -> None:
    console.print(Markdown(response))
    console.print("[dim]/copiar[/dim]")
    console.print()


def print_separator() -> None:
    console.rule(style="#444444")


def input_prompt(n_attachments: int) -> str:
    if n_attachments:
        n = n_attachments
        markup = f"[dim]({n} anexo{'s' if n > 1 else ''})[/dim] [bold cyan]>[/bold cyan] "
    else:
        markup = "  [bold cyan]>[/bold cyan] "
    ansi_prefix = _render_rich_to_ansi(markup)
    return _get_prompt_session().prompt(ANSI(ansi_prefix)).strip()


def print_user_message(text: str) -> None:
    line = f"  > {text}"
    t = Text(line.ljust(console.width), style="bold on #3a3a3a")
    t.stylize("bold cyan", 2, 3)
    console.print(Padding(t, (1, 0)))


def choose_model(session) -> str:
    from . import ollama_client
    import msvcrt
    from rich.live import Live

    try:
      models = ollama_client.list_models()
    except ConnectionError:
      console.print(
            "\n[bold red]Erro:[/bold red] Não foi possível conectar ao Ollama.\n"
            "Verifique se o Ollama está instalado e em execução.\n"
            "Download: [link=https://ollama.com/download]https://ollama.com/download[/link]\n"
      )
      sys.exit(1)

    if not models:
      console.print(
            "\n[bold red]Erro:[/bold red] Nenhum modelo instalado no Ollama.\n"
            "Instale um modelo com: [bold cyan]ollama pull <modelo>[/bold cyan]\n"
            "Exemplo: [dim]ollama pull gemma3:4b[/dim]\n"
      )
      sys.exit(1)

    idx = 0
    with Live(console=console, auto_refresh=False, transient=True) as live:
        while True:
            lines = [
                "[bold cyan]Selecione um modelo (Use as setas ↑ ↓ e Enter):[/bold cyan]",
                "[dim italic]Os modelos só aparecem se forem instalados através do 'ollama pull'.[/dim italic]\n",
            ]
            for i, m in enumerate(models):
                if i == idx:
                    lines.append(f"  [bold green]> {m}[/bold green]")
                else:
                    lines.append(f"    [dim]{m}[/dim]")
            live.update(Text.from_markup("\n".join(lines)), refresh=True)

            c = msvcrt.getch()
            if c in (b'\xe0', b'\x00'):
                c2 = msvcrt.getch()
                if c2 == b'H':
                    idx = max(0, idx - 1)
                elif c2 == b'P':
                    idx = min(len(models) - 1, idx + 1)
            elif c == b'\r':
                break
            elif c == b'\x03':
                raise KeyboardInterrupt

    new_model = models[idx]
    session.model = new_model
    session.max_ctx = ollama_client.get_max_ctx(new_model)
    console.print(f"[bold green]✓ Modelo ativo:[/bold green] [cyan]{new_model}[/cyan] [dim]({session.max_ctx:,} tokens)[/dim]\n")

    return new_model
