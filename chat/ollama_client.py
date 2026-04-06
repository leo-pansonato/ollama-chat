import msvcrt

import ollama
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from .ui import build_stream_grid


def list_models() -> list[str]:
    try:
        res = ollama.list()
        models_raw = res.get("models", []) if isinstance(res, dict) else getattr(res, "models", [])
        models = []
        for m in models_raw:
            if isinstance(m, dict):
                models.append(m.get("model", m.get("name", "")))
            else:
                models.append(getattr(m, "model", getattr(m, "name", "")))
        return [m for m in models if m]
    except ConnectionError:
        raise
    except Exception:
        return []


def get_max_ctx(model: str) -> int:
    try:
        info = ollama.show(model)
        for k, v in (getattr(info, "modelinfo", None) or {}).items():
            if "context_length" in k:
                return int(v)
        for line in (getattr(info, "parameters", "") or "").splitlines():
            parts = line.split()
            if parts and parts[0] == "num_ctx":
                return int(parts[1])
    except Exception:
        pass
    return 131072


def stream_response(
    model: str,
    messages: list[dict],
    max_ctx: int,
    console: Console,
) -> tuple[str, dict]:
    full = ""
    stats = {}
    spinner_analisando = Spinner("dots", text="Analisando...", style="#c89b3c")
    spinner_gerando = Spinner("dots", text="Gerando...", style="#c89b3c")
    tip = Text("esc para interromper", style="dim italic")

    initial_grid = build_stream_grid(spinner_analisando, "", tip)

    with Live(initial_grid, console=console, refresh_per_second=12, transient=True) as live:
        for part in ollama.chat(model=model, messages=messages, stream=True, options={"num_ctx": max_ctx}):
            while msvcrt.kbhit():
                if msvcrt.getch() == b'\x1b':
                    return full, stats

            token = getattr(part, "message", None)
            if token and token.content:
                full += token.content

            if getattr(part, "done", False):
                stats = {k: getattr(part, k, 0) or 0 for k in
                         ("prompt_eval_count", "eval_count",
                          "total_duration", "eval_duration")}

            live.update(build_stream_grid(spinner_gerando, full, tip))

    return full, stats
