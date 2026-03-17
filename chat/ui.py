# import os

from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
# from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

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

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}


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


# def print_welcome(model: str, max_ctx: int, cwd: str) -> None:
#     console.print()
#     console.print(Panel(
#         f"[bold green]{model}[/bold green] · [dim]{max_ctx:,} tokens[/dim]\n"
#         f"[dim]{cwd}[/dim]",
#         title="[bold]Ollama Chat[/bold]",
#         border_style="cyan",
#         padding=(1, 4),
#         expand=True,
#     ))
#     console.print()


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
   #  if total:
   #      right = Text(f"tokens {used:,}/{total:,}", style="dim")
   #      grid = Table.grid(expand=True)
   #      grid.add_column()
   #      grid.add_column(justify="right")
   #      grid.add_row(left, right)
   #      console.print(grid)
   #  else:
    console.print(left)


def print_response(response: str) -> None:
    console.print(Markdown(response))
    console.print()


def print_separator() -> None:
    console.rule(style="#444444")


def input_prompt(n_attachments: int) -> str:
    if n_attachments:
        n = n_attachments
        prefix = f"[dim]({n} anexo{'s' if n > 1 else ''})[/dim] [bold cyan]>[/bold cyan] "
    else:
        prefix = "  [bold cyan]>[/bold cyan] "
    return console.input(prefix).strip()


def print_user_message(text: str) -> None:
    line = f"  > {text}"
    t = Text(line.ljust(console.width), style="bold on #3a3a3a")
    t.stylize("bold cyan", 2, 3)
    console.print(Padding(t, (1, 0)))


def choose_model(session) -> str:
    from . import ollama_client
    import msvcrt
    from rich.live import Live

    models = ollama_client.list_models()

    if not models:
        console.print("[yellow]Nenhum modelo encontrado. (Os modelos só aparecem se forem instalados através do 'ollama pull')[/yellow]")
        return console.input("  [cyan]Modelo[/cyan] [dim](gemma3:4b)[/dim]: ").strip() or "gemma3:4b"

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
