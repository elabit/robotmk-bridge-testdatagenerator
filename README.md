# robotmk-bridge-testdatagenerator

Generates synthetic test result files for [robotmk-bridge-plugin](https://github.com/simonmeggle/robotmk-bridge-plugin) testing. Produces realistic, randomized output in the formats consumed by the bridge plugin's handlers.

## Supported Formats

| Handler | Format | Extension |
|---|---|---|
| `junit` | JUnit XML | `.xml` |
| `zaproxy` | OWASP ZAP XML v2.7.0 | `.xml` |
| `gatling` | Gatling simulation.log v2.0 | `.log` |

## Installation

```bash
pip install robotmk-bridge-testdatagenerator
```

## CLI Usage

```bash
# Generate all handlers (output: tests/e2e/data/)
rmkb-testgen

# Specify output directory and status
rmkb-testgen --output-dir /tmp/test-data --status failed

# Generate specific handlers only
rmkb-testgen --handlers junit gatling

# Continuous mode (Ctrl+C to stop)
rmkb-testgen --continuous --interval 5

# List available handlers
rmkb-testgen --list
```

### Options

| Flag | Short | Default | Description |
|---|---|---|---|
| `--output-dir` | `-o` | `tests/e2e/data` | Output directory |
| `--status` | `-s` | `passed` | `passed` / `failed` / `mixed` |
| `--handlers` | `-H` | all | Specific handlers to generate |
| `--pattern` | `-p` | `{handler}.{ext}` | Filename pattern |
| `--continuous` | `-c` | off | Regenerate on interval |
| `--interval` | `-i` | `5.0` | Seconds between generations |
| `--list` | `-l` | — | List handlers and exit |
| `--verbose` | `-v` | off | Verbose output |

## Library Usage

```python
from robotmk_bridge_testdatagenerator import (
    generate_all_handler_files,
    generate_handler_file,
    get_supported_handlers,
)
from pathlib import Path

# Generate all handlers
files = generate_all_handler_files(Path("/tmp/test-data"), test_status="mixed")

# Generate a single handler
generate_handler_file("junit", Path("/tmp/result.xml"), test_status="failed")

# List handlers
handlers = get_supported_handlers()  # ['junit', 'gatling', 'zaproxy']
```

## Custom handlers.yaml

By default the bundled `handlers.yaml` is used. Override via environment variable:

```bash
ROBOTMK_HANDLERS_YAML=/path/to/your/handlers.yaml rmkb-testgen
```

## Test Status Semantics

| Status | JUnit | ZAP | Gatling |
|---|---|---|---|
| `passed` | All pass | Low-risk alerts only | All requests OK |
| `failed` | All fail | High-risk alerts | All requests KO |
| `mixed` | Every 3rd fails | Low + medium risk | Every 4th KO |

## License

MIT
