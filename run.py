"""PyFS entry point."""

from __future__ import annotations

from pyfs.core.fs_executive import FSExecutive

def main() -> None:
    """Initialise the executive and run until shutdown."""
    exec_ = FSExecutive()
    exec_.start()

if __name__ == "__main__":
    main()