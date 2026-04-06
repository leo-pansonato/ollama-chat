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
        self.model: str = ""
        self.max_ctx: int = 0
        self.used_ctx: int = 0
        self.messages: list[dict] = []
        self.attachments: list[dict] = []
        self.commands: CommandRegistry = build_default_registry()
        print_welcome()
        choose_model(self)

    def run(self) -> None:

        while True:
            try:
                print_separator()
                user_input = input_prompt(len(self.attachments))
                print("\033[2A\033[J", end="", flush=True)
            except (EOFError, KeyboardInterrupt):
                console.print("\n[dim]Sessão encerrada[/dim]")
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
            self.used_ctx = stats.get("prompt_eval_count", 0) + stats.get("eval_count", 0)
            print_response(response)
            print_stats(stats, self.used_ctx, self.max_ctx)
        else:
            console.print("[red]sem resposta[/red]")

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
