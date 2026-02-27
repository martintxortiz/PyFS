"""PyFS entry point — discover nodes, then run the executive lifecycle."""

from __future__ import annotations

import pyfs.nodes  # noqa: F401 — triggers node auto-discovery before executive init
from pyfs.core.fs_executive import FSExecutive


def main() -> None:
    exec_ = FSExecutive()
    exec_.start()


if __name__ == "__main__":
    main()