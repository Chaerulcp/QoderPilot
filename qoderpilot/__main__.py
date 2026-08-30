"""Allow QoderPilot to run with ``python -m qoderpilot``."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())

