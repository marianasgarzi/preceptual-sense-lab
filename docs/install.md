# Installation and Troubleshooting Guide

This guide is written for students with little or no coding experience.
Follow sections in order and do not skip steps.

## 1) What You Need

- A computer with internet access
- VS Code (recommended)
- A terminal:
  - macOS: Terminal
  - Linux: terminal emulator
  - Windows: PowerShell or Git Bash

You do not need to install Python manually; `uv` will manage it.

## 2) Get Project Files

Choose one method.

### Method A: Git Clone

```sh
git clone https://github.com/marianasgarzi/preceptual-sense-lab.git
cd preceptual-sense-lab
```

### Method B: GitHub ZIP Download

1. Open repo page on GitHub.
2. Click `Code` -> `Download ZIP`.
3. Extract ZIP.
4. Open the extracted `preceptual-sense-lab` folder in VS Code.
5. Open terminal in that folder.

Folder check:
- You are in the correct folder if `app.py` is visible with `ls` (`dir` in PowerShell).

## 3) Install `uv`

Install from official guide:
https://docs.astral.sh/uv/getting-started/installation/

After installing, close terminal and open a new terminal window.

Verify:

```sh
uv --version
```

## 4) Install Dependencies and Run

Run these commands exactly:

```sh
uv python install 3.11
uv sync
uv run streamlit run app.py
```

Open `http://localhost:8501` in your browser.

## 5) Windows Command Examples

### PowerShell

```powershell
uv python install 3.11
uv sync
uv run streamlit run app.py
```

### Git Bash

```bash
uv python install 3.11
uv sync
uv run streamlit run app.py
```

If Git Bash is missing, install Git for Windows:
https://gitforwindows.org

## 6) Daily Commands During Assignment

Run app:

```sh
uv run streamlit run app.py
```

Run tests:

```sh
uv run pytest
```

## 7) Troubleshooting

## `uv` command not found

Fix:
1. Install `uv` from official docs.
2. Restart terminal.
3. Run `uv --version`.

## `git` command not found (Windows)

Fix:
1. Install Git for Windows.
2. Restart terminal.
3. Run `git --version`.

## Streamlit starts, but app page is blank or crashes

Fix:
1. Read terminal traceback.
2. Hard refresh browser (`Ctrl+Shift+R` or `Cmd+Shift+R`).
3. Restart Streamlit command.

## Import/dependency error (`ModuleNotFoundError`)

Fix:
1. Run `uv sync` again.
2. If still failing, delete `.venv` and reinstall.

macOS/Linux/Git Bash:

```bash
rm -rf .venv
uv sync
```

PowerShell:

```powershell
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
uv sync
```

## No audio output

Fix:
1. Check system output device.
2. Check browser tab mute state.
3. Try another browser.
4. Lower/raise amplitude in app and test again.

## ZIP users: commands fail due to wrong folder

Fix:
1. Run `pwd` (PowerShell: `Get-Location`).
2. Move to folder containing `app.py`.
3. Re-run setup commands.

## 8) Help Request Template

Include this when asking for help:

- OS and terminal type
- exact command run
- full terminal error output
- whether you used Git clone or ZIP download
