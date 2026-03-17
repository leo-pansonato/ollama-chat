import os

from . import ollama_client
from .attachments import build_message, load_attachment, size_str, is_image
from .commands import CommandRegistry, build_default_registry
from .ui import (
    console,
    choose_model,
    input_prompt,
    print_response,
    print_separator,
    print_stats,
    print_user_message,
    print_welcome,
)


class ChatSession:
    def __init__(self) -> None:
        self.model: str = choose_model()
        self.max_ctx: int = ollama_client.get_max_ctx(self.model)
        self.messages: list[dict] = []
        self.attachments: list[dict] = []
        self.commands: CommandRegistry = build_default_registry(self)

    def run(self) -> None:
        print_welcome(self.model, self.max_ctx, os.getcwd())
        console.print("[dim]comandos: /help | /sair | /arquivo <caminho> | /limpar[/dim]\n")

        while True:
            try:
                print_separator()
                user_input = input_prompt(len(self.attachments))
                print("\033[2A\033[J", end="", flush=True)
            except (EOFError, KeyboardInterrupt):
                console.print("\n[dim]encerrado[/dim]")
                break

            if not user_input:
                continue

            handled, should_exit = self.commands.dispatch(self, user_input)
            if should_exit:
                break
            if handled:
                continue

            self.send_message(user_input)

    def send_message(self, text: str) -> None:
        print_user_message(text)

        msg = build_message(text, self.attachments)
        self.attachments.clear()
        self.messages.append(msg)

        try:
            response, stats = ollama_client.stream_response(
                self.model, self.messages, self.max_ctx, console
            )
        except Exception as e:
            self.messages.pop()
            console.print(f"[red]Erro: {e}[/red]\n")
            return

        if response:
            self.messages.append({"role": "assistant", "content": response})
            print_response(response)
            print_stats(stats)
        else:
            console.print("[red]sem resposta[/red]")
        console.print()

    def add_attachment(self, path: str) -> None:
        att = load_attachment(path)
        self.attachments.append(att)
        name = os.path.basename(path)
        if is_image(path):
            console.print(f"[green]+ imagem[/green] {name} ({size_str(path)})")
        else:
            console.print(f"[green]+ arquivo[/green] {name} ({size_str(path)})")

    def clear_attachments(self) -> None:
        self.attachments.clear()
        console.print("  [dim]anexos removidos[/dim]\n")
