#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# import heartrate
# heartrate.trace(browser=True)

MANAGE_DIR = Path(__file__).resolve().parent


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.web.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    if "--help" in sys.argv:
        load_dotenv(MANAGE_DIR / "config" / ".env")
        return execute_from_command_line(sys.argv)

    if "startapp" in sys.argv:
        if "--notemplate" in sys.argv:
            sys.argv.remove("--notemplate")
        elif "--template" not in sys.argv:
            sys.argv.insert(sys.argv.index("startapp") + 1, "--template")
            sys.argv.insert(
                sys.argv.index("startapp") + 2,
                str(MANAGE_DIR / "config" / "app_template"),
            )

        if "--" in sys.argv[-3] or sys.argv[-2] == "startapp":
            # No folder
            try:
                os.makedirs(MANAGE_DIR / "apps" / sys.argv[-1])
            except FileExistsError:
                pass
            sys.argv.append(str(MANAGE_DIR / "apps" / sys.argv[-1]))

    # elif "runserver" in sys.argv:
        # from apps.MyServer import MyServer
        # return asyncio.run(MyServer.run())

    elif "runbot" in sys.argv:
        from apps.MyBot import MyBot
        return asyncio.run(MyBot.run())

    # elif "runcheck" in sys.argv:
    #     from apps.PeriodicCheck import PeriodicCheck
    #     return asyncio.run(PeriodicCheck.run())

    elif "runapp" in sys.argv:
        from app import run_app
        return asyncio.run(run_app())

    load_dotenv(MANAGE_DIR / "config" / ".env")

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
