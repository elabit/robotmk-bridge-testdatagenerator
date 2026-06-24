# robotmk-bridge-testdatagenerator

Generates synthetic test result files for [robotmk-bridge-plugin](https://github.com/elabit/robotmk-bridge-plugin) testing.
Produces realistic, randomized output in the formats consumed by the bridge plugin's handlers.

## Supported Formats

| Handler | Format | Extension | Default count |
|---|---|---|---|
| `junit` | JUnit XML | `.xml` | 5 test cases |
| `zaproxy` | OWASP ZAP XML v2.7.0 | `.xml` | 3 sites |
| `gatling` | Gatling simulation.log v2.0 | `.log` | 10 requests |

---

## Quick Start with uv

[uv](https://docs.astral.sh/uv/) is the recommended way to run this tool.

### Run without installing (one-liner)

```bash
uvx --from robotmk-bridge-testdatagenerator rmkb-testgen --list
uvx --from robotmk-bridge-testdatagenerator rmkb-testgen --output-dir /tmp/test-data
```

### Install as a persistent tool

```bash
uv tool install robotmk-bridge-testdatagenerator
rmkb-testgen --help

# Upgrade later
uv tool upgrade robotmk-bridge-testdatagenerator

# Uninstall
uv tool uninstall robotmk-bridge-testdatagenerator
```

---

## Development Setup with uv

```bash
git clone https://github.com/elabit/robotmk-bridge-testdatagenerator.git
cd robotmk-bridge-testdatagenerator

# Create venv + install package + dev deps in one step
uv sync --group dev

# Run the CLI from source
uv run rmkb-testgen --list
uv run rmkb-testgen --output-dir /tmp/test-data --verbose

# Build distributable artifacts
uv build
# -> dist/robotmk_bridge_testdatagenerator-*.whl
# -> dist/robotmk_bridge_testdatagenerator-*.tar.gz

# Editable install (changes take effect immediately, no reinstall needed)
uv pip install -e .

# Install local wheel into another project
uv add /path/to/dist/robotmk_bridge_testdatagenerator-0.2.0-py3-none-any.whl
```

---

## CLI Reference

```text
rmkb-testgen [options]
python -m robotmk_bridge_testdatagenerator [options]
```

| Flag | Short | Default | Description |
|---|---|---|---|
| `--output-dir PATH` | `-o` | `tests/e2e/data` | Output directory |
| `--status` | `-s` | `passed` | `passed` / `failed` / `mixed` |
| `--handlers HANDLER...` | `-H` | all | Generate specific handlers only |
| `--count [HANDLER=]N` | `-n` | handler default | Item count (repeatable) |
| `--pattern` | `-p` | `{handler}.{ext}` | Filename pattern |
| `--continuous` | `-c` | off | Regenerate on interval |
| `--interval SECS` | `-i` | `5.0` | Seconds between continuous runs |
| `--list` | `-l` | — | List available handlers and exit |
| `--verbose` | `-v` | off | Verbose output |

### Examples

```bash
# List available handlers
rmkb-testgen --list

# Generate all with defaults
rmkb-testgen --output-dir /tmp/test-data

# Specific status
rmkb-testgen --status failed --output-dir /tmp/test-data

# Specific handlers only
rmkb-testgen --handlers junit gatling --output-dir /tmp/test-data

# Control item count — all handlers
rmkb-testgen --count 20 --output-dir /tmp/test-data

# Per-handler counts
rmkb-testgen -n junit=20 -n gatling=50 -n zaproxy=2 --output-dir /tmp/test-data

# Continuous regeneration (Ctrl+C to stop)
rmkb-testgen --continuous --interval 5 --output-dir /tmp/test-data

# Custom handlers.yaml
ROBOTMK_HANDLERS_YAML=/path/to/handlers.yaml rmkb-testgen --output-dir /tmp/test-data
```

---

## Library Usage

```python
from robotmk_bridge_testdatagenerator import (
    generate_all_handler_files,
    generate_handler_file,
    get_supported_handlers,
)
from pathlib import Path

# Generate all handlers
files = generate_all_handler_files(
    output_dir=Path("/tmp/test-data"),
    test_status="mixed",
    handler_kwargs={
        "junit":   {"num_tests": 20},
        "gatling": {"num_requests": 50},
        "zaproxy": {"num_sites": 2},
    },
)

# Generate a single handler
generate_handler_file(
    handler_name="junit",
    output_path=Path("/tmp/result.xml"),
    test_status="failed",
    num_tests=10,
)

# List available handlers
handlers = get_supported_handlers()  # ['junit', 'gatling', 'zaproxy']
```

---

## Test Status Semantics

| Status | JUnit | ZAP | Gatling |
|---|---|---|---|
| `passed` | All pass | Low-risk alerts only | All requests OK |
| `failed` | All fail | High-risk alerts | All requests KO |
| `mixed` | Every 3rd fails | Low + medium risk | Every 4th KO |

---

## handlers.yaml

The handler registry is bundled with the package. Override for custom handler definitions:

```bash
ROBOTMK_HANDLERS_YAML=/path/to/your/handlers.yaml rmkb-testgen --output-dir /tmp/test-data
```

---

## Installation without uv

```bash
pip install robotmk-bridge-testdatagenerator
rmkb-testgen --help
```

---

## License

GPLv2, see [LICENSE](LICENSE) for details.
