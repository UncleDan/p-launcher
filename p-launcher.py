"""
P-Launcher - Reads the command from a .ini file with the same name as the executable.
Parameters defined in the [launcher] section are substituted into the command
when enclosed in square brackets, e.g. [profile]

Built-in parameters (computed automatically, cannot be defined in the ini):
    [absolute_path]  absolute path of the folder containing the launcher

Optional parameters in the [launcher] section:
    working_dir=     working directory for the child process
                     (default: launcher folder; supports [absolute_path])
    delay=0          seconds to wait before launching the process
    delay_exit=0     seconds to wait before the launcher itself exits

Compile with:
    pyinstaller --onefile --noconsole p-launcher.py
"""

import subprocess
import os
import sys
import configparser
import re
import shlex
import time


DETACHED  = subprocess.DETACHED_PROCESS
NEW_GROUP = subprocess.CREATE_NEW_PROCESS_GROUP
NO_WINDOW = subprocess.CREATE_NO_WINDOW

# Reserved parameters: computed automatically, cannot be overridden in the ini
RESERVED = {"absolute_path"}


def get_launcher_dir() -> str:
    """Returns the absolute path of the folder containing the launcher (exe or script)."""
    if getattr(sys, "frozen", False):
        base = sys.executable
    else:
        base = os.path.abspath(__file__)
    return os.path.dirname(base)


def get_ini_path() -> str:
    """Returns the path of the .ini file located next to the launcher."""
    if getattr(sys, "frozen", False):
        base = sys.executable
    else:
        base = os.path.abspath(__file__)
    return os.path.splitext(base)[0] + ".ini"


def parse_delay(params: dict, key: str) -> float:
    """Parses a delay value from the ini parameters. Must be a non-negative number."""
    value = params.get(key, "0").strip()
    try:
        seconds = float(value)
        if seconds < 0:
            raise ValueError
        return seconds
    except ValueError:
        sys.exit(f"Error: '{key}' must be a number >= 0 (found: '{value}').")


def read_and_resolve(ini_path: str, launcher_dir: str) -> tuple:
    """
    Reads the ini file, resolves all [placeholder] substitutions in the command,
    and returns the argument list, working directory, and delay values.
    """
    if not os.path.isfile(ini_path):
        sys.exit(f"Error: configuration file not found:\n  {ini_path}")

    cfg = configparser.ConfigParser()
    cfg.read(ini_path, encoding="utf-8")

    if "launcher" not in cfg:
        sys.exit("Error: [launcher] section missing from the ini file.")

    params = dict(cfg["launcher"])

    # Prevent the user from redefining reserved parameters
    for key in RESERVED:
        if key in params:
            sys.exit(f"Error: '{key}' is a reserved parameter and cannot be defined in the ini file.")

    command = params.get("command", "").strip()
    if not command:
        sys.exit("Error: 'command' key is missing or empty in the [launcher] section.")

    delay      = parse_delay(params, "delay")
    delay_exit = parse_delay(params, "delay_exit")

    # Built-in parameters available for substitution
    builtins = {
        "absolute_path": launcher_dir,
    }

    def replace(match):
        key = match.group(1).lower()
        if key in builtins:
            return builtins[key]
        if key in RESERVED:
            sys.exit(f"Error: '{key}' is a reserved parameter and cannot be used in the command.")
        if key not in params:
            sys.exit(f"Error: placeholder '[{key}]' used in command but not defined in the ini file.")
        return params[key]

    # Substitute all [placeholder] tokens in the command string
    command = re.sub(r"\[([^\[\]]+)\]", replace, command)
    args    = shlex.split(command, posix=False)

    # Resolve working_dir — also supports [absolute_path] substitution
    working_dir = params.get("working_dir", "").strip()
    working_dir = re.sub(r"\[([^\[\]]+)\]", replace, working_dir)
    working_dir = working_dir or launcher_dir   # default: launcher folder

    if not os.path.isdir(working_dir):
        sys.exit(f"Error: working_dir not found:\n  {working_dir}")

    return args, working_dir, delay, delay_exit


def main():
    launcher_dir = get_launcher_dir()
    ini_path     = get_ini_path()
    args, working_dir, delay, delay_exit = read_and_resolve(ini_path, launcher_dir)

    if delay > 0:
        time.sleep(delay)

    try:
        # Launch the child process fully detached — no cmd window, no console
        subprocess.Popen(
            args,
            cwd=working_dir,
            close_fds=True,
            creationflags=DETACHED | NEW_GROUP | NO_WINDOW,
        )
    except Exception as e:
        sys.exit(f"Error launching process: {e}")

    if delay_exit > 0:
        time.sleep(delay_exit)


if __name__ == "__main__":
    main()
