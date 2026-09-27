"""Text REPL — test the planner without voice.

Usage: python -m assistant.core.repl
"""

from __future__ import annotations

from assistant.core.planner import Planner


def main() -> None:
    planner = Planner()
    print("Aether text mode. Type a request (or 'quit').\n")
    while True:
        try:
            text = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text or text.lower() in ("quit", "exit"):
            break
        print(f"<<< {planner.handle(text)}\n")


if __name__ == "__main__":
    main()
