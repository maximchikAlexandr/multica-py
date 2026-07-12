from __future__ import annotations

import os
import sys

from multica_py.cli.exec import exec_command
from multica_py.cli.main import main


def test_cli_bare_exits_zero():
    old_argv = sys.argv
    sys.argv = ["multica-py"]
    try:
        result = main()
        assert result == 0
    finally:
        sys.argv = old_argv


def test_cli_help_flag_exits_zero():
    old_argv = sys.argv
    sys.argv = ["multica-py", "--help"]
    try:
        result = main()
        assert result == 0
    finally:
        sys.argv = old_argv


def test_cli_unknown_command():
    old_argv = sys.argv
    sys.argv = ["multica-py", "unknown"]
    try:
        result = main()
        assert result == 1
    finally:
        sys.argv = old_argv


def test_cli_version_command():
    old_argv = sys.argv
    sys.argv = ["multica-py", "version"]
    try:
        result = main()
        assert result == 0
    finally:
        sys.argv = old_argv


def test_cli_coverage_command():
    old_argv = sys.argv
    sys.argv = ["multica-py", "coverage"]
    try:
        result = main()
        assert result == 0
    finally:
        sys.argv = old_argv


def test_cli_exec_no_args():
    old_argv = sys.argv
    sys.argv = ["multica-py", "exec"]
    try:
        result = main()
        assert result == 1
    finally:
        sys.argv = old_argv


def test_exec_missing_multica():
    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = "/nonexistent"
    try:
        result = exec_command(["-c", "print('x')"])
        assert result == 1
    finally:
        os.environ["PATH"] = old_path
