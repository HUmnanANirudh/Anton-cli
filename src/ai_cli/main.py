"""Anton CLI main entrypoint."""

import sys
from ai_cli.config.settings import get_settings


def main() -> None:
    """Main CLI entry function."""
    settings = get_settings()
    if "--version" in sys.argv:
        print(f"{settings.APP_NAME} v{settings.APP_VERSION}")
        sys.exit(0)

    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}...")
    # Step 1: Scaffolding complete. CLI loop will be wired in upcoming steps.


if __name__ == "__main__":
    main()
