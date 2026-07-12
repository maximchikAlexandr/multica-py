from __future__ import annotations

import sys

from multica_py.cli.coverage import coverage
from multica_py.cli.doctor import doctor
from multica_py.cli.exec import exec_command
from multica_py.cli.version import show_version


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        print("Usage: multica-py <command> [args...]")
        print("Commands: doctor  — check Python, executable, and auth status")
        print("         version — print SDK and upstream CLI versions")
        print("         coverage — print command coverage against pinned manifest")
        print("         exec    — run multica command with passthrough (diagnostic)")
        return 0

    command = sys.argv[1]

    if command == "doctor":
        return doctor()
    if command == "version":
        return show_version()
    if command == "coverage":
        return coverage()
    if command == "exec":
        return exec_command(sys.argv[2:])
    print(f"Unknown command: {command}", file=sys.stderr)
    print("Available: doctor, version, coverage, exec", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
