from watchfiles import run_process


def main() -> None:
    run_process("worker", target="python -m worker.main", target_type="command")
