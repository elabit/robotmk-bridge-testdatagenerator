"""Core test data generator module.

Reads the bundled handlers.yaml (or ROBOTMK_HANDLERS_YAML env override) and
provides a unified API for generating test result files for different handler types.
"""

import os
from importlib import resources
from pathlib import Path
from typing import Dict, List

import yaml


def _open_handlers_yaml():
    """Return an open file-like object for handlers.yaml.

    Checks ROBOTMK_HANDLERS_YAML env var first; falls back to the file
    bundled inside the package via importlib.resources.
    """
    env_override = os.environ.get("ROBOTMK_HANDLERS_YAML")
    if env_override:
        return open(env_override, "r", encoding="utf-8")
    ref = resources.files("robotmk_bridge_testdatagenerator").joinpath("handlers.yaml")
    return ref.open("r", encoding="utf-8")


def load_handlers_registry() -> List[Dict]:
    """Load handler definitions from handlers.yaml.

    Returns:
        List of handler definitions, each with 'name', 'title', 'class_import',
        'result_ext', and optional 'handler_params'.
    """
    with _open_handlers_yaml() as f:
        data = yaml.safe_load(f)

    if not data or "handlers" not in data:
        raise ValueError("handlers.yaml must contain a 'handlers' key")

    return data["handlers"]


def get_supported_handlers() -> List[str]:
    """Return list of handler names from handlers.yaml.

    Returns:
        List of handler names (e.g., ['junit', 'gatling', 'zaproxy'])
    """
    return [h["name"] for h in load_handlers_registry()]


def generate_handler_file(
    handler_name: str,
    output_path: Path,
    test_status: str = "passed",
    **kwargs
) -> Path:
    """Generate a test result file for the specified handler.

    Args:
        handler_name: Name of handler (e.g., 'junit', 'zaproxy', 'gatling')
        output_path: Path where the result file should be written
        test_status: Test outcome - 'passed', 'failed', or 'mixed' (default: 'passed')
        **kwargs: Handler-specific parameters (e.g., num_tests, duration_ms)

    Returns:
        Path to the generated file

    Raises:
        ValueError: If handler_name is not supported
        RuntimeError: If handler generator fails
    """
    handlers = load_handlers_registry()
    handler_def = next((h for h in handlers if h["name"] == handler_name), None)

    if not handler_def:
        supported = [h["name"] for h in handlers]
        raise ValueError(
            f"Handler '{handler_name}' not found in handlers.yaml. "
            f"Supported handlers: {', '.join(supported)}"
        )

    handler_to_module = {
        "zaproxy": "zap",
        "junit": "junit",
        "gatling": "gatling",
    }

    module_name = handler_to_module.get(handler_name, handler_name)

    try:
        from . import handlers as handler_module
        generator_name = f"{module_name}_generator"
        generator = getattr(handler_module, generator_name)
    except (ImportError, AttributeError) as e:
        raise RuntimeError(
            f"Could not import generator for '{handler_name}'. "
            f"Expected module: robotmk_bridge_testdatagenerator.handlers.{generator_name}"
        ) from e

    try:
        generator.generate(
            output_path=output_path,
            test_status=test_status,
            handler_def=handler_def,
            **kwargs
        )
    except Exception as e:
        raise RuntimeError(
            f"Failed to generate test data for handler '{handler_name}': {e}"
        ) from e

    try:
        if output_path.exists():
            output_path.chmod(0o644)
    except Exception:
        pass

    return output_path


def generate_all_handler_files(
    output_dir: Path,
    test_status: str = "passed",
    filename_pattern: str = "{handler}.{ext}"
) -> Dict[str, Path]:
    """Generate test result files for all supported handlers.

    Args:
        output_dir: Directory where files should be written
        test_status: Test outcome - 'passed', 'failed', or 'mixed'
        filename_pattern: Pattern for output filenames (variables: {handler}, {ext})

    Returns:
        Dict mapping handler name to generated file path

    Example:
        >>> files = generate_all_handler_files(Path("tests/e2e/data"))
        >>> files
        {'junit': Path('tests/e2e/data/junit.xml'),
         'gatling': Path('tests/e2e/data/gatling.log'),
         'zaproxy': Path('tests/e2e/data/zaproxy.xml')}
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        output_dir.chmod(0o755)
    except Exception:
        pass

    handlers = load_handlers_registry()
    generated_files = {}

    for handler_def in handlers:
        handler_name = handler_def["name"]
        result_ext = handler_def.get("result_ext", "txt")
        filename = filename_pattern.format(handler=handler_name, ext=result_ext)
        output_path = output_dir / filename
        generate_handler_file(
            handler_name=handler_name,
            output_path=output_path,
            test_status=test_status
        )
        generated_files[handler_name] = output_path

    return generated_files
