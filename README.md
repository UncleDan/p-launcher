# P-Launcher

> Inspired by [WinPenPack](https://www.winpenpack.com) and its X-Launcher concept — reimagined in a minimalistic and focused way.

A minimal Windows utility that launches any executable as a fully detached process — no `cmd` window, no console flash — configured entirely through a `.ini` file with the same name as the executable.

## How It Works

Place `p-launcher.exe` and `p-launcher.ini` in the same folder. When run, the launcher reads the ini, resolves any placeholders in the command, then spawns the target process as a fully independent child (equivalent to `start "" "app.exe"`) and exits immediately.

You can duplicate and rename the exe freely. Each copy automatically reads its own matching ini file:

```
📁 my-launchers\
├── thunderbird-work.exe        ← copy 1
├── thunderbird-work.ini
├── thunderbird-personal.exe    ← copy 2
└── thunderbird-personal.ini
```

## INI File Structure

```ini
[launcher]
command=<the command to run, with optional [placeholders]>
working_dir=<working directory for the child process>   ; optional
delay=0                                                 ; optional, seconds
delay_exit=0                                            ; optional, seconds
myvar=some value                                        ; any custom parameter
```

### Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `command` | Yes | Full command line to execute. Supports `[placeholder]` substitution. |
| `working_dir` | No | Working directory for the child process (equivalent to `CD` in DOS). Defaults to the launcher's own folder. |
| `delay` | No | Seconds to wait **before** launching. Useful to stagger simultaneous launches. Default: `0`. |
| `delay_exit` | No | Seconds to wait **after** launching before the launcher exits. Default: `0`. |

Any additional key defined in `[launcher]` becomes a custom parameter available as a `[placeholder]` in the command.

### Built-in Parameters

These are computed automatically and **cannot** be defined in the ini:

| Placeholder | Value |
|-------------|-------|
| `[absolute_path]` | Absolute path of the folder containing the launcher exe. Enables fully portable setups. |

## Placeholder Substitution

Any `[key]` token in the `command` or `working_dir` values is replaced with the corresponding ini parameter at launch time. Keys are case-insensitive.

**Example:**

```ini
[launcher]
command="C:\Apps\mytool.exe" --profile [profile] --lang [lang]
profile=admin
lang=en
```

Resolved command:

```
"C:\Apps\mytool.exe" --profile admin --lang en
```

## Portable Setup with `[absolute_path]`

Using `[absolute_path]` makes the entire setup relocatable — move the folder to any machine or drive without editing the ini:

```ini
[launcher]
command="[absolute_path]\app\myapp.exe" --data "[absolute_path]\data"
working_dir=[absolute_path]\app
```

## Example: Two Thunderbird Instances Simultaneously

Thunderbird requires the `--no-remote` flag to allow multiple simultaneous instances with different profiles.

**thunderbird-work.ini**
```ini
[launcher]
command="[absolute_path]\thunderbird\thunderbird.exe" --profile "[absolute_path]\profiles\Work" --no-remote
working_dir=[absolute_path]\thunderbird
```

**thunderbird-personal.ini**
```ini
[launcher]
command="[absolute_path]\thunderbird\thunderbird.exe" --profile "[absolute_path]\profiles\Personal" --no-remote
working_dir=[absolute_path]\thunderbird
```

Both launchers share the same exe (renamed twice). Clicking either one opens a fully independent Thunderbird window and the launcher disappears instantly.

## Compilation

Requires Python 3.10+ and [PyInstaller](https://pyinstaller.org):

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole p-launcher.py
```

The resulting `dist\p-launcher.exe` is a single self-contained binary with no external dependencies.

> **Note:** The `--noconsole` flag suppresses any console window or flash on startup. Omit it only if you need to see error messages during development.

## Error Handling

The launcher exits with a descriptive error message if:

- The ini file is not found next to the executable
- The `[launcher]` section or `command` key is missing
- A `[placeholder]` in the command has no matching parameter
- A reserved parameter name (`absolute_path`) is defined in the ini
- `working_dir` points to a path that does not exist
- `delay` or `delay_exit` is not a valid non-negative number
- The target process fails to start

## Requirements

- Windows only (uses Windows-specific process creation flags)
- Python 3.10+ (for compilation)
- No runtime dependencies beyond the Python standard library
