"""Root-level convenience shim.

The canonical package lives in src/robotmk_bridge_testdatagenerator/.
Prefer importing from there directly:

    from robotmk_bridge_testdatagenerator import generate_all_handler_files
"""

from robotmk_bridge_testdatagenerator import (
    generate_all_handler_files,
    generate_handler_file,
    get_supported_handlers,
)

__all__ = [
    "generate_all_handler_files",
    "generate_handler_file",
    "get_supported_handlers",
]
