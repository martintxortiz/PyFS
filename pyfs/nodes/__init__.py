"""Node auto-discovery — importing this package registers all FSNode subclasses."""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path


def _discover_nodes() -> None:
    """Import every module in the pyfs.nodes package to trigger metaclass registration."""
    package_dir  = Path(__file__).parent
    package_name = __name__

    for module_info in pkgutil.iter_modules([str(package_dir)]):
        importlib.import_module(f"{package_name}.{module_info.name}")


_discover_nodes()
