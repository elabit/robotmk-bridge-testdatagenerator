"""CLI entry point for the test data generator.

Usage:
    rmkb-testgen [options]
    python -m robotmk_bridge_testdatagenerator [options]

Examples:
    # Generate all handler test files in default location
    rmkb-testgen

    # Generate in a specific directory
    rmkb-testgen --output-dir /tmp/test-data

    # Generate with failed test status
    rmkb-testgen --status failed

    # Generate only specific handlers
    rmkb-testgen --handlers junit gatling

    # Continuous mode: regenerate every 5 seconds
    rmkb-testgen --continuous --interval 5

    # Control item counts (all handlers)
    rmkb-testgen --count 20

    # Per-handler counts
    rmkb-testgen -n junit=20 -n gatling=50 -n zaproxy=2

    # Use a custom handlers.yaml
    ROBOTMK_HANDLERS_YAML=/path/to/handlers.yaml rmkb-testgen
"""

import argparse
import signal
import sys
import time
from pathlib import Path

from .generator import (
    HANDLER_COUNT_KWARG,
    generate_all_handler_files,
    generate_handler_file,
    get_supported_handlers,
)

_shutdown_requested = False


def signal_handler(signum, frame):
    global _shutdown_requested
    _shutdown_requested = True
    print("\n\nShutdown requested. Stopping after current generation...")


def _parse_counts(count_args) -> dict:
    """Parse --count values into a {handler: {kwarg: n}} dict.

    Accepts:
      --count 10          → apply to all handlers
      --count junit=10    → apply only to junit
    """
    if not count_args:
        return {}

    all_handlers = get_supported_handlers()
    result = {}

    for entry in count_args:
        entry = entry.strip()
        if "=" in entry:
            handler, raw = entry.split("=", 1)
            handler = handler.strip()
            if handler not in all_handlers:
                print(
                    f"Error: Unknown handler '{handler}' in --count. "
                    f"Known: {', '.join(all_handlers)}",
                    file=sys.stderr,
                )
                sys.exit(1)
            targets = [handler]
        else:
            raw = entry
            targets = all_handlers

        try:
            n = int(raw)
        except ValueError:
            print(f"Error: --count value must be an integer, got: {raw!r}", file=sys.stderr)
            sys.exit(1)
        if n < 1:
            print(f"Error: --count must be >= 1, got {n}", file=sys.stderr)
            sys.exit(1)

        for h in targets:
            kwarg = HANDLER_COUNT_KWARG.get(h)
            if kwarg:
                result.setdefault(h, {})[kwarg] = n

    return result


def generate_files(args):
    """Generate test data files based on arguments."""
    handler_kwargs = _parse_counts(args.count)

    if args.handlers:
        generated_files = {}
        for handler in args.handlers:
            from .generator import load_handlers_registry
            handlers_def = load_handlers_registry()
            handler_def = next(
                (h for h in handlers_def if h["name"] == handler), None
            )
            if not handler_def:
                print(f"Error: Handler '{handler}' not found", file=sys.stderr)
                sys.exit(1)

            result_ext = handler_def.get("result_ext", "txt")
            filename = args.pattern.format(handler=handler, ext=result_ext)
            output_path = args.output_dir / filename
            generate_handler_file(
                handler_name=handler,
                output_path=output_path,
                test_status=args.status,
                **handler_kwargs.get(handler, {}),
            )
            generated_files[handler] = output_path
    else:
        generated_files = generate_all_handler_files(
            output_dir=args.output_dir,
            test_status=args.status,
            filename_pattern=args.pattern,
            handler_kwargs=handler_kwargs,
        )
    return generated_files


def main():
    """CLI entry point for test data generation."""
    parser = argparse.ArgumentParser(
        description="Generate test result files for Robotmk Bridge handlers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate all handlers:
    rmkb-testgen

  Specific output directory:
    rmkb-testgen --output-dir /tmp/test-data

  Failed status:
    rmkb-testgen --status failed

  Specific handlers:
    rmkb-testgen --handlers junit gatling

  Continuous mode (Ctrl+C to stop):
    rmkb-testgen --continuous --interval 5

  Custom handlers.yaml:
    ROBOTMK_HANDLERS_YAML=/path/to/handlers.yaml rmkb-testgen
        """,
    )

    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path("tests/e2e/data"),
        help="Output directory for generated test files (default: tests/e2e/data)",
    )
    parser.add_argument(
        "-s", "--status",
        choices=["passed", "failed", "mixed"],
        default="passed",
        help="Test status for generated files (default: passed)",
    )
    parser.add_argument(
        "-H", "--handlers",
        nargs="+",
        choices=get_supported_handlers(),
        help="Generate only specific handlers (default: all)",
    )
    parser.add_argument(
        "-p", "--pattern",
        default="{handler}.{ext}",
        help="Filename pattern (default: {handler}.{ext})",
    )
    parser.add_argument(
        "-n", "--count",
        action="append",
        metavar="[HANDLER=]N",
        help=(
            "Number of items to generate. "
            "Use N to apply to all handlers, or HANDLER=N for a specific one. "
            "Repeatable: -n junit=20 -n gatling=50. "
            "Maps to: junit→num_tests, zaproxy→num_sites (max 3), gatling→num_requests."
        ),
    )
    parser.add_argument(
        "-c", "--continuous",
        action="store_true",
        help="Continuous mode: regenerate files at regular intervals",
    )
    parser.add_argument(
        "-i", "--interval",
        type=float,
        default=5.0,
        help="Interval in seconds between generations in continuous mode (default: 5)",
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List supported handlers and exit",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    if args.list:
        print("Supported handlers:")
        for handler in get_supported_handlers():
            print(f"  - {handler}")
        return 0

    if args.interval <= 0:
        print("Error: Interval must be greater than 0", file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if args.verbose:
        print(f"Output directory: {args.output_dir.absolute()}")
        print(f"Test status: {args.status}")
        print(f"Filename pattern: {args.pattern}")
        if args.continuous:
            print(f"Continuous mode: regenerating every {args.interval}s")
            print("Press Ctrl+C to stop\n")

    try:
        if args.continuous:
            generation_count = 0
            while not _shutdown_requested:
                generation_count += 1
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                if args.verbose:
                    print(f"[{timestamp}] Generation #{generation_count}")
                generated_files = generate_files(args)
                if generation_count == 1 or args.verbose:
                    print(f"Generated {len(generated_files)} test file(s):")
                    for handler, path in generated_files.items():
                        size = path.stat().st_size
                        print(f"  ✓ {handler:12s} → {path.name:20s} ({size:,} bytes)")
                else:
                    print(f"[{timestamp}] Generation #{generation_count}: "
                          f"{len(generated_files)} files updated")
                if not _shutdown_requested:
                    if args.verbose:
                        print(f"Waiting {args.interval}s until next generation...\n")
                    time.sleep(args.interval)
            print(f"\nStopped after {generation_count} generation(s)")
        else:
            generated_files = generate_files(args)
            print(f"Generated {len(generated_files)} test file(s):")
            for handler, path in generated_files.items():
                size = path.stat().st_size
                print(f"  ✓ {handler:12s} → {path.name:20s} ({size:,} bytes)")
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
