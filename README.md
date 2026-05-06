# Codex Session Console

Codex Session Console is a local desktop-style manager for Codex CLI sessions.

It reads the session data stored under `~/.codex` and presents it as a searchable UI where you can continue, classify, rename, delete, restore, and export conversations.

## Screenshots

### Session Overview

![Overview](docs/screenshots/overview.png)

### Deleted Sessions

![Deleted View](docs/screenshots/deleted-view.png)

### Themes

![Cohere Theme](docs/screenshots/theme-cohere.png)

![Lamborghini Theme](docs/screenshots/theme-lamborghini.png)

## What It Does

- Shows existing and deleted Codex sessions in one local interface.
- Groups sessions by project or custom class.
- Lets you set a display title without overwriting the original Codex title.
- Lets you move a session into a custom class without changing its real working directory.
- Opens selected existing sessions from the UI.
- Deletes, permanently deletes, and restores sessions when recovery data exists.
- Exports session lists as `TXT` or `JSON`.
- Creates backups before high-impact write operations.

## Requirements

- macOS or Linux
- `python3`
- `lsof`
- Local Codex data in `~/.codex` if you want to see real sessions

If Codex is not installed, or if no session data exists, the app can still open. The list will simply be empty.

## Installation

### macOS App

Run this from the project directory:

```bash
./tools/install_mac_app.sh
```

This creates:

```text
~/Desktop/Codex Session Console.app
```

You can move the app to Applications or keep it on the Desktop. If the project folder is moved later, run the installer again so the app points to the new path.

### Linux Desktop Launcher

Run:

```bash
./tools/install_linux_app.sh
```

This creates:

- `~/.local/bin/codex-session-console`
- `~/.local/share/applications/codex-session-console.desktop`
- `~/Desktop/Codex Session Console.desktop` when a Desktop folder exists

Some Linux desktops require you to right-click the `.desktop` file and choose an option such as `Allow Launching` before double-clicking works.

## Run Without Installing

Start the UI and open the browser:

```bash
python3 app.py --open
```

Start only the local server:

```bash
python3 app.py
```

Default address:

```text
http://127.0.0.1:8876
```

The project root also includes a macOS launcher:

```text
Launch Codex Session Manager.command
```

Double-click it to start the local service and open the page.

## Interface Guide

### Header

The top-right controls provide:

- Theme switcher
- Refresh
- Quick command menu

### Search

Search matches:

- Session ID
- Custom title
- Codex title
- Project path
- Class name
- First user message

### Projects/Class Panel

The left panel controls the session group shown on the right.

- `全部会话` shows every session.
- `Default Class` represents sessions opened from your home directory.
- Project groups come from the original Codex `cwd`.
- Custom classes are created from the row action menu.
- Empty custom classes are hidden automatically after their last session is moved away.

Custom class data is stored here:

```text
~/.codex/session_manager_classes.json
```

Changing a class does not change the original Codex working directory.

### Session List

The right panel has two status views:

- `可继续`: sessions whose rollout file still exists
- `已删除`: sessions whose current rollout file is missing

Columns:

- `ID`: shortened session ID, with a copy button for the full ID
- `时间`: session creation time; hover to see last opened time
- `标题`: your display title
- `Codex 标题`: original Codex title
- `操作`: row actions

Status dots:

- Green: session can still be continued
- Yellow: deleted and recoverable
- Red: deleted and not recoverable

### Row Actions

Click `···` on an existing session.

Available actions:

- `改标题`: sets the display title shown in the `标题` column
- `改分类`: moves the session into an existing project/class or a new custom class

Display titles are stored in:

```text
~/.codex/session_index.jsonl
```

The original Codex title remains visible in the `Codex 标题` column.

### Batch Actions

In the `可继续` view:

- Select multiple sessions
- Open selected sessions
- Delete selected sessions

In the `已删除` view:

- Select multiple sessions
- Permanently delete selected sessions
- Restore a recoverable session from backups

## Export

Export text:

```bash
python3 app.py export txt
```

Export JSON:

```bash
python3 app.py export json
```

The UI also has `导出 TXT` and `导出 JSON` buttons.

## Data and Backups

The app reads local Codex data from:

- `~/.codex/state_5.sqlite`
- `~/.codex/session_index.jsonl`
- `~/.codex/history.jsonl`
- `~/.codex/sessions/...`

The app writes its own management data to:

- `~/.codex/session_index.jsonl`
- `~/.codex/session_manager_classes.json`
- `~/.codex/session_manager_backups/`

Before write operations such as delete, restore, permanent delete, and title changes, the app creates backups when the underlying Codex data may be affected.

Backup folder:

```text
~/.codex/session_manager_backups/
```

Recoverability depends on whether both metadata and the original rollout file exist in backup data.

## Safety Notes

- Setting a display title does not overwrite the original Codex title.
- Setting a custom class does not modify the original project path.
- Delete operations create backups before changing Codex metadata.
- Permanent delete removes matching data from current Codex records and stored manager backups.
- Damaged or incomplete backup files are skipped instead of blocking current operations.

## Troubleshooting

### The app opens but the page does not change after an update

Restart the local service by closing the app and opening it again. If a browser tab still shows an old page, refresh `http://127.0.0.1:8876`.

### The macOS app does not open

Check:

- `python3` is installed
- The project folder still exists at the path used during installation

Reinstall:

```bash
./tools/install_mac_app.sh
```

### The Linux launcher does not open

Check:

- `python3` is installed
- `lsof` is installed
- `xdg-open` is available if automatic browser opening is expected
- The project folder was not moved after installation

Reinstall:

```bash
./tools/install_linux_app.sh
```

### The page shows no sessions

Common causes:

- Codex has not been used on this machine
- `~/.codex` does not exist
- The current user cannot read the Codex data files

### A deleted session is not recoverable

Single-session restore requires both:

- Session metadata
- The original rollout file

If either part is missing, the session is shown as non-recoverable.

## Project Layout

```text
app.py                  CLI entry point
config.py               Paths, timezone, and theme settings
models.py               Shared data models
codex_store/            Codex data reading, writing, backup, restore, delete logic
web/                    Local HTTP server, HTML, CSS, and browser-side scripts
tools/                  Run and install scripts
macos/                  macOS app template and icon
linux/                  Linux desktop launcher template and icon
docs/screenshots/       README screenshots
```

## Development Checks

Before committing changes, run:

```bash
python3 -m py_compile app.py config.py models.py codex_store/*.py web/*.py web/style_sections/*.py
bash -n tools/run_local_ui.sh
bash -n tools/install_mac_app.sh
bash -n tools/install_linux_app.sh
git diff --check
```
